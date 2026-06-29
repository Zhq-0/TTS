# OmniVoice SIM 单句提升样例

说明：按 `finetuned_best SIM-o - base SIM-o` 排序筛选。优先推荐试听“SIM 提升且 CER/WER 未变差”的样例；仅 SIM 提升但内容准确率下降的样例不建议用于展示。

## 推荐试听样例

| case | 说话人 | 类别 | 文本 | SIM-o | CER/WER 变化 | 结论 |
|---|---|---|---|---:|---|---|
| short_text_019 | Yoimiya | 短文本 | 请继续往前走。 | 0.4103 -> 0.5389 (+0.1286) | 0.00%/0.00% -> 0.00%/0.00% | 推荐 |
| game_terms_018 | Yelan | 游戏专有词 | 托马准备了热腾腾的家政料理，也安排好了接待流程。 | 0.6366 -> 0.7476 (+0.1110) | 0.00%/0.00% -> 0.00%/0.00% | 推荐 |
| medium_long_text_037 | Kaedehara Kazuha | 中长文本 | 我们会用相同的随机种子生成音频，尽量减少采样随机性带来的影响。 | 0.6869 -> 0.7947 (+0.1078) | 0.00%/0.00% -> 0.00%/0.00% | 推荐 |
| game_terms_002 | Arataki Itto | 游戏专有词 | 派蒙提醒大家，深境螺旋的挑战需要合理搭配元素反应。 | 0.4714 -> 0.5694 (+0.0981) | 4.35%/15.38% -> 0.00%/0.00% | 推荐 |
| zh_en_mixed_019 | Nahida | 中英混合 | 如果 model 多说了 extra words，WER 会明显升高。 | 0.6529 -> 0.7449 (+0.0920) | 7.14%/22.22% -> 3.57%/11.11% | 可试听 |
| zh_en_mixed_017 | Kaedehara Kazuha | 中英混合 | 我们使用 fixed seed 来减少 sampling randomness。 | 0.5711 -> 0.6572 (+0.0861) | 32.35%/66.67% -> 5.88%/16.67% | 可试听 |
| short_text_049 | Nahida | 短文本 | 请读得自然。 | 0.5138 -> 0.5980 (+0.0841) | 0.00%/0.00% -> 0.00%/0.00% | 推荐 |
| game_terms_046 | Gorou | 游戏专有词 | 基尼奇和阿乔一起行动，总能用独特的方法解决问题。 | 0.6850 -> 0.7608 (+0.0758) | 4.55%/16.67% -> 0.00%/0.00% | 推荐 |

## 对应音频路径

### short_text_019 / Yoimiya

- reference: `D:\audio\OmniVoice\data\genshin_20_speakers\audio\yoimiya\yoimiya_003909.wav`
- base: `D:\audio\OmniVoice\outputs\genshin_20_speakers_extended_texts\base\short_text\short_text_019_yoimiya.wav`
- finetuned_best: `D:\audio\OmniVoice\outputs\genshin_20_speakers_extended_texts\finetuned_best\short_text\short_text_019_yoimiya.wav`

### game_terms_018 / Yelan

- reference: `D:\audio\OmniVoice\data\genshin_20_speakers\audio\yelan\yelan_015551.wav`
- base: `D:\audio\OmniVoice\outputs\genshin_20_speakers_extended_texts\base\game_terms\game_terms_018_yelan.wav`
- finetuned_best: `D:\audio\OmniVoice\outputs\genshin_20_speakers_extended_texts\finetuned_best\game_terms\game_terms_018_yelan.wav`

### medium_long_text_037 / Kaedehara Kazuha

- reference: `D:\audio\OmniVoice\data\genshin_20_speakers\audio\kaedehara_kazuha\kaedehara_kazuha_058363.wav`
- base: `D:\audio\OmniVoice\outputs\genshin_20_speakers_extended_texts\base\medium_long_text\medium_long_text_037_kaedehara_kazuha.wav`
- finetuned_best: `D:\audio\OmniVoice\outputs\genshin_20_speakers_extended_texts\finetuned_best\medium_long_text\medium_long_text_037_kaedehara_kazuha.wav`

### game_terms_002 / Arataki Itto

- reference: `D:\audio\OmniVoice\data\genshin_20_speakers\audio\arataki_itto\arataki_itto_035893.wav`
- base: `D:\audio\OmniVoice\outputs\genshin_20_speakers_extended_texts\base\game_terms\game_terms_002_arataki_itto.wav`
- finetuned_best: `D:\audio\OmniVoice\outputs\genshin_20_speakers_extended_texts\finetuned_best\game_terms\game_terms_002_arataki_itto.wav`

### zh_en_mixed_019 / Nahida

- reference: `D:\audio\OmniVoice\data\genshin_20_speakers\audio\nahida\nahida_045427.wav`
- base: `D:\audio\OmniVoice\outputs\genshin_20_speakers_extended_texts\base\zh_en_mixed\zh_en_mixed_019_nahida.wav`
- finetuned_best: `D:\audio\OmniVoice\outputs\genshin_20_speakers_extended_texts\finetuned_best\zh_en_mixed\zh_en_mixed_019_nahida.wav`

### zh_en_mixed_017 / Kaedehara Kazuha

- reference: `D:\audio\OmniVoice\data\genshin_20_speakers\audio\kaedehara_kazuha\kaedehara_kazuha_003226.wav`
- base: `D:\audio\OmniVoice\outputs\genshin_20_speakers_extended_texts\base\zh_en_mixed\zh_en_mixed_017_kaedehara_kazuha.wav`
- finetuned_best: `D:\audio\OmniVoice\outputs\genshin_20_speakers_extended_texts\finetuned_best\zh_en_mixed\zh_en_mixed_017_kaedehara_kazuha.wav`

### short_text_049 / Nahida

- reference: `D:\audio\OmniVoice\data\genshin_20_speakers\audio\nahida\nahida_045594.wav`
- base: `D:\audio\OmniVoice\outputs\genshin_20_speakers_extended_texts\base\short_text\short_text_049_nahida.wav`
- finetuned_best: `D:\audio\OmniVoice\outputs\genshin_20_speakers_extended_texts\finetuned_best\short_text\short_text_049_nahida.wav`

### game_terms_046 / Gorou

- reference: `D:\audio\OmniVoice\data\genshin_20_speakers\audio\gorou\gorou_058824.wav`
- base: `D:\audio\OmniVoice\outputs\genshin_20_speakers_extended_texts\base\game_terms\game_terms_046_gorou.wav`
- finetuned_best: `D:\audio\OmniVoice\outputs\genshin_20_speakers_extended_texts\finetuned_best\game_terms\game_terms_046_gorou.wav`

## 不建议单独展示的高 SIM 提升样例

| case | 说话人 | SIM-o | 问题 |
|---|---|---:|---|
| short_text_028 | Kamisato Ayaka | 0.5880 -> 0.7411 (+0.1530) | SIM 提升最大，但 WER 0.00% -> 33.33%，CER 0.00% -> 16.67%。 |
| short_text_048 | Kamisato Ayaka | 0.5719 -> 0.6656 (+0.0937) | SIM 提升明显，但 WER 0.00% -> 33.33%，CER 0.00% -> 16.67%。 |
