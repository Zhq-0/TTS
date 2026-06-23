# Zero-shot 克隆模型对比

## 结论快照

| 模型 | 完成数 | 加权 CER | 加权 WER | 平均 RTF | 总体 RTF | 平均 UTMOS | 平均 SIM-o |
|---|---:|---:|---:|---:|---:|---:|---:|
| dots.tts-mf | 4 | 9.47% | 16.76% | 0.769 | 0.814 | 2.668 | 0.789 |
| CosyVoice3 | 4 | 3.16% | 7.82% | 0.536 | 0.493 | 3.114 | 0.758 |

## 分项结果

| 用例 | 模型 | CER | WER | RTF | UTMOS | SIM-o | 音频时长 | 输出 |
|---|---|---:|---:|---:|---:|---:|---:|---|
| 中文 zero-shot 语音克隆 | dots.tts-mf | 7.50% | 15.79% | 0.751 | 2.237 | 0.862 | 12.800 秒 | `outputs/dots_tts_mf/zh_zero_shot_aishell.wav` |
| 中文 zero-shot 语音克隆 | CosyVoice3 | 5.00% | 10.53% | 0.561 | 2.586 | 0.868 | 13.320 秒 | `outputs/cosyvoice3/zh_zero_shot_aishell.wav` |
| 英文 zero-shot 语音克隆 | dots.tts-mf | 0.00% | 13.64% | 0.744 | 3.627 | 0.674 | 7.680 秒 | `outputs/dots_tts_mf/en_zero_shot_official_xvec.wav` |
| 英文 zero-shot 语音克隆 | CosyVoice3 | 0.00% | 13.64% | 0.527 | 4.474 | 0.473 | 11.880 秒 | `outputs/cosyvoice3/en_zero_shot_official_xvec.wav` |
| 动漫角色音色克隆：钟离 | dots.tts-mf | 11.76% | 36.36% | 0.725 | 2.983 | 0.811 | 5.600 秒 | `outputs/dots_tts_mf/anime_zhongli.wav` |
| 动漫角色音色克隆：钟离 | CosyVoice3 | 5.88% | 18.18% | 0.590 | 3.303 | 0.793 | 6.320 秒 | `outputs/cosyvoice3/anime_zhongli.wav` |
| 长文本生成稳定性测试 | dots.tts-mf | 13.19% | 15.75% | 0.857 | 1.825 | 0.811 | 42.720 秒 | `outputs/dots_tts_mf/long_text_zh_stability.wav` |
| 长文本生成稳定性测试 | CosyVoice3 | 3.83% | 5.51% | 0.468 | 2.094 | 0.899 | 77.680 秒 | `outputs/cosyvoice3/long_text_zh_stability.wav` |

## 自动判断

- 中文 zero-shot 语音克隆：CER 最低 `CosyVoice3`；WER 最低 `CosyVoice3`；RTF 最低 `CosyVoice3`；UTMOS 最高 `CosyVoice3`；SIM-o 最高 `CosyVoice3`。
- 英文 zero-shot 语音克隆：CER 最低 `dots.tts-mf`；WER 最低 `dots.tts-mf`；RTF 最低 `CosyVoice3`；UTMOS 最高 `CosyVoice3`；SIM-o 最高 `dots.tts-mf`。
- 动漫角色音色克隆：钟离：CER 最低 `CosyVoice3`；WER 最低 `CosyVoice3`；RTF 最低 `CosyVoice3`；UTMOS 最高 `CosyVoice3`；SIM-o 最高 `dots.tts-mf`。
- 长文本生成稳定性测试：CER 最低 `CosyVoice3`；WER 最低 `CosyVoice3`；RTF 最低 `CosyVoice3`；UTMOS 最高 `CosyVoice3`；SIM-o 最高 `CosyVoice3`。

## Whisper 回识别文本

