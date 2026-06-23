# OmniVoice 原神 20 说话人 1200 条训练数据微调对比

## 实验条件

- 说话人：Paimon、Nahida、Yae Miko、Arataki Itto、Alhaitham、Thoma、Zhongli、Noelle、Ningguang、Tighnari、Shikanoin Heizou、Beidou、Yelan、Yoimiya、Kamisato Ayaka、Kaedehara Kazuha、Nilou、Diona、Dehya、Gorou。
- 训练集：1200 条高质量音频，共 101.07 分钟；每位说话人 60 条。
- 验证集：200 条独立音频，共 17.00 分钟；每位说话人 10 条。
- 筛选规则：文本完整度、音频时长、响度、静音比例、削波情况及说话人可用样本量。
- 微调配置：400 steps、学习率 `2e-6`、SDPA、BF16；每 100 steps 保存并评估一次。
- 正式对比采用验证集 Loss 最低的检查点，并复制到 `best` 目录。
- 推理条件：32 步、Batch 1、预热后计时、固定随机种子 0。
- 固定测试文本：今天阳光很好，我们准备开始新的语音合成测试，请保持清晰自然的表达。
- 每位说话人均使用未参与训练的验证音频作为零样本克隆参考。

## 训练检查点

| 检查点 | 验证集 Loss |
|---|---:|
| checkpoint-100 | 4.1361 |
| checkpoint-200（最佳） | **3.9543** |
| checkpoint-300 | 4.1102 |
| checkpoint-400 | 4.0033 |

## 综合结果

| 模型 | CER | WER | 带声调拼音错误率 | 不带声调拼音错误率 | UTMOS | SIM-o | 平均 RTF | 总体 RTF |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| base | 0.83% | 1.39% | 0.83% | 0.83% | 2.7381 | 0.7544 | 0.1193 | 0.1132 |
| finetuned_best | 0.67% | 1.11% | 0.67% | 0.67% | 2.7254 | 0.7632 | 0.1166 | 0.1104 |

## 对比结论

- CER：基础模型 0.83%，微调模型 0.67%，变化 -0.17%。
- WER：基础模型 1.39%，微调模型 1.11%，变化 -0.28%。
- UTMOS：基础模型 2.7381，微调模型 2.7254。
- SIM-o：基础模型 0.7544，微调模型 0.7632。
- 总体 RTF：基础模型 0.1132，微调模型 0.1104；微调未改变模型结构，因此推理速度应接近。
- 逐说话人统计：微调模型在 20 个说话人中的 13 个 SIM-o 更高，10 个 UTMOS 更高。
- CER/WER 由 Whisper medium 回识别计算，可能同时包含 TTS 发音错误与 ASR 识别错误，需结合试听判断。
- 当前测试只覆盖一条固定中文短文本，不能代表长文本、英文、中英混合文本和游戏专有词表现。

## 逐说话人结果

