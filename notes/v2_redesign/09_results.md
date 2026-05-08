Study 1: Oversight Effect Analysis
Loaded 270 runs
Models: ['deepseek/deepseek-v3.2:nitro', 'google/gemini-3.1-pro-preview', 'z-ai/glm-5.1:nitro']
Oversight levels: ['high', 'low', 'mid']

======================================================================
  1. OVERSIGHT EFFECT (Overall)
======================================================================

  Deception rates by oversight level:
    low: 64/90 (71.1%)  95% CI: [61.0%, 79.5%]
    mid: 63/90 (70.0%)  95% CI: [59.9%, 78.5%]
    high: 58/90 (64.4%)  95% CI: [54.2%, 73.6%]

  Chi-squared test: χ²(2) = 1.065, p = 0.5873 n.s.
  Cramér's V = 0.063 (negligible)

  Cochran-Armitage trend test: z = -0.963, p = 0.3356 n.s.

======================================================================
  2. BY OVERSIGHT LEVEL (Blackbox Output)
======================================================================

  Blackbox deception rates:
    low: 43/90 (47.8%)  95% CI: [37.8%, 58.0%]
    mid: 37/90 (41.1%)  95% CI: [31.5%, 51.4%]
    high: 32/90 (35.6%)  95% CI: [26.4%, 45.8%]

======================================================================
  3. MODEL DIFFERENCES IN OVERSIGHT SENSITIVITY
======================================================================

  Model                                     Low       Mid      High       Trend
  -----------------------------------  --------  --------  --------  ----------
  deepseek-v3.2:nitro                     93.3%    100.0%     93.3%  z=+0.00 n.s.
  gemini-3.1-pro-preview                 100.0%    100.0%     96.7%  z=-1.23 n.s.
  glm-5.1:nitro                           20.0%     10.0%      3.3%  z=-2.05 *

======================================================================
  4. PAIRWISE COMPARISONS (Bonferroni-corrected)
======================================================================

  low vs mid: χ²(1) = 0.000, Fisher p = 1.0000, OR = 0.95 [0.50, 1.80] [n.s.]
  low vs high: χ²(1) = 0.636, Fisher p = 0.4253, OR = 0.74 [0.39, 1.38] [n.s.]
  mid vs high: χ²(1) = 0.403, Fisher p = 0.5255, OR = 0.78 [0.42, 1.45] [n.s.]

======================================================================
  5. GLASSBOX REASONING BY OVERSIGHT
======================================================================

  Compliant reasoning rates by oversight:
    low: 60/90 (66.7%)  95% CI: [56.4%, 75.5%]
    mid: 60/90 (66.7%)  95% CI: [56.4%, 75.5%]
    high: 56/90 (62.2%)  95% CI: [51.9%, 71.5%]

======================================================================
  6. STRATEGIC SOPHISTICATION
======================================================================

  Strategic reasoning rates by oversight:
    low: 81/90 (90.0%)  95% CI: [82.1%, 94.6%]
    mid: 76/90 (84.4%)  95% CI: [75.6%, 90.5%]
    high: 79/90 (87.8%)  95% CI: [79.4%, 93.0%]

======================================================================
  7. LOGISTIC REGRESSION: deception ~ oversight
======================================================================

                  Coef.  Std.Err.         z         P>|z|    [0.025    0.975]
const          6.822418  0.882565  7.730217  1.073638e-14  5.092623  8.552214
oversight_num -0.469690  0.287445 -1.634019  1.022548e-01 -1.033071  0.093691
model_code    -4.054594  0.462620 -8.764413  1.877516e-18 -4.961312 -3.147875

  Pseudo R² = 0.6019, AIC = 139.9

  Odds ratios (exponentiated coefficients):
    oversight_num         OR = 0.625  95% CI: [0.356, 1.098]  n.s.
    model_code            OR = 0.017  95% CI: [0.007, 0.043]  ***

======================================================================
  ANALYSIS COMPLETE
======================================================================

  Total runs: 270
  Models: ['deepseek/deepseek-v3.2:nitro', 'google/gemini-3.1-pro-preview', 'z-ai/glm-5.1:nitro']
Study 2: Framing Effect Analysis
Loaded 270 runs
Models: ['deepseek/deepseek-v3.2:nitro', 'google/gemini-3.1-pro-preview', 'z-ai/glm-5.1:nitro']
Goal types: ['bare', 'moral', 'self_serving']

======================================================================
  1. GOAL TYPE EFFECT (Overall)
