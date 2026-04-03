"""
utils/iv_solver.py
──────────────────
Implied volatility solver: Newton-Raphson with bisection fallback.

Given a market-observed option price P*, finds σ* such that BS(σ*) = P*.

No-arbitrage bounds (call):
  max(S·e^(-qT) − K·e^(-rT), 0)  ≤  P*  ≤  S·e^(-qT)

No-arbitrage bounds (put):
  max(K·e^(-rT) − S·e^(-qT), 0)  ≤  P*  ≤  K·e^(-rT)

If P* lies outside these bounds, IV does not exist and a ValueError is raised.

Newton-Raphson:
  σ_{n+1} = σ_n − (BS(σ_n) − P*) / Vega(σ_n)
  Quadratic convergence; typically 3-5 iterations.

Bisection fallback:
  Used when Vega < 1e-12 (near-zero — deep OTM/ITM, near expiry).
  Slower but guaranteed convergence within the bracket.
"""

import math
from dataclasses import replace
from option_pricer_classic.models.contract import OptionContract
from option_pricer_classic.pricers.black_scholes import BlackScholesPricer

_bs = BlackScholesPricer()


def solve_iv(
    market_price: float,
    contract: OptionContract,
    tol: float = 1e-9,
    max_iter: int = 100,
) -> float:
    """
    Solve for the implied volatility given a market option price.

    Parameters
    ──────────
    market_price : Observed market price of the option.
    contract     : OptionContract (vol field is a placeholder — it will be solved).
    tol          : Convergence tolerance on |BS(σ) − market_price|.
    max_iter     : Max Newton-Raphson iterations before switching to bisection.

    Returns
    ───────
    float : Implied volatility as a decimal (e.g. 0.20 = 20%).

    Raises
    ──────
    ValueError : If market_price is outside no-arbitrage bounds.
    ValueError : If solver fails to converge.
    """
    S, K, T = contract.spot, contract.strike, contract.maturity
    r, q    = contract.rate, contract.dividend
    type_   = contract.opt_type

    erT = math.exp(-r * T)
    eqT = math.exp(-q * T)
    fwd = S * eqT

    lo_bound = max(fwd - K * erT, 0.0) if type_ == "call" else max(K * erT - fwd, 0.0)
    hi_bound = fwd                      if type_ == "call" else K * erT

    if market_price < lo_bound - 1e-8 or market_price > hi_bound + 1e-8:
        raise ValueError(
            f"market_price {market_price:.4f} is outside no-arbitrage bounds "
            f"[{lo_bound:.4f}, {hi_bound:.4f}]. Implied vol does not exist."
        )

    # Newton-Raphson
    sig = 0.20
    for _ in range(max_iter):
        res  = _bs.price(replace(contract, vol=sig))
        diff = res.price - market_price
        if abs(diff) < tol:
            return sig
        vega = res.greeks.vega * 100.0   # restore from per-% to per-unit
        if abs(vega) < 1e-12:
            break
        sig -= diff / vega
        sig  = max(1e-6, min(sig, 10.0))

    # Bisection fallback
    lo, hi = 1e-6, 10.0
    for _ in range(300):
        mid     = 0.5 * (lo + hi)
        bs_mid  = _bs.price(replace(contract, vol=mid)).price
        if abs(bs_mid - market_price) < tol:
            return mid
        if bs_mid < market_price:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-12:
            return 0.5 * (lo + hi)

    raise ValueError("IV solver did not converge. Check inputs.")
