import numpy as np
import pandas as pd

# Standard UST tenors in years
TENOR_YEARS = np.array([0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30], dtype=float)

def interp_yield(curve: pd.Series, t: float) -> float:
    """
    Linearly interpolate the yield for maturity t (in years)
    given a curve indexed by tenor (years).
    """
    xs = curve.index.astype(float).to_numpy()
    ys = curve.to_numpy(dtype=float)

    if t <= xs.min():
        return float(ys[xs.argmin()])
    if t >= xs.max():
        return float(ys[xs.argmax()])

    return float(np.interp(t, xs, ys))

