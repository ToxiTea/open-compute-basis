from decimal import Decimal

import pytest

from open_compute_basis.flop_basis import (
    basis_pct,
    external_usd_per_eflop,
    flop_per_eflop,
    summarize_sessions,
    usd_per_eflop,
)


def test_flop_formulas():
    assert flop_per_eflop(Decimal("2.5"), Decimal("5e18")) == Decimal("0.500000")
    assert usd_per_eflop(Decimal("2.5"), Decimal("0.10"), Decimal("5e18")) == Decimal("0.050000")
    ext = external_usd_per_eflop(Decimal("3.6"), Decimal("1"))
    assert ext == Decimal("1.000000")
    assert basis_pct(Decimal("1.2"), Decimal("1.0")) == Decimal("20.000000")


def test_no_usd_from_test_tokens_and_challenged_dropped():
    summary = summarize_sessions(
        [
            {
                "session_id": "ok",
                "state": "completed",
                "challenged": False,
                "fee_flop": "2.5",
                "compute_flops": "5e18",
            },
            {
                "session_id": "no",
                "state": "completed",
                "challenged": True,
                "fee_flop": "9",
                "compute_flops": "1e18",
            },
        ],
        usd_per_flop_token=None,
        profile=None,
        simulated=True,
    )
    assert summary["quality_flags"] == ["SIMULATED"]
    assert len(summary["sessions"]) == 1
    assert summary["sessions"][0]["usd_per_eflop"] is None


def test_unset_profile_refuses_conversion():
    with pytest.raises(ValueError):
        external_usd_per_eflop(Decimal("4"), Decimal("0"))
