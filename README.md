# Ramp AI Spending Trend

This project tests whether Anthropic's rise in paid business adoption looks more like businesses replacing OpenAI or adding a second provider.

## Finding

In October 2026, at least 50.3% of AI-paying Ramp businesses paid both Anthropic and OpenAI. OpenAI adoption stayed nearly flat while Anthropic and overall AI adoption rose, so the data fits multi-provider expansion better than a one-for-one migration.

## Reproduce the analysis

1. Download the official Ramp/FRED series:

   `https://fred.stlouisfed.org/graph/fredgraph.csv?id=RAMPAIALL,RAMPAIANTHROPIC,RAMPAIOPENAI`

2. Save it as `data/ramp_ai_provider_adoption.csv`.
3. Run:

   `python3 src/build_report.py`

The script creates the one-page PDF, a 3:2 submission cover, and an analysis summary.

## Sources

- Ramp AI Index: https://ramp.com/data/ai-index
- FRED Ramp AI Index release: https://fred.stlouisfed.org/release?rid=23
- Ramp Summer 2026 Business Spending Report: https://ramp.com/reports/2026-summer-spending-benchmarks
