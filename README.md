# TTS Projects

这个仓库整理了三个本地语音合成项目的可公开材料，覆盖 zero-shot 语音克隆、小数据多说话人微调、自动评测和模型对比。仓库只包含自写脚本、配置样例、实验报告、指标汇总和局部源码改动 patch；不包含模型权重、训练数据、生成音频、checkpoint 或第三方大仓库源码。

## 项目概览

| 项目 | 模型/方向 | 重点工作 | 代表结果 |
|---|---|---|---|
| CosyVoice3 原神角色小数据 LLM-only 微调 | CosyVoice3-0.5B | 数据清洗、LLM-only 微调、base/finetune 对比、未见说话人测试 | 困难短句中 clean_epoch_2 的 CER/WER/RTF 优于 base；普通短句复盘强基座下小数据收益边界 |
| dots.tts zero-shot 与小数据实验 | dots.tts-mf / dots.tts-soar / CosyVoice3 | 中文/英文/角色/多语言 zero-shot 对比，官方风格 WER/CER/SIM/RTF，soar LoRA 试跑 | 180 条短文本对比中 dots.tts-mf SIM 更高，CosyVoice3 WER/CER 更低 |
| OmniVoice 20 说话人多说话人微调 | OmniVoice | 20 说话人高质量筛选、BF16+SDPA 微调、base/finetuned 公平评测 | CER 0.83% -> 0.67%，WER 1.39% -> 1.11%，SIM-o 0.7544 -> 0.7632 |

## 仓库结构

```text
projects/
  cosyvoice3-genshin-llm-finetune/
  dots-tts-zero-shot-and-finetune/
  omnivoice-20-speaker-finetune/
patches/
  cosyvoice-local-changes.patch
  dots-tts-local-changes.patch
  omnivoice-local-changes.patch
```

## 评测口径

- 内容准确率：ASR 回识别后的 CER/WER。
- 音色相似度：WavLM/CampPlus speaker similarity。
- 自然度和质量：UTMOS/DNSMOS/PESQ/STOI，按项目可用性记录。
- 推理效率：RTF，统一 warmup、batch size 和推理参数后对比。

## 公开边界

本仓库不直接提供原神语音数据、AISHELL-3 音频、模型权重或生成音频。报告中的指标来自本地实验环境，复现时需要自行准备数据、模型权重和对应上游仓库。

上游项目：

- CosyVoice: https://github.com/FunAudioLLM/CosyVoice
- dots.tts: https://github.com/rednote-hilab/dots.tts
- OmniVoice: https://github.com/k2-fsa/OmniVoice
