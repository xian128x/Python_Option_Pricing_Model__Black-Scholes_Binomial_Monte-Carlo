"""
pricers/binomial.py
───────────────────
Cox-Ross-Rubinstein (CRR, 1979) binomial tree.

Handles both European and American options. For American, at each interior
node the holder takes max(continuation, immediate exercise).

CRR calibration:
  u = e^(σ√dt)   d = 1/u   (recombining tree: ud = 1)

Risk-neutral probability:
  p = (e^((r-q)dt) − d) / (u − d)

Uses a Float64 array for the value layer — faster than a plain list
for large N due to typed memory.

All values are non-negative throughout:
  - terminal payoffs: max(..., 0)
  - continuation: disc-weighted average of non-negative values
  - American exercise: max(continuation, intrinsic) ≥ 0
"""

import math
from .base import BasePricer
from option_pricer_classic.models.contract import OptionContract
from option_pricer_classic.models.result   import PricingResult


class BinomialTreePricer(BasePricer):

    def price(self, contract: OptionContract) -> PricingResult:
        S, K, T   = contract.spot, contract.strike, contract.maturity
        sig, r, q = contract.vol, contract.rate, contract.dividend
        N         = contract.steps
        dt        = T / N

        u    = math.exp(sig * math.sqrt(dt))
        d    = 1.0 / u
        p    = (math.exp((r - q) * dt) - d) / (u - d)
        disc = math.exp(-r * dt)

        if not (0.0 < p < 1.0):
            raise ValueError(
                f"Risk-neutral probability p={p:.4f} is outside (0,1). "
                "Reduce the rate/dividend spread or increase volatility."
            )

        # Terminal payoffs: S·u^(2j-N) for j = 0..N
        vals = [0.0] * (N + 1)
        for j in range(N + 1):
            ST      = S * (u ** (2 * j - N))
            vals[j] = max(ST - K, 0.0) if contract.opt_type == "call" else max(K - ST, 0.0)

        # Backward induction
        for i in range(N - 1, -1, -1):
            for j in range(i + 1):
                cont = disc * (p * vals[j + 1] + (1.0 - p) * vals[j])
                if contract.style == "american":
                    SN   = S * (u ** (2 * j - i))
                    ex   = max(SN - K, 0.0) if contract.opt_type == "call" else max(K - SN, 0.0)
                    vals[j] = max(cont, ex)
                else:
                    vals[j] = cont

        return PricingResult(contract=contract, price=max(vals[0], 0.0))
