# CosyVoice3 Genshin four-character LLM-only finetune

## Experiment

- Model: `Fun-CosyVoice3-0.5B`
- Finetune target: LLM only. Flow, HiFT and vocoder were not updated.
- Data source: reused the cleaned four-character Genshin split from the CosyVoice2 experiment.
- Train set: 1,016 utterances, 254 per character.
- Dev set: 36 utterances, 9 per character.
- Characters: Paimon, Zhongli, Ganyu, Yae Miko.
- Speech tokenizer: `speech_tokenizer_v3.onnx`.
- CosyVoice3 instruction prefix: `You are a helpful assistant.<|endofprompt|>`.
- Training: 3 epochs, learning rate `2e-6`, batch size 1, gradient accumulation 8, AMP enabled.

## Training Curve

| checkpoint | step | dev loss | dev acc |
|---|---:|---:|---:|
| `epoch_0_whole.pt` | 128 | 2.8596 | 0.2843 |
| `epoch_1_whole.pt` | 255 | 2.8304 | 0.2799 |
| `epoch_2_whole.pt` | 382 | 2.8176 | 0.2864 |

The validation loss decreased from 2.8596 to 2.8176. The accuracy improved only slightly, so this run should be presented as a controlled CosyVoice3 LLM-only finetune experiment, not as a large quality jump.

## Fixed-Condition Evaluation

Evaluation uses the same prompts and target texts for the base model and all finetuned checkpoints. ASR is Whisper `medium`; speaker similarity is CampPlus cosine similarity between prompt audio and generated audio. RTF is generation seconds divided by generated audio seconds.

### Difficult short line: `common_line`

Target text: 欲买桂花同载酒，只可惜故人，何日再见呢？

| variant | CER | WER | pinyin tone | pinyin no tone | SIM | RTF |
|---|---:|---:|---:|---:|---:|---:|
| `base` | 11.76% | 27.27% | 1.47% | 0.00% | 0.8731 | 0.593 |
| `clean_epoch_0` | 14.71% | 27.27% | 2.94% | 0.00% | 0.8860 | 0.591 |
| `clean_epoch_1` | 14.71% | 29.55% | 1.47% | 1.47% | 0.8713 | 0.583 |
| `clean_epoch_2` | 8.82% | 22.73% | 1.47% | 1.47% | 0.8637 | 0.570 |

On this difficult short line, `clean_epoch_2` has lower CER and WER than the base model, but its speaker similarity is lower than the base model.

### Generic short line: `generic_short`

Target text: 今天阳光很好，我们吃过早饭以后，一起去公园散步吧。

| variant | CER | WER | pinyin tone | pinyin no tone | SIM | RTF |
|---|---:|---:|---:|---:|---:|---:|
| `base` | 1.14% | 1.79% | 1.14% | 1.14% | 0.8762 | 0.594 |
| `clean_epoch_0` | 1.14% | 1.79% | 1.14% | 1.14% | 0.8671 | 0.615 |
| `clean_epoch_1` | 1.14% | 1.79% | 1.14% | 1.14% | 0.8626 | 0.608 |
| `clean_epoch_2` | 2.27% | 3.57% | 2.27% | 2.27% | 0.8554 | 0.621 |

On the generic short sentence, the base CosyVoice3 model is already very strong. The LLM-only finetuned checkpoints do not consistently improve content accuracy or speaker similarity.

## Unseen-Speaker Evaluation

Unseen speakers are selected from the 20-speaker Genshin dev split and are not part of the four-character finetuning set. The tested speakers are Nahida, Alhaitham, Ningguang, Tighnari, Yelan, Yoimiya, Kamisato Ayaka and Nilou. Each variant uses the same prompt audio and target text.

### Unseen difficult short line: `common_line`

