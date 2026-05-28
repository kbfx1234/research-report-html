# LingBot-Map 论文与代码研读总结

本文档基于本 repo 中的 `lingbot-map_paper.pdf`、`README.md` 以及 `lingbot_map/`、`benchmark/`、`demo.py` 的当前代码整理。目标是把论文中的方法创新、算法流程、网络框架和代码实现对应起来，并给出它相较于 VGGT 的优缺点。

说明：

- 论文 PDF 已按 `pdf` skill 流程渲染检查，并结合抽取文本阅读。本文中的实验数值来自论文表格，不代表我在本机重新跑通了 benchmark。
- 当前 repo 主要包含推理、demo、benchmark、可视化和预处理代码，没有完整训练代码；训练策略部分主要来自论文。
- VGGT 对比参考了 VGGT repo 的代码和 README，重点比较架构与任务边界。

## 1. 一句话概括

LingBot-Map 可以理解为一个面向视频流的 VGGT-style 3D foundation model：它继承了 DINOv2 ViT、frame/global alternating attention、camera head 和 DPT dense head 这些 VGGT 的强几何先验，但把离线全局注意力改造成了适合长视频在线推理的 Geometric Context Attention (GCA)。GCA 用三类上下文管理历史信息：

- anchor context：用最开始的若干帧建立坐标系和尺度。
- local pose-reference window：保留最近窗口内的完整图像 token，用于局部配准和稠密几何。
- trajectory memory：对更早的帧只保留 camera/register/scale 等少量 special tokens，作为低成本的轨迹记忆。

因此它的核心卖点不是单纯“把 VGGT 改成 causal attention”，而是把 SLAM 中 reference frame、local map、global trajectory memory 的思想变成了一个端到端可学习的 attention/memory 结构，并通过 paged KV cache 做到了长序列实时推理。

## 2. Repo 结构与论文概念对应

| 模块 | 代码位置 | 作用 |
| --- | --- | --- |
| 总模型入口 | `lingbot_map/models/gct_stream.py` | 定义 `GCTStream`，构建 streaming aggregator、causal camera head，并提供 `inference_streaming()`。 |
| 通用模型骨架 | `lingbot_map/models/gct_base.py` | 组织 aggregator -> camera/depth/point/local point heads 的 forward 流程。 |
| Transformer backbone 公共逻辑 | `lingbot_map/aggregator/base.py` | DINOv2 patch embedding、special tokens、2D RoPE、frame attention 与 global attention 交替调度。 |
| GCA/streaming aggregator | `lingbot_map/aggregator/stream.py` | streaming/causal cross-frame attention、scale token、3D RoPE、FlashInfer 或 SDPA KV cache 后端。 |
| Paged KV cache | `lingbot_map/layers/flashinfer_cache.py` | 两流 page 设计：patch pages 可回收，special pages append-only。 |
| Attention block | `lingbot_map/layers/block.py`, `lingbot_map/layers/attention.py` | FlashInfer/SDPA streaming attention、non-keyframe append-rollback 逻辑。 |
| Camera head | `lingbot_map/heads/camera_head.py` | `CameraCausalHead` 从 camera token 迭代 refine 9D pose encoding。 |
| Depth/point head | `lingbot_map/heads/dpt_head.py` | DPT 风格多层 token feature 融合，输出 depth/confidence 或 point/confidence。 |
| Windowed/VO 模式 | `lingbot_map/models/gct_stream_window.py` | 长序列切窗、overlap、keyframe、Sim(3) 对齐与拼接。 |
| Demo | `demo.py` | 载入模型、预处理图像/视频、streaming/windowed 推理、viser 点云可视化。 |
| Benchmark adapter | `benchmark/methods/lingbot_map.py` | 将模型输出转换为 benchmark 标准格式，支持 streaming/windowed 和 auto keyframe interval。 |

代码层面最重要的映射：

