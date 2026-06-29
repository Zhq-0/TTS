# CosyVoice3 原神角色小数据 LLM-only 微调

## 目标

基于 `Fun-CosyVoice3-0.5B` 做四个原神角色的小数据音色克隆实验，只更新 LLM 参数，冻结 Flow、HiFT 和声码器，观察小数据条件下内容准确率、音色相似度和泛化能力的变化。

## 方法

- 数据：从原始角色语音清单中筛选 1,016 条高质量训练样本，约 1.321 小时，每个角色 254 条。
- 清洗规则：时长、文本长度、RMS、削波、静音比例、Whisper 回识别 CER、带声调/不带声调拼音错误率。
- 微调：CosyVoice3 LLM-only，3 epoch，固定 seed 和 prompt。
- 补测：已见 4 角色每人 25 条文本，未见 8 角色每人 10 条文本，共 180 个 case；base 与 `clean_epoch_2` 使用相同 prompt 和目标文本。

## 关键结果

- 验证 loss 从 2.8596 降至 2.8176。
- 180 case 补测中，`clean_epoch_2` 相较 base 的 CER `5.58% -> 5.34%`，WER `9.79% -> 9.01%`，UTMOS `3.1257 -> 3.1448`。
- SIM 从 `0.8704` 降至 `0.8624`，说明小数据 LLM-only 微调虽然带来内容准确率小幅改善，但存在音色相似度退化风险。
- 项目定位：强基座模型小数据 LLM-only 微调边界分析，而不是广义质量提升结论。

## 文件说明

- `prepare_data.ps1`：训练数据准备流程。
- `train_llm_clean.ps1`：LLM-only 微调入口。
- `inference_four_characters.py`：四角色固定 prompt 推理。
- `inference_unseen_speakers.py`：未见说话人测试。
- `evaluate_outputs.py` / `evaluate_unseen_speakers.py`：原始自动评测脚本。
- `run_extended_comparison.py` / `evaluate_extended_comparison.py`：180 case 补充评测脚本。
- `conf/cosyvoice3_four_characters.yaml`：CosyVoice3 训练配置。
- `training_result_clean.md` 与 `evaluation/**/*.md`：训练和评测报告。
