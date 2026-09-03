import json
from pathlib import Path

from open_compute_basis.cli import main
from open_compute_basis.technocore import keygen

ROOT = Path(__file__).resolve().parents[1]


def test_fixture_run_and_technocore_dry_run(capsys, monkeypatch):
    assert main(["run", "--observation-time", "2026-09-02T12:00:00Z"]) == 0
    latest = json.loads((ROOT / "public" / "latest.json").read_text(encoding="utf-8"))
    assert latest["methodology_version"] == "0.1.0"
    assert latest["flop"]["FLOP_STATUS"] == "AWAITING_OFFICIAL_SESSION_API"
    seed, _ = keygen()
    monkeypatch.setenv("TECHNOCORE_AGENT_SEED", seed)
    monkeypatch.setenv("TECHNOCORE_PUBLISH", "false")
    assert main(["technocore", "publish", "--room", "d-open-compute-basis", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert seed not in out
    assert "dry-run" in out
    assert "did:key:" in out
    assert main(["flop", "doctor"]) == 0
    assert main(["technocore", "doctor"]) == 0
