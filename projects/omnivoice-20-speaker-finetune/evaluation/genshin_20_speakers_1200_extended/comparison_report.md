# OmniVoice 原神 20 说话人微调扩展评估

## 实验条件

- 对比模型：基础模型与 1200 条训练数据微调后的最佳模型 `best`（checkpoint-200）。
- 已见说话人：Paimon、Zhongli、Nahida、Arataki Itto。
- 未见说话人：`AISHELL3_SSB0273_unseen`，参考音频来自 AISHELL-3，未参与原神数据微调。
- 测试类别：中文长文本、多音字、游戏专有词与角色名、中英混合、英文、未见说话人 zero-shot。
- 每个已见说话人对前五类各测试 3 条文本；未见说话人测试 3 条文本。
- 合计：每个模型 63 条输出，共 126 条输出。
- 推理条件：32 步、Batch 1、模型预热后计时、固定随机种子 0。
- 指标：Whisper medium CER/WER、拼音错误率、UTMOS、SIM-o、RTF。

## 总体多文本平均结果

| 模型 | 数量 | CER | WER | 带声调拼音错误率 | UTMOS | SIM-o | 平均 RTF | 总体 RTF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| base | 63 | 2.79% | 7.29% | 1.44% | 2.6409 | 0.6478 | 0.1042 | 0.0759 |
| finetuned_best | 63 | 2.64% | 7.08% | 1.02% | 2.6628 | 0.6494 | 0.1031 | 0.0759 |

## 分类平均结果

| 类别 | 模型 | 数量 | CER | WER | 带声调拼音错误率 | UTMOS | SIM-o | 平均 RTF | 总体 RTF |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 英文文本 | base | 12 | 0.00% | 0.00% | 0.00% | 3.4045 | 0.4839 | 0.1458 | 0.1034 |
| 英文文本 | finetuned_best | 12 | 0.00% | 0.00% | 0.00% | 3.3992 | 0.4951 | 0.1403 | 0.1013 |
| 游戏专有词与角色名文本 | base | 12 | 16.99% | 32.22% | 2.56% | 2.4528 | 0.6987 | 0.1080 | 0.0995 |
| 游戏专有词与角色名文本 | finetuned_best | 12 | 17.95% | 32.78% | 2.24% | 2.5004 | 0.6828 | 0.1078 | 0.0975 |
| 中文长文本 | base | 12 | 2.16% | 4.35% | 1.04% | 2.3061 | 0.6686 | 0.0490 | 0.0519 |
| 中文长文本 | finetuned_best | 12 | 2.00% | 4.21% | 0.80% | 2.2879 | 0.6888 | 0.0507 | 0.0538 |
| 中英混合文本 | base | 12 | 2.39% | 7.58% | 2.39% | 2.7461 | 0.6516 | 0.1077 | 0.0970 |
| 中英混合文本 | finetuned_best | 12 | 1.11% | 4.55% | 1.11% | 2.7315 | 0.6585 | 0.1067 | 0.0944 |
| 多音字文本 | base | 12 | 0.96% | 2.50% | 0.64% | 2.2544 | 0.7032 | 0.1101 | 0.1032 |
| 多音字文本 | finetuned_best | 12 | 1.60% | 3.12% | 0.96% | 2.3604 | 0.6849 | 0.1114 | 0.1024 |
| 未见说话人 zero-shot | base | 3 | 0.00% | 0.00% | 0.00% | 2.8019 | 0.7786 | 0.1058 | 0.0703 |
| 未见说话人 zero-shot | finetuned_best | 3 | 0.00% | 0.00% | 0.00% | 2.8002 | 0.7969 | 0.0977 | 0.0671 |

## 对比结论

- 总体：微调模型 CER 从 2.79% 降至 2.64%，WER 从 7.29% 降至 7.08%；UTMOS 与 SIM-o 均略有提高，整体 RTF 基本不变。
- 中文长文本：CER 从 2.16% 降至 2.00%，SIM-o 从 0.6686 升至 0.6888，但 UTMOS 略降。
- 多音字：微调后 CER 从 0.96% 升至 1.60%，说明当前微调没有提升多音字稳定性。
- 游戏专有词与角色名：两组错误率均明显偏高，微调后 CER 从 16.99% 升至 17.95%；需要专门增加角色名和专有词训练文本，并结合人工试听排除 ASR 误识别。
- 中英混合：微调后 CER 从 2.39% 降至 1.11%，WER 从 7.58% 降至 4.55%，是本轮改善最明显的类别。
- 英文：基础与微调模型 CER/WER 均为 0；微调模型 SIM-o 从 0.4839 升至 0.4951，未观察到明显英文能力退化。
- 未见说话人 zero-shot：两组 CER/WER 均为 0，微调模型 SIM-o 从 0.7786 升至 0.7969，当前测试中未出现明显泛化能力退化。

## 人工试听结论

- 微调模型并非全面优于基础模型，主要改善了部分角色的音色与部分长文本流畅度。
- 微调后的荒泷一斗长文本第 1 条、纳西妲游戏文本和钟离长文本主观表现更好。
- 派蒙仍存在较明显的停顿异常、语速过慢、有气无力、重音错误与音色漂移问题。
- 英文和中英混合文本中，`system` 等英语单词发音不清晰、英语片段不流畅及停顿异常较常见。
- 多个游戏专有词文本存在停顿与流畅度问题；高 CER/WER 不能完整反映这些主观缺陷。
- 长文本仍可能出现音色漂移、多个音色、机械感、卡顿和背景杂音。
- 未列出的输出整体表现稍微正常。完整逐条记录见 `manual_listening_evaluation.md`。

## 每条测试文本平均结果