- paper 的 anchor/scale initialization 在代码中主要体现为 `num_scale_frames` 和 `scale_token`。`GCTStream.inference_streaming()` 先把 `scale_frames` 一起处理，再逐帧进入 streaming phase。
- paper 的 local pose-reference window 在 runtime 中对应 patch KV cache 的 `live_window_patch_pages`，超过 `kv_cache_sliding_window` 后旧 patch pages 被回收。
- paper 的 trajectory memory 对应 append-only special stream：每帧保留 6 个 special tokens，包括 camera token、4 个 register tokens、scale token；patch tokens 只保留 scale frames 和最近窗口。
- paper 的 high-efficiency streaming 对应 `FlashInferKVCacheManager` 的 paged KV cache，以及 `FlashInferBlock` 中 single-frame hot path。

## 3. 创新点

### 3.1 Geometric Context Attention

传统 full attention 可以让每帧看到所有帧，但它需要完整输入并且计算/显存随序列长度急剧增长；普通 causal attention 可以在线处理，但如果保留所有历史图像 token，同样会线性增长到不可用；纯 sliding window 成本可控，但容易丢失长期轨迹信息。

LingBot-Map 的 GCA 把历史拆成三种粒度：

1. 初始 anchor frames 保留完整 token，用来固定世界坐标和尺度。
2. 最近 k 帧保留完整 image tokens，用来做局部相对位姿和稠密深度估计。
3. 更早历史只保留 6 个 context/special tokens，用来表达长期轨迹记忆。

论文给出的复杂度直觉是：对 T 帧、每帧 M 个 image tokens，GCA 每帧上下文规模约为 `(n + k) * M + 6T`，而 naive causal 是 `T * (M + 6)`。当 `M ~= 500` 时，每个被逐出窗口的历史帧只新增 6 个 token，token 增长率比保留完整 image tokens 低约 80 倍。论文示例 `n=3, k=16, T=10000` 时，causal attention 约 5e6 tokens，而 GCA 约 7e4 tokens。

代码对应：

- `lingbot_map/aggregator/stream.py` 构建 `FlashInferBlock` 或 `SDPABlock` 作为 global blocks，参数包含 `kv_cache_sliding_window`、`kv_cache_scale_frames` 和 `kv_cache_cross_frame_special`。
- `lingbot_map/layers/flashinfer_cache.py` 明确把 cache 拆成 patch stream 和 special stream。patch stream 中 scale pages 不逐出，recent pages 超出 sliding window 后回收；special stream 对每帧 append-only。

### 3.2 SLAM-like memory，但端到端学习

论文的设计很像把经典 SLAM 的几个状态放进 transformer：

- reference frame / anchor：建立尺度和坐标。
- local map / pose-reference window：保留最近强重叠帧，用于稳定局部配准。
- global map / trajectory memory：以压缩形式保留历史轨迹，减小漂移。

和传统 SLAM 的区别是，LingBot-Map 没有手写特征匹配、回环检测或 BA 作为主流程，而是让 attention 学会在这三类上下文之间取信息。这样保留了 feed-forward 模型的速度和端到端训练优势。

### 3.3 针对长序列的训练 recipe

论文提出两阶段训练：

1. Stage 1：训练 VGGT-like offline base model。使用 DINOv2 ViT-L、24 层 frame attention + global attention，随机 2 到 24 views，建立通用多视图几何先验。
2. Stage 2：把 global attention 替换为 GCA，从 Stage 1 权重初始化，视角数从 24 线性增加到 320，local window 随机采样 16 到 64，使用 context parallelism 解决长序列训练显存瓶颈。

损失上，LingBot-Map 继承 VGGT 的 depth loss 和 absolute pose loss，又额外加入 local window 内所有帧对的 relative pose loss。论文还强调使用 camera-to-world 监督，而不是 VGGT 里常见的 world-to-camera 表达，以降低长序列中旋转误差对平移估计的耦合影响。

### 3.4 Runtime 层面的 paged KV cache

