from open_compute_basis.hashing import hash_obj
from open_compute_basis.pipeline import calculate_bundle, run
from open_compute_basis.settings import load_settings


def test_identical_receipts_byte_identical():
    settings = load_settings()
    first = run(observation_time="2026-09-02T12:00:00Z")
    run_dir = settings.root / "var" / "runs" / "2026-09-02T120000Z"
    a = calculate_bundle(settings, run_dir, observation_time="2026-09-02T12:00:00Z")
    b = calculate_bundle(settings, run_dir, observation_time="2026-09-02T12:00:00Z")
    assert hash_obj(a) == hash_obj(b)
    assert first["print_hash"]
    assert first["series"]["OCB-H100-SXM-OD-GLOBAL"]["status"] in {"OBSERVATION", "NO_PRINT", "CANONICAL"}
