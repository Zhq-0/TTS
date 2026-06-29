# CosyVoice3 四角色 LLM-only 微调补测

## 实验条件

- 对比模型：`base` 与 `clean_epoch_2`。
- 测试规模：已见 4 角色每人 25 条文本，未见 8 角色每人 10 条文本，共 180 个 case；两模型共 360 条生成音频。
- 文本类型：困难短句、普通短句、游戏专有词、中长文本、中英混合。
- 评测方式：base 与 clean_epoch_2 使用相同 prompt audio、prompt text、target text 和随机种子。
- ASR：Whisper `medium` 回识别后计算 CER/WER；SIM 使用 CampPlus prompt-output cosine similarity。
- RTF 仅作为推理耗时记录，不作为微调收益结论。
- UTMOS：UTMOS22Strong 无参考自然度估计。

## 总体结果

| 模型 | n | CER | WER | 拼音错误率 | SIM | UTMOS | 总体 RTF |
|---|---:|---:|---:|---:|---:|---:|---:|
| base | 180 | 5.58% | 9.79% | 2.46% | 0.8704 | 3.1257 | 0.5924 |
| clean_epoch_2 | 180 | 5.34% | 9.01% | 2.29% | 0.8624 | 3.1448 | 0.5985 |

## 已见 / 未见说话人

| split | 模型 | n | CER | WER | SIM | UTMOS |
|---|---|---:|---:|---:|---:|---:|
| seen | base | 100 | 5.48% | 9.50% | 0.8688 | 3.0998 |
| seen | clean_epoch_2 | 100 | 4.76% | 8.65% | 0.8626 | 3.1014 |
| unseen | base | 80 | 5.71% | 10.19% | 0.8725 | 3.1580 |
| unseen | clean_epoch_2 | 80 | 6.11% | 9.49% | 0.8621 | 3.1991 |

## 分文本类型结果

| 类别 | 模型 | n | CER | WER | SIM | UTMOS |
|---|---|---:|---:|---:|---:|---:|
| difficult_short | base | 36 | 10.17% | 20.97% | 0.8695 | 3.0433 |
| difficult_short | clean_epoch_2 | 36 | 8.97% | 18.55% | 0.8598 | 3.0917 |
| game_terms | base | 36 | 9.97% | 14.39% | 0.8733 | 3.2182 |
| game_terms | clean_epoch_2 | 36 | 11.75% | 16.51% | 0.8631 | 3.1792 |
| generic_short | base | 36 | 1.02% | 1.58% | 0.8605 | 3.0071 |
| generic_short | clean_epoch_2 | 36 | 0.20% | 0.32% | 0.8565 | 3.1336 |
| medium_text | base | 36 | 2.52% | 3.80% | 0.8835 | 2.9635 |
| medium_text | clean_epoch_2 | 36 | 2.26% | 3.48% | 0.8792 | 2.9513 |
| zh_en_mixed | base | 36 | 5.49% | 10.76% | 0.8653 | 3.3964 |
| zh_en_mixed | clean_epoch_2 | 36 | 4.73% | 7.29% | 0.8534 | 3.3684 |

## 成对统计

- 完整成对 case：180。
- clean_epoch_2 CER 更低：39 个。
- clean_epoch_2 WER 更低：42 个。
- clean_epoch_2 SIM 更高：71 个。
- clean_epoch_2 UTMOS 更高：90 个。

## 文件位置

- cases：`evaluation/extended_comparison/cases.jsonl`
- 自动指标：`evaluation/extended_comparison/automatic_metrics.json`
- 合成音频：`outputs/extended_comparison`