只提出 GCA 还不够，因为 streaming attention 每帧都要 append 新 KV、逐出旧 patch tokens。如果使用连续大 tensor，频繁拼接和切片会带来很重的内存搬运开销。

当前代码用 FlashInfer paged KV cache 解决这个问题：

- patch pages：每帧 image patch tokens 占一个 page。scale frames 的 patch pages 永久保留，recent window patch pages 超窗后回收到 free list。
- special pages：每帧 6 个 special tokens 连续打包，append-only，不回收。
- visible attention pages 顺序是 scale patch pages + live window patch pages + all special pages。
- `plan()` 只在每个 frame step 的 block 0 做一次，后续层复用 page table 结构。

论文报告在 518 x 378 输入、1000 frames、window=64 下，FlashInfer 实现约 20 FPS，PyTorch contiguous KV baseline 约 10.5 FPS。Table 7 中 window=64 相比 full causal attention 达到 20.29 FPS vs 11.87 FPS，显存 13.28 GB vs 36.06 GB。

## 4. 算法流程

下面是从代码和论文合并后的推理流程。

### 4.1 输入与 tokenization

1. 输入图像或视频帧被预处理到 patch size 对齐的分辨率，默认 `image_size=518`、`patch_size=14`。
2. DINOv2 ViT backbone 产生每帧 patch/image tokens。
3. 每帧前面拼接 special tokens：camera token、4 个 register tokens、scale token，总计 6 个 special tokens。
4. 2D RoPE 用于空间 patch 位置；streaming 模式可启用 3D RoPE，把时间维也编码进 attention。

代码对应：

- `AggregatorBase._embed_images()` 做图像归一化、patch embedding、special token 拼接。
- `AggregatorStream._setup_special_tokens()` 定义 camera/register/scale tokens，并设置 `patch_start_idx = 1 + num_register_tokens + 1`。

### 4.2 Transformer 主干

主干是 VGGT-style alternating attention：

1. Frame Attention：每帧内部独立做 self-attention，增强单帧视觉表征。
2. Geometric Context Attention：跨帧做结构化 causal/global attention，当前帧只从 anchor、local window、trajectory memory 中取信息。
3. 一共 24 组 attention blocks，默认 selected outputs 是 `[4, 11, 17, 23]`，给 DPT head 做多层 feature fusion。

代码对应：

- `AggregatorBase.forward()` 以 `aa_order=["frame", "global"]` 交替调用 `_process_frame_attention()` 和 `_process_global_attention()`。
- `GCTStream._aggregate_features()` 选择 `[4, 11, 17, 23]` 作为输出层。

### 4.3 Streaming inference

`GCTStream.inference_streaming()` 分两阶段：

1. Phase 1：取前 `num_scale_frames` 帧作为 scale/anchor frames，一次性 batch 处理。它们之间是 bidirectional/full attention，用于建立尺度和初始坐标。
2. Phase 2：从第 `num_scale_frames` 帧之后开始逐帧处理。每次只把当前帧送入模型，利用 KV cache 读取历史上下文。
3. 如果 `keyframe_interval > 1`，非 keyframe 仍然会输出 pose/depth，但不会把当前 KV 永久写入 cache。FlashInfer 路径会临时 append、attention、rollback，语义上等价于“看当前帧但不把它记入长期状态”。
4. 输出按时间 concat，得到 `pose_enc`、`depth`、`depth_conf`，如果 point head 开启则还有 `world_points` 和 `world_points_conf`。

代码对应：

- `GCTStream._set_skip_append()` 同时标记 aggregator 和 camera head 的 cache，控制 non-keyframe 不持久化。
- `FlashInferBlock.forward()` 对 non-keyframe 做 append -> attention -> rollback。
- `demo.py` 的 user-facing 参数中，`--keyframe_interval` 用于长序列降 cache 增长；README 建议超过 320 帧时开启 keyframe 策略。

### 4.4 Windowed / VO mode

论文把推理分为 Direct Output 和 VO 两种模式：

