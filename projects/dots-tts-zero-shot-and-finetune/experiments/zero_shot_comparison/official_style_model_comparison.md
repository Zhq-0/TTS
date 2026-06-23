# Seed-TTS-Eval Style 模型对比

## 结论快照

| 模型 | 完成数 | 官方风格 WER | 官方风格 SIM | 平均 RTF |
|---|---:|---:|---:|---:|
| dots.tts-mf | 4 | 10.13% | 0.789 | 0.769 |
| CosyVoice3 | 4 | 6.09% | 0.758 | 0.536 |

## 分项结果

| 用例 | 模型 | 语言 | WER | SIM | RTF | 输出 |
|---|---|---|---:|---:|---:|---|
| 中文 zero-shot 语音克隆 | dots.tts-mf | zh | 10.00% | 0.862 | 0.751 | `outputs/dots_tts_mf/zh_zero_shot_aishell.wav` |
| 中文 zero-shot 语音克隆 | CosyVoice3 | zh | 2.50% | 0.868 | 0.561 | `outputs/cosyvoice3/zh_zero_shot_aishell.wav` |
| 英文 zero-shot 语音克隆 | dots.tts-mf | en | 19.05% | 0.674 | 0.744 | `outputs/dots_tts_mf/en_zero_shot_official_xvec.wav` |
| 英文 zero-shot 语音克隆 | CosyVoice3 | en | 14.29% | 0.473 | 0.527 | `outputs/cosyvoice3/en_zero_shot_official_xvec.wav` |
| 动漫角色音色克隆：钟离 | dots.tts-mf | zh | 0.00% | 0.811 | 0.725 | `outputs/dots_tts_mf/anime_zhongli.wav` |
| 动漫角色音色克隆：钟离 | CosyVoice3 | zh | 5.88% | 0.793 | 0.590 | `outputs/cosyvoice3/anime_zhongli.wav` |
| 长文本生成稳定性测试 | dots.tts-mf | zh | 11.49% | 0.811 | 0.857 | `outputs/dots_tts_mf/long_text_zh_stability.wav` |
| 长文本生成稳定性测试 | CosyVoice3 | zh | 1.70% | 0.899 | 0.468 | `outputs/cosyvoice3/long_text_zh_stability.wav` |

## 自动判断

- 中文 zero-shot 语音克隆：WER 最低 `CosyVoice3`；SIM 最高 `CosyVoice3`；RTF 最低 `CosyVoice3`。
- 英文 zero-shot 语音克隆：WER 最低 `CosyVoice3`；SIM 最高 `dots.tts-mf`；RTF 最低 `CosyVoice3`。
- 动漫角色音色克隆：钟离：WER 最低 `dots.tts-mf`；SIM 最高 `dots.tts-mf`；RTF 最低 `CosyVoice3`。
- 长文本生成稳定性测试：WER 最低 `CosyVoice3`；SIM 最高 `CosyVoice3`；RTF 最低 `CosyVoice3`。

## ASR 回识别文本

