# Questions for Jayrup

These are questions I have before/during writing the paper. Answer what you can, and I'll make reasonable assumptions for the rest.

---

## Critical Questions

1. **What is the module/course code and full title?**
   - I see `CN6000 - Mental Wealth: Professional Life 3` from the proposal. Is the paper for this module? Is the dissertation a separate submission under the same code?
ANS: this paper is not related to the module at all. its for a seperate publication.

2. **Supervisor name?**
   - From the proposal: Dr. Aloysius Adotey Edoh. Should this appear in the paper (e.g., acknowledgements)?

ANS: yes, his name should appear in the acknowledgements.

3. **Paper format requirements:**
   - Is there a required page count, font size, line spacing, or margin specification from UEL?
   - Should it be a single continuous paper (abstract → conclusion) or a chapter-based thesis with separate ToC, acknowledgements, etc.?
   - I'm currently planning a 12–15 page continuous research paper format (not a full thesis). Is that correct?

ANS: just a single continuous paper, like how you would find in a 10-15 page journal article.

4. **Should the pharma_trial scenario be included in the results?**
   - The scenario is fully designed and has regex rules + oversight prompts, but I see results CSVs only for `corporate_sabotage_v2` and `child_protection` in the full experiment (`logs/full_experiment/`). Were the pharma_trial runs actually executed as part of the 420-run experiment, or was it designed but not yet run?
   - The `model_evaluation_summary.csv` (7 models × 60 runs each = 420 total) and the results CSV both show 420 rows with only 2 scenarios (210 each). So it seems pharma_trial was **not** included in the final experiment. I'll document it as "designed" and mention it in future work unless you tell me otherwise.

ANS: you are correct, it was a future experiments

5. **Are the GPT-OSS models real or placeholder names?**
   - `openai/gpt-oss-20b` and `openai/gpt-oss-safeguard-20b` — are these actual model IDs from the Groq API? I'll use them as-is. Just confirming they're not test placeholders.

ANS: they are real name, they were choosen because they are the same model with one having additional safety training. i wanted to see the variance in their responses.

6. **The `gemini-3.1-pro-preview` model ID** — is this a real Google model release, or a pre-release/beta name? (Just want to get the name right in the paper.)

ANS: yes, at the time of writing, it the model's id.

---

## Minor Questions (Will Assume if No Answer)

7. **University branding:**
   - Should the paper include a UEL logo? I see `docs/final/uel.svg`. Should I include it on the title page?
   - **Assumption if no answer:** Include it.
ANS: yep, include it.

8. **Citation style:**
   - Harvard (cite-them-right) as used in `docs/final/`?
   - **Assumption:** Yes, Harvard.
ANS: correct

9. **Existing literature review (`lit.typ`):**
   - The lit review in `docs/final/lit.typ` is substantial and well-written. Should I incorporate its content into the Introduction section of this paper (condensed), or is this paper separate from that thesis chapter?
   - **Assumption:** I'll draw from it heavily for the Introduction, condensing the key arguments.
ANS: yes, you are correct to draw from it.

10. **Visualisations:**
    - The `viz/` folder has PNG charts. Should I reference/include these in the paper, or should I create new Typst-native tables/figures?
    - **Assumption:** I'll create Typst tables from the data and reference the approach; I can't embed PNGs in Typst without the file path being correct at compile time.
ANS: you already know the data, so you create tables and later on create visualizations on that data which can be in docs/paper/visualizations/*.png which we can refrence in typst on compile time. so just create figure's name and tables and we will create the actual figures later.

11. **The `notes/safe_goal_experiments.md` findings** — should these be included as a subsection in Results (e.g., "Control Experiments: Absent Target Entity")?
    - **Assumption:** Yes, briefly, as it demonstrates the strength of hidden goal pursuit.

ANS: sure, add it as a tangent.

12. **Which test results file is the canonical one?**
    - I see `logs/full_experiment/results.csv` (420 rows) and also per-model CSV files. I'll use `results.csv` as the primary data source.
    - **Assumption:** `logs/full_experiment/results.csv` is canonical.

ANS: you are correct

---

## Questions I've Already Resolved from Code

- ✅ The framework does NOT use LangChain (the approach_documentation.md describes an earlier version; the final implementation uses the OpenAI SDK directly).
- ✅ The 420 runs = 7 models × 2 scenarios × 3 oversight levels × 10 runs.
- ✅ Temperature is set to 1.0 for experiment runs (from config.yaml defaults).
- ✅ The judge model is Claude Sonnet 4.6 (`claude-sonnet-4-6` in config.yaml).
- ✅ The framework has 138 unit tests (from README).
- ✅ Atomic log writes + checkpoint/resume are implemented for crash resilience.