- Direct Output：不 reset 状态，适合训练长度的若干倍，论文经验是约 3000 帧以内更准确。
- VO mode：把超长视频切成重叠窗口，每个窗口内部独立 streaming，窗口之间用 overlap 区域做 Sim(3) 对齐并拼接，适合上万帧甚至更长的视频，但窗口边界会引入额外对齐漂移。

代码中 `gct_stream_window.py` 实现了这一套：

- `window_size` 表示 cache 中保留的 keyframes 数量，不一定等于实际帧数。
- 当 `keyframe_interval > 1` 时，实际窗口覆盖帧数为 `scale_frames + (window_size - scale_frames) * keyframe_interval`。
- `overlap_keyframes` 会换算成实际 overlap 帧数，用于提升窗口间对齐稳定性。
- 还支持 `flow_threshold > 0` 的 flow-based keyframe selection，但主 demo CLI 默认更多暴露的是固定 `keyframe_interval`。

## 5. 网络框架细节

### 5.1 Backbone

LingBot-Map 的主干基本沿用 VGGT 结构：

- ViT-L style embed dim 1024。
- patch size 14。
- 24 层 frame blocks 和 24 层 cross-frame/global blocks。
- 16 attention heads。
- DINOv2 ViT-L/14 register backbone 初始化。

和 VGGT 最大的差异在 global blocks：

- VGGT 的 `vggt/models/aggregator.py` 在 `_process_global_attention()` 中把 token reshape 成 `[B, S * P, C]`，对所有输入 view 做 full cross-view attention。
- LingBot-Map 的 `AggregatorStream` 把 global blocks 换成 `FlashInferBlock` 或 `SDPABlock`，并通过 KV cache 和 GCA 控制可见历史。

### 5.2 Special tokens

VGGT 使用 1 个 camera token + 4 个 register tokens，并且第一帧和其他帧使用两套 token，让模型知道哪一帧是参考帧。

LingBot-Map 在此基础上增加 scale token：

- camera token：进入 camera head 预测 pose。
- register tokens：作为上下文汇聚/记忆 token。
- scale token：标识 scale/anchor frames，帮助建立尺度。

这 6 个 special tokens 是 trajectory memory 的最小单元。patch tokens 会被逐出窗口，但 special tokens 对每帧都会写入 append-only cache。

### 5.3 Camera head

`CameraCausalHead` 从最后一层 camera token 提取 `[B, S, C]`，经过 4 层 camera transformer trunk，并进行多次 iterative refinement。每次迭代：

1. 将上一次 pose encoding 或 empty pose token embed 成 modulation。
2. 用 AdaLN 风格的 shift/scale/gate 调制 pose tokens。
3. 通过 camera transformer trunk。
4. 输出 pose delta，并累加到当前 pose encoding。
5. 激活成 9D pose：translation 3D、quaternion 4D、FoV 2D。

streaming 模式下 camera head 自己也维护 KV cache，并可以使用 camera-level 3D RoPE。

### 5.4 Depth / point heads

`DPTHead` 继承 VGGT/DepthAnything 风格：

- 从多个 transformer 层取 patch tokens。
- LayerNorm 后 reshape 成 feature map。
- 用 1x1 projection + resize layers 构成多尺度特征。
- 用 refinenet fusion 上采样到图像尺度。
- depth head 输出 2 通道：depth + depth confidence。
- point head 输出 4 通道：xyz + point confidence。

当前 `GCTStream` 默认 `enable_depth=True`、`enable_point=False`。demo 可视化主要可以用 depth + pose 反投影生成点云；如果开启 point head，也可直接输出 `world_points`。

### 5.5 输出与 pose convention 注意点

论文明确说 LingBot-Map 使用 camera-to-world 监督，区别于 VGGT 的 world-to-camera 监督。当前代码中有一个需要使用者注意的 convention 差异：

