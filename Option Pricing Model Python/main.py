"""
main.py
───────
Entry point. Edit CONTRACTS below, then run:
  python main.py

QUICK REFERENCE
  method:   'black_scholes'  — European only, gives Greeks, instant
            'binomial'       — European or American, no Greeks
            'monte_carlo'    — European only, gives std error, extensible

  style:    'european'       — exercise at expiry only
            'american'       — exercise any time (binomial only)

  opt_type: 'call'           — right to buy at strike
            'put'            — right to sell at strike
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from option_pricer_classic          import OptionContract, OptionPricer
from option_pricer_classic.utils    import print_banner, print_run_summary, solve_iv
from dataclasses                    import replace


# ─────────────────────────────────────────────────────────────────────────────
#  CONTRACTS — edit here
# ─────────────────────────────────────────────────────────────────────────────

CONTRACTS = [

    # 1. OTM European Call — Black-Scholes (instant, gives Greeks)
    OptionContract(
        spot=100.0, strike=105.0, maturity=0.5,
        vol=0.20, rate=0.05, dividend=0,
        opt_type="call", style="european", method="black_scholes",
    ),

    # 2. ATM European Put — Black-Scholes
    OptionContract(
        spot=100.0, strike=100.0, maturity=1.0,
        vol=0.25, rate=0.05, dividend=0.0,
        opt_type="put", style="european", method="black_scholes",
    ),

    # 3. ATM American Put — Binomial Tree
    #    Same params as above but American style.
    #    American price should be >= European price (early exercise premium > 0).
    OptionContract(
        spot=100.0, strike=100.0, maturity=1.0,
        vol=0.25, rate=0.05, dividend=0.0,
        opt_type="put", style="american", method="binomial", steps=500,
    ),

    # 4. OTM European Call — Monte Carlo (should converge to contract 1)
    OptionContract(
        spot=100.0, strike=105.0, maturity=0.5,
        vol=0.20, rate=0.05, dividend=0.02,
        opt_type="call", style="european", method="monte_carlo", simulations=300_000,
    ),

]

# ─────────────────────────────────────────────────────────────────────────────
#  IMPLIED VOL DEMO — set True to enable
# ─────────────────────────────────────────────────────────────────────────────

RUN_IV_DEMO  = True
IV_MKT_PRICE = 4.50
IV_CONTRACT  = OptionContract(
    spot=100.0, strike=105.0, maturity=0.5,
    vol=0.01,   # placeholder — will be solved
    rate=0.05, dividend=0.02,
    opt_type="call", style="european", method="black_scholes",
)


# ─────────────────────────────────────────────────────────────────────────────
#  RUN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print_banner()
    print(f"\n  Pricing {len(CONTRACTS)} contract(s)…\n")

    results, errors = OptionPricer.price_batch(CONTRACTS)

    successful = []
    for i, (contract, result) in enumerate(zip(CONTRACTS, results), 1):
        print(f"[Contract {i} of {len(CONTRACTS)}]")
        if result is not None:
            result.display()
            successful.append(result)
        else:
            _, exc = next((e for e in errors if e[0] == i - 1), (None, Exception("unknown")))
            print(f"\n  ❌  Error on contract {i}: {exc}\n")

    if len(successful) > 1:
        print_run_summary(successful)

    # Early exercise premium (contracts 2 and 3 — same params, EU vs AM put)
    if len(results) >= 3 and results[1] and results[2]:
        eu, am = results[1].price, results[2].price
        print(f"  📊  Early exercise premium: {am - eu:.6f}")
        print(f"      European put (BS):       {eu:.6f}")
        print(f"      American put (Binomial): {am:.6f}\n")

    # Implied vol demo
    if RUN_IV_DEMO:
        print("─" * 62)
        print("  IMPLIED VOLATILITY SOLVER")
        print("─" * 62)
        try:
            iv = solve_iv(IV_MKT_PRICE, IV_CONTRACT)
            print(f"  Market price  : {IV_MKT_PRICE:.4f}")
            print(f"  Implied vol   : {iv * 100:.4f}%")
            verify = OptionPricer.price(replace(IV_CONTRACT, vol=iv))
            print(f"  Verification  : BS({iv*100:.4f}%) = {verify.price:.6f}")
            print(f"  Residual      : {abs(verify.price - IV_MKT_PRICE):.2e}")
        except ValueError as e:
            print(f"  ❌  {e}")
        print("─" * 62 + "\n")


if __name__ == "__main__":
    main()
