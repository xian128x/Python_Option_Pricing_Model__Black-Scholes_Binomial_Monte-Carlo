"""
pricers/black_scholes.py
────────────────────────
Black-Scholes-Merton closed-form pricer for European vanilla options.

Model: dS = (r - q)S dt + σS dW  under the risk-neutral measure.

  d1 = [ln(S/K) + (r - q + σ²/2)T] / (σ√T)
  d2 = d1 − σ√T

  Call = S·e^(-qT)·Φ(d1) − K·e^(-rT)·Φ(d2)
  Put  = K·e^(-rT)·Φ(-d2) − S·e^(-qT)·Φ(-d1)

Greeks convention:
  Vega  ÷ 100  →  price change per 1% vol move
  Rho   ÷ 100  →  price change per 1% rate move
  Theta ÷ 365  →  price change per calendar day

Math.max(..., 0) floor guards against tiny floating-point negatives at
extreme inputs (deep OTM, T → 0).
"""

import math
from .base import BasePricer
from option_pricer_classic.models.contract import OptionContract
from option_pricer_classic.models.result   import Greeks, PricingResult


class BlackScholesPricer(BasePricer):

    # ── Normal distribution helpers ───────────────────────────────────────

    @staticmethod
    def _cdf(x: float) -> float:
        """
        Standard normal CDF via Abramowitz & Stegun 26.2.17.
        Max |error| < 7.5e-8 — sufficient for all option pricing.
        Tail guards at ±8 prevent exp underflow.
        """
        if x < -8: return 0.0
        if x >  8: return 1.0
        a1, a2, a3 =  0.319381530, -0.356563782,  1.781477937
        a4, a5     = -1.821255978,  1.330274429
        k    = 1.0 / (1.0 + 0.2316419 * abs(x))
        poly = k * (a1 + k * (a2 + k * (a3 + k * (a4 + k * a5))))
        phi  = math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)
        cdf  = 1.0 - phi * poly
        return cdf if x >= 0 else 1.0 - cdf

    @staticmethod
    def _pdf(x: float) -> float:
        """Standard normal PDF φ(x). Used in Gamma, Vega, Theta."""
        return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)

    # ── Pricing ───────────────────────────────────────────────────────────

    def price(self, contract: OptionContract) -> PricingResult:
        S, K, T   = contract.spot, contract.strike, contract.maturity
        sig, r, q = contract.vol, contract.rate, contract.dividend
        sqrtT     = math.sqrt(T)

        d1 = (math.log(S / K) + (r - q + 0.5 * sig * sig) * T) / (sig * sqrtT)
        d2 = d1 - sig * sqrtT

        erT  = math.exp(-r * T)    # e^(-rT)
        eqT  = math.exp(-q * T)    # e^(-qT)
        Nd1  = self._cdf(d1);   Nd2  = self._cdf(d2)
        Nnd1 = self._cdf(-d1);  Nnd2 = self._cdf(-d2)
        nd1  = self._pdf(d1)

        # Price — floored at 0 as a numerical safety guard
        raw = (S * eqT * Nd1 - K * erT * Nd2
               if contract.opt_type == "call"
               else K * erT * Nnd2 - S * eqT * Nnd1)
        price = max(raw, 0.0)

        # Greeks
        delta = (eqT * Nd1) if contract.opt_type == "call" else (-eqT * Nnd1)
        gamma = (nd1 * eqT) / (S * sig * sqrtT)
        vega  = S * eqT * nd1 * sqrtT / 100.0

        if contract.opt_type == "call":
            theta = (-(S * eqT * nd1 * sig) / (2 * sqrtT)
                     - r * K * erT * Nd2
                     + q * S * eqT * Nd1) / 365.0
            rho   =  K * T * erT * Nd2  / 100.0
        else:
            theta = (-(S * eqT * nd1 * sig) / (2 * sqrtT)
                     + r * K * erT * Nnd2
                     - q * S * eqT * Nnd1) / 365.0
            rho   = -K * T * erT * Nnd2 / 100.0

        greeks = Greeks(delta=delta, gamma=gamma, vega=vega, theta=theta, rho=rho)
        return PricingResult(contract=contract, price=price, greeks=greeks)