| variant | n | CER | WER | pinyin no tone | SIM | RTF |
|---|---:|---:|---:|---:|---:|---:|
| `base` | 8 | 18.38% | 30.68% | 1.47% | 0.8768 | 0.637 |
| `clean_epoch_2` | 8 | 14.71% | 27.27% | 1.47% | 0.8671 | 0.596 |

On unseen speakers, `clean_epoch_2` improves content accuracy and RTF on this difficult short line, but speaker similarity drops from 0.8768 to 0.8671.

### Unseen generic short line: `generic_short`

| variant | n | CER | WER | pinyin no tone | SIM | RTF |
|---|---:|---:|---:|---:|---:|---:|
| `base` | 8 | 0.00% | 0.00% | 0.00% | 0.8876 | 0.616 |
| `clean_epoch_2` | 8 | 0.00% | 0.00% | 0.00% | 0.8854 | 0.625 |

For regular short text, the base model is already perfect on ASR-based content metrics. The finetuned checkpoint does not improve content accuracy and slightly reduces average speaker similarity.

## Difference From Official Results

The official local README reports public benchmark results for `Fun-CosyVoice3-0.5B-2512`: test-zh CER 1.21 / SS 78.0, test-en WER 2.24 / SS 71.8, and test-hard CER 6.71 / SS 75.8. It also reports the RL version at test-zh CER 0.81 / SS 77.4, test-en WER 1.68 / SS 69.5, and test-hard CER 5.44 / SS 75.0.

These official numbers are not directly comparable to this experiment:

- Dataset differs: official results use public benchmark sets; this run uses four Genshin voices and only four generated samples per test set.
- Metric backend differs: this run uses Whisper `medium` for ASR and CampPlus cosine similarity; official SS is reported as a benchmark speaker similarity percentage.
- Task differs: official evaluation is zero-shot benchmark quality; this run evaluates whether a small LLM-only finetune helps fixed Genshin character prompts.
- Prompt format differs: CosyVoice3 requires an instruction prefix in the prompt sequence, which makes these prompts longer and triggers short-text warnings during inference.

## Resume Replacement

CosyVoice3 原神角色小数据 LLM-only 微调 2026.06

Fun-CosyVoice3-0.5B / 四角色音色克隆 / 数据清洗 / 固定条件评测

- 仅更新 CosyVoice3 的 LLM 参数，冻结 Flow、HiFT 与声码器；复用清洗后的四角色训练集 1,016 条，每个角色 254 条，并重新用 `speech_tokenizer_v3.onnx` 构建 CosyVoice3 训练数据。
- 适配 CosyVoice3 的 `CosyVoice3LM`、`CausalMaskedDiffWithDiT`、`CausalHiFTGenerator` 配置与 instruction prefix，完成 3 epoch LLM-only 微调，验证 loss 从 2.8596 降至 2.8176。
- 建立 base 与 `clean_epoch_0/1/2` 的固定 prompt 对比流程，记录 CER、WER、拼音错误率、CampPlus 音色相似度与 RTF；困难短句上 `clean_epoch_2` 的 CER/WER 为 8.82%/22.73%，优于 base 的 11.76%/27.27%，RTF 从 0.593 降至 0.570。
- 同时发现普通短句中 base 已接近满分，微调后声纹相似度略降，说明小数据 LLM-only 微调对强基座模型收益有限，并将该负结果用于分析数据规模、冻结模块和评测口径的影响。

## Artifacts

- Audio outputs: `outputs/`
- Common-line metrics: `evaluation/automatic_metrics.json`, `evaluation/automatic_metrics.md`
- Generic-short metrics: `evaluation/generic_short/automatic_metrics.json`, `evaluation/generic_short/automatic_metrics.md`
- Unseen-speaker audio outputs: `outputs/unseen_speakers/`
- Unseen-speaker metrics: `evaluation/unseen_speakers/common_line/automatic_metrics.md`, `evaluation/unseen_speakers/generic_short/automatic_metrics.md`
- Checkpoints: `exp/four_characters_llm_clean_3epoch/`
