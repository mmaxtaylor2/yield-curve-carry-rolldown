import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

def plot_bar_decomp(df: pd.DataFrame, title: str, filename: str = "carry_vs_rolldown.png"):
    ax = df[["carry", "rolldown"]].plot(kind="bar", figsize=(9, 5))
    ax.set_title(title)
    ax.set_ylabel("Return (fraction)")
    ax.axhline(0)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / filename, dpi=150)
    plt.show()

def plot_total(df: pd.DataFrame, title: str, filename: str = "total_carry_rolldown.png"):
    series = df["carry_plus_roll"] if "carry_plus_roll" in df.columns else (df["carry"] + df["rolldown"])
    ax = series.plot(kind="bar", figsize=(9, 5))
    ax.set_title(title)
    ax.set_ylabel("Return (fraction)")
    ax.axhline(0)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / filename, dpi=150)
    plt.show()

def plot_scenario_total_per_dv01(pivot_df: pd.DataFrame, title: str, filename: str = "scenario_total_per_dv01.png"):
    ax = pivot_df.plot(kind="bar", figsize=(11, 5))
    ax.set_title(title)
    ax.set_ylabel("Total Return per DV01")
    ax.axhline(0)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / filename, dpi=150)
    plt.show()

def plot_horizon_total_per_dv01(pivot_df: pd.DataFrame, title: str, filename: str = "horizon_total_per_dv01.png"):
    """
    pivot_df:
      index = maturity
      columns = horizon labels (e.g., '1M','3M','6M','12M')
      values = carry_plus_roll_per_dv01
    """
    ax = pivot_df.plot(kind="bar", figsize=(11, 5))
    ax.set_title(title)
    ax.set_ylabel("(Carry + Roll) per DV01")
    ax.axhline(0)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / filename, dpi=150)
    plt.show()

def plot_pm_dashboard(
    base_df,
    scenario_pivot,
    horizon_pivot,
    takeaway_text,
    filename="pm_dashboard.png"
):
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))

    # --------------------------------------------------
    # Top-left: Carry vs Roll-down
    # --------------------------------------------------
    base_df[["carry", "rolldown"]].plot(
        kind="bar",
        ax=axes[0, 0],
        width=0.8
    )
    axes[0, 0].set_title("Carry vs Roll-Down (Base Curve)")
    axes[0, 0].axhline(0)
    axes[0, 0].set_ylabel("Return")

    # --------------------------------------------------
    # Top-right: Scenario sensitivity (Total per DV01)
    # --------------------------------------------------
    scenario_pivot.plot(
        kind="bar",
        ax=axes[0, 1],
        width=0.8
    )
    axes[0, 1].set_title("Scenario Sensitivity: Total Return per DV01")
    axes[0, 1].axhline(0)
    axes[0, 1].set_ylabel("Return per DV01")

    # --------------------------------------------------
    # Bottom-left: Horizon sensitivity
    # --------------------------------------------------
    horizon_pivot.plot(
        kind="bar",
        ax=axes[1, 0],
        width=0.8
    )
    axes[1, 0].set_title("Horizon Sensitivity: (Carry + Roll) per DV01")
    axes[1, 0].axhline(0)
    axes[1, 0].set_ylabel("Return per DV01")

    # --------------------------------------------------
    # Bottom-right: PM Takeaway text
    # --------------------------------------------------
    axes[1, 1].axis("off")
    axes[1, 1].text(
        0,
        1,
        takeaway_text,
        fontsize=11,
        va="top",
        ha="left",
        wrap=True
    )
    axes[1, 1].set_title("PM Takeaway")

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / filename, dpi=150)
    plt.show()

