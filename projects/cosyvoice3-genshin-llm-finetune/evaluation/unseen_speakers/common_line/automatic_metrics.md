# CosyVoice3 unseen-speaker automatic metrics: common_line

- Whisper ASR: `medium`
- Speaker similarity: CampPlus cosine similarity between prompt audio and generated audio.
- RTF: generation seconds / generated audio seconds.
- Speakers are not included in the four-character LLM-only finetuning set.

## Variant averages

| variant | n | CER | WER | pinyin tone | pinyin no tone | SIM | RTF | audio s | gen s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| base | 8 | 18.38% | 30.68% | 3.68% | 1.47% | 0.8768 | 0.637 | 5.040 | 3.207 |
| clean_epoch_2 | 8 | 14.71% | 27.27% | 4.41% | 1.47% | 0.8671 | 0.596 | 5.750 | 3.406 |

## Per speaker

| speaker | variant | CER | WER | pinyin no tone | SIM | RTF | ASR transcript |
|---|---|---:|---:|---:|---:|---:|---|
| Alhaitham | base | 29.41% | 36.36% | 0.00% | 0.8912 | 0.692 | 玉埋桂花童再久,只可惜故人何日再見呢? |
| Alhaitham | clean_epoch_2 | 11.76% | 36.36% | 0.00% | 0.8636 | 0.610 | 玉买桂花同在酒,只可惜故人何日再见呢? |
| Kamisato Ayaka | base | 17.65% | 27.27% | 0.00% | 0.8192 | 0.593 | 玉买桂花童在酒,只可惜故人何日再见呢? |
| Kamisato Ayaka | clean_epoch_2 | 11.76% | 18.18% | 5.88% | 0.8141 | 0.552 | 亦买桂花童载酒,只可惜故人,何日再见呢? |
| Nahida | base | 11.76% | 27.27% | 0.00% | 0.8918 | 0.676 | 玉买桂花童载酒,只可惜,故人何日再见呢? |
| Nahida | clean_epoch_2 | 11.76% | 27.27% | 0.00% | 0.9086 | 0.701 | 玉买桂花同宰酒,只可惜故人何日再見呢? |
| Nilou | base | 11.76% | 18.18% | 5.88% | 0.8834 | 0.574 | 願賣桂花同載酒 只可惜故人何日再見呢? |
| Nilou | clean_epoch_2 | 0.00% | 0.00% | 0.00% | 0.8261 | 0.530 | 欲買桂花同載酒,只可惜故人何日再見呢? |
| Ningguang | base | 11.76% | 36.36% | 0.00% | 0.8912 | 0.655 | 玉买桂花同在酒,只可惜故人何日再见呢? |
| Ningguang | clean_epoch_2 | 17.65% | 36.36% | 0.00% | 0.8820 | 0.635 | 与买桂花同在久,只可惜故人何日再见呢。 |
| Tighnari | base | 23.53% | 45.45% | 0.00% | 0.8729 | 0.575 | 玉买桂花桶再久,只可惜故人何日再见呢? |
| Tighnari | clean_epoch_2 | 23.53% | 45.45% | 0.00% | 0.8747 | 0.570 | 玉脉桂花同在久 只可惜故人何日再見呢 |
| Yelan | base | 23.53% | 36.36% | 0.00% | 0.9031 | 0.687 | 遇买桂花童再久,只可惜故人何日再见呢。 |
| Yelan | clean_epoch_2 | 17.65% | 27.27% | 0.00% | 0.8976 | 0.535 | 玉买桂花童宰酒,只可惜故人何日再见呢? |
| Yoimiya | base | 17.65% | 18.18% | 5.88% | 0.8615 | 0.643 | 欲买桂花童在酒 只可惜故人何日再见呐 |
| Yoimiya | clean_epoch_2 | 23.53% | 27.27% | 5.88% | 0.8701 | 0.637 | 哼,玉买桂花童在酒,只可惜故人,何日再见呢? |
