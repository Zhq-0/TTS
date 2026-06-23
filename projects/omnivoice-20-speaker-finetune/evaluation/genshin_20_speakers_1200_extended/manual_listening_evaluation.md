# OmniVoice 原神 20 说话人扩展评估人工试听记录

## 记录说明

- 试听模型：基础模型 `base`、微调模型 `finetuned_best`。
- 本记录以人工听感为准，重点关注发音、停顿、流畅度、语速、音色稳定性与背景噪声。
- 未列出的输出整体表现稍微正常，未发现特别明显的问题。
- 文件名已按照实际输出目录统一修正。

## 总体结论

- 基础模型的主要问题集中在角色台词停顿、派蒙长文本流畅度、部分英文单词发音，以及长文本音色漂移。
- 微调模型改善了部分角色音色和长文本流畅度，尤其是荒泷一斗长文本第 1 条、纳西妲游戏文本和钟离长文本。
- 微调后仍存在停顿异常、英语发音不清晰、派蒙声音有气无力、部分音色不稳定和开头噪声。
- 自动 CER/WER 无法反映停顿异常、机械感、重音错误、音色漂移和背景噪声，必须保留人工试听评价。

## 基础模型试听记录

### 英文文本

| 输出音频 | 人工试听问题 |
|---|---|
| `base/english/arataki_itto_english_2.wav` | 部分发音不清晰。 |
| `base/english/nahida_english_1.wav` | 与第 2、3 条音色差异很大，听感像不同说话人。 |
| `base/english/paimon_english_2.wav` | 停顿异常；部分发音不准确，`system` 发音存在问题。 |
| `base/english/zhongli_english_2.wav` | `system` 处发音不清晰。 |

### 游戏专有词与角色名

| 输出音频 | 人工试听问题 |
|---|---|
| `base/game_terms/arataki_itto_game_terms_1.wav` | 停顿异常。 |
| `base/game_terms/arataki_itto_game_terms_2.wav` | 停顿异常，朗读不流畅。 |
| `base/game_terms/arataki_itto_game_terms_3.wav` | 停顿异常。 |
| `base/game_terms/paimon_game_terms_1.wav` | 停顿异常。 |
| `base/game_terms/paimon_game_terms_2.wav` | 停顿异常。 |
| `base/game_terms/paimon_game_terms_3.wav` | 停顿异常。 |
| `base/game_terms/zhongli_game_terms_1.wav` 至 `zhongli_game_terms_3.wav` | 停顿略有问题。 |

### 中文长文本

| 输出音频 | 人工试听问题 |
|---|---|
| `base/long_zh/arataki_itto_long_zh_1.wav` | 停顿异常，背景存在杂音。 |
| `base/long_zh/arataki_itto_long_zh_2.wav` | 音色不像角色，但停顿正确、朗读流畅。 |
| `base/long_zh/arataki_itto_long_zh_3.wav` | 音色偶尔漂移，稳定性不足。 |
| `base/long_zh/nahida_long_zh_1.wav` | 整体正常。 |
| `base/long_zh/nahida_long_zh_2.wav` | 音色漂移严重，听感中出现约三个不同音色。 |
| `base/long_zh/paimon_long_zh_1.wav` | 停顿异常、朗读不流畅、机械感重、重音错误。 |
| `base/long_zh/paimon_long_zh_2.wav` | 停顿异常、朗读不流畅、存在多个音色、重音错误。 |
| `base/long_zh/paimon_long_zh_3.wav` | 停顿异常、朗读不流畅、重音错误。 |
| `base/long_zh/zhongli_long_zh_3.wav` | 中间朗读出现短暂卡顿。 |

### 中英混合文本

| 输出音频 | 人工试听问题 |
|---|---|
| `base/mixed/arataki_itto_mixed_2.wav` | 语速稍快。 |
| `base/mixed/arataki_itto_mixed_3.wav` | 英语部分语速稍快。 |
| `base/mixed/nahida_mixed_1.wav` | 停顿异常。 |
| `base/mixed/nahida_mixed_3.wav` | 英语发音不清楚。 |
| `base/mixed/paimon_mixed_1.wav` | 停顿异常，英语部分发音不标准且不流畅。 |
| `base/mixed/paimon_mixed_2.wav` | 英语发音不标准，并出现多字。 |
| `base/mixed/paimon_mixed_3.wav` | 停顿异常、发音不标准、音色不稳定。 |

### 多音字文本

