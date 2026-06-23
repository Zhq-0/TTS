# dots.tts Zero-shot 对比与小数据微调实验

## 目标

评估 dots.tts-mf、dots.tts-soar 和 CosyVoice3 在中文、英文、动漫角色、多语言/跨语言/方言等场景下的 zero-shot 表现，并尝试 dots.tts-soar 的小数据 LoRA 微调。

## 方法

- 统一 cases、prompt、目标文本和输出目录，生成可复查的 JSON/Markdown 报告。
- 采用 Seed-TTS-Eval 风格口径：英文 ASR、中文 ASR、speaker similarity、RTF。
- 将短文本评测扩展到每类 60 条，共 180 条，避免小样本偶然结论。
- 对 dots.tts-soar 进行 20 说话人、350-shot、1000 step LoRA 试跑，并和原始模型、checkpoint-500、checkpoint-1000 对比。

## 关键结果

180 条短文本对比：

| 模型 | WER | CER | SIM | RTF | WER=0 |
|---|---:|---:|---:|---:|---:|
| dots.tts-mf | 5.94% | 4.23% | 0.742 | 0.875 | 132/180 |
| CosyVoice3 | 2.14% | 1.74% | 0.696 | 0.878 | 143/180 |

结论：dots.tts-mf 在音色相似度上更强，CosyVoice3 在整体内容准确率上更强。dots.tts-soar 小数据 LoRA 试跑后未稳定超过原始模型，因此没有把它包装成成功微调项目，而是保留为对模型适配边界的实验记录。

## 文件说明

- `scripts/run_zero_shot_suite.py`：dots.tts 批量 zero-shot 生成。
- `scripts/run_cosyvoice3_suite.py`：CosyVoice3 对照组生成。
- `scripts/evaluate_zero_shot_official_style.py`：官方风格 WER/CER/SIM/RTF 评测。
- `scripts/train_dots_tts.py`：LoRA 微调入口。
- `experiments/short_text_comparison_60_each/`：180 条短文本评测报告。
- `experiments/high_quality_voice_clone/`：高质量音色克隆场景报告。
- `experiments/multilingual_crosslingual_dialect/`：多语言/跨语言/方言报告。
- `experiments/small_multispeaker_finetune/`：dots.tts-soar LoRA 试跑报告。
