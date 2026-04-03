# Option Pricer Classic — Python Codebase

Modular option valuation framework. Pure Python standard library, no dependencies.

## Structure

```
option_pricer_classic/
├── main.py                    ← Entry point. Edit contracts here.
├── engine.py                  ← Dispatcher: routes contracts to pricers.
├── models/
│   ├── contract.py            ← OptionContract dataclass + validation.
│   └── result.py              ← PricingResult + Greeks + display().
├── pricers/
│   ├── base.py                ← Abstract BasePricer (ABC).
│   ├── black_scholes.py       ← BSM analytical pricer + 5 Greeks.
│   ├── binomial.py            ← CRR binomial tree (European + American).
│   └── monte_carlo.py         ← GBM simulation + antithetic variates.
├── utils/
│   ├── display.py             ← Banner and run summary table.
│   └── iv_solver.py           ← Newton-Raphson + bisection IV solver.
└── tests/
    └── test_pricers.py        ← 22 unit tests, no pytest needed.
```

## Usage

```bash
python main.py
python tests/test_pricers.py
```

## Quick API

```python
from option_pricer_classic import OptionContract, OptionPricer

result = OptionPricer.price(OptionContract(
    spot=100, strike=105, maturity=0.5,
    vol=0.20, rate=0.05, dividend=0.02,
    opt_type="call", style="european",
    method="black_scholes",
))
result.display()
print(result.greeks.delta)

# Implied vol
from option_pricer_classic.utils import solve_iv
iv = solve_iv(4.50, contract)
```

## Method guide

| Method          | European | American | Greeks | Best for                     |
|-----------------|----------|----------|--------|------------------------------|
| `black_scholes` | ✓        | ✗        | ✓      | Vanilla European, benchmarks |
| `binomial`      | ✓        | ✓        | ✗      | American options             |
| `monte_carlo`   | ✓        | ✗        | ✗      | Extensible exotic base       |

## Extending

Add a new pricer in three steps:
1. Create `pricers/my_pricer.py` — subclass `BasePricer`, implement `price()`.
2. Register in `engine.py`: `_REGISTRY["my_method"] = MyPricer()`.
3. Add `"my_method"` to `VALID_METHODS` in `models/contract.py`.
