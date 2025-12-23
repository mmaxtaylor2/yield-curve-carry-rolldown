# ============================================================
# Yield Curve Carry & Roll-Down Analyzer
# + Scenario Analysis
# + Horizon Sensitivity
# + One-Page PM Dashboard
#
# Run from project root:
#   python main.py
# ============================================================

import sys
import datetime as dt
from pathlib import Path
import pandas as pd

# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
OUTPUT_DIR = BASE_DIR / "output"

sys.path.append(str(SRC_DIR))
OUTPUT_DIR.mkdir(exist_ok=True)

# ------------------------------------------------------------
# Local imports
# ------------------------------------------------------------
import analytics
import plotting

print("MAIN.PY STARTED")

# ------------------------------------------------------------
# FRED Treasury series
# ------------------------------------------------------------
FRED_SERIES = {
    0.25: "DGS3MO",
    0.5:  "DGS6MO",
    1.0:  "DGS1",
    2.0:  "DGS2",
    3.0:  "DGS3",
    5.0:  "DGS5",
    7.0:  "DGS7",
    10.0: "DGS10",
    20.0: "DGS20",
    30.0: "DGS30",
}

def fetch_latest_ust_curve() -> pd.Series:
    end = dt.date.today()
    start = end - dt.timedelta(days=30)

    data = {}
    for tenor, code in FRED_SERIES.items():
        url = (
            "https://fred.stlouisfed.org/graph/fredgraph.csv"
            f"?id={code}&cosd={start}&coed={end}"
        )
        df = pd.read_csv(url)
        df = df.rename(columns={code: "yield"}).dropna()
        data[tenor] = df["yield"].iloc[-1]

    curve = pd.Series(data).sort_index()
    return curve / 100.0  # % → decimal


# ------------------------------------------------------------
# Scenario helpers
# ------------------------------------------------------------
def parallel_shift(curve, bp):
    return curve + bp / 10000.0

def apply_twist(curve, front_bp, long_bp):
    tenors = curve.index.astype(float)
    t_min, t_max = tenors.min(), tenors.max()

    out = {}
    for t in tenors:
        w = (t - t_min) / (t_max - t_min)
        bp = front_bp + (long_bp - front_bp) * w
        out[t] = curve.loc[t] + bp / 10000.0

    return pd.Series(out).sort_index()


# ============================================================
# MAIN EXECUTION
# ============================================================

