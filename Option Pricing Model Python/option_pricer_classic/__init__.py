"""
option_pricer_classic
─────────────────────
Modular option valuation framework matching the classic UI.

Quick start:
  from option_pricer_classic import OptionContract, OptionPricer
  result = OptionPricer.price(OptionContract(...))
  result.display()
"""
from .models.contract import OptionContract
from .models.result   import Greeks, PricingResult
from .engine          import OptionPricer
__all__ = ["OptionContract", "Greeks", "PricingResult", "OptionPricer"]
__version__ = "1.0.0"