| 测试文本 | 模型 | 数量 | CER | WER | 带声调拼音错误率 | UTMOS | SIM-o | 平均 RTF | 总体 RTF |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 英文文本 1 | base | 4 | 0.00% | 0.00% | 0.00% | 3.5209 | 0.4026 | 0.2656 | 0.2334 |
| 英文文本 1 | finetuned_best | 4 | 0.00% | 0.00% | 0.00% | 3.5338 | 0.4275 | 0.2483 | 0.2193 |
| 英文文本 2 | base | 4 | 0.00% | 0.00% | 0.00% | 3.2472 | 0.5071 | 0.0901 | 0.0836 |
| 英文文本 2 | finetuned_best | 4 | 0.00% | 0.00% | 0.00% | 3.2075 | 0.5381 | 0.0891 | 0.0827 |
| 英文文本 3 | base | 4 | 0.00% | 0.00% | 0.00% | 3.4455 | 0.5420 | 0.0818 | 0.0782 |
| 英文文本 3 | finetuned_best | 4 | 0.00% | 0.00% | 0.00% | 3.4564 | 0.5197 | 0.0834 | 0.0794 |
| 游戏专有词与角色名文本 1 | base | 4 | 3.41% | 9.62% | 1.14% | 2.3518 | 0.7248 | 0.1272 | 0.1198 |
| 游戏专有词与角色名文本 1 | finetuned_best | 4 | 4.55% | 11.54% | 1.14% | 2.4719 | 0.6885 | 0.1313 | 0.1200 |
| 游戏专有词与角色名文本 2 | base | 4 | 20.19% | 38.33% | 0.00% | 2.5687 | 0.6667 | 0.1075 | 0.1012 |
| 游戏专有词与角色名文本 2 | finetuned_best | 4 | 18.27% | 36.67% | 0.00% | 2.5591 | 0.6760 | 0.1015 | 0.0943 |
| 游戏专有词与角色名文本 3 | base | 4 | 24.17% | 44.12% | 5.83% | 2.4379 | 0.7048 | 0.0894 | 0.0834 |
| 游戏专有词与角色名文本 3 | finetuned_best | 4 | 27.50% | 45.59% | 5.00% | 2.4704 | 0.6841 | 0.0907 | 0.0840 |
| 中文长文本 1 | base | 4 | 3.02% | 5.43% | 1.01% | 2.1405 | 0.6974 | 0.0538 | 0.0559 |
| 中文长文本 1 | finetuned_best | 4 | 3.02% | 6.16% | 0.81% | 2.1015 | 0.6977 | 0.0549 | 0.0572 |
| 中文长文本 2 | base | 4 | 2.13% | 5.26% | 2.13% | 2.6062 | 0.6288 | 0.0461 | 0.0476 |
| 中文长文本 2 | finetuned_best | 4 | 1.60% | 3.95% | 1.60% | 2.5887 | 0.6826 | 0.0483 | 0.0500 |
| 中文长文本 3 | base | 4 | 1.05% | 1.92% | 0.00% | 2.1717 | 0.6797 | 0.0473 | 0.0508 |
| 中文长文本 3 | finetuned_best | 4 | 1.05% | 1.92% | 0.00% | 2.1735 | 0.6862 | 0.0490 | 0.0530 |
| 中英混合文本 1 | base | 4 | 1.67% | 5.00% | 1.67% | 2.6890 | 0.6861 | 0.1393 | 0.1292 |
| 中英混合文本 1 | finetuned_best | 4 | 2.50% | 7.50% | 2.50% | 2.7188 | 0.6907 | 0.1399 | 0.1279 |
| 中英混合文本 2 | base | 4 | 5.80% | 15.38% | 5.80% | 2.6341 | 0.6304 | 0.0947 | 0.0889 |
| 中英混合文本 2 | finetuned_best | 4 | 1.79% | 5.77% | 1.79% | 2.6311 | 0.6302 | 0.0956 | 0.0890 |
| 中英混合文本 3 | base | 4 | 0.00% | 0.00% | 0.00% | 2.9153 | 0.6384 | 0.0892 | 0.0843 |
| 中英混合文本 3 | finetuned_best | 4 | 0.00% | 0.00% | 0.00% | 2.8446 | 0.6548 | 0.0845 | 0.0792 |
| 多音字文本 1 | base | 4 | 2.88% | 7.69% | 1.92% | 2.1797 | 0.7137 | 0.1074 | 0.1010 |
| 多音字文本 1 | finetuned_best | 4 | 2.88% | 5.77% | 2.88% | 2.2185 | 0.6626 | 0.1096 | 0.1023 |
| 多音字文本 2 | base | 4 | 0.00% | 0.00% | 0.00% | 2.3847 | 0.6953 | 0.1149 | 0.1065 |
| 多音字文本 2 | finetuned_best | 4 | 0.00% | 0.00% | 0.00% | 2.5262 | 0.7096 | 0.1235 | 0.1123 |
| 多音字文本 3 | base | 4 | 0.00% | 0.00% | 0.00% | 2.1988 | 0.7005 | 0.1079 | 0.1025 |
| 多音字文本 3 | finetuned_best | 4 | 1.85% | 3.57% | 0.00% | 2.3365 | 0.6826 | 0.1010 | 0.0936 |
| 未见说话人长文本 | base | 1 | 0.00% | 0.00% | 0.00% | 2.5827 | 0.8305 | 0.0403 | 0.0403 |
| 未见说话人长文本 | finetuned_best | 1 | 0.00% | 0.00% | 0.00% | 2.5629 | 0.8285 | 0.0405 | 0.0405 |
| 未见说话人多音字文本 | base | 1 | 0.00% | 0.00% | 0.00% | 2.8316 | 0.7778 | 0.1214 | 0.1214 |
| 未见说话人多音字文本 | finetuned_best | 1 | 0.00% | 0.00% | 0.00% | 2.8377 | 0.7831 | 0.1158 | 0.1158 |
| 未见说话人短文本 | base | 1 | 0.00% | 0.00% | 0.00% | 2.9914 | 0.7276 | 0.1556 | 0.1556 |
| 未见说话人短文本 | finetuned_best | 1 | 0.00% | 0.00% | 0.00% | 2.9999 | 0.7790 | 0.1368 | 0.1368 |

## Whisper 回识别与输出音频

