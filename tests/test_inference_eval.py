import json
from pathlib import Path

import pytest

from open_compute_basis.inference_eval import CORPUS_VERSION, prompt_hash, run_fixture, score, validate_extraction

ROOT = Path(__file__).resolve().parents[1]


def test_strict_schema_and_deterministic_score():
    gold = {
        "gpu_sku": "H100 SXM",
        "region": "us-east",
        "service_class": "managed cloud",
        "commitment": "none",
        "availability": "in stock",
        "usd_per_gpu_hour": 4.41,
    }
    first = score(gold, gold)
    second = score(gold, gold)
    assert first == second
    assert first["passed"] is True
    assert first["corpus_version"] == CORPUS_VERSION
    assert first["prompt_hash"] == prompt_hash()
    with pytest.raises(ValueError):
        validate_extraction({**gold, "extra": 1})
    with pytest.raises(ValueError):
        validate_extraction({k: gold[k] for k in gold if k != "region"})


def test_fixture_job_does_not_touch_canonical_print():
    job = json.loads((ROOT / "tests/fixtures/inference/job.json").read_text(encoding="utf-8"))
    result = run_fixture(job["document"], job["predicted"], job["gold"])
    assert result["passed"] is True
    assert result["canonical_print_touched"] is False
    assert result["quarantined"] is False
