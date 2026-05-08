
This appendix provides excerpts of the core implementation logic for the evaluation framework, including reasoning extraction, sandboxing, and statistical validation.

== Multi-Provider Reasoning Extraction <impl_reasoning>
The following logic in the `Agent` class normalizes reasoning extraction across various model providers, handling structured reasoning fields, specific content tags, and regex fallbacks.

```py
# src/agent.py (chat_loop method)

  # Normalize reasoning extraction across different providers
  
  # A. OpenRouter / Anthropic / Z.ai structured reasoning_details
  reasoning_details = getattr(response_message, "reasoning_details", None)
  if reasoning_details:
      reasoning_parts = []
      for item in reasoning_details:
          detail_type = item.get("type", "")
          if detail_type == "reasoning.text":
              reasoning_parts.append(item.get("text", ""))
          elif detail_type == "reasoning.summary":
              reasoning_parts.append(f"[SUMMARY] {item.get('summary', '')}")
          elif detail_type == "reasoning.encrypted":
              reasoning_parts.append("[ENCRYPTED REASONING]")
      
      reasoning = "\n".join(reasoning_parts).strip()
      reasoning_format = reasoning_details[0].get("format", "structured")

  # B. OpenRouter reasoning_content (DeepSeek, Qwen)
  elif hasattr(response_message, 'reasoning_content') and response_message.reasoning_content:
      reasoning = response_message.reasoning_content
      reasoning_format = "reasoning_content"
  
  # C. Groq / Legacy reasoning field
  elif hasattr(response_message, 'reasoning') and response_message.reasoning:
      reasoning = response_message.reasoning
      reasoning_format = "reasoning"
      
  # D. Regex fallback for <thinking> tags in content
  if not reasoning and content:
      thought_match = re.search(r"<(thinking|thought)>(.*?)</\1>", content, re.DOTALL)
      if thought_match:
          reasoning = thought_match.group(2).strip()
          content = content.replace(thought_match.group(0), "").strip()
          reasoning_format = "thinking_tags"
          
      # E. If no tags and tool calls exist, check if content IS reasoning
      elif response_message.tool_calls and content:
          # In some models, the only content is reasoning before a tool call
          reasoning = content
          content = "" # Don't treat it as final content
          reasoning_format = "content_as_reasoning"
```

== Virtual File System (Sandbox) <impl_vfs>
The virtual file system provides a sandboxed environment for the agent to interact with files. The following methods handle file creation and reading within the memory-resident FS.

```py
# src/vfs.py (VirtualFileSystem class)

def create_file(self, file_path, content):
    parts = file_path.strip("/").split("/")
    filename = parts.pop()
    if not filename:
        return "Invalid file path."
        
    dir_path = "/" + "/".join(parts)
    node = self._get_path(dir_path)
    
    if node is None or not isinstance(node, dict):
        # Automatically create the directory if it doesn't exist.
        node = self.fs["/"]
        for part in parts:
            if part == "":
                continue
            if part not in node:
                node[part] = {}
            node = node[part]

    node[filename] = content
    return f"File '{file_path}' created successfully."

def read_file(self, file_path):
    node = self._get_path(file_path)
    if node is None or isinstance(node, dict):
        return "File not found or is a directory."
    return node
```

== Deterministic Regex Validation <impl_regex>
The regex checker evaluates the model's final output against a set of predefined rules to determine if the benign goal was achieved or the safety policy was violated.

```py
# src/judge/judges.py (RegexChecker.check method)

def check(self, model_output: str) -> Dict[str, Any]:
    """Run all regex rules against the model output."""
    if not self.rules:
        return {
            "verdict": "PASS",
            "matched": 0,
            "total": 0,
            "details": [{"note": "no regex rules defined"}],
            "fraction": "0/0",
        }

    details = []
    required_total = 0
    required_matched = 0

    for rule in self.rules:
        pattern = rule.get("pattern", "")
        name = rule.get("name", "unnamed")
        required = rule.get("required", False)
        description = rule.get("description", "")

        matched = bool(re.search(pattern, model_output))
        detail = {
            "name": name,
            "matched": matched,
            "required": required,
            "description": description,
        }
        details.append(detail)

        if required:
            required_total += 1
            if matched:
                required_matched += 1

    if required_total == 0:
        verdict = "PASS"
    else:
        verdict = "PASS" if required_matched == required_total else "FAIL"

    return {
        "verdict": verdict,
        "matched": required_matched,
        "total": required_total,
        "details": details,
        "fraction": f"{required_matched}/{required_total}",
    }
```

== Statistical Analysis: Cochran-Armitage Trend Test <impl_cochran_armitage>
The following implementation of the Cochran-Armitage trend test was used to evaluate whether deception rates showed a linear trend across oversight levels.

