"""
pricers/monte_carlo.py
──────────────────────
Monte Carlo simulation under risk-neutral GBM.

  S_T = S · exp[(r - q - σ²/2)T + σ√T · Z],   Z ~ N(0,1)

The Itô correction (-σ²/2) ensures E[S_T] = S·e^((r-q)T).

Variance reduction — antithetic variates:
  For each Z drawn, we also compute the payoff using -Z.
  The two payoffs are negatively correlated, reducing variance ~30-50%.
  We draw M/2 normals to produce M payoffs total.

Memory efficiency:
  Uses an online sum/sum-of-squares accumulator instead of storing all M
  payoffs — O(1) memory regardless of simulation count.

Standard error:
  SE = e^(-rT) · σ_payoffs / √M   (CLT; Bessel-corrected sample variance)

All prices are floored at 0. The discounted average of non-negative payoffs
is always ≥ 0 in theory, but the floor guards floating-point edge cases.
"""

import math
import random
from .base import BasePricer
from option_pricer_classic.models.contract import OptionContract
from option_pricer_classic.models.result   import PricingResult


class MonteCarloPricer(BasePricer):

    def price(self, contract: OptionContract) -> PricingResult:
        S, K, T   = contract.spot, contract.strike, contract.maturity
        sig, r, q = contract.vol, contract.rate, contract.dividend
        M         = contract.simulations

        drift = (r - q - 0.5 * sig * sig) * T
        vol_T = sig * math.sqrt(T)
        disc  = math.exp(-r * T)

        # Online accumulator — O(1) memory
        n = max((M // 2), 1) * 2   # ensure even
        total = 0.0
        sq    = 0.0

        for _ in range(n // 2):
            Z = random.gauss(0.0, 1.0)
            for z in (Z, -Z):
                ST      = S * math.exp(drift + vol_T * z)
                payoff  = max(ST - K, 0.0) if contract.opt_type == "call" else max(K - ST, 0.0)
                total  += payoff
                sq     += payoff * payoff

        avg      = total / n
        variance = max((sq - n * avg * avg) / (n - 1), 0.0)   # Bessel-corrected
        price    = max(disc * avg, 0.0)
        se       = disc * math.sqrt(variance / n)

        return PricingResult(contract=contract, price=price, std_error=se)

    @staticmethod
    def simulate_path(S: float, r: float, q: float, sig: float,
                      T: float, steps: int) -> list[float]:
        """
        Simulate a full GBM price path with `steps` time steps.
        Returns a list of length (steps + 1): [S₀, S₁, …, S_T].

        Ready-made building block for path-dependent extensions:
          Asian option  → use average of path
          Barrier       → check if any node crosses the barrier
          Lookback      → use min or max of path
        """
        dt   = T / steps
        drft = (r - q - 0.5 * sig * sig) * dt
        vdt  = sig * math.sqrt(dt)
        path = [S]
        for _ in range(steps):
            path.append(path[-1] * math.exp(drft + vdt * random.gauss(0.0, 1.0)))
        return path
