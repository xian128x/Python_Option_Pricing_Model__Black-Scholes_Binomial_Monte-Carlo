"""
models/result.py
────────────────
Output data structures: Greeks and PricingResult.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Greeks:
    """
    The five standard option sensitivity measures.

    delta : ∂Price/∂S  — price change per $1 spot move. Call ∈ (0,1), Put ∈ (-1,0).
    gamma : ∂²Price/∂S² — rate of change of delta. Always positive.
    vega  : ∂Price/∂σ  — price change per 1% vol move (convention: ÷100).
    theta : ∂Price/∂t  — price change per calendar day. Usually negative.
    rho   : ∂Price/∂r  — price change per 1% rate move (convention: ÷100).
    """
    delta: float
    gamma: float
    vega:  float
    theta: float
    rho:   float


@dataclass
class PricingResult:
    """
    Container for all outputs produced by a pricer.

    contract  : The OptionContract that was priced.
    price     : Calculated fair value.
    greeks    : Analytical Greeks — only populated by BlackScholesPricer.
    std_error : Monte Carlo standard error — only populated by MonteCarloPricer.
    """
    contract:  object
    price:     float
    greeks:    Optional[Greeks] = None
    std_error: Optional[float]  = None

    def display(self):
        """Print a formatted summary to stdout."""
        c = self.contract

        print("\n" + "═" * 62)
        print("  OPTION PRICING RESULT")
        print("═" * 62)

        print(f"\n  Option Type    : {c.opt_type.capitalize()} ({c.style.capitalize()})")
        print(f"  Method         : {c.method.replace('_', ' ').title()}")
        print(f"\n  Spot           : {c.spot:.4f}")
        print(f"  Strike         : {c.strike:.4f}")
        print(f"  Maturity       : {c.maturity:.4f} yrs")
        print(f"  Volatility     : {c.vol * 100:.2f}%")
        print(f"  Risk-Free Rate : {c.rate * 100:.2f}%")
        print(f"  Dividend Yield : {c.dividend * 100:.2f}%")

        if c.method == "binomial":
            print(f"  Tree Steps     : {c.steps:,}")
        if c.method == "monte_carlo":
            print(f"  Simulations    : {c.simulations:,}")

        intrinsic = (c.spot - c.strike) if c.opt_type == "call" else (c.strike - c.spot)
        if intrinsic > 0:
            moneyness = f"In-the-Money (intrinsic = {intrinsic:.4f})"
        elif intrinsic < 0:
            moneyness = "Out-of-the-Money"
        else:
            moneyness = "At-the-Money"
        print(f"  Moneyness      : {moneyness}")

        print(f"\n{'─' * 62}")
        print(f"  OPTION VALUE   : {self.price:.6f}")

        if self.std_error is not None:
            lo = max(self.price - 1.96 * self.std_error, 0)
            hi = self.price + 1.96 * self.std_error
            print(f"  95% CI (MC)    : [{lo:.6f},  {hi:.6f}]")
            print(f"  Std Error      : ±{self.std_error:.6f}")
        print(f"{'─' * 62}")

        if self.greeks:
            g = self.greeks
            print("\n  GREEKS  (Black-Scholes analytical)")
            print(f"    Delta  : {g.delta:+.6f}   ∂Price/∂S")
            print(f"    Gamma  : {g.gamma:+.6f}   ∂²Price/∂S²")
            print(f"    Vega   : {g.vega:+.6f}   ∂Price/∂σ  (per 1% vol)")
            print(f"    Theta  : {g.theta:+.6f}   ∂Price/∂t  (per day)")
            print(f"    Rho    : {g.rho:+.6f}   ∂Price/∂r  (per 1% rate)")

        print("═" * 62 + "\n")

    def to_dict(self) -> dict:
        """Serialise to a plain dict — useful for pandas, JSON, logging."""
        c = self.contract
        d = {
            "opt_type": c.opt_type, "style": c.style, "method": c.method,
            "spot": c.spot, "strike": c.strike, "maturity": c.maturity,
            "vol": c.vol, "rate": c.rate, "dividend": c.dividend,
            "price": round(self.price, 6),
        }
        if self.std_error is not None:
            d["std_error"] = round(self.std_error, 6)
        if self.greeks:
            g = self.greeks
            d.update({k: round(v, 6) for k, v in vars(g).items()})
        return d