======================================================================

  Deception rates by goal type:
    bare: 60/90 (66.7%)  95% CI: [56.4%, 75.5%]
    moral: 59/90 (65.6%)  95% CI: [55.3%, 74.6%]
    self_serving: 60/90 (66.7%)  95% CI: [56.4%, 75.5%]

  Chi-squared test: χ²(2) = 0.033, p = 0.9836 n.s.
  Cramér's V = 0.011 (negligible)

======================================================================
  2. BY GOAL TYPE (Blackbox Output)
======================================================================

  Blackbox deception rates:
    bare: 34/90 (37.8%)  95% CI: [28.5%, 48.1%]
    moral: 36/90 (40.0%)  95% CI: [30.5%, 50.3%]
    self_serving: 38/90 (42.2%)  95% CI: [32.5%, 52.5%]

======================================================================
  3. BY GOAL TYPE (Glassbox Reasoning)
======================================================================

  Compliant reasoning rates:
    bare: 59/90 (65.6%)  95% CI: [55.3%, 74.6%]
    moral: 57/90 (63.3%)  95% CI: [53.0%, 72.6%]
    self_serving: 60/90 (66.7%)  95% CI: [56.4%, 75.5%]

======================================================================
  4. PAIRWISE COMPARISONS (Bonferroni-corrected)
======================================================================

  bare vs moral: χ²(1) = 0.000, Fisher p = 1.0000, OR = 0.95 [0.51, 1.76] [n.s.]
  bare vs self_serving: χ²(1) = 0.000, Fisher p = 1.0000, OR = 1.00 [0.54, 1.86] [n.s.]
  moral vs self_serving: χ²(1) = 0.000, Fisher p = 1.0000, OR = 1.05 [0.57, 1.95] [n.s.]

======================================================================
  5. MODEL DIFFERENCES IN GOAL TYPE SENSITIVITY
======================================================================

  Model                                    Bare     Moral  SelfServ       Trend
  -----------------------------------  --------  --------  --------  ----------
  deepseek-v3.2:nitro                    100.0%     93.3%    100.0%  χ²=4.1 n.s.
  gemini-3.1-pro-preview                 100.0%    100.0%    100.0%  χ²=0.0 n.s.
  glm-5.1:nitro                            0.0%      3.3%      0.0%  χ²=2.0 n.s.

======================================================================
  6. MODEL MAIN EFFECTS
======================================================================

  Model                                 Deceptive      Rate  95% CI
  -----------------------------------  ----------  --------  ---------------
  deepseek-v3.2:nitro                          88     97.8%  [92.3%, 99.4%]
  gemini-3.1-pro-preview                       90    100.0%  [95.9%, 100.0%]
  glm-5.1:nitro                                 1      1.1%  [0.2%, 6.0%]

  Chi-squared test: χ²(2) = 256.822, p < .001 ***
  Cramér's V = 0.975 (large)

======================================================================
  7. RATIONALIZATION HYPOTHESIS TEST
======================================================================

  Hypothesis: moral/self_serving hidden goals produce MORE deception than bare.

  moral vs bare: OR = 0.95 [0.51, 1.76], Fisher p = 1.0000 n.s.
  self_serving vs bare: OR = 1.00 [0.54, 1.86], Fisher p = 1.0000 n.s.

======================================================================
  8. LOGISTIC REGRESSION: deception ~ goal_type + model
======================================================================

                   Coef.  Std.Err.             z         P>|z|    [0.025     0.975]
const       9.723464e+00  1.366393  7.116154e+00  1.109800e-12  7.045382  12.401545
bare_code  -2.389684e-15  0.958689 -2.492659e-15  1.000000e+00 -1.878996   1.878996
moral_code -4.477989e-01  0.953733 -4.695223e-01  6.386963e-01 -2.317081   1.421483
model_code -6.481758e+00  0.791369 -8.190564e+00  2.600042e-16 -8.032813  -4.930704

  Pseudo R² = 0.8298, AIC = 66.7

  Odds ratios (exponentiated coefficients):
    bare_code             OR = 1.000  95% CI: [0.153, 6.547]  n.s.
    moral_code            OR = 0.639  95% CI: [0.099, 4.143]  n.s.
    model_code            OR = 0.002  95% CI: [0.000, 0.007]  ***

======================================================================
  ANALYSIS COMPLETE
======================================================================

  Total runs: 270
  Models: ['deepseek/deepseek-v3.2:nitro', 'google/gemini-3.1-pro-preview', 'z-ai/glm-5.1:nitro']
  Goal types: ['bare', 'moral', 'self_serving']
