# Yield Curve Carry & Roll-Down Analyzer

![PM Dashboard](output/pm_dashboard.png)

This project builds a **PM-style fixed-income analytics engine** that decomposes Treasury returns into **carry, roll-down, and duration (DV01) effects**, and evaluates their behavior across **macro scenarios and holding horizons**.

The objective is not just to compute returns, but to answer the core portfolio question:

> “Where on the curve do I earn the most risk-adjusted carry, and how does that change under different macro regimes?”

The analysis culminates in a **one-page portfolio-manager dashboard** summarizing trade-relevant insights.

---

## Key Concepts Demonstrated

- Treasury yield curve construction (UST curve)
- Carry vs roll-down return decomposition
- DV01-normalized (risk-adjusted) returns
- Curve positioning (front-end, belly, long-end)
- Scenario analysis:
  - Parallel shifts
  - Bull flatteners
  - Bear steepeners
- Horizon sensitivity (1M, 3M, 6M, 12M)
- PM-style trade framing and interpretation
- Professional visualization and CSV outputs

---

## What This Project Answers

- Which maturities deliver the best **risk-adjusted carry**?
- How does carry performance change as **holding horizon increases**?
- Which curve segments perform best in different macro environments?
- How should a PM think about **absolute vs DV01-adjusted carry**?

---

## Project Structure