- `demo.py` 的 `postprocess()` 把 `pose_encoding_to_extri_intri()` 输出再 inverse 一次，注释写的是 “Convert w2c to c2w”。
- `benchmark/methods/lingbot_map.py` 的 `_process_outputs()` 则注释说 `pose_encoding_to_extri_intri()` 输出是 C2W，直接写入 benchmark pose。
- `utils/pose_enc.py` 的 docstring 仍然描述为 OpenCV camera-from-world。

这不影响本文对算法的总结，但如果你要复现实验或把模型输出接到别的系统里，建议先用一小段有 GT 的序列验证 pose 矩阵方向。

## 6. 论文实验结论

下面列出最能说明方法性质的数字。

### 6.1 Oxford Spires pose

Oxford Spires sparse setting (320 frames)：

| Method | Type | AUC@15 higher | AUC@30 higher | ATE lower |
| --- | --- | ---: | ---: | ---: |
| VGGT | offline | 23.84 | 35.09 | 24.78 |
| DA3 | offline | 49.84 | 56.68 | 12.87 |
| VIPE | optim | 45.35 | 51.88 | 10.52 |
| Best online competitor in table | online | 13.92 (TTT3R) | 25.90 (TTT3R) | 18.16 (CUT3R) |
| LingBot-Map | online | 61.64 | 75.16 | 6.42 |

这个结果的重点是：LingBot-Map 虽然是 online streaming 模式，但在 Oxford 这种有大尺度、室内外切换、重访和长时漂移的场景里，超过了 VGGT/DA3 这类 offline feed-forward 方法和 VIPE 这类优化方法。

### 6.2 Oxford dense long sequence

Oxford Spires dense setting 从 320 帧扩展到 3840 帧。论文 Table 3 中：

- LingBot-Map ATE 从 6.42 增加到 7.11，只增加 0.69。
- CUT3R 从 18.16 增加到 32.47。
- Wint3R 从 21.10 增加到 32.90。
- LingBot-Map FPS 为 20.29。

这说明它真正解决的是长视频状态管理，而不是只在短 clip 上提高了深度或位姿 head。

### 6.3 跨数据集泛化

论文 Table 4 报告：

- ETH3D：LingBot-Map ATE 0.22，第二名 Wint3R 0.86。
- 7-Scenes：LingBot-Map ATE 0.08，优于其他 streaming baselines。
- Tanks and Temples：LingBot-Map AUC@30 92.80、ATE 0.20，明显优于 Stream3R 的 81.33 和 0.76。

论文 Table 5 中点云重建：

- ETH3D F1：LingBot-Map 98.98，Wint3R 77.28。
- 7-Scenes F1：LingBot-Map 80.39。
- NRGBD F1：LingBot-Map 64.26。

### 6.4 Ablation

论文 Table 6/7 给出了关键机制的贡献：

- Anchor initialization：AUC@3 从 9.80 到 13.63，ATE 从 8.59 到 7.88。
- Context tokens：AUC@3 从 13.63 到 15.75，ATE 从 7.88 到 7.46。
- Relative pose loss：缺失时 RPE-rot 从 2.26 退化到 5.35。
- Video RoPE：ATE 从 7.46 到 5.98，是 ablation 中最大单项提升。
- Window 64 vs full causal：window=64 不仅更快更省显存，也有更低 ATE。Table 7 是 5.98 ATE、20.29 FPS、13.28 GB vs full causal 的 6.60 ATE、11.87 FPS、36.06 GB。

## 7. 相较于 VGGT 的优点

### 7.1 真正支持在线流式输入

VGGT 的强项是离线多视角重建：把一组 views 一次性喂入模型，global attention 可以双向看所有图像。这个设置非常适合 unordered image collection 或短序列，但不适合相机不断输入新帧的机器人/AR/导航场景。

LingBot-Map 的 `inference_streaming()` 明确是 frame-by-frame causal inference：先处理 anchor/scale frames，然后每来一帧只处理当前帧和 KV cache。它不需要未来帧，因此任务定义上比 VGGT 更贴近 SLAM/VO。

### 7.2 长序列成本更可控

