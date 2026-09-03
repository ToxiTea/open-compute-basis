from open_compute_basis.digest import build_report
from open_compute_basis.pipeline import run
from open_compute_basis.settings import load_settings


def test_report_lists_open_pages_todo_and_no_secrets():
    bundle = run(observation_time="2026-09-02T12:00:00Z")
    text = build_report(bundle, load_settings())
    assert "OCB STATUS" in text
    assert "Enable GitHub Pages" in text
    assert "[ ]" in text
    assert "STAY PARKED" in text
    assert "TECHNOCORE_AGENT_SEED" not in text
    assert "did:key:" not in text