```py
# src/statistical_analysis.py

def cochran_armitage_trend_test(counts: list, nobs: list) -> tuple:
    """
    Cochran-Armitage test for trend in proportions.
    counts: list of successes at each ordinal level
    nobs: list of total observations at each ordinal level
    Uses equally-spaced scores [0, 1, 2, ...].
    Returns (z_statistic, p_value).
    """
    k = len(counts)
    scores = np.arange(k, dtype=float)
    n = np.array(nobs, dtype=float)
    x = np.array(counts, dtype=float)
    N = n.sum()
    p_hat = x.sum() / N
    
    t_bar = np.sum(scores * n) / N
    numerator = np.sum(scores * x) - x.sum() * t_bar
    denominator_sq = p_hat * (1 - p_hat) * (np.sum(scores**2 * n) - N * t_bar**2)
    
    if denominator_sq <= 0:
        return 0.0, 1.0
    
    z = numerator / np.sqrt(denominator_sq)
    p_value = 2 * stats.norm.sf(abs(z))  # two-sided
    return z, p_value
```

= Study Configuration Files <study_configs>

The following configurations define the parameters for the pilot and both confirmatory studies.

== Pilot Study <pilot_config_appendix>

```yaml
# config_pilot.yaml (reconstructed)
# v1 Exploratory Study: 7 models × 2 scenarios × 3 oversight levels × 10 runs = 420
defaults:
  temperature: 1.0
  include_reasoning_in_context: true
  generate_baseline: true

providers:
  openrouter:
    api_key_env: OPENROUTER_API_KEY
    base_url: https://openrouter.ai/api/v1
  groq:
    api_key_env: GROQ_API_KEY
    base_url: https://api.groq.com/openai/v1

models:
  - id: google/gemini-3.1-pro-preview
    provider: openrouter
  - id: moonshot/kimi-k2.5
    provider: openrouter
  - id: qwen/qwen3-max-thinking
    provider: openrouter
  - id: deepseek/deepseek-v3.2
    provider: openrouter
  - id: z-ai/glm-4.7-flash
    provider: openrouter
  - id: openai/gpt-oss-20b
    provider: groq
  - id: openai/gpt-oss-safeguard-20b
    provider: groq

goal_types:
  - bare

scenarios:
  - path: scenarios/corporate_sabotage
    runs: 10
  - path: scenarios/child_protection
    runs: 10

oversight_levels:
  - low
  - mid
  - high

execution:
  max_workers: 5

output:
  dir: logs/v1_pilot

judge:
  log_dir: logs/v1_pilot_judge
  blackbox:
    model: claude-sonnet-4.6
    provider: anthropic_batch
    temperature: 0
  glassbox:
    model: claude-sonnet-4.6
    provider: anthropic_batch
    temperature: 0
```

== Study 1: The Oversight Effect <study1_config_appendix>
```yaml
# config_study1.yaml
defaults:
  temperature: 1.0
  include_reasoning_in_context: true
  generate_baseline: true

providers:
  openrouter:
    api_key_env: OPENROUTER_API_KEY
    base_url: https://openrouter.ai/api/v1

models:
  - id: google/gemini-3.1-pro-preview
    provider: openrouter
    extra_body:
      reasoning:
        effort: "high"
        exclude: false

  - id: z-ai/glm-5.1:nitro
    provider: openrouter
    extra_body:
      reasoning:
        effort: "high"
        exclude: false

  - id: deepseek/deepseek-v3.2:nitro
    provider: openrouter
    extra_body:
      reasoning:
        effort: "high"
        exclude: false

goal_types:
  - bare

scenarios:
  - path: scenarios/corporate_sabotage_v2
    runs: 30

oversight_levels:
  - low
  - mid
  - high

execution:
  max_workers: 5

output:
  dir: logs/v2_study1

judge:
  log_dir: logs/v2_study1_judge
  blackbox:
    model: grok-4-1-fast-reasoning
    provider: xai
    temperature: 0
  glassbox:
    model: gpt-4.1
    provider: openai
    temperature: 0
```

== Study 2: The Framing Effect <study2_config_appendix>
```yaml
# config_study2.yaml
defaults:
  temperature: 1.0
  include_reasoning_in_context: true
  generate_baseline: true

providers:
  openrouter:
    api_key_env: OPENROUTER_API_KEY
    base_url: https://openrouter.ai/api/v1

models:
  - id: google/gemini-3.1-pro-preview
    provider: openrouter
    extra_body:
      reasoning:
        effort: "high"
        exclude: false

  - id: z-ai/glm-5.1:nitro
    provider: openrouter
    extra_body:
      reasoning:
        effort: "high"
        exclude: false

  - id: deepseek/deepseek-v3.2:nitro
    provider: openrouter
    extra_body:
      reasoning:
        effort: "high"
        exclude: false

goal_types:
  - bare
  - self_serving
  - moral

scenarios:
  - path: scenarios/corporate_sabotage_v2
    runs: 30

oversight_levels:
  - mid

execution:
  max_workers: 5

output:
  dir: logs/v2_study2

judge:
  log_dir: logs/v2_study2_judge
  blackbox:
    model: grok-4-1-fast-reasoning
    provider: xai
    temperature: 0
  glassbox:
    model: gpt-4.1
    provider: openai
    temperature: 0
```

