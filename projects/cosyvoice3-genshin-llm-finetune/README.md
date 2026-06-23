# CosyVoice3 原神角色小数据 LLM-only 微调

## 目标

基于 Fun-CosyVoice3-0.5B 做四个原神角色的小数据音色克隆实验，只更新 LLM 参数，冻结 Flow、HiFT 与声码器，观察小数据条件下内容准确率、音色相似度和推理效率的变化。

## 方法

- 数据：从原始角色语音清单中筛选 1,016 条高质量训练样本，约 1.321 小时，每个角色 254 条。
- 清洗规则：时长、文本长度、RMS、削波、静音比例、Whisper 回识别 CER、带声调/不带声调拼音错误率。
- 微调：CosyVoice3 LLM-only，3 epoch，固定 seed 和 prompt。
- 评测：base、clean_epoch_0/1/2 对比；包含普通短句、困难短句和未见说话人测试。

## 关键结果

- 验证 loss 从 2.8596 降至 2.8176。
- 困难短句中 clean_epoch_2 的 CER 8.82%、WER 22.73%、RTF 0.570，优于 base 的 CER 11.76%、WER 27.27%、RTF 0.593。
- 普通短句中 base 已经很强，微调后未稳定超越强基座，因此结论定位为“小数据 LLM-only 适配边界分析”，而不是夸大微调收益。

## 文件说明

- `prepare_data.ps1`：训练数据准备流程。
- `train_llm_clean.ps1`：LLM-only 微调入口。
- `inference_four_characters.py`：四角色固定 prompt 推理。
- `inference_unseen_speakers.py`：未见说话人测试。
- `evaluate_outputs.py` / `evaluate_unseen_speakers.py`：自动评测脚本。
- `conf/cosyvoice3_four_characters.yaml`：CosyVoice3 训练配置。
- `training_result_clean.md` 与 `evaluation/**/*.md`：训练和评测报告。
