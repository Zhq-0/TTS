# OmniVoice 原神 20 说话人扩展文本评测

## 实验条件

- 文本类别：短文本、中长文本、游戏专有词、中英混合；每类 50 条，共 200 个 text-speaker case。
- 评测方式：每个 case 使用一个未参与训练的验证音频作为 zero-shot prompt；base 与 finetuned_best 使用相同 case。
- 训练集：1200 条高质量音频，共 101.07 分钟；每位说话人 60 条。
- 验证集：200 条独立音频，共 17.00 分钟；每位说话人 10 条。
- 推理条件：32 steps、batch 1、warmup 后计时、固定随机种子 0。
- 指标：Whisper medium 回识别 CER/WER，UTMOS22Strong，WavLM-large + ECAPA-TDNN SIM-o，RTF。

## 总体结果

| 模型 | n | CER | WER | 拼音错误率 | UTMOS | SIM-o | 平均 RTF | 总体 RTF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| base | 200 | 4.38% | 7.12% | 2.62% | 3.0416 | 0.7054 | 0.2569 | 0.1959 |
| finetuned_best | 200 | 3.98% | 6.64% | 2.30% | 3.0366 | 0.7072 | 0.2504 | 0.1930 |

## 分类别结果

| 类别 | 模型 | n | CER | WER | UTMOS | SIM-o | 总体 RTF |
|---|---|---:|---:|---:|---:|---:|---:|
| 游戏专有词 | base | 50 | 7.78% | 15.40% | 3.0771 | 0.7514 | 0.1793 |
| 中长文本 | base | 50 | 1.04% | 1.85% | 2.9288 | 0.7711 | 0.1310 |
| 短文本 | base | 50 | 1.24% | 2.14% | 2.9837 | 0.6004 | 0.4819 |
| 中英混合 | base | 50 | 5.76% | 8.04% | 3.1770 | 0.6986 | 0.1962 |
| 游戏专有词 | finetuned_best | 50 | 7.50% | 14.75% | 3.0585 | 0.7590 | 0.1777 |
| 中长文本 | finetuned_best | 50 | 0.91% | 1.50% | 2.8712 | 0.7763 | 0.1312 |
| 短文本 | finetuned_best | 50 | 0.93% | 1.60% | 2.9745 | 0.6006 | 0.4709 |
| 中英混合 | finetuned_best | 50 | 5.02% | 7.57% | 3.2422 | 0.6930 | 0.1868 |

## 对比结论

- CER：base 4.38%，finetuned_best 3.98%，变化 -0.40%。
- WER：base 7.12%，finetuned_best 6.64%，变化 -0.48%。
- SIM-o：base 0.7054，finetuned_best 0.7072。
- RTF：base 0.1959，finetuned_best 0.1930。
- 成对统计：200 个 case 中，finetuned_best 的 SIM-o 更高 101 个，WER 更低 24 个。
- CER/WER 依赖 Whisper medium 回识别，可能混入 ASR 误差；中英混合文本尤其需要结合人工试听。

## 文件位置

- 用例：`evaluation/genshin_20_speakers_extended_texts/cases.jsonl`
- 生成结果：`evaluation/genshin_20_speakers_extended_texts/generation_results.json`
- 自动指标：`evaluation/genshin_20_speakers_extended_texts/automatic_metrics.json`
- 合成音频：`outputs/genshin_20_speakers_extended_texts`