| 模型 | 说话人 | RTF | CER | WER | 拼音错误率（带/不带声调） | UTMOS | SIM-o | Whisper 回识别文本 | 输出音频 |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| base | Alhaitham | 0.1145 | 3.33% | 5.56% | 3.33% / 3.33% | 3.4300 | 0.8131 | 今天陽光很好,我們準備開始新的語音合成測試,請保持清晰自然地表達。 | `outputs\genshin_20_speakers_1200_finetune\base\alhaitham.wav` |
| base | Arataki Itto | 0.1089 | 6.67% | 11.11% | 6.67% / 6.67% | 2.2892 | 0.5653 | 哎!今天阳光很好我们准备开始新的语音合成测试请保持清晰自然地表达 | `outputs\genshin_20_speakers_1200_finetune\base\arataki_itto.wav` |
| base | Beidou | 0.1059 | 0.00% | 0.00% | 0.00% / 0.00% | 2.3882 | 0.7417 | 今天陽光很好,我們準備開始新的語音合成測試,請保持清晰自然的表達。 | `outputs\genshin_20_speakers_1200_finetune\base\beidou.wav` |
| base | Dehya | 0.1565 | 3.33% | 5.56% | 3.33% / 3.33% | 2.9500 | 0.7929 | 今天陽光很好我們準備開始新的語音合成測試請保持清晰自然地表達 | `outputs\genshin_20_speakers_1200_finetune\base\dehya.wav` |
| base | Diona | 0.1499 | 0.00% | 0.00% | 0.00% / 0.00% | 2.0599 | 0.7726 | 今天阳光很好,我们准备开始新的语音合成测试,请保持清晰自然的表达。 | `outputs\genshin_20_speakers_1200_finetune\base\diona.wav` |
| base | Gorou | 0.1375 | 0.00% | 0.00% | 0.00% / 0.00% | 2.8755 | 0.8217 | 今天陽光很好,我們準備開始新的語音合成測試,請保持清晰自然的表達。 | `outputs\genshin_20_speakers_1200_finetune\base\gorou.wav` |
| base | Kaedehara Kazuha | 0.1469 | 0.00% | 0.00% | 0.00% / 0.00% | 3.2077 | 0.7199 | 今天阳光很好,我们准备开始新的语音合成测试,请保持清晰自然的表达。 | `outputs\genshin_20_speakers_1200_finetune\base\kaedehara_kazuha.wav` |
| base | Kamisato Ayaka | 0.1150 | 0.00% | 0.00% | 0.00% / 0.00% | 2.5925 | 0.7218 | 今天陽光很好,我們準備開始新的語音合成測試,請保持清晰自然的表達。 | `outputs\genshin_20_speakers_1200_finetune\base\kamisato_ayaka.wav` |
| base | Nahida | 0.1052 | 0.00% | 0.00% | 0.00% / 0.00% | 2.0114 | 0.8010 | 今天陽光很好,我們準備開始新的語音合成測試,請保持清晰自然的表達。 | `outputs\genshin_20_speakers_1200_finetune\base\nahida.wav` |
| base | Nilou | 0.1324 | 0.00% | 0.00% | 0.00% / 0.00% | 2.3829 | 0.7368 | 今天阳光很好,我们准备开始新的语音合成测试,请保持清晰自然的表达。 | `outputs\genshin_20_speakers_1200_finetune\base\nilou.wav` |
| base | Ningguang | 0.1244 | 0.00% | 0.00% | 0.00% / 0.00% | 3.1502 | 0.8280 | 今天陽光很好,我們準備開始新的語音合成測試,請保持清晰自然的表達。 | `outputs\genshin_20_speakers_1200_finetune\base\ningguang.wav` |
| base | Noelle | 0.1007 | 0.00% | 0.00% | 0.00% / 0.00% | 1.9872 | 0.7472 | 今天陽光很好,我們準備開始新的語音合成測試,請保持清晰自然的表達。 | `outputs\genshin_20_speakers_1200_finetune\base\noelle.wav` |
| base | Paimon | 0.0618 | 0.00% | 0.00% | 0.00% / 0.00% | 1.9953 | 0.6729 | 今天陽光很好,我們準備開始新的語音合成測試,請保持清晰自然的表達。 | `outputs\genshin_20_speakers_1200_finetune\base\paimon.wav` |
| base | Shikanoin Heizou | 0.1628 | 0.00% | 0.00% | 0.00% / 0.00% | 3.2863 | 0.7407 | 今天阳光很好,我们准备开始新的语音合成测试,请保持清晰自然的表达。 | `outputs\genshin_20_speakers_1200_finetune\base\shikanoin_heizou.wav` |
| base | Thoma | 0.1080 | 0.00% | 0.00% | 0.00% / 0.00% | 2.9411 | 0.7574 | 今天陽光很好,我們準備開始新的語音合成測試,請保持清晰自然的表達。 | `outputs\genshin_20_speakers_1200_finetune\base\thoma.wav` |
| base | Tighnari | 0.1187 | 0.00% | 0.00% | 0.00% / 0.00% | 3.3839 | 0.7696 | 今天阳光很好,我们准备开始新的语音合成测试。请保持清晰自然的表达。 | `outputs\genshin_20_speakers_1200_finetune\base\tighnari.wav` |
| base | Yae Miko | 0.0780 | 0.00% | 0.00% | 0.00% / 0.00% | 3.1553 | 0.8259 | 今天陽光很好,我們準備開始新的語音合成測試,請保持清晰自然的表達。 | `outputs\genshin_20_speakers_1200_finetune\base\yae_miko.wav` |
| base | Yelan | 0.1075 | 0.00% | 0.00% | 0.00% / 0.00% | 3.5446 | 0.8297 | 今天陽光很好,我們準備開始新的語音合成測試,請保持清晰自然的表達。 | `outputs\genshin_20_speakers_1200_finetune\base\yelan.wav` |
| base | Yoimiya | 0.1403 | 0.00% | 0.00% | 0.00% / 0.00% | 2.0449 | 0.6765 | 今天阳光很好,我们准备开始新的语音合成测试,请保持清晰自然的表达。 | `outputs\genshin_20_speakers_1200_finetune\base\yoimiya.wav` |
| base | Zhongli | 0.1116 | 3.33% | 5.56% | 3.33% / 3.33% | 3.0862 | 0.7542 | 今天陽光很好,我們準備開始新的語音合成測試,請保持清晰自然地表達。 | `outputs\genshin_20_speakers_1200_finetune\base\zhongli.wav` |
| finetuned_best | Alhaitham | 0.1253 | 0.00% | 0.00% | 0.00% / 0.00% | 3.3174 | 0.7937 | 今天陽光很好,我們準備開始新的語音合成測試,請保持清晰自然的表達。 | `outputs\genshin_20_speakers_1200_finetune\finetuned_best\alhaitham.wav` |
| finetuned_best | Arataki Itto | 0.1015 | 6.67% | 11.11% | 6.67% / 6.67% | 2.1899 | 0.5078 | 哎!今天阳光很好,我们准备开始新的语音合成测试,请保持清晰自然地表达! | `outputs\genshin_20_speakers_1200_finetune\finetuned_best\arataki_itto.wav` |
| finetuned_best | Beidou | 0.0989 | 0.00% | 0.00% | 0.00% / 0.00% | 2.4151 | 0.7768 | 今天陽光很好,我們準備開始新的語音合成測試,請保持清晰自然的表達。 | `outputs\genshin_20_speakers_1200_finetune\finetuned_best\beidou.wav` |
| finetuned_best | Dehya | 0.1416 | 0.00% | 0.00% | 0.00% / 0.00% | 2.6864 | 0.7454 | 今天陽光很好,我們準備開始新的語音合成測試請保持清晰自然的表達 | `outputs\genshin_20_speakers_1200_finetune\finetuned_best\dehya.wav` |
| finetuned_best | Diona | 0.1375 | 0.00% | 0.00% | 0.00% / 0.00% | 1.7777 | 0.7998 | 今天阳光很好,我们准备开始新的语音合成测试,请保持清晰自然的表达。 | `outputs\genshin_20_speakers_1200_finetune\finetuned_best\diona.wav` |
| finetuned_best | Gorou | 0.1295 | 0.00% | 0.00% | 0.00% / 0.00% | 2.9852 | 0.8397 | 今天阳光很好,我们准备开始新的语音合成测试,请保持清晰自然的表达。 | `outputs\genshin_20_speakers_1200_finetune\finetuned_best\gorou.wav` |
| finetuned_best | Kaedehara Kazuha | 0.1559 | 0.00% | 0.00% | 0.00% / 0.00% | 3.1067 | 0.7206 | 今天阳光很好,我们准备开始新的语音合成测试,请保持清晰自然的表达。 | `outputs\genshin_20_speakers_1200_finetune\finetuned_best\kaedehara_kazuha.wav` |
| finetuned_best | Kamisato Ayaka | 0.1063 | 0.00% | 0.00% | 0.00% / 0.00% | 2.5711 | 0.7831 | 今天陽光很好,我們準備開始新的語音合成測試,請保持清晰自然的表達。 | `outputs\genshin_20_speakers_1200_finetune\finetuned_best\kamisato_ayaka.wav` |
| finetuned_best | Nahida | 0.1107 | 0.00% | 0.00% | 0.00% / 0.00% | 2.0674 | 0.8750 | 今天陽光很好,我們準備開始新的語音合成測試,請保持清晰自然的表達。 | `outputs\genshin_20_speakers_1200_finetune\finetuned_best\nahida.wav` |
| finetuned_best | Nilou | 0.1385 | 0.00% | 0.00% | 0.00% / 0.00% | 2.4960 | 0.7415 | 今天陽光很好,我們準備開始新的語音合成測試,請保持清晰自然的表達。 | `outputs\genshin_20_speakers_1200_finetune\finetuned_best\nilou.wav` |
| finetuned_best | Ningguang | 0.1231 | 0.00% | 0.00% | 0.00% / 0.00% | 3.2391 | 0.7593 | 今天陽光很好,我們準備開始新的語音合成測試,請保持清晰自然的表達。 | `outputs\genshin_20_speakers_1200_finetune\finetuned_best\ningguang.wav` |
| finetuned_best | Noelle | 0.0954 | 0.00% | 0.00% | 0.00% / 0.00% | 2.0476 | 0.7274 | 今天陽光很好,我們準備開始新的語音合成測試,請保持清晰自然的表達。 | `outputs\genshin_20_speakers_1200_finetune\finetuned_best\noelle.wav` |
| finetuned_best | Paimon | 0.0598 | 0.00% | 0.00% | 0.00% / 0.00% | 2.1184 | 0.6952 | 今天陽光很好,我們準備開始,新的語音合成,測試,請保持清晰自然的表達。 | `outputs\genshin_20_speakers_1200_finetune\finetuned_best\paimon.wav` |
| finetuned_best | Shikanoin Heizou | 0.1665 | 3.33% | 5.56% | 3.33% / 3.33% | 3.0082 | 0.7681 | 今天陽光很好,我們準備開始新的語音合成測試,請保持清晰自然地表達。 | `outputs\genshin_20_speakers_1200_finetune\finetuned_best\shikanoin_heizou.wav` |
| finetuned_best | Thoma | 0.1124 | 0.00% | 0.00% | 0.00% / 0.00% | 2.9377 | 0.7761 | 今天陽光很好,我們準備開始新的語音合成測試,請保持清晰自然的表達。 | `outputs\genshin_20_speakers_1200_finetune\finetuned_best\thoma.wav` |
| finetuned_best | Tighnari | 0.1101 | 3.33% | 5.56% | 3.33% / 3.33% | 3.3217 | 0.7990 | 今天阳光很好我们准备开始新的语音合成测试请保持清晰自然地表达 | `outputs\genshin_20_speakers_1200_finetune\finetuned_best\tighnari.wav` |
| finetuned_best | Yae Miko | 0.0806 | 0.00% | 0.00% | 0.00% / 0.00% | 3.2719 | 0.8165 | 今天陽光很好,我們準備開始新的語音合成測試,請保持清晰自然的表達。 | `outputs\genshin_20_speakers_1200_finetune\finetuned_best\yae_miko.wav` |
| finetuned_best | Yelan | 0.1041 | 0.00% | 0.00% | 0.00% / 0.00% | 3.4777 | 0.8605 | 今天陽光很好,我們準備開始新的語音合成測試,請保持清晰自然的表達。 | `outputs\genshin_20_speakers_1200_finetune\finetuned_best\yelan.wav` |
| finetuned_best | Yoimiya | 0.1338 | 0.00% | 0.00% | 0.00% / 0.00% | 2.2821 | 0.7266 | 今天陽光很好,我們準備開始新的語音合成測試,請保持清晰自然的表達。 | `outputs\genshin_20_speakers_1200_finetune\finetuned_best\yoimiya.wav` |
| finetuned_best | Zhongli | 0.1012 | 0.00% | 0.00% | 0.00% / 0.00% | 3.1915 | 0.7521 | 今天陽光很好,我們準備開始新的語音合成測試,請保持清晰自然的表達。 | `outputs\genshin_20_speakers_1200_finetune\finetuned_best\zhongli.wav` |

## 文件位置

- 数据筛选详情：`data/genshin_20_speakers/manifests/selection_details.jsonl`
- 训练检查点：`exp/genshin_20_speakers_1200_sdpa`
- 合成音频：`outputs/genshin_20_speakers_1200_finetune`
- 完整自动指标：`evaluation/genshin_20_speakers_1200_finetune/automatic_metrics.json`