| 输出音频 | 人工试听问题 |
|---|---|
| `base/polyphone/arataki_itto_polyphone_1.wav` | 停顿异常，开头存在杂音。 |
| `base/polyphone/paimon_polyphone_1.wav` | 停顿异常，声音有气无力。 |
| `base/polyphone/paimon_polyphone_2.wav` | 朗读不流畅。 |

## 微调模型试听记录

### 英文文本

| 输出音频 | 人工试听问题 |
|---|---|
| `finetuned_best/english/nahida_english_2.wav` | 开头存在杂音，`system` 处发音不清晰。 |
| `finetuned_best/english/paimon_english_1.wav` | 声音有气无力，朗读不流畅。 |
| `finetuned_best/english/paimon_english_2.wav` | `system` 处发音不清晰。 |

### 游戏专有词与角色名

| 输出音频 | 人工试听问题或改善 |
|---|---|
| `finetuned_best/game_terms/arataki_itto_game_terms_2.wav` | 开头存在轻微噪声。 |
| `finetuned_best/game_terms/arataki_itto_game_terms_3.wav` | 起始存在噪声，停顿异常。 |
| `finetuned_best/game_terms/nahida_game_terms_1.wav` 至 `nahida_game_terms_3.wav` | 音色比基础模型更好。 |
| `finetuned_best/game_terms/paimon_game_terms_1.wav` | 停顿异常。 |
| `finetuned_best/game_terms/paimon_game_terms_2.wav` | 语速过慢。 |
| `finetuned_best/game_terms/paimon_game_terms_3.wav` | 存在轻微破音。 |
| `finetuned_best/game_terms/zhongli_game_terms_1.wav` 至 `zhongli_game_terms_3.wav` | 音色比基础模型稍好。 |

### 中文长文本

| 输出音频 | 人工试听问题或改善 |
|---|---|
| `finetuned_best/long_zh/arataki_itto_long_zh_1.wav` | 比基础模型更好，朗读流畅且未听到明显错误。 |
| `finetuned_best/long_zh/arataki_itto_long_zh_2.wav` | 音色不符合角色。 |
| `finetuned_best/long_zh/arataki_itto_long_zh_3.wav` | 停顿略有异常。 |
| `finetuned_best/long_zh/nahida_long_zh_1.wav` | 部分位置略有加速，其他表现正常。 |
| `finetuned_best/long_zh/nahida_long_zh_2.wav` | 整体正常。 |
| `finetuned_best/long_zh/paimon_long_zh_1.wav` | 语速过慢、声音有气无力、偶尔停顿异常。 |
| `finetuned_best/long_zh/zhongli_long_zh_1.wav` 至 `zhongli_long_zh_3.wav` | 音色比基础模型更好。 |

### 中英混合文本

| 输出音频 | 人工试听问题 |
|---|---|
| `finetuned_best/mixed/arataki_itto_mixed_2.wav` | 英语发音不标准，停顿异常。 |
| `finetuned_best/mixed/arataki_itto_mixed_3.wav` | 停顿异常。 |
| `finetuned_best/mixed/nahida_mixed_3.wav` | 英语发音不清楚。 |
| `finetuned_best/mixed/paimon_mixed_2.wav` | 存在明显问题，需要重点复听。 |
| `finetuned_best/mixed/paimon_mixed_3.wav` | 音色不稳定。 |

### 多音字与未见说话人

| 输出音频 | 人工试听问题 |
|---|---|
| `finetuned_best/polyphone/arataki_itto_polyphone_1.wav` | 停顿异常。 |
| `finetuned_best/polyphone/arataki_itto_polyphone_2.wav` | 停顿异常。 |
| `finetuned_best/polyphone/arataki_itto_polyphone_3.wav` | 停顿异常。 |
| `finetuned_best/unseen_zero_shot/aishell3_ssb0273_unseen_unseen_long.wav` | 约三处停顿异常。 |

## 人工对比结论

- 微调模型并非全面优于基础模型，改善主要集中在部分角色的音色与部分长文本流畅度。
- 荒泷一斗长文本第 1 条、纳西妲游戏文本、钟离长文本在微调后主观效果更好。
- 派蒙仍是稳定性问题最明显的角色，主要表现为语速过慢、有气无力、停顿异常、重音错误和音色漂移。
- 英文与中英混合文本中，`system`、英语片段发音、句间停顿仍是高频问题。
- 游戏专有词自动 CER/WER 很高，但人工试听显示主要问题不仅是发音，也包括停顿与流畅度。
- 自动指标显示微调模型总体略有提升，但人工试听证明其仍存在自动指标无法覆盖的明显问题。

