"""
option_pricer_classic/engine.py
────────────────────────────────
OptionPricer: central dispatcher. Routes contracts to the correct pricer.

To add a new method:
  1. Write pricers/my_pricer.py (subclass BasePricer)
  2. Add "my_method": MyPricer() to _REGISTRY
  3. Add "my_method" to VALID_METHODS in models/contract.py
"""

from option_pricer_classic.models.contract import OptionContract
from option_pricer_classic.models.result   import PricingResult
from option_pricer_classic.pricers         import (
    BlackScholesPricer, BinomialTreePricer, MonteCarloPricer,
)


class OptionPricer:
    """Stateless orchestrator — safe to share across calls."""

    _REGISTRY = {
        "black_scholes": BlackScholesPricer(),
        "binomial":      BinomialTreePricer(),
        "monte_carlo":   MonteCarloPricer(),
    }

    @classmethod
    def price(cls, contract: OptionContract) -> PricingResult:
        pricer = cls._REGISTRY.get(contract.method)
        if pricer is None:
            raise KeyError(
                f"No pricer for method='{contract.method}'. "
                f"Available: {list(cls._REGISTRY)}"
            )
        return pricer.price(contract)

    @classmethod
    def price_batch(
        cls, contracts: list[OptionContract]
    ) -> tuple[list[PricingResult | None], list[tuple[int, Exception]]]:
        """
        Price a list of contracts. Returns:
          results : one PricingResult per contract (None if that contract errored)
          errors  : list of (index, exception) for failed contracts
        """
        results, errors = [], []
        for i, c in enumerate(contracts):
            try:
                results.append(cls.price(c))
            except Exception as e:
                errors.append((i, e))
                results.append(None)
        return results, errors
