# OmniVoice 20 说话人多说话人微调

## 目标

基于 OmniVoice 做 20 个原神角色的小数据多说话人微调，验证高质量筛选样本在内容准确率和音色相似度上的影响，并通过多文本类型测试观察模型泛化表现。

## 方法

- 数据：20 个说话人，每人 60 条高质量训练样本，共 1,200 条、101.07 分钟；验证集每人 10 条，共 200 条、17.00 分钟。
- 训练：固定 seed，400 steps，按验证 loss 选择 checkpoint-200 作为 best。
- 推理：base 与 finetuned 统一 prompt、目标文本、32 steps、batch 1 和 warmup 后计时。
- 评测：短文本、中长文本、游戏专有词和中英混合，共 200 条扩展文本 case；记录 CER/WER、SIM-o、UTMOS 和 RTF。

## 关键结果

- CER：4.38% -> 3.98%
- WER：7.12% -> 6.64%
- SIM-o：0.7054 -> 0.7072
- RTF 只作为推理耗时记录，不解释为微调带来的速度提升。
- 单句样例中存在 SIM-o 明显提升且 CER/WER 不变差的 case，见 `evaluation/genshin_20_speakers_extended_texts/sim_improvement_examples.md`。

## 文件说明

- `scripts/prepare_genshin_20_speakers_finetune.py`：训练/验证数据筛选。
- `scripts/run_genshin_20_speakers_finetune.ps1`：训练入口。
- `scripts/run_genshin_20_speakers_comparison.py`：原始 base 与 finetuned 对比推理。
- `scripts/evaluate_genshin_20_speakers_comparison.py`：原始自动指标评测。
- `scripts/prepare_genshin_20_speakers_extended_text_cases.py`：扩展文本测试集构造。
- `scripts/run_genshin_20_speakers_extended_text_comparison.py`：扩展文本 base 与 finetuned 对比推理。
- `scripts/evaluate_genshin_20_speakers_extended_text_comparison.py`：扩展文本自动指标评测。
- `configs/genshin_20_speakers_*.json`：数据与训练配置。
- `evaluation/genshin_20_speakers_1200_*`：评测报告。