VGGT 的 global attention 对 `S * P` tokens 做 full attention，显存和计算对 view 数很敏感。几百张图还能作为 batch 处理，但上千到上万帧不现实。

LingBot-Map 只保留少量长期 special tokens 和固定窗口 patch tokens。runtime 中 patch page pool 是固定大小，special page pool 随帧数按 6 tokens/frame 增长。结合 FlashInfer，它能在论文设置下以约 20 FPS 处理长序列。

### 7.3 更抗长程漂移

VGGT 用第一帧/全局点云隐式建立参考坐标，但它不是为了长视频逐帧漂移控制训练的。LingBot-Map 的 anchor + local window + trajectory memory 是专门为漂移控制设计的，并额外用 relative pose loss 和 video RoPE 强化局部一致性与时间顺序。

Oxford Spires 的对比很直接：VGGT ATE 24.78，LingBot-Map ATE 6.42；VGGT AUC@15 23.84，LingBot-Map 61.64。

### 7.4 更接近工程实时系统

LingBot-Map repo 不只是模型 forward，还包含：

- `demo.py`：流式/窗口化推理、offload、keyframe interval、FlashInfer/SDPA 后端、torch.compile 热路径。
- `gct_profile.py`：FPS profiling。
- `benchmark/`：KITTI/Oxford 等评估脚本和统一 artifact 格式。
- `demo_render/`：长视频离线渲染 pipeline。

这比原始 VGGT 更偏向“模型即在线系统”。

## 8. 相较于 VGGT 的缺点和风险

### 8.1 失去 full bidirectional context

VGGT 的 full global attention 可以同时利用所有 views，包括未来帧。对小规模、静态、unordered image set，这种全局信息通常是优势。LingBot-Map 为了 online causal 约束，当前帧不能看未来，Direct mode 中未来帧不会反过来 refine 早期结果。

因此如果任务是离线、高精度、多视角全局重建，且 views 数不大，VGGT 或 VGGT + BA/后处理仍可能更合适。

### 8.2 输出任务少于 VGGT

VGGT 原生输出 camera、depth、point map、point tracks。LingBot-Map 论文和当前代码重点是 pose + depth + point cloud reconstruction，核心 `GCTStream` 默认不开启 point head，也没有 VGGT 那样完整的 track head 使用路径。

这意味着如果你的任务依赖 dense point tracks 或跨视角匹配特征，VGGT 的多任务输出更完整。

### 8.3 Runtime 更复杂，依赖更重

LingBot-Map 的优势依赖一套复杂 runtime：

- FlashInfer paged KV cache。
- keyframe interval 或 flow-based keyframe。
- sliding window eviction。
- non-keyframe append/rollback。
- 可选 torch.compile hot path。
- windowed 模式下的 overlap 和 Sim(3) alignment。

这些设计带来速度和长序列能力，但也增加了调参和调试成本。VGGT 的 forward 逻辑更简单，输入图像 -> aggregator -> heads，更容易部署成一个普通 batched inference 模型。

### 8.4 Direct mode 仍有训练长度边界

README 明确提醒：默认不做 state resetting，最大推理范围受训练见过的最长距离约束；超过范围可能出现 pose collapse，需要切到 windowed mode。论文也说 Direct mode 经验上约 3000 帧内更好，超长序列切 VO/windowed 会在窗口边界引入额外 Sim(3) 对齐误差。

所以 LingBot-Map 不是无限长无漂移 SLAM。它没有显式 loop closure，也没有在线 BA；极长序列仍会受 trajectory memory 压缩和窗口拼接误差影响。

### 8.5 初始 anchor/scale frames 很关键

由于 monocular reconstruction 有尺度歧义，LingBot-Map 依赖前 `num_scale_frames` 建立尺度和坐标。如果开头几帧纹理差、运动退化、动态物体多或视角覆盖不足，后续全局坐标会被拖累。VGGT 在离线设置下可以用全局 views 来共同定标，理论上对“坏开头”更不敏感。

## 9. 当前代码与论文的实现差异/注意事项