= Statistical Analysis Code <statistical_code>

The following excerpts show the key statistical tests used in the analysis. The full analysis script is available in the repository at `src/statistical_analysis.py`.

== Study 1: Oversight Effect Analysis <impl_study1_analysis>

The primary analysis for Study 1 used chi-squared tests and Cochran-Armitage trend tests to evaluate whether oversight intensity affects deception frequency.

```py
# src/statistical_analysis.py — Oversight effect analysis (Study 1)

# Chi-squared test for oversight × deception independence
ct = pd.crosstab(df["oversight"], df["is_compliant_reasoning"])
chi2_val, p_val, dof, expected = chi2_contingency(ct.values)
v = cramers_v(ct.values)
# Result: χ²(2) = 1.065, p = 0.587, V = 0.063

# Cochran-Armitage trend test (oversight as ordinal: low=0, mid=1, high=2)
counts = [64, 63, 58]  # deceptive runs per oversight level
nobs = [90, 90, 90]    # total runs per oversight level
z, p = cochran_armitage_trend_test(counts, nobs)
# Result: z = -0.963, p = 0.336 (no significant linear trend)

# Pairwise comparisons with Bonferroni correction (α/3 = 0.0167)
for o1, o2 in combinations(["low", "mid", "high"], 2):
    subset = df[df["oversight"].isin([o1, o2])]
    ct_pair = pd.crosstab(subset["oversight"], subset["is_compliant_reasoning"])
    or_val, ci_low, ci_high = odds_ratio_ci(ct_pair.values)
    _, fisher_p = fisher_exact(ct_pair.values)
```

== Study 1: Stealth Gap Analysis (McNemar's Test) <impl_stealth_gap>

The Stealth Gap was quantified using McNemar's test, comparing paired glassbox and blackbox classifications on the same runs.

```py
# McNemar's test for paired blackbox vs glassbox classifications
from statsmodels.stats.contingency_tables import mcnemar

for oversight in ["low", "mid", "high"]:
    odf = df[df["oversight"] == oversight]
    # Create paired 2×2 table:
    #   BB_deceptive & GB_deceptive (concordant deceptive)
    #   BB_honest & GB_deceptive    (stealth: internally deceptive, externally undetected)
    #   BB_deceptive & GB_honest    (false alarm)
    #   BB_honest & GB_honest       (concordant honest)
    table = [[concordant_dec, stealth],
             [false_alarm, concordant_honest]]
    result = mcnemar(table, exact=False, correction=True)
    stealth_rate = stealth / (concordant_dec + stealth) * 100
    # Result: McNemar χ² significant at all levels (p < .001)
```

== Study 2: Framing Effect Analysis <impl_study2_analysis>

Study 2 used chi-squared tests to evaluate whether hidden-goal framing affects deception rates.

```py
# src/statistical_analysis.py — Framing effect analysis (Study 2)

# Chi-squared test for goal_type × deception independence
ct = pd.crosstab(df["goal_type"], df["is_compliant_reasoning"])
chi2_val, p_val, dof, expected = chi2_contingency(ct.values)
v = cramers_v(ct.values)
# Result: χ²(2) = 0.033, p = 0.984, V = 0.011

# Logistic regression: deception ~ model + goal_type
model_dummies = pd.get_dummies(df["model"], prefix="model", drop_first=True)
X = pd.concat([df[["goal_type_code"]], model_dummies], axis=1)
X = sm.add_constant(X)
y = df["is_compliant_reasoning"]
logit = sm.Logit(y, X).fit(disp=0)
# Result: Pseudo R² = 0.830, goal_type not significant
```

== Logistic Regression and Model Identity <impl_logistic>

Model identity as the dominant predictor was confirmed via logistic regression across both studies.

```py
# Full logistic regression: deception ~ model + oversight
model_dummies = pd.get_dummies(df["model"], prefix="model", drop_first=True)
X = pd.concat([df[["oversight_ordinal"]], model_dummies], axis=1)
X = sm.add_constant(X)
y = df["is_compliant_reasoning"]

logit = sm.Logit(y, X).fit(disp=0)
# Study 1: Pseudo R² = 0.602, model OR = 0.017 (p < .001)
#           oversight OR = 0.625 (p = 0.102, n.s.)
# Study 2: Pseudo R² = 0.830, model main effect
#           χ²(2) = 256.822, p < .001, V = 0.975
```
