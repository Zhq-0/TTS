# OmniVoice 20 说话人多说话人微调

## 目标

基于 OmniVoice 做 20 个原神角色的小数据多说话人微调，验证高质量筛选样本在内容准确率、音色相似度和推理效率上的收益。

## 方法

- 数据：20 个说话人，每人 60 条高质量训练样本，共 1,200 条、101.07 分钟；验证集每人 10 条，共 200 条、17.00 分钟。
- 训练：SDPA、BF16、固定 seed，400 steps，按验证 loss 选择 checkpoint-200 作为 best。
- 推理：base 与 finetuned 统一 32 steps、batch 1、warmup 后计时。
- 评测：CER/WER、SIM-o、RTF，并记录每个说话人的变化。

## 关键结果

- CER：0.83% -> 0.67%
- WER：1.39% -> 1.11%
- SIM-o：0.7544 -> 0.7632
- RTF：0.1132 -> 0.1104
- 20 个说话人中 13 个 SIM-o 提升

## 文件说明

- `scripts/prepare_genshin_20_speakers_finetune.py`：训练/验证数据筛选。
- `scripts/run_genshin_20_speakers_finetune.ps1`：训练入口。
- `scripts/run_genshin_20_speakers_comparison.py`：base 与 finetuned 对比推理。
- `scripts/evaluate_genshin_20_speakers_comparison.py`：自动指标评测。
- `configs/genshin_20_speakers_*.json`：数据与训练配置。
- `evaluation/genshin_20_speakers_1200_*`：评测报告。
