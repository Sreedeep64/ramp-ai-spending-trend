# Mission checks

## Question and baseline

Question: Does Anthropic's rise among Ramp businesses look more like firms replacing OpenAI or adding a second provider?

The baseline uses the official monthly Ramp AI Index series for all businesses and the Anthropic and OpenAI vendor series. The reproducible chart window is January 2025 through October 2026; the tested change window is January through October 2026.

## Finding stress test

| Series | Jan. 2026 | Oct. 2026 | Point change | Percent of starting level | Typical monthly move* |
| --- | ---: | ---: | ---: | ---: | ---: |
| Any AI provider | 45.44% | 56.80% | +11.36 points | +25.00% | 0.96 points |
| Anthropic | 21.07% | 44.78% | +23.71 points | +112.56% | 0.92 points |
| OpenAI | 40.79% | 40.56% | -0.23 points | -0.56% | 0.47 points |

*Median absolute month-to-month change from January 2025 through October 2026.

The overall increase is much larger than its usual monthly movement. Anthropic remained above OpenAI for six consecutive months, May through October 2026, so the crossover is not a one-month spike. Anthropic is the major visible driver of the change, while OpenAI remains almost flat.

October's inclusion-exclusion lower bound is:

`44.78% + 40.56% - 56.80% = 28.55%`

At least 28.55% of all Ramp businesses, or 50.26% of AI adopters, therefore paid both providers. Other AI vendors mean this is a minimum, not the exact overlap.

## Competing explanations

1. **Provider switching.** Prediction: Anthropic should pass OpenAI and OpenAI adoption should fall. Timing: Anthropic passed OpenAI in May 2026. Evidence: the first prediction holds, but OpenAI was essentially flat from January to October. This weakens a broad one-for-one exodus without ruling out some switching.
2. **Multi-provider expansion.** Prediction: Anthropic and overall AI adoption should rise while OpenAI remains stable, producing a large overlap. Evidence: all three predictions hold, so this explanation fits better.

Microsoft's dated October 28, 2026 announcement describes its enterprise stack as deliberately multi-model and able to choose the right model for each job. That supports the plausibility of multi-provider portfolios, but the announcement follows most of the observed rise and does not measure Ramp customers, so it cannot establish cause.

## Measurement limits

- Ramp observes paid vendor relationships, not active use.
- Free tools and personal accounts are not captured.
- Ramp customers are not representative of every U.S. business.
- Historical estimates can be revised.
- The aggregate provider view cannot identify which individual firms switched, added, or dropped a provider.

## Sources

- Ramp AI Index: https://ramp.com/data/ai-index
- FRED/Ramp series: https://fred.stlouisfed.org/release?rid=23
- Ramp Summer 2026 report: https://ramp.com/reports/2026-summer-spending-benchmarks
- Microsoft multi-model announcement, October 28, 2026: https://blogs.microsoft.com/blog/2026/10/28/introducing-the-microsoft-copilot-harness-unlocking-the-potential-of-truly-multi-model-agentic-work/
