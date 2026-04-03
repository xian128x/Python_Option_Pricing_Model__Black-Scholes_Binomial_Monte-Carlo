"""
pricers/base.py
───────────────
Abstract base class all pricers must implement.
Enforces the interface: every pricer exposes price(contract) → PricingResult.
"""

from abc import ABC, abstractmethod
from option_pricer_classic.models.contract import OptionContract
from option_pricer_classic.models.result   import PricingResult


class BasePricer(ABC):

    @abstractmethod
    def price(self, contract: OptionContract) -> PricingResult:
        """Compute fair value for the given contract."""
        ...

    def __repr__(self):
        return f"<{self.__class__.__name__}>"