| 模型 | 类别 | 说话人 | 测试文本 | Whisper 回识别文本 | CER | WER | 输出音频 |
|---|---|---|---|---|---:|---:|---|
| base | 中文长文本 | Paimon | 今天我们进行一次长中文语音合成测试。系统需要准确朗读每一个词语，并在连续表达时保持稳定的音色、自然的语速和清晰的停顿。测试过程中，我们会关注是否出现漏字、重复、异常停顿或者声音漂移。最后，将结合生成耗时、字符错误率、词错误率、自然度和说话人相似度，对本次实验结果进行完整记录。 | 今天我們進行一次長中文語音合成測試系統需要準確朗讀每一個詞語並在連續表達時保持穩定的音色自然的語速和清晰的停頓測試過程中,我們會關注是否出現漏字、重複、異常停頓或者聲音飄移最後,將結合聲成耗時自符錯誤率、詞錯誤率、自然度和說話人相似度對,本次實驗結果進行完整記錄 | 2.42% | 4.35% | `outputs\genshin_20_speakers_1200_extended\base\long_zh\paimon_long_zh_1.wav` |
| base | 中文长文本 | Paimon | 清晨的城市逐渐苏醒，街道上的车辆和行人慢慢增多。有人准备开始一天的工作，有人带着早餐匆匆赶路，也有人在公园里安静地散步。随着阳光穿过云层，周围的建筑和树木显得更加清晰，新的一天也在平稳而有序的节奏中展开。 | 清晨的城市逐漸甦醒,街道上的車輛和行人慢慢增多,有人準備開始一天的工作。有人帶著早餐,匆匆趕路,也有人在公園裡安靜地散步,隨著陽光穿過雲層。周圍的建築和樹木顯得更加清晰,新的一天也在平穩而有序的節奏中展開。 | 2.13% | 5.26% | `outputs\genshin_20_speakers_1200_extended\base\long_zh\paimon_long_zh_2.wav` |
| base | 中文长文本 | Paimon | 为了验证语音系统在长时间连续表达中的稳定性，我们准备了一段包含多个句子和不同停顿位置的测试内容。模型不仅需要保证文字完整，还要控制合理的语速、重音与句间停顿，并尽量避免音色漂移、重复朗读或突然加速等问题。 | 為了驗證語音系統,在長時間連續表達中的穩定性我們準備了一段包含多個句子和不同停頓位置的測試、內容模型不僅需要保證文字完整,還要控制合理的語速重音與句間停頓,並盡量避免音色飄移、重複朗讀或突然加速等問題 | 1.05% | 1.92% | `outputs\genshin_20_speakers_1200_extended\base\long_zh\paimon_long_zh_3.wav` |
| base | 多音字文本 | Paimon | 银行门口的人沿着人行道行走，工作人员认真核对每一行记录。 | 銀行門口的人沿著人行道行走,工作人員認真,核對每一行記錄。 | 3.85% | 7.69% | `outputs\genshin_20_speakers_1200_extended\base\polyphone\paimon_polyphone_1.wav` |
| base | 多音字文本 | Paimon | 音乐老师强调快乐学习的重要性，并带领大家提高练习效率。 | 音樂老師強調,快樂學習的重要性,並帶領大家提高練習效率。 | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\base\polyphone\paimon_polyphone_2.wav` |
| base | 多音字文本 | Paimon | 他重新测量物品的重量，又重复检查数据，最后率领团队完成任务。 | 他重新測量物品的重量,又重複檢查數據,最後率領團隊完成任務。 | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\base\polyphone\paimon_polyphone_3.wav` |
| base | 游戏专有词与角色名文本 | Paimon | 派蒙和旅行者离开蒙德后，准备前往璃月港拜访钟离。 | 派蒙和旅行者離開蒙德後,準備前往璃月港拜訪。鍾離。 | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\base\game_terms\paimon_game_terms_1.wav` |
| base | 游戏专有词与角色名文本 | Paimon | 纳西妲在须弥城遇见艾尔海森和提纳里，并讨论世界树的变化。 | 納西達在虛謎城遇見艾爾·海森和提娜里,並討論世界術的變化。 | 19.23% | 40.00% | `outputs\genshin_20_speakers_1200_extended\base\game_terms\paimon_game_terms_2.wav` |
| base | 游戏专有词与角色名文本 | Paimon | 八重神子邀请雷电将军前往鸣神大社，荒泷一斗则在花见坂等待久岐忍。 | 八重神子邀請雷電將軍前往冥神大社, 荒龍一抖則在花、劍板等待,久其忍! | 20.00% | 47.06% | `outputs\genshin_20_speakers_1200_extended\base\game_terms\paimon_game_terms_3.wav` |
| base | 中英混合文本 | Paimon | 今天的 meeting 很顺利，我们下午继续测试 OmniVoice。 | 今天的Meeting很順利我們下午繼續測試Omnivice | 3.33% | 10.00% | `outputs\genshin_20_speakers_1200_extended\base\mixed\paimon_mixed_1.wav` |
| base | 中英混合文本 | Paimon | 系统会记录 generation time、audio duration 和 RTF，然后使用 Whisper 计算 CER 与 WER。 | 系統會記錄generation time, audio duration和RTF,然後使用Whisper,計算C1-2與WL1-2。 | 8.93% | 15.38% | `outputs\genshin_20_speakers_1200_extended\base\mixed\paimon_mixed_2.wav` |
| base | 中英混合文本 | Paimon | 完成 multilingual speech synthesis 测试后，我们将比较 speaker similarity 和 naturalness score。 | 完成Multilingual Speech Synthesis测试后我们将比较Speaker Similarity和Naturalness Score | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\base\mixed\paimon_mixed_3.wav` |
| base | 英文文本 | Paimon | Today is a good day to learn something new. | Today is a good day to learn something new. | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\base\english\paimon_english_1.wav` |
| base | 英文文本 | Paimon | The speech synthesis system should pronounce every word clearly and maintain a natural speaking rhythm. | The speech synthesis system should pronounce every word clearly and maintain a natural speaking rhythm. | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\base\english\paimon_english_2.wav` |
| base | 英文文本 | Paimon | During this evaluation, we compare pronunciation accuracy, generation speed, naturalness, and speaker similarity. | During this evaluation, we compare pronunciation accuracy, generation speed, naturalness, and speaker similarity. | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\base\english\paimon_english_3.wav` |
| base | 中文长文本 | Zhongli | 今天我们进行一次长中文语音合成测试。系统需要准确朗读每一个词语，并在连续表达时保持稳定的音色、自然的语速和清晰的停顿。测试过程中，我们会关注是否出现漏字、重复、异常停顿或者声音漂移。最后，将结合生成耗时、字符错误率、词错误率、自然度和说话人相似度，对本次实验结果进行完整记录。 | 今天我们进行一次常中文语音合成测试系统需要准确朗读每一个词语并在连续表达时保持稳定的音色自然的语速和清晰的听顿测试过程中,我们会关注是否出现漏字重复异常听顿或者声音飘移最后将结合生成耗时、字符错误率、词错误率自然度和说话人相似度对本次实验结果进行完整记录 | 3.23% | 5.80% | `outputs\genshin_20_speakers_1200_extended\base\long_zh\zhongli_long_zh_1.wav` |
| base | 中文长文本 | Zhongli | 清晨的城市逐渐苏醒，街道上的车辆和行人慢慢增多。有人准备开始一天的工作，有人带着早餐匆匆赶路，也有人在公园里安静地散步。随着阳光穿过云层，周围的建筑和树木显得更加清晰，新的一天也在平稳而有序的节奏中展开。 | 清晨的城市逐漸蘇醒,街道上的車輛和行人慢慢增多。有人準備開始一天的工作,有人帶著早餐匆匆趕路,也有人在公園裡安靜地散步。隨著陽光穿過雲層,周圍的建築和樹木顯得更加清晰,新的一天也在平穩而有序的節奏中展開。 | 2.13% | 5.26% | `outputs\genshin_20_speakers_1200_extended\base\long_zh\zhongli_long_zh_2.wav` |
| base | 中文长文本 | Zhongli | 为了验证语音系统在长时间连续表达中的稳定性，我们准备了一段包含多个句子和不同停顿位置的测试内容。模型不仅需要保证文字完整，还要控制合理的语速、重音与句间停顿，并尽量避免音色漂移、重复朗读或突然加速等问题。 | 为了验证语音系统在长时间连续表达中的稳定性,我们准备了一段包含多个句子和不同停顿位置的测试内容。模型不仅需要保证文字完整,还要控制合理的语速、重音与句间停顿,并尽量避免音色飘移、重复朗读或突然加速等问题。 | 1.05% | 1.92% | `outputs\genshin_20_speakers_1200_extended\base\long_zh\zhongli_long_zh_3.wav` |
| base | 多音字文本 | Zhongli | 银行门口的人沿着人行道行走，工作人员认真核对每一行记录。 | 银行门口的人沿着人行道行走,工作人员认真核对每一行记录。 | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\base\polyphone\zhongli_polyphone_1.wav` |
| base | 多音字文本 | Zhongli | 音乐老师强调快乐学习的重要性，并带领大家提高练习效率。 | 音樂老師強調快樂學習的重要性並帶領大家提高練習效率 | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\base\polyphone\zhongli_polyphone_2.wav` |
| base | 多音字文本 | Zhongli | 他重新测量物品的重量，又重复检查数据，最后率领团队完成任务。 | 他重新测量物品的重量,又重复检查数据,最后率领团队完成任务。 | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\base\polyphone\zhongli_polyphone_3.wav` |
| base | 游戏专有词与角色名文本 | Zhongli | 派蒙和旅行者离开蒙德后，准备前往璃月港拜访钟离。 | 派盟和旅行者離開蒙德後,準備前往璃月港拜訪鍾離。 | 4.55% | 15.38% | `outputs\genshin_20_speakers_1200_extended\base\game_terms\zhongli_game_terms_1.wav` |
| base | 游戏专有词与角色名文本 | Zhongli | 纳西妲在须弥城遇见艾尔海森和提纳里，并讨论世界树的变化。 | 納西達在虛謎城遇見艾爾·海森和提那里,並討論世界術的變化。 | 19.23% | 40.00% | `outputs\genshin_20_speakers_1200_extended\base\game_terms\zhongli_game_terms_2.wav` |
| base | 游戏专有词与角色名文本 | Zhongli | 八重神子邀请雷电将军前往鸣神大社，荒泷一斗则在花见坂等待久岐忍。 | 八重神子邀請雷電將軍前往明神大社荒龍一斗,則在花劍版等待九騎人。 | 23.33% | 41.18% | `outputs\genshin_20_speakers_1200_extended\base\game_terms\zhongli_game_terms_3.wav` |
| base | 中英混合文本 | Zhongli | 今天的 meeting 很顺利，我们下午继续测试 OmniVoice。 | 今天的Meeting很顺利,我们下午继续测试OmniVoice。 | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\base\mixed\zhongli_mixed_1.wav` |
| base | 中英混合文本 | Zhongli | 系统会记录 generation time、audio duration 和 RTF，然后使用 Whisper 计算 CER 与 WER。 | 系统会记录 Generation Time Audio Duration 和 RTF,然后使用 Whisper 计算,CR 与 W2。 | 5.36% | 15.38% | `outputs\genshin_20_speakers_1200_extended\base\mixed\zhongli_mixed_2.wav` |
| base | 中英混合文本 | Zhongli | 完成 multilingual speech synthesis 测试后，我们将比较 speaker similarity 和 naturalness score。 | 完成Multilingual Speech Synthesis测试后,我们将比较Speaker Similarity和Naturalness Score。 | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\base\mixed\zhongli_mixed_3.wav` |
| base | 英文文本 | Zhongli | Today is a good day to learn something new. | Today is a good day to learn something new. | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\base\english\zhongli_english_1.wav` |
| base | 英文文本 | Zhongli | The speech synthesis system should pronounce every word clearly and maintain a natural speaking rhythm. | The speech synthesis system should pronounce every word clearly and maintain a natural speaking rhythm. | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\base\english\zhongli_english_2.wav` |
| base | 英文文本 | Zhongli | During this evaluation, we compare pronunciation accuracy, generation speed, naturalness, and speaker similarity. | During this evaluation, we compare pronunciation accuracy, generation speed, naturalness, and speaker similarity. | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\base\english\zhongli_english_3.wav` |
| base | 中文长文本 | Nahida | 今天我们进行一次长中文语音合成测试。系统需要准确朗读每一个词语，并在连续表达时保持稳定的音色、自然的语速和清晰的停顿。测试过程中，我们会关注是否出现漏字、重复、异常停顿或者声音漂移。最后，将结合生成耗时、字符错误率、词错误率、自然度和说话人相似度，对本次实验结果进行完整记录。 | 今天我們進行一次長中文語音合成測試系統需要準確朗讀每一個詞語並在連續表達時保持穩定的音色、自然的語速和清晰的停頓測試過程中我們會關注是否出現漏字重複一長停頓或者聲音飄移最後將結合聲成耗時自符錯誤率、詞錯誤率自然度和說話人相似度對本次實驗結果進行完整記錄 | 4.03% | 5.80% | `outputs\genshin_20_speakers_1200_extended\base\long_zh\nahida_long_zh_1.wav` |
| base | 中文长文本 | Nahida | 清晨的城市逐渐苏醒，街道上的车辆和行人慢慢增多。有人准备开始一天的工作，有人带着早餐匆匆赶路，也有人在公园里安静地散步。随着阳光穿过云层，周围的建筑和树木显得更加清晰，新的一天也在平稳而有序的节奏中展开。 | 清晨的城市逐漸蘇醒街道上的車輛和行人慢慢增多有人準備開始一天的工作有人帶著早餐匆匆趕路也有人在公園裡安靜地散步隨著陽光穿過雲層周圍的建築和樹木顯得更加清晰新的一天也在平穩而有序的節奏中展開 | 2.13% | 5.26% | `outputs\genshin_20_speakers_1200_extended\base\long_zh\nahida_long_zh_2.wav` |
| base | 中文长文本 | Nahida | 为了验证语音系统在长时间连续表达中的稳定性，我们准备了一段包含多个句子和不同停顿位置的测试内容。模型不仅需要保证文字完整，还要控制合理的语速、重音与句间停顿，并尽量避免音色漂移、重复朗读或突然加速等问题。 | 為了驗證語音系統在長時間連續表達中的穩定性我們準備了一段包含多個句子和不同停頓位置的測試內容模型不僅需要保證文字完整,還要控制合理的語速重音與句間停頓,並盡量避免音色飄移、重複朗讀或突然加速等問題 | 1.05% | 1.92% | `outputs\genshin_20_speakers_1200_extended\base\long_zh\nahida_long_zh_3.wav` |
| base | 多音字文本 | Nahida | 银行门口的人沿着人行道行走，工作人员认真核对每一行记录。 | 銀行門口的人沿著人行道行走工作人員認真核對每一行記錄 | 3.85% | 7.69% | `outputs\genshin_20_speakers_1200_extended\base\polyphone\nahida_polyphone_1.wav` |
| base | 多音字文本 | Nahida | 音乐老师强调快乐学习的重要性，并带领大家提高练习效率。 | 音樂老師強調快樂學習的重要性並帶領大家提高練習效率 | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\base\polyphone\nahida_polyphone_2.wav` |
| base | 多音字文本 | Nahida | 他重新测量物品的重量，又重复检查数据，最后率领团队完成任务。 | 他重新測量物品的重量 又重複檢查數據最後率領團隊完成任務 | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\base\polyphone\nahida_polyphone_3.wav` |
| base | 游戏专有词与角色名文本 | Nahida | 派蒙和旅行者离开蒙德后，准备前往璃月港拜访钟离。 | 派蒙和旅行者離開蒙德後 準備前往璃月港拜訪鍾離 | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\base\game_terms\nahida_game_terms_1.wav` |
| base | 游戏专有词与角色名文本 | Nahida | 纳西妲在须弥城遇见艾尔海森和提纳里，并讨论世界树的变化。 | 納西達在虛謎城遇見艾爾海森和提娜里,並討論世界術的變化。 | 19.23% | 40.00% | `outputs\genshin_20_speakers_1200_extended\base\game_terms\nahida_game_terms_2.wav` |
| base | 游戏专有词与角色名文本 | Nahida | 八重神子邀请雷电将军前往鸣神大社，荒泷一斗则在花见坂等待久岐忍。 | 八重神子邀請雷電將軍前往明神大社荒廊一抖則在花劍版等待九騎人 | 26.67% | 47.06% | `outputs\genshin_20_speakers_1200_extended\base\game_terms\nahida_game_terms_3.wav` |
| base | 中英混合文本 | Nahida | 今天的 meeting 很顺利，我们下午继续测试 OmniVoice。 | 今天的Meeting很順利,我們下午繼續測試OmniVoice | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\base\mixed\nahida_mixed_1.wav` |
| base | 中英混合文本 | Nahida | 系统会记录 generation time、audio duration 和 RTF，然后使用 Whisper 计算 CER 与 WER。 | 系统会记录Generation Time Audio Duration和RTF,然后使用Whisper计算CR与WR。 | 3.57% | 15.38% | `outputs\genshin_20_speakers_1200_extended\base\mixed\nahida_mixed_2.wav` |
| base | 中英混合文本 | Nahida | 完成 multilingual speech synthesis 测试后，我们将比较 speaker similarity 和 naturalness score。 | 完成Multilingual Speech Synthesis 测试后,我们将比较Speaker Similarity和Naturalness Score。 | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\base\mixed\nahida_mixed_3.wav` |
| base | 英文文本 | Nahida | Today is a good day to learn something new. | Today is a good day to learn something new. | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\base\english\nahida_english_1.wav` |
| base | 英文文本 | Nahida | The speech synthesis system should pronounce every word clearly and maintain a natural speaking rhythm. | The speech synthesis system should pronounce every word clearly and maintain a natural speaking rhythm. | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\base\english\nahida_english_2.wav` |
| base | 英文文本 | Nahida | During this evaluation, we compare pronunciation accuracy, generation speed, naturalness, and speaker similarity. | During this evaluation, we compare pronunciation accuracy, generation speed, naturalness, and speaker similarity. | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\base\english\nahida_english_3.wav` |
| base | 中文长文本 | Arataki Itto | 今天我们进行一次长中文语音合成测试。系统需要准确朗读每一个词语，并在连续表达时保持稳定的音色、自然的语速和清晰的停顿。测试过程中，我们会关注是否出现漏字、重复、异常停顿或者声音漂移。最后，将结合生成耗时、字符错误率、词错误率、自然度和说话人相似度，对本次实验结果进行完整记录。 | 今天我们进行一次长中文语音合成测试系统需要准确朗读每一个词语并在连续表达时保持稳定的音色自然的语速和清晰的停顿测试过程中我们会关注是否出现漏字重复异常停顿或者声音飘移最后将结合声、成号时、字符、错误率词错误率、自然度和说话人相似度对本次实验结果进行完整记录 | 2.42% | 5.80% | `outputs\genshin_20_speakers_1200_extended\base\long_zh\arataki_itto_long_zh_1.wav` |
| base | 中文长文本 | Arataki Itto | 清晨的城市逐渐苏醒，街道上的车辆和行人慢慢增多。有人准备开始一天的工作，有人带着早餐匆匆赶路，也有人在公园里安静地散步。随着阳光穿过云层，周围的建筑和树木显得更加清晰，新的一天也在平稳而有序的节奏中展开。 | 清晨的城市逐漸蘇醒,街道上的車輛和行人慢慢增多有人準備開始一天的工作,有人帶著早餐匆匆趕路也有人在公園裡安靜地散步隨著陽光穿過雲層,周圍的建築和樹木顯得更加清晰新的一天也在平穩而有序的節奏中展開 | 2.13% | 5.26% | `outputs\genshin_20_speakers_1200_extended\base\long_zh\arataki_itto_long_zh_2.wav` |
| base | 中文长文本 | Arataki Itto | 为了验证语音系统在长时间连续表达中的稳定性，我们准备了一段包含多个句子和不同停顿位置的测试内容。模型不仅需要保证文字完整，还要控制合理的语速、重音与句间停顿，并尽量避免音色漂移、重复朗读或突然加速等问题。 | 为了验证语音系统在长时间连续表达中的稳定性我们准备了一段包含多个句子和不同停顿位置的测试内容模型不仅需要保证文字完整还要控制合理的语速重音与句间停顿并尽量避免音色飘移重复朗读或突然加速等问题 | 1.05% | 1.92% | `outputs\genshin_20_speakers_1200_extended\base\long_zh\arataki_itto_long_zh_3.wav` |
| base | 多音字文本 | Arataki Itto | 银行门口的人沿着人行道行走，工作人员认真核对每一行记录。 | 银行门口的人 沿着人行倒行走工作人员认真核对每一行记录 | 3.85% | 15.38% | `outputs\genshin_20_speakers_1200_extended\base\polyphone\arataki_itto_polyphone_1.wav` |
| base | 多音字文本 | Arataki Itto | 音乐老师强调快乐学习的重要性，并带领大家提高练习效率。 | 音乐老师强调快乐学习的重要性并带领大家提高练习效率 | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\base\polyphone\arataki_itto_polyphone_2.wav` |
| base | 多音字文本 | Arataki Itto | 他重新测量物品的重量，又重复检查数据，最后率领团队完成任务。 | 他重新测量物品的重量又重复检查数据最后,率领团队完成任务 | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\base\polyphone\arataki_itto_polyphone_3.wav` |
| base | 游戏专有词与角色名文本 | Arataki Itto | 派蒙和旅行者离开蒙德后，准备前往璃月港拜访钟离。 | 派门和旅行者离开蒙德厚准备前往璃月港拜访钟离 | 9.09% | 23.08% | `outputs\genshin_20_speakers_1200_extended\base\game_terms\arataki_itto_game_terms_1.wav` |
| base | 游戏专有词与角色名文本 | Arataki Itto | 纳西妲在须弥城遇见艾尔海森和提纳里，并讨论世界树的变化。 | 那希达在虛谜城遇见艾尔海森和提纳里,并讨论世界术的变化。 | 23.08% | 33.33% | `outputs\genshin_20_speakers_1200_extended\base\game_terms\arataki_itto_game_terms_2.wav` |
| base | 游戏专有词与角色名文本 | Arataki Itto | 八重神子邀请雷电将军前往鸣神大社，荒泷一斗则在花见坂等待久岐忍。 | 八重神子邀请雷电将军前往明神大社慌龙一斗则在花剑版等待九七人 | 26.67% | 41.18% | `outputs\genshin_20_speakers_1200_extended\base\game_terms\arataki_itto_game_terms_3.wav` |
| base | 中英混合文本 | Arataki Itto | 今天的 meeting 很顺利，我们下午继续测试 OmniVoice。 | 今天的Meeting很順利我們下午繼續測試Omnivice | 3.33% | 10.00% | `outputs\genshin_20_speakers_1200_extended\base\mixed\arataki_itto_mixed_1.wav` |
| base | 中英混合文本 | Arataki Itto | 系统会记录 generation time、audio duration 和 RTF，然后使用 Whisper 计算 CER 与 WER。 | 系統會記錄 Generation Time, Audio Duration 和 RTF然後使用 Whisper 計算,CR 與 W2 | 5.36% | 15.38% | `outputs\genshin_20_speakers_1200_extended\base\mixed\arataki_itto_mixed_2.wav` |
| base | 中英混合文本 | Arataki Itto | 完成 multilingual speech synthesis 测试后，我们将比较 speaker similarity 和 naturalness score。 | 完成Multilingual Speech Synthesis测试后,我们将比较Speaker Similarity和Naturalness Score | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\base\mixed\arataki_itto_mixed_3.wav` |
| base | 英文文本 | Arataki Itto | Today is a good day to learn something new. | Today is a good day to learn something new! | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\base\english\arataki_itto_english_1.wav` |
| base | 英文文本 | Arataki Itto | The speech synthesis system should pronounce every word clearly and maintain a natural speaking rhythm. | The speech synthesis system should pronounce every word clearly and maintain a natural speaking rhythm! | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\base\english\arataki_itto_english_2.wav` |
| base | 英文文本 | Arataki Itto | During this evaluation, we compare pronunciation accuracy, generation speed, naturalness, and speaker similarity. | During this evaluation, we compare pronunciation accuracy, generation speed, naturalness, and speaker similarity. | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\base\english\arataki_itto_english_3.wav` |
| base | 未见说话人 zero-shot | AISHELL3_SSB0273_unseen | 今天阳光很好，我们准备开始新的语音合成测试。 | 今天阳光很好,我们准备开始新的语音合成测试。 | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\base\unseen_zero_shot\aishell3_ssb0273_unseen_unseen_short.wav` |
| base | 未见说话人 zero-shot | AISHELL3_SSB0273_unseen | 银行门口的人沿着人行道行走，音乐老师正在提高练习效率。 | 银行门口的人沿着人行道行走音乐老师正在提高练习效率 | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\base\unseen_zero_shot\aishell3_ssb0273_unseen_unseen_polyphone.wav` |
| base | 未见说话人 zero-shot | AISHELL3_SSB0273_unseen | 今天我们使用一段从未参与微调的说话人音频进行零样本声音克隆测试。系统需要准确生成目标文本，同时保持参考音频中的音色特征、自然语速和清晰停顿。测试完成后，我们会比较基础模型和微调模型在未见说话人上的泛化能力。 | 今天我们使用一段从未参与微调的说话人音频进行零样本声音克隆测试系统需要准确生成目标文本同时保持参考音频中的音色特征、自然语速和清晰停顿测试完成后,我们会比较基础模型和微调模型在未见说话人上的泛化能力 | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\base\unseen_zero_shot\aishell3_ssb0273_unseen_unseen_long.wav` |
| finetuned_best | 中文长文本 | Paimon | 今天我们进行一次长中文语音合成测试。系统需要准确朗读每一个词语，并在连续表达时保持稳定的音色、自然的语速和清晰的停顿。测试过程中，我们会关注是否出现漏字、重复、异常停顿或者声音漂移。最后，将结合生成耗时、字符错误率、词错误率、自然度和说话人相似度，对本次实验结果进行完整记录。 | 今天我們進行一次長中文語音合成測試系統需要準確朗讀每一個詞語並在連續表達時使保持穩定的音色、自然的語速和清晰的停頓測試過程中,我們會關注是否出現漏字、重複、異常停頓或者聲音飄移最後,將結合聲成耗時、字符錯誤率、詞錯誤率、自然度和說話人相似度對,本次實驗結果進行完整記錄 | 2.42% | 4.35% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\long_zh\paimon_long_zh_1.wav` |
| finetuned_best | 中文长文本 | Paimon | 清晨的城市逐渐苏醒，街道上的车辆和行人慢慢增多。有人准备开始一天的工作，有人带着早餐匆匆赶路，也有人在公园里安静地散步。随着阳光穿过云层，周围的建筑和树木显得更加清晰，新的一天也在平稳而有序的节奏中展开。 | 清晨的城市逐漸甦醒,街道上的車輛和行人慢慢增多,有人準備開始一天的工作。有人帶著早餐匆匆趕路,也有人在公園裡安靜地散步,隨著陽光穿過雲層,周圍的建築和樹木顯得更加清晰,新的一天也在平穩而有序的節奏中展開。 | 2.13% | 5.26% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\long_zh\paimon_long_zh_2.wav` |
| finetuned_best | 中文长文本 | Paimon | 为了验证语音系统在长时间连续表达中的稳定性，我们准备了一段包含多个句子和不同停顿位置的测试内容。模型不仅需要保证文字完整，还要控制合理的语速、重音与句间停顿，并尽量避免音色漂移、重复朗读或突然加速等问题。 | 為了驗證語音系統,在長時間連續表達中的穩定性我們準備了一段包含多個句子和不同停頓位置的測試內容模型不僅需要保證文字完整,還要控制合理的語速、重音與句間停頓並盡量避免音色飄移、重複、朗讀或突然加速等問題 | 1.05% | 1.92% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\long_zh\paimon_long_zh_3.wav` |
| finetuned_best | 多音字文本 | Paimon | 银行门口的人沿着人行道行走，工作人员认真核对每一行记录。 | 銀行門口的人,沿著人行道行走,工作,人員認真核對每一行記錄。 | 3.85% | 7.69% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\polyphone\paimon_polyphone_1.wav` |
| finetuned_best | 多音字文本 | Paimon | 音乐老师强调快乐学习的重要性，并带领大家提高练习效率。 | 音乐老师强调快乐学习的重要性,并带领大家提高练习效率。 | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\polyphone\paimon_polyphone_2.wav` |
| finetuned_best | 多音字文本 | Paimon | 他重新测量物品的重量，又重复检查数据，最后率领团队完成任务。 | 她重新測量,物品的重量又重複,檢查數據,最後率領團隊完成任務。 | 3.70% | 7.14% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\polyphone\paimon_polyphone_3.wav` |
| finetuned_best | 游戏专有词与角色名文本 | Paimon | 派蒙和旅行者离开蒙德后，准备前往璃月港拜访钟离。 | 派蒙和旅行者離開蒙德後,準備前往璃月港拜訪。鍾離? | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\game_terms\paimon_game_terms_1.wav` |
| finetuned_best | 游戏专有词与角色名文本 | Paimon | 纳西妲在须弥城遇见艾尔海森和提纳里，并讨论世界树的变化。 | 納西達在虛謎城遇見艾爾海森和提娜里,並討論世界術的變化。 | 19.23% | 40.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\game_terms\paimon_game_terms_2.wav` |
| finetuned_best | 游戏专有词与角色名文本 | Paimon | 八重神子邀请雷电将军前往鸣神大社，荒泷一斗则在花见坂等待久岐忍。 | 八重神子邀請雷電將軍前往冥神大社慌龍一抖,則在花劍板等待九騎人 | 30.00% | 47.06% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\game_terms\paimon_game_terms_3.wav` |
| finetuned_best | 中英混合文本 | Paimon | 今天的 meeting 很顺利，我们下午继续测试 OmniVoice。 | 今天的Meeting很順利,我們下午繼續測試Omnivice | 3.33% | 10.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\mixed\paimon_mixed_1.wav` |
| finetuned_best | 中英混合文本 | Paimon | 系统会记录 generation time、audio duration 和 RTF，然后使用 Whisper 计算 CER 与 WER。 | 系統會記錄generation time audio duration和RTF然後使用Whisper計算CER與WER | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\mixed\paimon_mixed_2.wav` |
| finetuned_best | 中英混合文本 | Paimon | 完成 multilingual speech synthesis 测试后，我们将比较 speaker similarity 和 naturalness score。 | 完成Multilingual Speech Synthesis測試後我們將比較Speaker Similarity和Naturalness Score | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\mixed\paimon_mixed_3.wav` |
| finetuned_best | 英文文本 | Paimon | Today is a good day to learn something new. | Today is a good day to learn something new. | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\english\paimon_english_1.wav` |
| finetuned_best | 英文文本 | Paimon | The speech synthesis system should pronounce every word clearly and maintain a natural speaking rhythm. | The speech synthesis system should pronounce every word clearly and maintain a natural speaking rhythm. | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\english\paimon_english_2.wav` |
| finetuned_best | 英文文本 | Paimon | During this evaluation, we compare pronunciation accuracy, generation speed, naturalness, and speaker similarity. | During this evaluation, we compare pronunciation accuracy, generation speed, naturalness, and speaker similarity. | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\english\paimon_english_3.wav` |
| finetuned_best | 中文长文本 | Zhongli | 今天我们进行一次长中文语音合成测试。系统需要准确朗读每一个词语，并在连续表达时保持稳定的音色、自然的语速和清晰的停顿。测试过程中，我们会关注是否出现漏字、重复、异常停顿或者声音漂移。最后，将结合生成耗时、字符错误率、词错误率、自然度和说话人相似度，对本次实验结果进行完整记录。 | 今天我们进行一次常中文语音合成测试系统需要准确朗读每一个词语并在连续表达时保持稳定的音色自然的语速和清晰的停顿测试过程中我们会关注是否出现漏字重复异常停顿或者声音飘移最后将结合生成耗时字符错误率、词错误率自然度和说话人相似度对本次实验结果进行完整记录 | 1.61% | 2.90% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\long_zh\zhongli_long_zh_1.wav` |
| finetuned_best | 中文长文本 | Zhongli | 清晨的城市逐渐苏醒，街道上的车辆和行人慢慢增多。有人准备开始一天的工作，有人带着早餐匆匆赶路，也有人在公园里安静地散步。随着阳光穿过云层，周围的建筑和树木显得更加清晰，新的一天也在平稳而有序的节奏中展开。 | 清晨的城市逐漸蘇醒,街道上的車輛和行人慢慢增多。有人準備開始一天的工作,有人帶著早餐匆匆趕路,也有人在公園裡安靜地散步,隨著陽光穿過雲層,周圍的建築和樹木顯得更加清晰。新的一天也在平穩而有序的節奏中展開。 | 2.13% | 5.26% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\long_zh\zhongli_long_zh_2.wav` |
| finetuned_best | 中文长文本 | Zhongli | 为了验证语音系统在长时间连续表达中的稳定性，我们准备了一段包含多个句子和不同停顿位置的测试内容。模型不仅需要保证文字完整，还要控制合理的语速、重音与句间停顿，并尽量避免音色漂移、重复朗读或突然加速等问题。 | 为了验证语音系统在长时间连续表达中的稳定性我们准备了一段包含多个句子和不同停顿位置的测试内容模型不仅需要保证文字完整还要控制合理的语速、重音与句间停顿并尽量避免音色飘移、重复朗读或突然加速等问题 | 1.05% | 1.92% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\long_zh\zhongli_long_zh_3.wav` |
| finetuned_best | 多音字文本 | Zhongli | 银行门口的人沿着人行道行走，工作人员认真核对每一行记录。 | 銀行門口的人沿著人行道行走,工作人員認真核對每一行記錄。 | 3.85% | 7.69% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\polyphone\zhongli_polyphone_1.wav` |
| finetuned_best | 多音字文本 | Zhongli | 音乐老师强调快乐学习的重要性，并带领大家提高练习效率。 | 音乐老师强调快乐学习的重要性,并带领大家提高练习效率。 | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\polyphone\zhongli_polyphone_2.wav` |
| finetuned_best | 多音字文本 | Zhongli | 他重新测量物品的重量，又重复检查数据，最后率领团队完成任务。 | 它重新測量物品的重量,又重複檢查數據,最後率領團隊完成任務。 | 3.70% | 7.14% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\polyphone\zhongli_polyphone_3.wav` |
| finetuned_best | 游戏专有词与角色名文本 | Zhongli | 派蒙和旅行者离开蒙德后，准备前往璃月港拜访钟离。 | 派盟和旅行者離開蒙德後準備前往璃月港拜訪鍾離 | 4.55% | 15.38% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\game_terms\zhongli_game_terms_1.wav` |
| finetuned_best | 游戏专有词与角色名文本 | Zhongli | 纳西妲在须弥城遇见艾尔海森和提纳里，并讨论世界树的变化。 | 納西達在虛謎城遇見艾爾·海森和提那里並討論世界術的變化。 | 19.23% | 40.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\game_terms\zhongli_game_terms_2.wav` |
| finetuned_best | 游戏专有词与角色名文本 | Zhongli | 八重神子邀请雷电将军前往鸣神大社，荒泷一斗则在花见坂等待久岐忍。 | 八重神子邀請雷電將軍前往明神大社,荒龍一斗則在花劍版等待九騎人。 | 23.33% | 41.18% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\game_terms\zhongli_game_terms_3.wav` |
| finetuned_best | 中英混合文本 | Zhongli | 今天的 meeting 很顺利，我们下午继续测试 OmniVoice。 | 今天的Meeting很顺利,我们下午继续测试Omnivice。 | 3.33% | 10.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\mixed\zhongli_mixed_1.wav` |
| finetuned_best | 中英混合文本 | Zhongli | 系统会记录 generation time、audio duration 和 RTF，然后使用 Whisper 计算 CER 与 WER。 | 系统会记录 Generation Time, Audio Duration 和 RTF,然后使用 Whisper 计算,CER 与 W2。 | 3.57% | 7.69% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\mixed\zhongli_mixed_2.wav` |
| finetuned_best | 中英混合文本 | Zhongli | 完成 multilingual speech synthesis 测试后，我们将比较 speaker similarity 和 naturalness score。 | 完成Multilingual Speech Synthesis,测试后,我们将比较Speaker Similarity和Naturalness Score。 | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\mixed\zhongli_mixed_3.wav` |
| finetuned_best | 英文文本 | Zhongli | Today is a good day to learn something new. | Today is a good day to learn something new. | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\english\zhongli_english_1.wav` |
| finetuned_best | 英文文本 | Zhongli | The speech synthesis system should pronounce every word clearly and maintain a natural speaking rhythm. | The speech synthesis system should pronounce every word clearly and maintain a natural speaking rhythm. | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\english\zhongli_english_2.wav` |
| finetuned_best | 英文文本 | Zhongli | During this evaluation, we compare pronunciation accuracy, generation speed, naturalness, and speaker similarity. | During this evaluation, we compare pronunciation accuracy, generation speed, naturalness, and speaker similarity. | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\english\zhongli_english_3.wav` |
| finetuned_best | 中文长文本 | Nahida | 今天我们进行一次长中文语音合成测试。系统需要准确朗读每一个词语，并在连续表达时保持稳定的音色、自然的语速和清晰的停顿。测试过程中，我们会关注是否出现漏字、重复、异常停顿或者声音漂移。最后，将结合生成耗时、字符错误率、词错误率、自然度和说话人相似度，对本次实验结果进行完整记录。 | 今天我們進行一次常中文語音合成測試系統需要準確朗讀每一個詞語並在連續表達時保持穩定的音色自然的語速和清晰的停頓測試過程中我們會關注是否出現漏字重複異常停頓或者聲音飄移最後將結合聲成號時字符錯誤律詞錯誤律自然度和說話人相似度對本次實驗結果進行完整記錄 | 4.84% | 13.04% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\long_zh\nahida_long_zh_1.wav` |
| finetuned_best | 中文长文本 | Nahida | 清晨的城市逐渐苏醒，街道上的车辆和行人慢慢增多。有人准备开始一天的工作，有人带着早餐匆匆赶路，也有人在公园里安静地散步。随着阳光穿过云层，周围的建筑和树木显得更加清晰，新的一天也在平稳而有序的节奏中展开。 | 清晨的城市逐漸蘇醒,街道上的車輛和行人慢慢增多有人準備開始一天的工作,有人帶著早餐匆匆趕路也有人在公園裡安靜地散步,隨著陽光穿過雲層周圍的建築和樹木顯得更加清晰新的一天也在平穩而有序的節奏中展開 | 2.13% | 5.26% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\long_zh\nahida_long_zh_2.wav` |
| finetuned_best | 中文长文本 | Nahida | 为了验证语音系统在长时间连续表达中的稳定性，我们准备了一段包含多个句子和不同停顿位置的测试内容。模型不仅需要保证文字完整，还要控制合理的语速、重音与句间停顿，并尽量避免音色漂移、重复朗读或突然加速等问题。 | 為了驗證語音系統在長時間連續表達中的穩定性我們準備了一段包含多個句子和不同停頓位置的測試內容模型不僅需要保證文字完整還要控制合理的語速、重音與句間停頓並盡量避免音色飄移、重複朗讀或突然加速等問題 | 1.05% | 1.92% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\long_zh\nahida_long_zh_3.wav` |
| finetuned_best | 多音字文本 | Nahida | 银行门口的人沿着人行道行走，工作人员认真核对每一行记录。 | 銀行門口的人沿著人行道行走工作人員認真核對每一行記錄 | 3.85% | 7.69% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\polyphone\nahida_polyphone_1.wav` |
| finetuned_best | 多音字文本 | Nahida | 音乐老师强调快乐学习的重要性，并带领大家提高练习效率。 | 音乐老师强调快乐学习的重要性,并带领大家提高练习效率。 | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\polyphone\nahida_polyphone_2.wav` |
| finetuned_best | 多音字文本 | Nahida | 他重新测量物品的重量，又重复检查数据，最后率领团队完成任务。 | 他重新測量物品的重量 又重複檢查數據最後率領團隊完成任務 | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\polyphone\nahida_polyphone_3.wav` |
| finetuned_best | 游戏专有词与角色名文本 | Nahida | 派蒙和旅行者离开蒙德后，准备前往璃月港拜访钟离。 | 派蒙和旅行者離開蒙德後,準備前往璃月港拜訪鍾琳。 | 4.55% | 7.69% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\game_terms\nahida_game_terms_1.wav` |
| finetuned_best | 游戏专有词与角色名文本 | Nahida | 纳西妲在须弥城遇见艾尔海森和提纳里，并讨论世界树的变化。 | 納西達在虛謎城遇見艾爾海森和提娜里並討論世界術的變化 | 19.23% | 40.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\game_terms\nahida_game_terms_2.wav` |
| finetuned_best | 游戏专有词与角色名文本 | Nahida | 八重神子邀请雷电将军前往鸣神大社，荒泷一斗则在花见坂等待久岐忍。 | 八重神子邀請雷電將軍前往明神大社慌龍一抖則在花劍版等待九騎人 | 30.00% | 47.06% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\game_terms\nahida_game_terms_3.wav` |
| finetuned_best | 中英混合文本 | Nahida | 今天的 meeting 很顺利，我们下午继续测试 OmniVoice。 | 今天的Meeting很順利我們下午繼續測試OmniVoice | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\mixed\nahida_mixed_1.wav` |
| finetuned_best | 中英混合文本 | Nahida | 系统会记录 generation time、audio duration 和 RTF，然后使用 Whisper 计算 CER 与 WER。 | 系統會記錄Generation Time, Audio Duration和RTF,然後使用Whisper計算CR與WR。 | 3.57% | 15.38% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\mixed\nahida_mixed_2.wav` |
| finetuned_best | 中英混合文本 | Nahida | 完成 multilingual speech synthesis 测试后，我们将比较 speaker similarity 和 naturalness score。 | 完成Multilingual Speech Synthesis测试后,我们将比较Speaker Similarity和Naturalness Score。 | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\mixed\nahida_mixed_3.wav` |
| finetuned_best | 英文文本 | Nahida | Today is a good day to learn something new. | Today is a good day to learn something new. | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\english\nahida_english_1.wav` |
| finetuned_best | 英文文本 | Nahida | The speech synthesis system should pronounce every word clearly and maintain a natural speaking rhythm. | The speech synthesis system should pronounce every word clearly and maintain a natural speaking rhythm. | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\english\nahida_english_2.wav` |
| finetuned_best | 英文文本 | Nahida | During this evaluation, we compare pronunciation accuracy, generation speed, naturalness, and speaker similarity. | During this evaluation, we compare pronunciation accuracy, generation speed, naturalness, and speaker similarity. | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\english\nahida_english_3.wav` |
| finetuned_best | 中文长文本 | Arataki Itto | 今天我们进行一次长中文语音合成测试。系统需要准确朗读每一个词语，并在连续表达时保持稳定的音色、自然的语速和清晰的停顿。测试过程中，我们会关注是否出现漏字、重复、异常停顿或者声音漂移。最后，将结合生成耗时、字符错误率、词错误率、自然度和说话人相似度，对本次实验结果进行完整记录。 | 今天我们进行一次长中文语音合成测试系统需要准确朗读每一个词语并在连续表达时保持稳定的音色自然的语速和清晰的停顿测试过程中我们会关注是否出现漏字重复异常停顿或者声音飘移最后将结合声成耗时自缚错误率词错误率自然度和说话人相似度对本次实验结果进行完整记录 | 3.23% | 4.35% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\long_zh\arataki_itto_long_zh_1.wav` |
| finetuned_best | 中文长文本 | Arataki Itto | 清晨的城市逐渐苏醒，街道上的车辆和行人慢慢增多。有人准备开始一天的工作，有人带着早餐匆匆赶路，也有人在公园里安静地散步。随着阳光穿过云层，周围的建筑和树木显得更加清晰，新的一天也在平稳而有序的节奏中展开。 | 清晨的城市逐渐苏醒,街道上的车辆和行人慢慢增多。有人准备开始一天的工作,有人带着早餐匆匆赶路,也有人在公园里安静地散步。随着阳光穿过云层,周围的建筑和树木显得更加清晰,新的一天也在平稳而有序的节奏中展开。 | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\long_zh\arataki_itto_long_zh_2.wav` |
| finetuned_best | 中文长文本 | Arataki Itto | 为了验证语音系统在长时间连续表达中的稳定性，我们准备了一段包含多个句子和不同停顿位置的测试内容。模型不仅需要保证文字完整，还要控制合理的语速、重音与句间停顿，并尽量避免音色漂移、重复朗读或突然加速等问题。 | 为了验证语音,系统在长时间连续表达中的稳定性,我们准备了一段包含多个句子和不同停顿位置的测试内容。模型不仅需要保证文字完整,还要控制合理的语速、重音与句间停顿,并尽量避免音色飘移、重复朗读或突然加速等问题。 | 1.05% | 1.92% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\long_zh\arataki_itto_long_zh_3.wav` |
| finetuned_best | 多音字文本 | Arataki Itto | 银行门口的人沿着人行道行走，工作人员认真核对每一行记录。 | 银行门口的人沿着人行道行走工作人员认真核对每一行记录 | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\polyphone\arataki_itto_polyphone_1.wav` |
| finetuned_best | 多音字文本 | Arataki Itto | 音乐老师强调快乐学习的重要性，并带领大家提高练习效率。 | 音乐老师强调快乐学习的重要性并带领大家提高练习效率 | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\polyphone\arataki_itto_polyphone_2.wav` |
| finetuned_best | 多音字文本 | Arataki Itto | 他重新测量物品的重量，又重复检查数据，最后率领团队完成任务。 | 他重新测量物品的重量又重复检查数据最后率领团队完成任务 | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\polyphone\arataki_itto_polyphone_3.wav` |
| finetuned_best | 游戏专有词与角色名文本 | Arataki Itto | 派蒙和旅行者离开蒙德后，准备前往璃月港拜访钟离。 | 派盟和旅行者離開蒙德厚準備前往璃月港拜訪鍾離 | 9.09% | 23.08% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\game_terms\arataki_itto_game_terms_1.wav` |
| finetuned_best | 游戏专有词与角色名文本 | Arataki Itto | 纳西妲在须弥城遇见艾尔海森和提纳里，并讨论世界树的变化。 | 纳西达在虚谜城遇见艾尔海森和提纳里,并讨论世界术的变化。 | 15.38% | 26.67% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\game_terms\arataki_itto_game_terms_2.wav` |
| finetuned_best | 游戏专有词与角色名文本 | Arataki Itto | 八重神子邀请雷电将军前往鸣神大社，荒泷一斗则在花见坂等待久岐忍。 | 八重神子邀請雷電將軍前往明神大社,慌龍一抖則在花劍版等待九騎忍! | 26.67% | 47.06% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\game_terms\arataki_itto_game_terms_3.wav` |
| finetuned_best | 中英混合文本 | Arataki Itto | 今天的 meeting 很顺利，我们下午继续测试 OmniVoice。 | 今天的Meeting很顺利我们下午继续测试Omnivice | 3.33% | 10.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\mixed\arataki_itto_mixed_1.wav` |
| finetuned_best | 中英混合文本 | Arataki Itto | 系统会记录 generation time、audio duration 和 RTF，然后使用 Whisper 计算 CER 与 WER。 | 系統會記錄 Generation Time, Audio Duration 和 RTF然後使用 Whisper 計算, CER 與 WER | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\mixed\arataki_itto_mixed_2.wav` |
| finetuned_best | 中英混合文本 | Arataki Itto | 完成 multilingual speech synthesis 测试后，我们将比较 speaker similarity 和 naturalness score。 | 完成Multilingual Speech Synthesis测试后,我们将比较Speaker Similarity和Naturalness Score | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\mixed\arataki_itto_mixed_3.wav` |
| finetuned_best | 英文文本 | Arataki Itto | Today is a good day to learn something new. | Today is a good day to learn something new! | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\english\arataki_itto_english_1.wav` |
| finetuned_best | 英文文本 | Arataki Itto | The speech synthesis system should pronounce every word clearly and maintain a natural speaking rhythm. | The speech synthesis system should pronounce every word clearly and maintain a natural speaking rhythm. | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\english\arataki_itto_english_2.wav` |
| finetuned_best | 英文文本 | Arataki Itto | During this evaluation, we compare pronunciation accuracy, generation speed, naturalness, and speaker similarity. | During this evaluation, we compare pronunciation accuracy, generation speed, naturalness, and speaker similarity. | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\english\arataki_itto_english_3.wav` |
| finetuned_best | 未见说话人 zero-shot | AISHELL3_SSB0273_unseen | 今天阳光很好，我们准备开始新的语音合成测试。 | 今天阳光很好,我们准备开始新的语音合成测试。 | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\unseen_zero_shot\aishell3_ssb0273_unseen_unseen_short.wav` |
| finetuned_best | 未见说话人 zero-shot | AISHELL3_SSB0273_unseen | 银行门口的人沿着人行道行走，音乐老师正在提高练习效率。 | 银行门口的人沿着人行道行走音乐老师正在提高练习效率 | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\unseen_zero_shot\aishell3_ssb0273_unseen_unseen_polyphone.wav` |
| finetuned_best | 未见说话人 zero-shot | AISHELL3_SSB0273_unseen | 今天我们使用一段从未参与微调的说话人音频进行零样本声音克隆测试。系统需要准确生成目标文本，同时保持参考音频中的音色特征、自然语速和清晰停顿。测试完成后，我们会比较基础模型和微调模型在未见说话人上的泛化能力。 | 今天我们使用一段从未参与微调的说话人音频进行零样本声音克隆测试系统需要准确生成目标文本同时保持参考音频中的音色特征、自然语速和清晰停顿测试完成后我们会比较基础模型和微调模型在未见说话人上的泛化能力 | 0.00% | 0.00% | `outputs\genshin_20_speakers_1200_extended\finetuned_best\unseen_zero_shot\aishell3_ssb0273_unseen_unseen_long.wav` |

## 说明

- CER/WER 同时受到合成发音和 Whisper 识别误差影响，角色名与游戏专有词尤其需要人工试听确认。
- 英文输出的拼音错误率不适用，因此分类统计中该项为 0，不应作为英文指标使用。
- SIM-o 衡量与对应参考音频的声纹嵌入余弦相似度；不同语言和文本长度会影响分数。

## 文件位置

- 合成音频：`outputs/genshin_20_speakers_1200_extended`
- 完整指标：`evaluation/genshin_20_speakers_1200_extended/automatic_metrics.json`
- 生成结果：`evaluation/genshin_20_speakers_1200_extended/generation_results.json`
- 人工试听记录：`evaluation/genshin_20_speakers_1200_extended/manual_listening_evaluation.md`
