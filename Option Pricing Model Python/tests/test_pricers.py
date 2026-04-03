"""
tests/test_pricers.py
─────────────────────
Unit tests — no pytest required. Run: python tests/test_pricers.py
"""

import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from option_pricer_classic          import OptionContract, OptionPricer
from option_pricer_classic.utils    import solve_iv
from dataclasses                    import replace

BASE = dict(spot=100.0, strike=100.0, maturity=1.0, vol=0.20, rate=0.05, dividend=0.0)

def make(method="black_scholes", opt_type="call", style="european", **kw):
    return OptionContract(**{**BASE, "method": method, "opt_type": opt_type, "style": style, **kw})

def bs(opt_type="call", **kw):
    return OptionPricer.price(make("black_scholes", opt_type, **kw)).price

def close(a, b, tol, label=""):
    if abs(a - b) > tol:
        raise AssertionError(f"{label}: |{a:.6f} - {b:.6f}| = {abs(a-b):.6f} > {tol}")

def raises(exc, fn, label=""):
    try:
        fn()
        raise AssertionError(f"{label}: expected {exc.__name__}, got no error")
    except exc:
        pass


TESTS = []

def test(name):
    def decorator(fn):
        TESTS.append((name, fn))
        return fn
    return decorator


@test("BS ATM call ≈ 10.4506")
def _():
    close(bs("call"), 10.4506, 1e-3, "ATM call")

@test("BS ATM put ≈ 5.5735")
def _():
    close(bs("put"), 5.5735, 1e-3, "ATM put")

@test("Put-call parity (BS)")
def _():
    c, p = bs("call"), bs("put")
    pcp = 100 - 100 * math.exp(-0.05)
    close(c - p, pcp, 1e-8, "PCP")

@test("Call delta ∈ (0,1)")
def _():
    d = OptionPricer.price(make()).greeks.delta
    assert 0 < d < 1, f"delta={d}"

@test("Put delta ∈ (-1,0)")
def _():
    d = OptionPricer.price(make(opt_type="put")).greeks.delta
    assert -1 < d < 0, f"delta={d}"

@test("Gamma always positive")
def _():
    for t in ("call", "put"):
        g = OptionPricer.price(make(opt_type=t)).greeks.gamma
        assert g > 0, f"{t} gamma={g}"

@test("Vega always positive")
def _():
    for t in ("call", "put"):
        v = OptionPricer.price(make(opt_type=t)).greeks.vega
        assert v > 0, f"{t} vega={v}"

@test("Call rho positive, put rho negative")
def _():
    assert OptionPricer.price(make()).greeks.rho > 0
    assert OptionPricer.price(make(opt_type="put")).greeks.rho < 0

@test("Deep OTM price ≥ 0")
def _():
    for K in [150, 200, 300]:
        p = bs("call", strike=K, maturity=0.01)
        assert p >= 0, f"K={K}: price={p}"

@test("Near-zero maturity ≥ 0")
def _():
    for T in [1/365, 1e-4, 1e-6]:
        p = bs("call", maturity=T)
        assert p >= 0, f"T={T}: price={p}"

@test("Binomial converges to BS (N=1000)")
def _():
    eu = OptionPricer.price(make("binomial", steps=1000)).price
    reference = bs("call")
    close(eu, reference, 0.01, "Binom→BS")

@test("American put ≥ European put")
def _():
    eu = OptionPricer.price(make("binomial", opt_type="put", style="european", steps=500)).price
    am = OptionPricer.price(make("binomial", opt_type="put", style="american", steps=500)).price
    assert am >= eu - 1e-9, f"am={am:.6f} < eu={eu:.6f}"

@test("American call = European call (no dividend)")
def _():
    eu = OptionPricer.price(make("binomial", style="european", steps=500)).price
    am = OptionPricer.price(make("binomial", style="american", steps=500)).price
    close(am, eu, 0.01, "Am call = Eu call")

@test("Binomial all outputs ≥ 0")
def _():
    for K in [70, 85, 100, 115, 130]:
        for sty in ("european", "american"):
            for ty in ("call", "put"):
                p = OptionPricer.price(make("binomial", ty, sty, strike=K, steps=100)).price
                assert p >= 0, f"{ty} {sty} K={K}: {p}"

@test("MC converges to BS (500k, within 3 SE)")
def _():
    res = OptionPricer.price(make("monte_carlo", simulations=500_000))
    ref = bs("call")
    assert abs(res.price - ref) < 3 * res.std_error, (
        f"MC={res.price:.4f}, BS={ref:.4f}, 3SE={3*res.std_error:.4f}"
    )
    assert res.price >= 0

@test("Validation: bad spot raises")
def _():
    raises(ValueError, lambda: make(spot=-1))
    raises(ValueError, lambda: make(spot=0))

@test("Validation: bad vol raises")
def _():
    raises(ValueError, lambda: make(vol=0))
    raises(ValueError, lambda: make(vol=-0.1))

@test("Validation: bad maturity raises")
def _():
    raises(ValueError, lambda: make(maturity=0))
    raises(ValueError, lambda: make(maturity=-1))

@test("Validation: bad opt_type raises")
def _():
    raises(ValueError, lambda: make(opt_type="straddle"))

@test("Validation: BS + American raises")
def _():
    raises(ValueError, lambda: make("black_scholes", "put", "american"))

@test("Validation: MC + American raises")
def _():
    raises(ValueError, lambda: make("monte_carlo", "put", "american"))

@test("IV round-trip: recover true vol")
def _():
    true_vol = 0.23
    c = make(vol=true_vol)
    mkt = OptionPricer.price(c).price
    iv  = solve_iv(mkt, c)
    close(iv, true_vol, 1e-6, "IV round-trip")

@test("IV: out-of-bounds market price raises")
def _():
    raises(ValueError, lambda: solve_iv(9999.0, make()))


if __name__ == "__main__":
    print("\n" + "=" * 62)
    print("  OPTION PRICER CLASSIC — TEST SUITE")
    print("=" * 62)

    passed = failed = 0
    for name, fn in TESTS:
        print(f"\n▶ {name}")
        try:
            fn()
            print("  ✓ passed")
            passed += 1
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            failed += 1

    print("\n" + "=" * 62)
    print(f"  {passed} passed · {failed} failed · {len(TESTS)} total")
    print("=" * 62 + "\n")
    sys.exit(0 if failed == 0 else 1)
