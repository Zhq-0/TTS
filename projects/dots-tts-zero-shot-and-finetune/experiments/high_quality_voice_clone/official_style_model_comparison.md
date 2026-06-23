# Seed-TTS-Eval Style 模型对比

## 结论快照

| 模型 | 完成数 | 官方风格 WER | 官方风格 SIM | 平均 RTF |
|---|---:|---:|---:|---:|
| dots.tts-soar | 4 | 7.69% | 0.815 | 1.441 |
| CosyVoice3 | 4 | 8.83% | 0.813 | 0.591 |

## 分项结果

| 用例 | 模型 | 语言 | WER | SIM | RTF | 输出 |
|---|---|---|---:|---:|---:|---|
| 高质量音色克隆：AISHELL 短句 | dots.tts-soar | zh | 0.00% | 0.827 | 1.511 | `outputs/dots_tts_soar/zh_aishell_quality_short.wav` |
| 高质量音色克隆：AISHELL 短句 | CosyVoice3 | zh | 0.00% | 0.857 | 0.684 | `outputs/cosyvoice3/zh_aishell_quality_short.wav` |
| 高质量音色克隆：AISHELL 中句 | dots.tts-soar | zh | 0.00% | 0.908 | 1.377 | `outputs/dots_tts_soar/zh_aishell_quality_medium.wav` |
| 高质量音色克隆：AISHELL 中句 | CosyVoice3 | zh | 0.00% | 0.883 | 0.493 | `outputs/cosyvoice3/zh_aishell_quality_medium.wav` |
| 高质量音色克隆：钟离短句 | dots.tts-soar | zh | 30.77% | 0.694 | 1.457 | `outputs/dots_tts_soar/anime_zhongli_quality_short.wav` |
| 高质量音色克隆：钟离短句 | CosyVoice3 | zh | 30.77% | 0.713 | 0.619 | `outputs/cosyvoice3/anime_zhongli_quality_short.wav` |
| 高质量音色克隆：钟离中句 | dots.tts-soar | zh | 0.00% | 0.832 | 1.417 | `outputs/dots_tts_soar/anime_zhongli_quality_medium.wav` |
| 高质量音色克隆：钟离中句 | CosyVoice3 | zh | 4.55% | 0.799 | 0.568 | `outputs/cosyvoice3/anime_zhongli_quality_medium.wav` |

## 自动判断

- 高质量音色克隆：AISHELL 短句：WER 最低 `dots.tts-soar`；SIM 最高 `CosyVoice3`；RTF 最低 `CosyVoice3`。
- 高质量音色克隆：AISHELL 中句：WER 最低 `dots.tts-soar`；SIM 最高 `dots.tts-soar`；RTF 最低 `CosyVoice3`。
- 高质量音色克隆：钟离短句：WER 最低 `dots.tts-soar`；SIM 最高 `CosyVoice3`；RTF 最低 `CosyVoice3`。
- 高质量音色克隆：钟离中句：WER 最低 `dots.tts-soar`；SIM 最高 `dots.tts-soar`；RTF 最低 `CosyVoice3`。

## ASR 回识别文本

| 用例 | 模型 | 目标文本 | 官方风格 ASR 回识别文本 |
|---|---|---|---|
| 高质量音色克隆：AISHELL 短句 | dots.tts-soar | 这是一段用于测试高质量音色克隆的短句。 | 这 是 一 段 用 于 测 试 高 质 量 音 色 克 隆 的 短 句 |
| 高质量音色克隆：AISHELL 短句 | CosyVoice3 | 这是一段用于测试高质量音色克隆的短句。 | 这 是 一 段 用 于 测 试 高 质 量 音 色 克 隆 的 短 句 |
| 高质量音色克隆：AISHELL 中句 | dots.tts-soar | 请用稳定自然的语气完成这段朗读，并尽量保持参考音频中的音色特点。 | 请 用 稳 定 自 然 的 语 气 完 成 这 段 朗 读 并 尽 量 保 持 参 考 音 频 中 的 音 色 特 点 |
| 高质量音色克隆：AISHELL 中句 | CosyVoice3 | 请用稳定自然的语气完成这段朗读，并尽量保持参考音频中的音色特点。 | 请 用 稳 定 自 然 的 语 气 完 成 这 段 朗 读 并 尽 量 保 持 参 考 音 频 中 的 音 色 特 点 |
| 高质量音色克隆：钟离短句 | dots.tts-soar | 契约既成，食言者当受食岩之罚。 | 契 约 继 承 食 盐 者 当 受 食 盐 之 罚 |
| 高质量音色克隆：钟离短句 | CosyVoice3 | 契约既成，食言者当受食岩之罚。 | 契 约 继 承 食 盐 者 当 受 食 盐 之 罚 |
| 高质量音色克隆：钟离中句 | dots.tts-soar | 旅途漫长，若能在闲暇之时品一盏热茶，也算不负此行。 | 旅 途 漫 长 若 能 在 闲 暇 之 时 品 一 盏 热 茶 也 算 不 负 此 行 |
| 高质量音色克隆：钟离中句 | CosyVoice3 | 旅途漫长，若能在闲暇之时品一盏热茶，也算不负此行。 | 旅 途 漫 长 若 能 在 闲 暇 之 时 品 一 盏 热 茶 别 算 不 负 此 行 |

## 口径说明

- WER/SIM 复用 Seed-TTS-Eval 风格：英文 `Whisper-large-v3`，中文 `Paraformer-zh`，SIM 为 WavLM-large speaker verification。
- 本报告使用当前自定义 4 条样本，不是完整 Seed-TTS-Eval 官方测试集；因此不能直接和论文/README 表格数值比较。
- 与 `model_comparison.md` 的差异：这里替换了 ASR/SIM 口径；`model_comparison.md` 仍保留本地 Whisper-medium/OmniVoice 自动评估口径。
