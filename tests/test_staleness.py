from open_compute_basis.confidence import is_stale


def test_stale_and_fresh():
    assert is_stale("2026-09-02", "2026-09-02T12:00:00Z", 36) is False
    assert is_stale("2026-08-01", "2026-09-02T12:00:00Z", 36) is True
    assert is_stale(None, "2026-09-02T12:00:00Z", 36) is True
    assert is_stale("not-a-date", "2026-09-02T12:00:00Z", 36) is True
