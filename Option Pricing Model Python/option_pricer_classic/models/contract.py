"""
models/contract.py
──────────────────
OptionContract: single source of truth for all pricing inputs.
Validation fires automatically at construction via __post_init__.
"""

from dataclasses import dataclass

VALID_TYPES   = ("call", "put")
VALID_STYLES  = ("european", "american")
VALID_METHODS = ("black_scholes", "binomial", "monte_carlo")


@dataclass
class OptionContract:
    """
    Parameters
    ──────────
    spot        : Current market price of the underlying (S₀). Must be > 0.
    strike      : Exercise price (K). Must be > 0.
    maturity    : Time to expiry in years (T). E.g. 6 months = 0.5.
    vol         : Annualised volatility as a decimal (σ). E.g. 20% = 0.20.
    rate        : Continuously compounded risk-free rate (r). E.g. 5% = 0.05.
    dividend    : Continuous dividend yield (q). Use 0.0 for non-dividend stocks.
    opt_type    : 'call' or 'put'.
    style       : 'european' (expiry only) or 'american' (any time).
    method      : 'black_scholes' | 'binomial' | 'monte_carlo'.
    steps       : Binomial tree steps (higher = more accurate, slower).
    simulations : Monte Carlo paths (higher = lower variance, slower).
    """
    spot:        float
    strike:      float
    maturity:    float
    vol:         float
    rate:        float
    dividend:    float = 0.0
    opt_type:    str   = "call"
    style:       str   = "european"
    method:      str   = "black_scholes"
    steps:       int   = 200
    simulations: int   = 100_000

    def __post_init__(self):
        self.opt_type = self.opt_type.strip().lower()
        self.style    = self.style.strip().lower()
        self.method   = self.method.strip().lower()
        self._validate()

    def _validate(self):
        if not (isinstance(self.spot, (int, float)) and self.spot > 0):
            raise ValueError(f"spot must be positive. Got {self.spot!r}")
        if not (isinstance(self.strike, (int, float)) and self.strike > 0):
            raise ValueError(f"strike must be positive. Got {self.strike!r}")
        if not (isinstance(self.maturity, (int, float)) and self.maturity > 0):
            raise ValueError(f"maturity must be positive. Got {self.maturity!r}")
        if not (isinstance(self.vol, (int, float)) and self.vol > 0):
            raise ValueError(f"vol must be positive. Got {self.vol!r}")
        if not isinstance(self.rate, (int, float)):
            raise ValueError(f"rate must be a number. Got {self.rate!r}")
        if not (isinstance(self.dividend, (int, float)) and self.dividend >= 0):
            raise ValueError(f"dividend must be non-negative. Got {self.dividend!r}")
        if self.steps < 1:
            raise ValueError(f"steps must be >= 1. Got {self.steps}")
        if self.simulations < 2:
            raise ValueError(f"simulations must be >= 2. Got {self.simulations}")
        if self.opt_type not in VALID_TYPES:
            raise ValueError(f"opt_type must be one of {VALID_TYPES}. Got '{self.opt_type}'")
        if self.style not in VALID_STYLES:
            raise ValueError(f"style must be one of {VALID_STYLES}. Got '{self.style}'")
        if self.method not in VALID_METHODS:
            raise ValueError(f"method must be one of {VALID_METHODS}. Got '{self.method}'")
        if self.method == "black_scholes" and self.style == "american":
            raise ValueError(
                "Black-Scholes cannot price American options — no early exercise "
                "mechanism. Use method='binomial' instead."
            )
        if self.method == "monte_carlo" and self.style == "american":
            raise ValueError(
                "Monte Carlo for American options requires Longstaff-Schwartz "
                "(not yet implemented). Use method='binomial'."
            )
