# CosyVoice3 unseen-speaker automatic metrics: generic_short

- Whisper ASR: `medium`
- Speaker similarity: CampPlus cosine similarity between prompt audio and generated audio.
- RTF: generation seconds / generated audio seconds.
- Speakers are not included in the four-character LLM-only finetuning set.

## Variant averages

| variant | n | CER | WER | pinyin tone | pinyin no tone | SIM | RTF | audio s | gen s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| base | 8 | 0.00% | 0.00% | 0.00% | 0.00% | 0.8876 | 0.616 | 5.215 | 3.198 |
| clean_epoch_2 | 8 | 0.00% | 0.00% | 0.00% | 0.00% | 0.8854 | 0.625 | 5.040 | 3.146 |

## Per speaker

| speaker | variant | CER | WER | pinyin no tone | SIM | RTF | ASR transcript |
|---|---|---:|---:|---:|---:|---:|---|
| Alhaitham | base | 0.00% | 0.00% | 0.00% | 0.9083 | 0.630 | 今天陽光很好,我們吃過早飯以後一起去公園散步吧 |
| Alhaitham | clean_epoch_2 | 0.00% | 0.00% | 0.00% | 0.9043 | 0.677 | 今天陽光很好,我們吃過早飯以後,一起去公園散步吧。 |
| Kamisato Ayaka | base | 0.00% | 0.00% | 0.00% | 0.8843 | 0.571 | 今天陽光很好,我們吃過早飯以後一起去公園散步吧 |
| Kamisato Ayaka | clean_epoch_2 | 0.00% | 0.00% | 0.00% | 0.8882 | 0.607 | 今天陽光很好,我們吃過早飯以後,一起去公園散步吧。 |
| Nahida | base | 0.00% | 0.00% | 0.00% | 0.8841 | 0.713 | 今天陽光很好,我們吃過早飯以後,一起去公園散步吧 |
| Nahida | clean_epoch_2 | 0.00% | 0.00% | 0.00% | 0.8938 | 0.676 | 今天陽光很好,我們吃過早飯以後,一起去公園散步吧 |
| Nilou | base | 0.00% | 0.00% | 0.00% | 0.8706 | 0.575 | 今天陽光很好,我們吃過早飯以後一起去公園散步吧! |
| Nilou | clean_epoch_2 | 0.00% | 0.00% | 0.00% | 0.8391 | 0.581 | 今天陽光很好,我們吃過早飯以後一起去公園散步吧。 |
| Ningguang | base | 0.00% | 0.00% | 0.00% | 0.8781 | 0.681 | 今天陽光很好,我們吃過早飯以後,一起去公園散步吧。 |
| Ningguang | clean_epoch_2 | 0.00% | 0.00% | 0.00% | 0.8854 | 0.650 | 今天陽光很好,我們吃過早飯以後,一起去公園散步吧。 |
| Tighnari | base | 0.00% | 0.00% | 0.00% | 0.8992 | 0.545 | 今天阳光很好我们吃过早饭以后一起去公园散步吧 |
| Tighnari | clean_epoch_2 | 0.00% | 0.00% | 0.00% | 0.8897 | 0.598 | 今天陽光很好我們吃過早飯以後一起去公園散步吧 |
| Yelan | base | 0.00% | 0.00% | 0.00% | 0.8927 | 0.546 | 今天陽光很好我們吃過早飯以後一起去公園散步吧 |
| Yelan | clean_epoch_2 | 0.00% | 0.00% | 0.00% | 0.8979 | 0.614 | 今天陽光很好,我們吃過早飯以後一起去公園散步吧。 |
| Yoimiya | base | 0.00% | 0.00% | 0.00% | 0.8834 | 0.668 | 今天阳光很好,我们吃过早饭以后一起去公园散步吧 |
| Yoimiya | clean_epoch_2 | 0.00% | 0.00% | 0.00% | 0.8848 | 0.596 | 今天阳光很好,我们吃过早饭以后一起去公园散步吧 |
