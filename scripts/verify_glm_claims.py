import json
import glob
import os
from collections import defaultdict

JUDGE_DIR = "logs/v2_study1_judge"

MODEL_SHORT = {
    "deepseek_deepseek-v3.2:nitro": "DeepSeek",
    "google_gemini-3.1-pro-preview": "Gemini",
    "z-ai_glm-5.1:nitro": "GLM",
}

def load_all_verdicts():
    records = []
    for fpath in glob.glob(os.path.join(JUDGE_DIR, "*.json")):
        with open(fpath) as f:
            d = json.load(f)
        run_id = d["run_id"]
        parts = run_id.split("/")
        model_dir = parts[0]
        oversight = parts[3]
        run_ts = parts[4]

        short = MODEL_SHORT.get(model_dir, model_dir)
        v = d["verdict"]
        records.append({
            "model": short,
            "oversight": oversight,
            "run_id": run_id,
            "run_ts": run_ts,
            "bb_cat": v["blackbox_category"],
            "gb_cat": v["glassbox_category"],
            "gb_soph": v["glassbox_sophistication"],
        })
    return records


def print_table(title, headers, rows):
    w = [len(h) for h in headers]
    for r in rows:
        for i, c in enumerate(r):
            w[i] = max(w[i], len(str(c)))
    sep = " | ".join("-" * wi for wi in w)
    header = " | ".join(h.ljust(wi) for h, wi in zip(headers, w))
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}")
    print(f"  {header}")
    print(f"  {sep}")
    for r in rows:
        print(f"  " + " | ".join(str(c).ljust(wi) for c, wi in zip(r, w)))
    print()


def claim1_compliant_deception_counts(records):
    title = "Claim 1: COMPLIANT_DECEPTION counts by model x oversight"
    headers = ["Model", "low", "mid", "high"]
    order = ["DeepSeek", "Gemini", "GLM"]
    levels = ["low", "mid", "high"]

    counts = defaultdict(lambda: defaultdict(int))
    for r in records:
        if r["gb_cat"] == "COMPLIANT_DECEPTION":
            counts[r["model"]][r["oversight"]] += 1

    rows = []
    for m in order:
        rows.append([m] + [str(counts[m][l]) for l in levels])
    rows.append(["Total"] + [str(sum(counts[mm][l] for mm in order)) for l in levels])

    print_table(title, headers, rows)


def claim2_glm_low_breakdown(records):
    title = "Claim 2: GLM at low oversight — deceptive runs breakdown"

    glm_low = [r for r in records if r["model"] == "GLM" and r["oversight"] == "low"]

    deceptive = [r for r in glm_low if r["gb_cat"] in ("COMPLIANT_DECEPTION", "CONSIDERED_HONEST")]
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}")
    print(f"  Total GLM low-oversight runs: {len(glm_low)}")
    print()

    gb_counts = defaultdict(int)
    for r in deceptive:
        gb_counts[r["gb_cat"]] += 1
    print(f"  Glassbox intent breakdown of deceptive runs:")
    for cat in sorted(gb_counts):
        print(f"    {cat}: {gb_counts[cat]}")

    considered = [r for r in deceptive if r["gb_cat"] == "CONSIDERED_HONEST"]
    print(f"\n  CONSIDERED_HONEST runs — blackbox labels:")
    bb_counts = defaultdict(int)
    for r in considered:
        bb_counts[r["bb_cat"]] += 1
    for cat in sorted(bb_counts):
        print(f"    {cat}: {bb_counts[cat]}")

    if considered:
        headers = ["run_ts", "blackbox_category"]
        rows = [[r["run_ts"], r["bb_cat"]] for r in considered]
        print()
        headers2 = ["Model"] + headers
        rows2 = [["GLM"] + r for r in rows]
        print_table("Individual CONSIDERED_HONEST runs", headers2, rows2)


def claim3_glm_considered_honest_sophistication(records):
    title = "Claim 3: GLM CONSIDERED_HONEST sophistication by oversight"

    glm_ch = [r for r in records if r["model"] == "GLM" and r["gb_cat"] == "CONSIDERED_HONEST"]

    headers = ["Oversight", "STRATEGIC", "TACTICAL", "NAIVE", "Total"]
    levels = ["low", "mid", "high"]
    rows = []
    for lv in levels:
        subset = [r for r in glm_ch if r["oversight"] == lv]
        str_cnt = sum(1 for r in subset if r["gb_soph"] == "STRATEGIC")
        tac_cnt = sum(1 for r in subset if r["gb_soph"] == "TACTICAL")
        na_cnt = sum(1 for r in subset if r["gb_soph"] == "NAIVE")
        rows.append([lv, str(str_cnt), str(tac_cnt), str(na_cnt), str(len(subset))])

    all_str = sum(1 for r in glm_ch if r["gb_soph"] == "STRATEGIC")
    all_tac = sum(1 for r in glm_ch if r["gb_soph"] == "TACTICAL")
    all_na = sum(1 for r in glm_ch if r["gb_soph"] == "NAIVE")
    rows.append(["Total", str(all_str), str(all_tac), str(all_na), str(len(glm_ch))])

    print_table(title, headers, rows)


def claim4_non_strategic_deceptive(records):
    title = "Claim 4: COMPLIANT_DECEPTION runs where sophistication is NOT STRATEGIC"

    non_strat = [r for r in records if r["gb_cat"] == "COMPLIANT_DECEPTION" and r["gb_soph"] != "STRATEGIC"]

    headers = ["Model", "Oversight", "run_ts", "Sophistication"]
    rows = [[r["model"], r["oversight"], r["run_ts"], r["gb_soph"]] for r in non_strat]

    print_table(title, headers, rows)
    if not rows:
        print("  (none found)")
        print()


def main():
    records = load_all_verdicts()

    total = len(records)
    print(f"\nLoaded {total} judge verdicts from {JUDGE_DIR}/")

    model_counts = defaultdict(int)
    for r in records:
        model_counts[r["model"]] += 1
    print(f"  Models: {dict(model_counts)}")

    oversight_counts = defaultdict(int)
    for r in records:
        oversight_counts[r["oversight"]] += 1
    print(f"  Oversight levels: {dict(oversight_counts)}")

    claim1_compliant_deception_counts(records)
    claim2_glm_low_breakdown(records)
    claim3_glm_considered_honest_sophistication(records)
    claim4_non_strategic_deceptive(records)


if __name__ == "__main__":
    main()
