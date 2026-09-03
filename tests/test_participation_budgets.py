from decimal import Decimal

import pytest

from open_compute_basis.inference_eval import CORPUS_VERSION
from open_compute_basis.participation import Budget, BudgetError, authorize_job, consume


def _budget(**kwargs) -> Budget:
    base = dict(
        per_session_cap=Decimal("10"),
        daily_cap=Decimal("12"),
        max_jobs=2,
        max_retries=1,
        allowlisted={CORPUS_VERSION},
        emergency_stop=False,
    )
    base.update(kwargs)
    return Budget(**base)


def _job(**kwargs) -> dict:
    job = {
        "role": "agent",
        "corpus_version": CORPUS_VERSION,
        "purpose": "price extraction eval",
        "prompt": "extract fields",
        "input_hash": "aaa",
        "fee_flop": "5",
        "retry_count": 0,
    }
    job.update(kwargs)
    return job


def test_caps_fail_closed():
    budget = _budget()
    with pytest.raises(BudgetError, match="per-session"):
        authorize_job(budget, _job(fee_flop="11"), "agent")
    consume(budget, _job())
    with pytest.raises(BudgetError, match="daily"):
        authorize_job(budget, _job(input_hash="bbb", fee_flop="8"), "agent")
    budget2 = _budget(daily_cap=Decimal("50"))
    consume(budget2, _job())
    consume(budget2, _job(input_hash="bbb"))
    with pytest.raises(BudgetError, match="max jobs"):
        authorize_job(budget2, _job(input_hash="ccc"), "agent")
    with pytest.raises(BudgetError, match="retry"):
        authorize_job(_budget(), _job(retry_count=2), "agent")
    with pytest.raises(BudgetError, match="corpus"):
        authorize_job(_budget(), _job(corpus_version="nope"), "agent")


def test_owner_recovery_cannot_participate_and_dupes_rejected():
    budget = _budget()
    for role in ("owner", "recovery", "staging", "replacement"):
        with pytest.raises(BudgetError, match="cannot enter"):
            authorize_job(budget, _job(), role)
    with pytest.raises(BudgetError, match="empty prompt"):
        authorize_job(budget, _job(prompt="   "), "agent")
    consume(budget, _job())
    with pytest.raises(BudgetError, match="duplicate"):
        authorize_job(budget, _job(), "agent")
