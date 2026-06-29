#!/usr/bin/env python3
"""Prepare extended text evaluation cases for the Genshin 20-speaker fine-tune."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEV_MANIFEST = ROOT / "data" / "genshin_20_speakers" / "manifests" / "dev.jsonl"
EVAL_DIR = ROOT / "evaluation" / "genshin_20_speakers_extended_texts"
CASES_PATH = EVAL_DIR / "cases.jsonl"
SUMMARY_PATH = EVAL_DIR / "case_summary.json"


SHORT_TEXTS = [
    "今天的风很轻。",
    "请把声音放慢一点。",
    "我们马上出发。",
    "这句话要说清楚。",
    "前面的路很安静。",
    "请保持自然的语气。",
    "我已经准备好了。",
    "这里的阳光很好。",
    "不要太快结束。",
    "这次测试很重要。",
    "请再确认一遍。",
    "我们一起看看吧。",
    "声音听起来不错。",
    "这段话很短。",
    "请用平稳的语速。",
    "现在开始录音。",
    "我听得很清楚。",
    "这个结果可以记录。",
    "请继续往前走。",
    "这里没有问题。",
    "稍微停顿一下。",
    "今天状态很好。",
    "这句话不要漏字。",
    "请自然地表达。",
    "我们准备完成测试。",
    "你可以慢慢说。",
    "现在切换角色。",
    "这是一条短句。",
    "请注意发音。",
    "测试马上结束。",
    "我会认真听。",
    "不要改变文本。",
    "请保持音色稳定。",
    "这段声音很干净。",
    "我们记录这个样例。",
    "请读出完整句子。",
    "这里需要重听。",
    "语气可以轻一点。",
    "请保持清晰。",
    "这次生成成功了。",
    "我们继续下一条。",
    "音量保持一致。",
    "请不要多说内容。",
    "这句用于对比。",
    "现在开始检查。",
    "请保持同样速度。",
    "这个样本很短。",
    "我们马上评测。",
    "请读得自然。",
    "最后一句结束。",
]


MEDIUM_LONG_TEXTS = [
    "今天的语音合成测试会覆盖不同长度的中文句子，用来观察模型在连续表达时的稳定性。",
    "如果生成结果能够保持清晰自然，同时不丢字也不多说，就说明模型的文本控制能力比较可靠。",
    "我们会把每条音频都保存下来，并记录对应的生成时间、音频时长和自动评测指标。",
    "在多说话人场景下，模型不仅要读准文本，还要尽量保留参考音频中的角色音色。",
    "这条测试文本包含较长的停顿和多个短语，用来检查模型是否会出现重复或提前结束。",
    "当输入文本变长以后，模型可能更容易出现漏字、吞字或者语速异常的问题。",
    "一个稳定的语音合成系统，需要在短句和长句之间都保持一致的发音质量。",
    "我们希望通过扩展测试集，减少单一句子带来的偶然性，让实验结论更加可信。",
    "如果微调后的模型只在某一句话上表现更好，那还不能说明它具备稳定提升。",
    "这段文本用于观察模型在叙述性语句中的自然度、停顿位置和整体节奏。",
    "测试过程中需要保证 base 和 finetuned 使用完全相同的参考音频和目标文本。",
    "只有控制住输入条件，才能比较公平地判断微调到底带来了哪些变化。",
    "这条句子会被不同角色的参考音频克隆出来，用来观察音色保持是否稳定。",
    "我们会重点关注文本内容是否准确，因为内容错误会直接影响语音合成的可用性。",
    "对于面试项目来说，单纯展示几个试听样例不够，还需要有可复现的评测流程。",
    "自动指标不能完全替代人工试听，但它能帮助我们快速发现模型的大致趋势。",
    "这次扩展评测会包含更多文本类型，从而更全面地观察模型的适配能力。",
    "在真实应用中，用户输入的文本往往不会只有一句固定模板，所以测试必须覆盖更多场景。",
    "当模型遇到中等长度文本时，最常见的问题是中途停顿不自然或者把句子顺序读乱。",
    "为了让实验结果更有说服力，我们需要同时记录内容准确率、音色相似度和推理效率。",
    "这条测试句会检查模型在普通叙述文本中的连贯性和稳定性。",
    "如果生成音频中出现明显的额外内容，就说明模型对目标文本的约束还不够强。",
    "多说话人微调的目标不是让某一个角色提升，而是让整体说话人分布更加稳定。",
    "我们在评测时会把每个模型的结果放在同一张表里，方便对比和复盘。",
    "这条文本稍微长一些，适合观察模型在连续生成时是否会改变语速。",
    "语音合成模型的效果不仅取决于模型结构，也很依赖训练数据的质量和覆盖范围。",
    "如果参考音频本身存在噪声或者文本不匹配，生成结果也可能受到明显影响。",
    "本次测试会保留每条样例的输出路径，方便后续进行人工试听检查。",
    "当模型面对较长的中文句子时，声调、停顿和断句都会影响最终听感。",
    "我们希望模型既能保持角色音色，又能按照输入文本完整准确地生成语音。",
    "这条中长文本主要用于评估模型是否能稳定处理普通口语化表达。",
    "在评测报告中，我会把不同类别的结果分开统计，避免总体平均掩盖细节。",
    "如果某一类文本的错误率明显更高，就需要进一步分析是文本类型还是模型能力造成的。",
    "这段话没有特殊名词，主要考察模型的基础中文表达能力。",
    "相比短文本，中长文本更能暴露模型在内容规划和生成持续性上的问题。",
    "这条句子包含多个逗号，适合检查模型能否在合适的位置自然停顿。",
    "我们会用相同的随机种子生成音频，尽量减少采样随机性带来的影响。",
    "扩展后的测试集可以帮助我们判断微调结果是不是具有一致性。",
    "如果微调后内容更准但音色相似度下降，就需要在训练策略上继续权衡。",
    "这次测试不是为了追求单个指标好看，而是为了更准确地理解模型行为。",
    "模型在短句上的表现很好，并不代表它在中长文本上也同样稳定。",
    "这条文本用于观察模型在连续语义表达中的语气是否自然。",
    "我们需要把生成音频、评测指标和文本内容一起保存，方便后续复查。",
    "当样本数量增加以后，评测结果会比单句测试更能反映真实表现。",
    "这条句子模拟普通用户可能输入的一段说明文本。",
    "如果模型在多条文本上都能保持低错误率，就说明它的文本服从性更可靠。",
    "这段文本用于检查模型是否会在结尾处重复或者突然截断。",
    "完成扩展评测后，我们可以重新判断简历中的指标是否足够可信。",
    "这条中长句包含几个连续动作，适合观察生成音频的节奏是否平滑。",
    "最后一条中长文本用于确认评测脚本能稳定处理更丰富的中文输入。",
]


GAME_TERM_TEXTS = [
    "旅行者准备前往蒙德城，寻找新的风神瞳和传送锚点。",
    "派蒙提醒大家，深境螺旋的挑战需要合理搭配元素反应。",
    "钟离提到璃月港的契约，也讲到了岩王帝君的旧事。",
    "甘雨整理了月海亭的文书，然后准备去绝云间巡查。",
    "八重神子在鸣神大社等待，她似乎已经看穿了所有计划。",
    "纳西妲希望旅行者在须弥城继续调查世界树的异常。",
    "艾尔海森认为教令院的问题不能只靠表面的推理解决。",
    "神里绫华准备在稻妻城迎接远道而来的客人。",
    "宵宫说长野原烟花会的烟火一定要在夜空中绽放。",
    "夜兰留下了新的线索，指向层岩巨渊深处的秘密。",
    "凝光在群玉阁上观察璃月港的变化，神情十分平静。",
    "荒泷一斗宣布荒泷派今天也要堂堂正正地赢下比赛。",
    "提纳里提醒柯莱，不要随便触碰雨林里陌生的蕈兽。",
    "迪奥娜调制了一杯特殊饮品，却依然讨厌酒馆的气味。",
    "北斗的南十字船队已经准备启航，目标是远方的海域。",
    "迪希雅握紧大剑，准备保护沙漠中的商队安全通过。",
    "五郎正在检查反抗军的阵地，确认补给是否已经送达。",
    "托马准备了热腾腾的家政料理，也安排好了接待流程。",
    "诺艾尔希望通过骑士团考核，成为真正可靠的西风骑士。",
    "枫原万叶听见风中的声音，判断前方会有新的相遇。",
    "七圣召唤的牌局已经开始，双方都在等待关键的行动牌。",
    "尘歌壶里的摆设还没有完成，需要更多洞天宝钱来兑换图纸。",
    "这次活动需要收集原石、摩拉、经验书和天赋培养材料。",
    "玩家需要先完成魔神任务，才能解锁后续的传说任务。",
    "队伍里同时带上水元素和雷元素，可以触发感电反应。",
    "草元素和雷元素配合以后，可以打出激化相关的伤害。",
    "如果想提升角色练度，就要刷圣遗物副本和周本材料。",
    "雷电将军的梦想一心和无想的一刀，是稻妻剧情的重要线索。",
    "温迪的风场可以帮助旅行者飞到更高的位置。",
    "胡桃在往生堂安排仪式，同时提醒客人不要害怕。",
    "可莉又在星落湖附近试验炸弹，琴团长可能会很头疼。",
    "魈守护着荻花洲，也一直记得自己和夜叉的责任。",
    "申鹤的红绳压制着情绪，她的力量来自特殊的修行。",
    "白术正在不卜庐配药，七七则认真记录每一件事情。",
    "芙宁娜站在欧庇克莱歌剧院里，等待审判继续进行。",
    "那维莱特听完证词以后，开始重新整理案件的关键细节。",
    "莱欧斯利在梅洛彼得堡处理事务，语气依然十分冷静。",
    "琳妮特安静地站在舞台旁边，等待林尼完成最后的魔术。",
    "娜维娅相信刺玫会一定能找到真相，也会保护身边的人。",
    "夏沃蕾正在检查特巡队的装备，确认行动不会出现漏洞。",
    "千织对服装细节很严格，每一处剪裁都不能随便应付。",
    "克洛琳德拔出佩剑，准备按照决斗代理人的规则行动。",
    "希格雯认真照顾病人，也会提醒大家按时休息。",
    "玛拉妮带着旅行者前往纳塔，介绍当地的部族和传说。",
    "卡齐娜虽然有些紧张，但仍然决定参加这次试炼。",
    "基尼奇和阿乔一起行动，总能用独特的方法解决问题。",
    "火神相关的传说仍然没有完全揭开，纳塔的冒险才刚开始。",
    "至冬女皇的计划牵动着七国局势，愚人众执行官也陆续登场。",
    "博士、散兵和公子都曾经让旅行者面对艰难的选择。",
    "神之眼、命之座和元素爆发共同决定了角色的战斗风格。",
]


ZH_EN_MIXED_TEXTS = [
    "这次 zero-shot voice cloning 的效果需要结合 CER 和 SIM 一起看。",
    "请记录 batch size、num steps 和最终 RTF，方便后续复现实验。",
    "模型加载完成后，先做 warmup，再开始正式 timing。",
    "如果 checkpoint 选择不稳定，就需要重新查看 validation loss。",
    "这条文本包含 English words，用来测试 mixed text 的生成效果。",
    "我们把 base model 和 finetuned model 放在同一组 case 里比较。",
    "当前 GPU 是 RTX 4090D，推理速度可以用 RTF 表示。",
    "请确认 prompt audio 和 target text 没有发生错配。",
    "如果 ASR transcript 出现 hallucination，需要结合人工试听判断。",
    "这个 demo 需要同时展示 audio samples 和 metric table。",
    "训练脚本里设置 learning rate 为 two e minus six。",
    "我会把 results json 和 markdown report 一起保存。",
    "中英混合场景下，Whisper 的 recognition error 需要单独分析。",
    "如果 speaker similarity 下降，说明 voice cloning 可能受影响。",
    "这个 pipeline 覆盖 generation、evaluation 和 report writing。",
    "请把 output wav 文件按照 model name 和 category 分类保存。",
    "我们使用 fixed seed 来减少 sampling randomness。",
    "这次 evaluation 需要包含 short text、long text 和 game terms。",
    "如果 model 多说了 extra words，WER 会明显升高。",
    "请检查 reference audio 是否来自 dev split。",
    "我希望 finetuned checkpoint 在 speaker embedding 上更接近 prompt。",
    "这个 case 用来测试 Chinese and English 混合读法。",
    "模型应该正确读出 GPU、RTF、SIM 和 WER 这些缩写。",
    "请生成一段 natural speech，不要改变原始 target text。",
    "我们后续可以把 audio demo 上传到 GitHub Pages。",
    "如果 throughput 下降，需要检查 num step 和 batch setting。",
    "这条句子包含 model selection 和 error analysis 两个关键词。",
    "请把 automatic metrics 写入 json file，方便后续统计。",
    "在 TTS project 中，data cleaning 通常非常关键。",
    "我会用 Python script 自动整理每个 speaker 的结果。",
    "如果 prompt text 太长，zero-shot conditioning 可能受到影响。",
    "这个样例包含 LoRA、LLM-only 和 finetune 三个术语。",
    "语音合成系统需要兼顾 content accuracy 和 voice similarity。",
    "请确认 output audio 没有 clipping，也没有明显 background noise。",
    "我们把 category summary 放在 report 的前半部分。",
    "如果 English pronunciation 很差，就需要单独做 mixed text analysis。",
    "这个 experiment 用来支持 internship resume 的项目描述。",
    "评测脚本会计算 CER、WER、UTMOS、SIM 和 RTF。",
    "请保证 base 和 finetuned 使用相同的 prompt audio。",
    "这条 mixed sentence 需要模型读准 checkpoint 和 tokenizer。",
    "如果 generated speech 太快，RTF 可能好看但听感不好。",
    "项目复盘时需要区分 training gain 和 evaluation noise。",
    "这次测试会保存 generation seconds 和 audio duration。",
    "请把 Qwen、Whisper 和 WavLM 这些模型名读清楚。",
    "如果 ASR backend 不适合某类文本，指标就只能作为参考。",
    "这个 case 用来观察 model robustness under mixed input。",
    "我们会对 each category 统计平均 CER 和 WER。",
    "如果 finetuned model 只在部分 speaker 上提升，也需要如实记录。",
    "这条文本包含 prompt、target、speaker 和 checkpoint。",
    "最后一个 mixed text 用来确认 evaluation pipeline 正常结束。",
]


TEXT_GROUPS = {
    "short_text": SHORT_TEXTS,
    "medium_long_text": MEDIUM_LONG_TEXTS,
    "game_terms": GAME_TERM_TEXTS,
    "zh_en_mixed": ZH_EN_MIXED_TEXTS,
}


def balanced_references(rows: list[dict]) -> list[dict]:
    by_speaker: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_speaker[row["speaker"]].append(row)
    speakers = sorted(by_speaker)
    output = []
    max_count = max(len(items) for items in by_speaker.values())
    for index in range(max_count):
        for speaker in speakers:
            items = by_speaker[speaker]
            if index < len(items):
                output.append(items[index])
    return output


def main() -> None:
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    dev_rows = [
        json.loads(line)
        for line in DEV_MANIFEST.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    refs = balanced_references(dev_rows)
    cases = []
    ref_index = 0
    for category, texts in TEXT_GROUPS.items():
        if len(texts) != 50:
            raise ValueError(f"{category} must contain 50 texts, got {len(texts)}")
        for item_index, text in enumerate(texts, start=1):
            reference = refs[ref_index % len(refs)]
            case_id = f"{category}_{item_index:03d}"
            cases.append(
                {
                    "case_id": case_id,
                    "category": category,
                    "category_index": item_index,
                    "speaker": reference["speaker"],
                    "reference_audio": reference["audio_path"],
                    "reference_text": reference["text"],
                    "reference_id": reference["id"],
                    "text": text,
                    "language_id": "zh",
                    "asr_language": "zh",
                }
            )
            ref_index += 1
    CASES_PATH.write_text(
        "\n".join(json.dumps(case, ensure_ascii=False) for case in cases) + "\n",
        encoding="utf-8",
    )
    summary = {
        "case_count": len(cases),
        "categories": Counter(case["category"] for case in cases),
        "speakers": Counter(case["speaker"] for case in cases),
        "cases_path": str(CASES_PATH),
        "reference_manifest": str(DEV_MANIFEST),
        "note": "Each category contains 50 text-speaker cases; reference prompts are balanced across the 20-speaker dev split.",
    }
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved cases: {CASES_PATH}")
    print(f"Saved summary: {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