| 用例 | 模型 | 目标文本 | Whisper medium 回识别文本 |
|---|---|---|---|
| 中文 zero-shot 语音克隆 | dots.tts-mf | 今天是第一次使用 dots.tts 进行中文零样本语音克隆测试。请保持自然、稳定、清晰的语气。 | 今天是第一次使用DOTS TTS进行中文灵样本语音课笼测试请保持自然稳定清晰的语气 |
| 中文 zero-shot 语音克隆 | CosyVoice3 | 今天是第一次使用 dots.tts 进行中文零样本语音克隆测试。请保持自然、稳定、清晰的语气。 | 今天是第一次使用DOT TTS进行中文灵样本语音克隆测试,请保持自然稳定清晰的语气。 |
| 英文 zero-shot 语音克隆 | dots.tts-mf | Today is my first zero-shot voice cloning test with dots T T S. Please keep the voice natural, stable, and clear. | Today is my first zero-shot voice cloning test with DOTS TTS. Please keep the voice natural, stable and clear. |
| 英文 zero-shot 语音克隆 | CosyVoice3 | Today is my first zero-shot voice cloning test with dots T T S. Please keep the voice natural, stable, and clear. | Today is my first zero-shot voice cloning test with DOTS-TTS. Please keep the voice natural, stable, and clear. |
| 动漫角色音色克隆：钟离 | dots.tts-mf | 欲买桂花同载酒，只可惜故人，何日再见呢？ | 玉买桂花同栽酒,只可惜故人何日再见呢? |
| 动漫角色音色克隆：钟离 | CosyVoice3 | 欲买桂花同载酒，只可惜故人，何日再见呢？ | 欲买桂花同在酒,只可惜故人何日再見呢? |
| 长文本生成稳定性测试 | dots.tts-mf | 今天我们进行一次长文本语音合成稳定性测试。随着人工智能技术不断发展，语音系统不仅需要准确读出每一个字，还需要在较长的段落中保持稳定的音色、自然的停顿和一致的语速。本次测试会观察模型在连续生成时是否出现声音漂移、语速变化、重复、漏字或者异常停顿。同时，我们也会关注数字二零二六、英文名称 dots T T S，以及不同标点符号对朗读节奏产生的影响。请用清晰、自然并且平稳的语气完成整段内容，让听众能够轻松理解其中表达的信息。最后，我们将结合生成耗时、音频时长、实时率、音色相似度和主观听感，对本次长文本合成效果进行完整记录。 | 随着人工承诺技术不断发展,语音系统不仅需要准确读出每一个字,还需要在较长的段落中保持稳定的音色,自然的停顿和一致的语速。本次测试会观察模型在连续生成时是否出现声音飘移,语速变化,重复漏字或者异常停顿。同时我们也会关注数字2026英文名称DOTS,TTS以及不同标点符号对朗读节奏产生的影响,请用清晰自然并且平稳的语气完成整段内容,让听众能够轻松理解其中表达的信息。最后我们将结合声成号时音频时长时时率,音色相似度和主观听感对本次常文本合成效果进行完整记录。 |
| 长文本生成稳定性测试 | CosyVoice3 | 今天我们进行一次长文本语音合成稳定性测试。随着人工智能技术不断发展，语音系统不仅需要准确读出每一个字，还需要在较长的段落中保持稳定的音色、自然的停顿和一致的语速。本次测试会观察模型在连续生成时是否出现声音漂移、语速变化、重复、漏字或者异常停顿。同时，我们也会关注数字二零二六、英文名称 dots T T S，以及不同标点符号对朗读节奏产生的影响。请用清晰、自然并且平稳的语气完成整段内容，让听众能够轻松理解其中表达的信息。最后，我们将结合生成耗时、音频时长、实时率、音色相似度和主观听感，对本次长文本合成效果进行完整记录。 | 今天我们进行一次长文本语音合成稳定性测试。随着人工智能技术不断发展,语音系统不仅需要准确读出每一个字,还需要在较长的段落中保持稳定的音色,自然的停顿和一致的语速。本次测试会观察模型在连续生成时是否出现声音飘移、语速变化、重复漏字,或者异常停顿。同时我们也会关注数字2026。英文名称DOUTS-TTS以及不同标点符号对朗读节奏产生的影响,请用清晰、自然并且平稳的语气完成整段内容,让听众能够轻松理解其中表达的信息。最后,我们将结合生成耗时音频时长、时时时相色相似度和主观听感,对本次长文本合成效果进行完整记录。 |

## 限制

- CER/WER 来自 Whisper medium 回识别；ASR 错误也会计入指标，不能直接等同真人听写错误。
- UTMOS 和 SIM-o 是自动指标，不能替代人工试听。
- 英文用例使用 `cross_lingual_prompt.wav`，没有人工参考文本，因此两个模型都按无参考文本的 x-vector/cross-lingual 模式生成。
- CosyVoice3 的长文本由官方前端切成 4 段后拼接；dots.tts 本轮是单次生成。
- 部分输出存在超过绝对幅值 1.0 的样本，脚本已记录 clip count，试听时需要关注是否有爆音。

## 产物

- dots.tts：`experiments/zero_shot_comparison/outputs/dots_tts_mf`
- CosyVoice3：`experiments/zero_shot_comparison/outputs/cosyvoice3`
- 小数据微调准备：`experiments/small_multispeaker_finetune/genshin_20_speakers_5shot`
