import json
from pathlib import Path

from open_compute_basis.adapters.internet_backyard_manual import validate_record
from open_compute_basis.settings import load_settings

ROOT = Path(__file__).resolve().parents[1]


def test_seeded_ib_record_preserves_count_mismatch():
    path = ROOT / "manual_checks/internet_backyard/2026-09-01-rtx4090.json"
    record = validate_record(json.loads(path.read_text(encoding="utf-8")))
    assert record["headline"]["usd_per_gpu_hour"] == 0.79
    assert record["headline"]["listing_count"] == 68
    assert record["provider_displayed_count_total"] == 79
    assert "COUNT_MISMATCH" in record["quality_flags"]
    assert record["captured_at"] is None
    assert record["constituent_of_ocb"] is False


def test_ib_is_loaded_as_comparison_not_constituent():
    from open_compute_basis.pipeline import run

    bundle = run(observation_time="2026-09-02T12:00:00Z")
    recs = bundle["comparisons"]["internet_backyard"]
    assert recs
    assert recs[0]["gpu"] == "RTX4090"
    garage = bundle["series"]["OCB-RTX4090-COMMUNITY-GLOBAL"]
    assert garage["status"] == "NO_PRINT"
    settings = load_settings()
    assert settings.sources["internet_backyard_manual"]["role"] == "comparison"