| 用例 | 模型 | 目标文本 | 官方风格 ASR 回识别文本 |
|---|---|---|---|
| 中文 zero-shot 语音克隆 | dots.tts-mf | 今天是第一次使用 dots.tts 进行中文零样本语音克隆测试。请保持自然、稳定、清晰的语气。 | 今 天 是 第 一 次 使 用 dot TTES 进 行 中 文 零 样 本 语 音 克 隆 测 试 请 保 持 自 然 稳 定 清 晰 的 语 气 |
| 中文 zero-shot 语音克隆 | CosyVoice3 | 今天是第一次使用 dots.tts 进行中文零样本语音克隆测试。请保持自然、稳定、清晰的语气。 | 今 天 是 第 一 次 使 用 dot tts 进 行 中 文 零 样 本 语 音 克 隆 测 试 请 保 持 自 然 稳 定 清 晰 的 语 气 |
| 英文 zero-shot 语音克隆 | dots.tts-mf | Today is my first zero-shot voice cloning test with dots T T S. Please keep the voice natural, stable, and clear. |  Today is my first zero-shot voice cloning test with DOT TTS. Please keep the voice natural, stable and clear. |
| 英文 zero-shot 语音克隆 | CosyVoice3 | Today is my first zero-shot voice cloning test with dots T T S. Please keep the voice natural, stable, and clear. |  Today is my first zero-shot voice cloning test with DOTS TTS. Please keep the voice natural, stable, and clear. |
| 动漫角色音色克隆：钟离 | dots.tts-mf | 欲买桂花同载酒，只可惜故人，何日再见呢？ | 欲 买 桂 花 同 载 酒 只 可 惜 故 人 何 日 再 见 呢 |
| 动漫角色音色克隆：钟离 | CosyVoice3 | 欲买桂花同载酒，只可惜故人，何日再见呢？ | 欲 买 桂 花 同 在 酒 只 可 惜 故 人 何 日 再 见 呢 |
| 长文本生成稳定性测试 | dots.tts-mf | 今天我们进行一次长文本语音合成稳定性测试。随着人工智能技术不断发展，语音系统不仅需要准确读出每一个字，还需要在较长的段落中保持稳定的音色、自然的停顿和一致的语速。本次测试会观察模型在连续生成时是否出现声音漂移、语速变化、重复、漏字或者异常停顿。同时，我们也会关注数字二零二六、英文名称 dots T T S，以及不同标点符号对朗读节奏产生的影响。请用清晰、自然并且平稳的语气完成整段内容，让听众能够轻松理解其中表达的信息。最后，我们将结合生成耗时、音频时长、实时率、音色相似度和主观听感，对本次长文本合成效果进行完整记录。 | 随 着 人 工 智 能 技 术 不 断 发 展 语 音 系 统 不 仅 需 要 准 确 读 出 每 一 个 字 还 需 要 在 较 长 的 段 落 中 保 持 稳 定 的 音 色 自 然 的 停 顿 和 一 致 的 语 速 本 次 测 试 会 观 察 模 型 在 连 续 生 成 时 是 否 出 现 声 音 漂 移 语 速 变 化 重 复 漏 字 或 者 异 常 停 顿 同 时 我 们 也 会 关 注 数 字 二 零 二 六 英 文 名 称 TT ts 以 及 不 同 标 点 符 号 对 朗 读 节 奏 产 生 的 影 响 请 用 清 晰 自 然 并 且 平 稳 的 语 气 完 成 整 段 内 容 让 听 众 能 够 轻 松 理 解 其 中 表 达 的 信 息 息 后 我 们 将 结 合 生 成 号 时 音 频 时 长 实 时 率 音 色 相 似 度 和 主 观 听 感 对 本 次 长 文 本 合 成 效 果 进 行 完 整 记 录 |
| 长文本生成稳定性测试 | CosyVoice3 | 今天我们进行一次长文本语音合成稳定性测试。随着人工智能技术不断发展，语音系统不仅需要准确读出每一个字，还需要在较长的段落中保持稳定的音色、自然的停顿和一致的语速。本次测试会观察模型在连续生成时是否出现声音漂移、语速变化、重复、漏字或者异常停顿。同时，我们也会关注数字二零二六、英文名称 dots T T S，以及不同标点符号对朗读节奏产生的影响。请用清晰、自然并且平稳的语气完成整段内容，让听众能够轻松理解其中表达的信息。最后，我们将结合生成耗时、音频时长、实时率、音色相似度和主观听感，对本次长文本合成效果进行完整记录。 | 今 天 我 们 进 行 一 次 长 文 本 语 音 合 成 稳 定 性 测 试 随 着 人 工 智 能 技 术 不 断 发 展 语 音 系 统 不 仅 需 要 准 确 读 出 每 一 个 字 还 需 要 在 较 长 的 段 落 中 保 持 稳 定 的 音 色 自 然 的 停 顿 和 一 致 的 语 速 本 次 测 试 会 观 察 模 型 在 连 续 生 成 时 是 否 出 现 声 音 漂 移 语 速 变 化 重 复 漏 字 或 者 异 常 停 顿 同 时 我 们 也 会 关 注 数 字 二 零 二 六 英 文 名 称 dot TTS 以 及 不 同 标 点 符 号 对 朗 读 节 奏 产 生 的 影 响 请 用 清 晰 自 然 并 且 平 稳 的 语 气 完 成 整 段 内 容 让 听 众 能 够 轻 松 理 解 其 中 表 达 的 信 息 最 后 我 们 将 结 合 生 成 耗 时 音 频 时 长 实 时 时 相 似 相 似 度 和 主 观 听 感 对 本 次 长 文 本 合 成 效 果 进 行 完 整 记 录 |

## 口径说明

- WER/SIM 复用 Seed-TTS-Eval 风格：英文 `Whisper-large-v3`，中文 `Paraformer-zh`，SIM 为 WavLM-large speaker verification。
- 本报告使用当前自定义 4 条样本，不是完整 Seed-TTS-Eval 官方测试集；因此不能直接和论文/README 表格数值比较。
- 与 `model_comparison.md` 的差异：这里替换了 ASR/SIM 口径；`model_comparison.md` 仍保留本地 Whisper-medium/OmniVoice 自动评估口径。
