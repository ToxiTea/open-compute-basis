from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from .inference_eval import CORPUS_VERSION

OWNER_ROLES = {"owner", "recovery", "staging", "replacement"}
PARTICIPANT_ROLE = "agent"


@dataclass
class Budget:
    per_session_cap: Decimal
    daily_cap: Decimal
    max_jobs: int
    max_retries: int
    allowlisted: set[str]
    emergency_stop: bool
    spent_today: Decimal = Decimal("0")
    jobs_today: int = 0
    retries_used: int = 0
    seen_job_hashes: set[str] = field(default_factory=set)


class BudgetError(RuntimeError):
    pass


def assert_participant(role: str) -> None:
    if role in OWNER_ROLES:
        raise BudgetError(f"{role} DID cannot enter a faucet or session request")
    if role != PARTICIPANT_ROLE:
        raise BudgetError(f"unknown role {role}")


def authorize_job(budget: Budget, job: dict[str, Any], role: str) -> None:
    assert_participant(role)
    if budget.emergency_stop:
        raise BudgetError("emergency stop")
    if job.get("corpus_version") not in budget.allowlisted:
        raise BudgetError("corpus not allow-listed")
    if not job.get("purpose"):
        raise BudgetError("job has no named research purpose")
    prompt = str(job.get("prompt") or "")
    if not prompt.strip():
        raise BudgetError("empty prompt rejected")
    job_hash = str(job.get("input_hash") or "")
    if not job_hash:
        raise BudgetError("missing input hash")
    if job_hash in budget.seen_job_hashes:
        raise BudgetError("duplicate job rejected")
    fee = Decimal(str(job.get("fee_flop") or 0))
    if fee <= 0:
        raise BudgetError("fee must be positive")
    if fee > budget.per_session_cap:
        raise BudgetError("per-session cap exceeded")
    if budget.spent_today + fee > budget.daily_cap:
        raise BudgetError("daily cap exceeded")
    if budget.jobs_today >= budget.max_jobs:
        raise BudgetError("max jobs exceeded")
    if int(job.get("retry_count") or 0) > budget.max_retries:
        raise BudgetError("retry cap exceeded")


def consume(budget: Budget, job: dict[str, Any]) -> None:
    authorize_job(budget, job, role=job.get("role") or PARTICIPANT_ROLE)
    budget.spent_today += Decimal(str(job["fee_flop"]))
    budget.jobs_today += 1
    budget.seen_job_hashes.add(str(job["input_hash"]))
    budget.retries_used += int(job.get("retry_count") or 0)


def render_participation(receipts: list[dict[str, Any]], *, simulated: bool) -> dict[str, Any]:
    useful = [
        r
        for r in receipts
        if r.get("final_state") == "completed"
        and r.get("validation_passed")
        and not r.get("challenged")
    ]
    return {
        "corpus_version": CORPUS_VERSION,
        "simulated": simulated,
        "completed_useful_sessions": len(useful),
        "validation_pass_rate": (len(useful) / len(receipts)) if receipts else 0,
        "total_test_flop_spend": str(sum(Decimal(str(r.get("fee_flop") or 0)) for r in useful)),
        "quality_flags": ["SIMULATED"] if simulated else [],
        "note": "Simulated activity does not earn tokens and is not a live faucet claim.",
    }


def budget_from_settings(flop_cfg: dict[str, Any]) -> Budget:
    return Budget(
        per_session_cap=Decimal(str(flop_cfg["per_session_cap_test_flop"])),
        daily_cap=Decimal(str(flop_cfg["daily_cap_test_flop"])),
        max_jobs=int(flop_cfg["max_jobs_per_day"]),
        max_retries=int(flop_cfg["max_retries"]),
        allowlisted=set(flop_cfg["allowlisted_corpus_versions"]),
        emergency_stop=bool(flop_cfg.get("emergency_stop")),
    )
