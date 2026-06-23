# 短文本 60 条/类官方风格对比（180 条）

- 实验目录：`<DOTS_TTS_ROOT>\experiments\short_text_comparison_60_each`
- 测试设置：中文短文本 60 条、英文短文本 60 条、动漫角色短文本 60 条，总计 180 条；两个模型使用同一份 `cases.jsonl`。
- 指标口径：WER/CER 越低越好，SIM 越高越好，RTF 越低越好；这里是自建短文本集，不是官方 Seed-TTS-Eval 分数。
- 中文和动漫角色文本主要由中文 ASR 计算 WER/CER，英文文本由英文 ASR 计算 WER/CER；SIM 使用同一套说话人相似度模型。

## 总体结果

| 模型 | 样本数 | WER | CER | SIM | RTF | WER=0 样本 |
|---|---:|---:|---:|---:|---:|---:|
| dots.tts-mf | 180 | 5.94% | 4.23% | 0.742 | 0.875 | 132/180 |
| CosyVoice3 | 180 | 2.14% | 1.74% | 0.696 | 0.878 | 143/180 |

## 分类结果

| 类别 | 模型 | 样本数 | WER | CER | SIM | RTF | WER=0 样本 |
|---|---|---:|---:|---:|---:|---:|---:|
| 中文短文本 | dots.tts-mf | 60 | 1.11% | 1.11% | 0.855 | 0.778 | 53/60 |
| 中文短文本 | CosyVoice3 | 60 | 1.47% | 1.47% | 0.854 | 0.709 | 51/60 |
| 英文短文本 | dots.tts-mf | 60 | 14.57% | 9.44% | 0.561 | 0.835 | 41/60 |
| 英文短文本 | CosyVoice3 | 60 | 2.39% | 1.19% | 0.436 | 1.385 | 54/60 |
| 动漫角色短文本 | dots.tts-mf | 60 | 2.14% | 2.14% | 0.812 | 1.012 | 38/60 |
| 动漫角色短文本 | CosyVoice3 | 60 | 2.57% | 2.57% | 0.798 | 0.539 | 38/60 |

## 逐样本胜负

| 指标 | dots.tts-mf 更好 | CosyVoice3 更好 | 打平 | 说明 |
|---|---:|---:|---:|---|
| WER | 14 | 26 | 140 | 越低越好 |
| CER | 14 | 25 | 141 | 越低越好 |
| SIM | 120 | 60 | 0 | 越高越好 |
| RTF | 68 | 112 | 0 | 越低越好 |

## 结论

1. 扩展到 180 条后，dots.tts-mf 的整体 WER 为 5.94%，说明短文本评测需要按类别和样本量拆分观察，不能只看少量样本的偶然结果。
2. 内容准确率上，CosyVoice3 整体更强：WER 2.14%、CER 1.74%，低于 dots.tts-mf 的 WER 5.94%、CER 4.23%。主要差距来自英文短文本，dots.tts-mf 英文 WER 为 14.57%。
3. 音色相似度上，dots.tts-mf 更强：整体 SIM 0.742，高于 CosyVoice3 的 0.696；逐样本 SIM 胜负为 dots.tts-mf 120 胜、CosyVoice3 60 胜。
4. 速度上整体接近：dots.tts-mf RTF 0.875，CosyVoice3 RTF 0.878；但分类看差异明显，CosyVoice3 在中文和动漫角色文本更快，dots.tts-mf 在英文短句更快。
5. 项目结论：180 条短文本测试集覆盖中文、英文与动漫角色短句；dots.tts-mf 在音色相似度上更优，CosyVoice3 在整体内容准确率上更优。

## 高错误样本

### dots.tts-mf

| case | 类别 | WER | CER | 文本 | ASR 转写 |
|---|---|---:|---:|---|---|
| en_short_23 | 英文短文本 | 120.00% | 86.67% | The speaker identity should remain. |  I'm going to read the Bible. |
| en_short_02 | 英文短文本 | 100.00% | 58.62% | Please read this sentence clearly. |  Please engine as in deading call. |
| en_short_37 | 英文短文本 | 80.00% | 71.43% | A stable output is useful. |  Alright, I think that output is useful. |
| en_short_59 | 英文短文本 | 80.00% | 66.67% | The final sample is complete. |  The online shop for anxiety is complete. |
| en_short_18 | 英文短文本 | 66.67% | 40.00% | Do not rush through the ending. |  Daongun rushed to do the ending. |
| en_short_36 | 英文短文本 | 60.00% | 30.77% | The final report needs numbers. |  But the Tai Lo report needs numbers. |
| en_short_58 | 英文短文本 | 50.00% | 33.33% | This case checks latency. |  The infinite checks latency. |
| en_short_54 | 英文短文本 | 50.00% | 24.14% | This sentence has six simple words. |  The best sentence has 6 simple words. |

### CosyVoice3

| case | 类别 | WER | CER | 文本 | ASR 转写 |
|---|---|---:|---:|---|---|
| en_short_31 | 英文短文本 | 50.00% | 20.00% | Please avoid repeating words. |  vis-a-void repeating words, |
| zh_short_53 | 中文短文本 | 21.05% | 21.05% | 广州失踪女大学生浮尸流花湖警方立案侦查 | 广 州 师 中 女 大 学 生 服 饰 流 花 湖 警 方 立 案 侦 查 |
| en_short_57 | 英文短文本 | 20.00% | 15.00% | The output path is fixed. |  the output path is fit |
| en_short_40 | 英文短文本 | 20.00% | 12.00% | The prompt audio is unchanged. |  The Propped Audio is unchanged. |
| en_short_24 | 英文短文本 | 20.00% | 3.57% | This line tests content accuracy. |  This line test content accuracy. |
| anime_short_29_nilou | 动漫角色短文本 | 18.52% | 18.52% | 大家可真会开玩笑啊，哈哈哈，我能在这里演出就已经很开心了哦。 | 大 家 可 真 会 开 玩 笑 啊 我 能 在 这 里 演 出 就 已 经 很 开 心 喽 |
| en_short_50 | 英文短文本 | 16.67% | 17.24% | The English subset has sixty cases. |  The English subset has 60 cases. |
| en_short_51 | 英文短文本 | 16.67% | 3.57% | Short text can still be difficult. |  Short texts can still be difficult |

## 文件

- 逐样本 CSV：`<DOTS_TTS_ROOT>\experiments\short_text_comparison_60_each\official_style_model_comparison_180_per_case.csv`
- 汇总 JSON：`<DOTS_TTS_ROOT>\experiments\short_text_comparison_60_each\official_style_model_comparison_180_summary.json`
- dots.tts-mf 指标：`<DOTS_TTS_ROOT>\experiments\short_text_comparison_60_each\outputs\dots_tts_mf\official_style_metrics.json`
- CosyVoice3 指标：`<DOTS_TTS_ROOT>\experiments\short_text_comparison_60_each\outputs\cosyvoice3\official_style_metrics.json`
