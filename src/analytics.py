import numpy as np
from dataclasses import dataclass
import curve

# ============================================================
# Bond specification
# ============================================================

@dataclass
class BondSpec:
    maturity_years: float
    coupon: float          # annual coupon rate (decimal)
    freq: int = 2
    face: float = 100.0


# ============================================================
# Bond pricing
# ============================================================

def bond_price_from_yield(
    spec: BondSpec,
    y: float,
    maturity_years: float | None = None
) -> float:
    T = spec.maturity_years if maturity_years is None else maturity_years
    n = int(round(T * spec.freq))

    if n <= 0:
        return spec.face

    c = spec.coupon * spec.face / spec.freq
    r = y / spec.freq

    disc = 1.0 / (1.0 + r)
    pv_coupons = c * (1 - disc**n) / (1 - disc)
    pv_face = spec.face * disc**n

    return float(pv_coupons + pv_face)


# ============================================================
# Carry & roll-down
# ============================================================

def carry_return(spec: BondSpec, y0: float, horizon_years: float) -> float:
    P0 = bond_price_from_yield(spec, y0)
    coupon_income = spec.coupon * spec.face * horizon_years
    return float(coupon_income / P0)


def rolldown_return(spec: BondSpec, curve0, horizon_years: float) -> float:
    remaining = max(spec.maturity_years - horizon_years, 0.0001)

    y0 = curve.interp_yield(curve0, spec.maturity_years)
    y_roll = curve.interp_yield(curve0, remaining)

    P0 = bond_price_from_yield(spec, y0, spec.maturity_years)
    P1_roll = bond_price_from_yield(spec, y_roll, remaining)

    return float((P1_roll - P0) / P0)


def total_expected_return(spec: BondSpec, curve0, horizon_years: float) -> dict:
    y0 = curve.interp_yield(curve0, spec.maturity_years)
    carry = carry_return(spec, y0, horizon_years)
    roll = rolldown_return(spec, curve0, horizon_years)

    return {
        "maturity": spec.maturity_years,
        "y0": y0,
        "carry": carry,
        "rolldown": roll,
    }


# ============================================================
# Duration & DV01
# ============================================================

def modified_duration(spec: BondSpec, y: float, bump: float = 0.0001) -> float:
    P = bond_price_from_yield(spec, y)
    P_up = bond_price_from_yield(spec, y + bump)
    P_dn = bond_price_from_yield(spec, y - bump)

    dP_dy = (P_dn - P_up) / (2 * bump)
    return float(dP_dy / P)


def dv01(spec: BondSpec, y: float) -> float:
    mod_dur = modified_duration(spec, y)
    return float(mod_dur * spec.face * 0.0001)


def carry_efficiency(spec: BondSpec, curve0, horizon_years: float) -> dict:
    y0 = curve.interp_yield(curve0, spec.maturity_years)

    carry = carry_return(spec, y0, horizon_years)
    roll = rolldown_return(spec, curve0, horizon_years)
    dv = dv01(spec, y0)

    return {
        "maturity": spec.maturity_years,
        "carry": carry,
        "rolldown": roll,
        "dv01": dv,
        "carry_per_dv01": carry / dv,
        "carry_plus_roll_per_dv01": (carry + roll) / dv,
    }


# ============================================================
# Scenario analysis
# Carry + Roll + Shift P/L decomposition
# ============================================================

def scenario_return_decomp(
    spec: BondSpec,
    base_curve,
    shocked_curve,
    horizon_years: float
) -> dict:
    T = spec.maturity_years
    rem = max(T - horizon_years, 0.0001)

    # Initial yield & price
    y0 = curve.interp_yield(base_curve, T)
    P0 = bond_price_from_yield(spec, y0, T)

    # Carry
    carry = (spec.coupon * spec.face * horizon_years) / P0

    # Roll-down (base curve, shorter maturity)
    y_roll = curve.interp_yield(base_curve, rem)
    P_roll = bond_price_from_yield(spec, y_roll, rem)
    roll = (P_roll - P0) / P0

    # Shocked terminal price
    y1 = curve.interp_yield(shocked_curve, rem)
    P1 = bond_price_from_yield(spec, y1, rem)

    total = (P1 - P0) / P0 + carry
    shift = total - carry - roll

    dv = dv01(spec, y0)

    return {
        "maturity": T,
        "y0": y0,
        "dv01": dv,
        "carry": float(carry),
        "rolldown": float(roll),
        "shift_pnl": float(shift),
        "total_return": float(total),
        "total_per_dv01": float(total / dv),
    }

