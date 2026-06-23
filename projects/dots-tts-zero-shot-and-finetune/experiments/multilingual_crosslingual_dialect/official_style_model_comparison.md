# Seed-TTS-Eval Style 模型对比

## 结论快照

| 模型 | 完成数 | 官方风格 WER | 官方风格 SIM | 平均 RTF |
|---|---:|---:|---:|---:|
| dots.tts-mf | 4 | 10.26% | 0.713 | 0.754 |
| dots.tts-soar | 4 | 32.37% | 0.686 | 1.399 |
| CosyVoice3 | 4 | 10.26% | 0.691 | 0.763 |

## 分项结果

| 用例 | 模型 | 语言 | WER | SIM | RTF | 输出 |
|---|---|---|---:|---:|---:|---|
| 跨语言：中文参考生成英文 | dots.tts-mf | en | 0.00% | 0.632 | 0.886 | `outputs/dots_tts_mf/cross_en_from_zh_ref.wav` |
| 跨语言：中文参考生成英文 | dots.tts-soar | en | 12.50% | 0.561 | 1.437 | `outputs/dots_tts_soar/cross_en_from_zh_ref.wav` |
| 跨语言：中文参考生成英文 | CosyVoice3 | en | 0.00% | 0.493 | 1.183 | `outputs/cosyvoice3/cross_en_from_zh_ref.wav` |
| 跨语言：官方参考生成中文 | dots.tts-mf | zh | 0.00% | 0.783 | 0.715 | `outputs/dots_tts_mf/cross_zh_from_official_ref.wav` |
| 跨语言：官方参考生成中文 | dots.tts-soar | zh | 0.00% | 0.697 | 1.400 | `outputs/dots_tts_soar/cross_zh_from_official_ref.wav` |
| 跨语言：官方参考生成中文 | CosyVoice3 | zh | 0.00% | 0.793 | 0.787 | `outputs/cosyvoice3/cross_zh_from_official_ref.wav` |
| 多语言：日语目标 | dots.tts-mf | ja | - | 0.717 | 0.721 | `outputs/dots_tts_mf/ja_cross_lingual.wav` |
| 多语言：日语目标 | dots.tts-soar | ja | - | 0.788 | 1.388 | `outputs/dots_tts_soar/ja_cross_lingual.wav` |
| 多语言：日语目标 | CosyVoice3 | ja | - | 0.736 | 0.550 | `outputs/cosyvoice3/ja_cross_lingual.wav` |
| 方言：广东话目标 | dots.tts-mf | zh | 30.77% | 0.721 | 0.695 | `outputs/dots_tts_mf/yue_dialect_cantonese.wav` |
| 方言：广东话目标 | dots.tts-soar | zh | 84.62% | 0.697 | 1.371 | `outputs/dots_tts_soar/yue_dialect_cantonese.wav` |
| 方言：广东话目标 | CosyVoice3 | zh | 30.77% | 0.741 | 0.533 | `outputs/cosyvoice3/yue_dialect_cantonese.wav` |

## 自动判断

- 跨语言：中文参考生成英文：WER 最低 `dots.tts-mf`；SIM 最高 `dots.tts-mf`；RTF 最低 `dots.tts-mf`。
- 跨语言：官方参考生成中文：WER 最低 `dots.tts-mf`；SIM 最高 `CosyVoice3`；RTF 最低 `dots.tts-mf`。
- 多语言：日语目标：WER 不适用；SIM 最高 `dots.tts-soar`；RTF 最低 `CosyVoice3`。
- 方言：广东话目标：WER 最低 `dots.tts-mf`；SIM 最高 `CosyVoice3`；RTF 最低 `CosyVoice3`。

## ASR 回识别文本

| 用例 | 模型 | 目标文本 | 官方风格 ASR 回识别文本 |
|---|---|---|---|
| 跨语言：中文参考生成英文 | dots.tts-mf | Please speak clearly and keep the same voice. |  Please speak clearly and keep the same voice. |
| 跨语言：中文参考生成英文 | dots.tts-soar | Please speak clearly and keep the same voice. |  Oh please speak clearly and keep the same voice. |
| 跨语言：中文参考生成英文 | CosyVoice3 | Please speak clearly and keep the same voice. |  Please speak clearly and keep the same voice. |
| 跨语言：官方参考生成中文 | dots.tts-mf | 请用自然清晰的声音，说出这句中文。 | 请 用 自 然 清 晰 的 声 音 说 出 这 句 中 文 |
| 跨语言：官方参考生成中文 | dots.tts-soar | 请用自然清晰的声音，说出这句中文。 | 请 用 自 然 清 晰 的 声 音 说 出 这 句 中 文 |
| 跨语言：官方参考生成中文 | CosyVoice3 | 请用自然清晰的声音，说出这句中文。 | 请 用 自 然 清 晰 的 声 音 说 出 这 句 中 文 |
| 多语言：日语目标 | dots.tts-mf | 今日は静かな朝です。窓の外で鳥が鳴いています。 |  |
| 多语言：日语目标 | dots.tts-soar | 今日は静かな朝です。窓の外で鳥が鳴いています。 |  |
| 多语言：日语目标 | CosyVoice3 | 今日は静かな朝です。窓の外で鳥が鳴いています。 |  |
| 方言：广东话目标 | dots.tts-mf | 今日天氣好好，我哋一齊去飲茶。 | 今 日 天 气 好 好 我 得 一 起 去 饮 茶 |
| 方言：广东话目标 | dots.tts-soar | 今日天氣好好，我哋一齊去飲茶。 | 碧 昂 一 见 吼 喉 我 得 要 采 回 洋 茶 |
| 方言：广东话目标 | CosyVoice3 | 今日天氣好好，我哋一齊去飲茶。 | 今 日 天 气 好 好 我 的 一 切 去 饮 茶 |

## 口径说明

- WER/SIM 复用 Seed-TTS-Eval 风格：英文 `Whisper-large-v3`，中文 `Paraformer-zh`，SIM 为 WavLM-large speaker verification。
- 本报告使用当前自定义 4 条样本，不是完整 Seed-TTS-Eval 官方测试集；因此不能直接和论文/README 表格数值比较。
- 与 `model_comparison.md` 的差异：这里替换了 ASR/SIM 口径；`model_comparison.md` 仍保留本地 Whisper-medium/OmniVoice 自动评估口径。
