# TTS Projects

这个仓库整理了三个本地语音合成项目的可公开材料，覆盖 zero-shot 语音克隆、小数据多说话人微调、自动评测和模型对比。仓库包含自写脚本、配置样例、实验报告、指标汇总、局部源码改动 patch，以及 5 条可试听的合成样例；不包含模型权重、训练数据、原始或参考音频、checkpoint 或第三方大仓库源码。

## 音频试听

以下均为模型生成结果，仅用于非商业研究与评测展示。音频链接与对应报告中的实验设置、指标一致；不上传原始数据、zero-shot 参考音频或批量生成结果。

| 项目 | 模型与任务 | 参考条件 | 对应指标 | 试听 |
|---|---|---|---|---|
| CosyVoice3 原神角色 LLM-only 微调 | CosyVoice3-0.5B，四角色通用短文本，base 与 `clean_epoch_2` 对照 | 两组使用相同参考音频、目标文本和随机种子 `0` | 通用短文本四角色平均：`clean_epoch_2` CER/WER `0.00%`，SIM `0.8462`，RTF `0.546` | [base](assets/audio/cosyvoice3-base-yae-miko-generic-short.wav) / [LLM-only 微调](assets/audio/cosyvoice3-llm-only-epoch2-yae-miko-generic-short.wav) |
| dots.tts zero-shot 对比 | `dots.tts-mf` 中文短文本 zero-shot 克隆 | AISHELL-3 普通话参考音频；示例文本为“请保持语速平稳，声音自然清晰。” | 中文短文本 60 条汇总：WER/CER `1.11%`，SIM `0.855`，RTF `0.778` | [dots.tts-mf](assets/audio/dots-tts-mf-zh-short-content.wav) |
| OmniVoice 20 说话人微调 | OmniVoice，`base` 与 `finetuned_best` 对照，展示 Yelan 测试样例 | 未参与训练的验证音频作为 zero-shot prompt；固定中文短文本 | Yelan：WER `0.00% -> 0.00%`，SIM-o `0.8297 -> 0.8605`，RTF `0.1041 -> 0.1041` | [base](assets/audio/omnivoice-base-yelan.wav) / [微调后](assets/audio/omnivoice-finetuned-yelan.wav) |

> 说明：dots.tts 的指标是同一实验设置下 60 条中文短文本的汇总值，不代表单条示例音频；其余两行指标分别来自对应的四角色和单说话人对照结果。

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

除下方列出的试听样例外，本仓库不公开原始数据、参考音频或批量生成结果。`assets/audio/` 仅包含表格中列出的 5 条合成展示音频。

本仓库不直接提供原神语音数据、AISHELL-3 音频、模型权重或 checkpoint。报告中的指标来自本地实验环境，复现时需要自行准备数据、模型权重和对应上游仓库。

上游项目：

- CosyVoice: https://github.com/FunAudioLLM/CosyVoice
- dots.tts: https://github.com/rednote-hilab/dots.tts
- OmniVoice: https://github.com/k2-fsa/OmniVoice