### 9.1 Adaptive keyframe selection

论文 Sec. 4.4 描述的是当序列超过最大训练长度时，根据当前帧相对最近 keyframe 的 optical flow magnitude 自适应决定是否保留为 keyframe。

当前代码中：

- `GCTStream.inference_streaming()` 主要使用固定 `keyframe_interval`。
- `GCTStreamWindow.inference_windowed()` 支持 `flow_threshold > 0` 的 flow-based keyframe selection。
- `benchmark/methods/lingbot_map.py` 暴露了 `flow_threshold` 参数。
- `demo.py` 默认 CLI 更强调 `--keyframe_interval`，未明显暴露 flow threshold。

所以 paper 描述和默认 demo 路径并不完全一致。默认使用时，它更像“固定间隔 keyframe streaming”；需要 flow-based 策略时应走 windowed/benchmark 对应入口或扩展 CLI。

### 9.2 Anchor token vs scale token 命名

论文叫 learnable anchor token，代码里是 `scale_token`，并且 special tokens 总数为 6。语义上它承担 anchor/scale frame 标识和尺度初始化功能，但命名和论文不是逐字对应。

### 9.3 Training code 缺失

repo 中没有论文 Stage 1/Stage 2 的完整训练 pipeline。因此 progressive view training、context parallelism、relative pose loss 的实现细节只能从 paper 复述，不能从当前 repo 逐行验证。

### 9.4 Pose convention 需要复核

如前所述，`demo.py`、`benchmark/methods/lingbot_map.py`、`utils/pose_enc.py` 对 `pose_encoding_to_extri_intri()` 输出方向的注释不完全一致。外部使用时应做最小验证，避免 C2W/W2C 方向弄反。

## 10. 我对这篇工作的判断

LingBot-Map 的真正价值在于“把 3D foundation model 从离线多视角重建推进到在线长视频重建”。它不是把 VGGT 简单改成 causal mask，而是围绕 streaming state management 设计了一套结构化几何上下文：

- anchor 解决尺度和坐标 grounding；
- local window 解决局部 dense geometry 和 relative pose；
- trajectory memory 解决长程 drift；
- paged KV cache 把这个结构变成可实时运行的系统。

从论文实验看，它在长序列 pose 和 reconstruction 上的提升很显著，尤其 Oxford Spires 这种大尺度、重访、室内外切换数据，正好击中 VGGT-style offline priors 的弱点。

但它也有清晰边界：

- 不替代 VGGT 的 unordered offline reconstruction 和 point tracking 能力；
- 不等于带显式回环/BA 的完整 SLAM；
- 依赖 CUDA/FlashInfer 和复杂 cache runtime；
- 超长序列仍需要 windowed reset + Sim(3) stitching，存在边界漂移。

如果任务是机器人、AR、具身智能、长视频 mapping，LingBot-Map 的方向明显比 VGGT 更适配；如果任务是离线多图重建、少量 views、需要 point tracks 或追求全局双向一致性，VGGT 仍是更简单、更通用的基础模型。

## 11. 后续阅读/复现实验建议

1. 先跑短序列 demo：使用 `example/courthouse` 或 `example/oxford`，确认 checkpoint、pose/depth 输出和可视化链路。
2. 再跑 `benchmark/configs/oxford.yaml` 或 `benchmark/configs/kitti.yaml`，验证 benchmark adapter 的 pose convention。
3. 对超过 320 帧的序列，比较 `keyframe_interval=1`、auto interval、以及 windowed mode 的轨迹稳定性和显存。
4. 如果要接入机器人系统，优先检查 C2W/W2C 输出、尺度稳定性、sky/dynamic object filtering，以及是否需要外部 loop closure/BA。
5. 如果要和 VGGT 复用能力，注意 README 中 `lingbot-map-stage1` checkpoint 可加载进 VGGT 做 bidirectional inference；这说明 Stage 1 更接近 VGGT-style offline base，而 Stage 2 才是 streaming GCA specialization。
