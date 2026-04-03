"""
utils/display.py
────────────────
Display helpers: banner and run summary table.
"""

from option_pricer_classic.models.result import PricingResult


def print_banner():
    print("\n" + "╔" + "═" * 60 + "╗")
    print("║" + "  OPTION VALUATION FRAMEWORK".center(60) + "║")
    print("║" + "  Black-Scholes · Binomial Tree · Monte Carlo".center(60) + "║")
    print("╚" + "═" * 60 + "╝")


def print_run_summary(results: list[PricingResult]):
    """Compact comparison table across a batch of results."""
    if not results:
        return
    print("\n" + "─" * 74)
    print("  RUN SUMMARY")
    print("─" * 74)
    hdr = (f"  {'#':>2}  {'Type':<6}  {'Style':<10}  {'Method':<14}  "
           f"{'Spot':>7}  {'Strike':>7}  {'Value':>10}  {'SE':>10}")
    print(hdr)
    print("  " + "─" * 70)
    for i, r in enumerate(results, 1):
        c  = r.contract
        se = f"±{r.std_error:.4f}" if r.std_error is not None else "—"
        print(f"  {i:>2}  {c.opt_type:<6}  {c.style:<10}  "
              f"{c.method.replace('_',' '):<14}  "
              f"{c.spot:>7.2f}  {c.strike:>7.2f}  "
              f"{r.price:>10.6f}  {se:>10}")
    print("─" * 74 + "\n")
