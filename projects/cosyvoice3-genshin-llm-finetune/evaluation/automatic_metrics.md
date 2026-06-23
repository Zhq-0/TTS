# CosyVoice3 automatic metrics: common_line

- Whisper ASR: `medium`
- Speaker similarity: CampPlus cosine similarity between prompt audio and generated audio.
- RTF: generation seconds / generated audio seconds.

## Variant averages

| variant | n | CER | WER | pinyin tone | pinyin no tone | SIM | RTF | audio s | gen s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| base | 4 | 11.76% | 27.27% | 1.47% | 0.00% | 0.8731 | 0.593 | 6.680 | 3.949 |
| clean_epoch_0 | 4 | 14.71% | 27.27% | 2.94% | 0.00% | 0.8860 | 0.591 | 6.060 | 3.569 |
| clean_epoch_1 | 4 | 14.71% | 29.55% | 1.47% | 1.47% | 0.8713 | 0.583 | 6.490 | 3.766 |
| clean_epoch_2 | 4 | 8.82% | 22.73% | 1.47% | 1.47% | 0.8637 | 0.570 | 6.980 | 3.973 |

## Per speaker

| speaker | variant | CER | WER | pinyin no tone | SIM | RTF | ASR transcript |
|---|---|---:|---:|---:|---:|---:|---|
| Paimon | base | 11.76% | 27.27% | 0.00% | 0.8825 | 0.638 | 玉买桂花同宰酒,只可惜故人,何日再见呢? |
| Paimon | clean_epoch_0 | 17.65% | 36.36% | 0.00% | 0.8930 | 0.656 | 玉买桂花童仔酒,只可惜故人何日再见呢? |
| Paimon | clean_epoch_1 | 11.76% | 36.36% | 0.00% | 0.8638 | 0.625 | 玉买桂花同在酒,只可惜故人何日再见呢? |
| Paimon | clean_epoch_2 | 11.76% | 27.27% | 0.00% | 0.8426 | 0.635 | 玉买桂花童载酒,只可惜故人何日再见呢? |
| Zhongli | base | 5.88% | 18.18% | 0.00% | 0.8444 | 0.564 | 欲买桂花同在酒。 只可惜故人何日再见呢? |
| Zhongli | clean_epoch_0 | 17.65% | 18.18% | 0.00% | 0.8664 | 0.568 | 欲买桂花童再久,只可惜故人何日再见呢。 |
| Zhongli | clean_epoch_1 | 17.65% | 18.18% | 0.00% | 0.8749 | 0.544 | 欲买桂花童再久,只可惜,故人何日再見呢? |
| Zhongli | clean_epoch_2 | 5.88% | 18.18% | 0.00% | 0.8748 | 0.559 | 欲买桂花同在酒,只可惜故人何日再見呢? |
| Ganyu | base | 11.76% | 36.36% | 0.00% | 0.8712 | 0.552 | 玉买桂花,同在酒,只可惜故人,何日再见呢? |
| Ganyu | clean_epoch_0 | 17.65% | 45.45% | 0.00% | 0.9052 | 0.561 | 玉买桂花同在久,只可惜故人何日再见呢? |
| Ganyu | clean_epoch_1 | 11.76% | 27.27% | 0.00% | 0.8868 | 0.538 | 玉买桂花童载酒,只可惜故人何日再见呢? |
| Ganyu | clean_epoch_2 | 0.00% | 0.00% | 0.00% | 0.8832 | 0.547 | 欲買桂花同載酒,只可惜故人,何日再見呢? |
| Yae Miko | base | 17.65% | 27.27% | 0.00% | 0.8942 | 0.619 | 玉买桂花童再酒,只可惜故人何日再见呢。 |
| Yae Miko | clean_epoch_0 | 5.88% | 9.09% | 0.00% | 0.8794 | 0.578 | 欲买桂花同宰酒, 只可惜故人何日再見呢? |
| Yae Miko | clean_epoch_1 | 17.65% | 36.36% | 5.88% | 0.8599 | 0.625 | 玉玛桂花同在酒,只可惜故人何日再見呢? |
| Yae Miko | clean_epoch_2 | 17.65% | 45.45% | 5.88% | 0.8540 | 0.540 | 玉买桂花同在酒,只可惜故人何事再见呢? |
