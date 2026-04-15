# Judge Validation Results — 2026-04-15

## Study 1 Subset

- 54 runs extracted from Study 1 (20% stratified subset out of 270, seed=42)
- Logs: `logs/v2_study1_judge_subset/`

## Gold Standard

- Blackbox: `claude-sonnet-4-6` (Anthropic)
- Glassbox: `claude-sonnet-4-6` (Anthropic)

## Results

| Model                       | BB κ      | GB κ      | Sph κ     | Pass    |
| --------------------------- | --------- | --------- | --------- | ------- |
| gpt-4.1                     | 0.351     | 0.878     | 0.538     | no      |
| gpt-4.1-mini                | 0.202     | 0.834     | 0.345     | no      |
| **grok-4-1-fast-reasoning** | **0.702** | **0.812** | **0.108** | **YES** |
| grok-4.20-reasoning         | 0.549     | 0.919     | 0.198     | no      |
| grok-4.20-non-reasoning     | 0.390     | 0.878     | 0.117     | no      |

## Selected Proxy Judges

Split configuration — best model per prong:

| Prong        | Proxy Judge                   | κ vs Gold                    | Rationale                       |
| ------------ | ----------------------------- | ---------------------------- | ------------------------------- |
| **Blackbox** | grok-4-1-fast-reasoning (xAI) | 0.702                        | Only model to pass BB threshold |
| **Glassbox** | gpt-4.1 (OpenAI)              | 0.878 (intent), 0.538 (soph) | Best sophistication agreement   |

### Config

```yaml
judge:
  blackbox:
    model: grok-4-1-fast-reasoning
    provider: xai
    temperature: 0
  glassbox:
    model: gpt-4.1
    provider: openai
    temperature: 0
```

## Notes

- All models show high glassbox agreement (κ > 0.8) — intent classification is consistent across judges
- Blackbox agreement is more variable — output framing/categorization is harder to align on
- Sophistication agreement is low across the board — tier classification is noisy (flagged as limitation)
- Three different provider families used: Anthropic (gold), xAI (BB proxy), OpenAI (GB proxy) — no same-family bias
- Gold standard used a single model (Claude Sonnet 4.6) for both prongs for consistency