def run():

    # --------------------------------------------------------
    # Load curve
    # --------------------------------------------------------
    curve0 = fetch_latest_ust_curve()
    print("\nLatest UST Curve (decimal yields):")
    print(curve0)

    bonds = [
        analytics.BondSpec(2, curve0.loc[2]),
        analytics.BondSpec(5, curve0.loc[5]),
        analytics.BondSpec(10, curve0.loc[10]),
        analytics.BondSpec(30, curve0.loc[30]),
    ]

    # --------------------------------------------------------
    # BASE CASE (3M)
    # --------------------------------------------------------
    horizon_3m = 0.25

    base_rows = [
        analytics.total_expected_return(b, curve0, horizon_3m)
        for b in bonds
    ]
    base_df = pd.DataFrame(base_rows).set_index("maturity")
    base_df["carry_plus_roll"] = base_df["carry"] + base_df["rolldown"]

    print("\nCarry / Roll-Down (absolute):")
    print(base_df)
    base_df.to_csv(OUTPUT_DIR / "carry_rolldown_absolute.csv")

    plotting.plot_bar_decomp(
        base_df,
        "Carry vs Roll-Down (3M Horizon)",
        "carry_vs_rolldown.png"
    )

    plotting.plot_total(
        base_df,
        "Carry + Roll-Down Total Return",
        "total_carry_rolldown.png"
    )

    # --------------------------------------------------------
    # DV01 efficiency
    # --------------------------------------------------------
    eff_rows = [
        analytics.carry_efficiency(b, curve0, horizon_3m)
        for b in bonds
    ]
    eff_df = pd.DataFrame(eff_rows).set_index("maturity")

    print("\nCarry Efficiency (per DV01):")
    print(eff_df)
    eff_df.to_csv(OUTPUT_DIR / "carry_efficiency_by_tenor.csv")

    # --------------------------------------------------------
    # PM framing
    # --------------------------------------------------------
    def bucket(m):
        if m <= 2:
            return "Front End"
        elif m <= 10:
            return "Belly"
        else:
            return "Long End"

    pm_df = eff_df.copy()
    pm_df["bucket"] = [bucket(m) for m in pm_df.index]
    pm_df = pm_df.sort_values("carry_plus_roll_per_dv01", ascending=False)

    print("\nPM Trade Framing (Base):")
    print(pm_df[["bucket", "carry_plus_roll_per_dv01"]])
    pm_df.to_csv(OUTPUT_DIR / "pm_trade_framing_ranked.csv")

    # --------------------------------------------------------
    # SCENARIOS (3M)
    # --------------------------------------------------------
    scenarios = {
        "Base": curve0,
        "Parallel +100bp": parallel_shift(curve0, 100),
        "Bear Steepener (+50/+150bp)": apply_twist(curve0, 50, 150),
        "Bull Flattener (-150/-50bp)": apply_twist(curve0, -150, -50),
    }

    scen_rows = []
    for name, scen_curve in scenarios.items():
        for b in bonds:
            r = analytics.scenario_return_decomp(
                b, curve0, scen_curve, horizon_3m
            )
            r["scenario"] = name
            scen_rows.append(r)

    scen_df = (
        pd.DataFrame(scen_rows)
        .set_index(["scenario", "maturity"])
        .sort_index()
    )

    print("\nScenario Decomposition:")
    print(scen_df)

    scen_df.to_csv(OUTPUT_DIR / "scenario_decomp.csv")

    pivot_scen = (
        scen_df.reset_index()
        .pivot(index="maturity", columns="scenario", values="total_per_dv01")
        .sort_index()
    )

    plotting.plot_scenario_total_per_dv01(
        pivot_scen,
        "Scenario: Total Return per DV01 (3M)",
        "scenario_total_per_dv01.png"
    )

    # --------------------------------------------------------
    # HORIZON SENSITIVITY
    # --------------------------------------------------------
    horizons = [
        ("1M", 1/12),
        ("3M", 3/12),
        ("6M", 6/12),
        ("12M", 1.0),
    ]

    hs_rows = []
    for label, h in horizons:
        for b in bonds:
            r = analytics.total_expected_return(b, curve0, h)
            dv = analytics.dv01(b, r["y0"])
            total = r["carry"] + r["rolldown"]

            hs_rows.append({
                "horizon": label,
                "maturity": b.maturity_years,
                "carry_plus_roll_per_dv01": total / dv,
            })

    hs_df = pd.DataFrame(hs_rows)
    hs_df.to_csv(OUTPUT_DIR / "horizon_sensitivity.csv", index=False)

    pivot_h = (
        hs_df.pivot(index="maturity", columns="horizon",
                    values="carry_plus_roll_per_dv01")
        .sort_index()
    )

    plotting.plot_horizon_total_per_dv01(
        pivot_h,
        "Horizon Sensitivity: (Carry + Roll) per DV01",
        "horizon_total_per_dv01.png"
    )

    # --------------------------------------------------------
    # ONE-PAGE PM DASHBOARD
    # --------------------------------------------------------
    takeaway_text = (
        "PM Takeaway\n\n"
        "- Front end offers the most efficient carry across all horizons due to low DV01.\n"
        "- Belly performance improves at longer horizons as roll-down becomes meaningful.\n"
        "- Long end remains DV01-constrained and is best used for macro duration views.\n"
        "- Bear steepeners penalize long duration; bull flatteners favor the front end."
    )

    plotting.plot_pm_dashboard(
        base_df=base_df,
        scenario_pivot=pivot_scen,
        horizon_pivot=pivot_h,
        takeaway_text=takeaway_text,
        filename="pm_dashboard.png"
    )

    print("\nSaved PM dashboard:")
    print("- output/pm_dashboard.png")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    run()

