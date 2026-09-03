from __future__ import annotations

import argparse
import json
import os
import sys
from getpass import getpass
from pathlib import Path

from . import __version__
from .adapters.internet_backyard_manual import write_record
from .digest import build_report
from .flop_basis import summarize_sessions
from .logging_utils import configure_logging, redact
from .participation import BudgetError
from .pipeline import run
from .receipts import read_json
from .settings import load_settings
from .technocore import (
    TechnocoreError,
    confirm_prompt,
    did_of,
    dry_run_post,
    get_json,
    key_from_seed,
    keygen,
    next_nonce,
    post_signed,
    render_digest,
    sign_message,
    sign_note,
    verify_signed_text,
)

log = configure_logging()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ocb", description="Open Compute Basis")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run_p = sub.add_parser("run", help="collect, calculate, verify, write public outputs")
    run_p.add_argument("--fixtures", action="store_true", help="use recorded fixtures (default)")
    run_p.add_argument("--live", action="store_true", help="fetch live licensed sources")
    run_p.add_argument("--fixture-dir", type=Path)
    run_p.add_argument("--observation-time")

    sub.add_parser("collect", help="alias of run without extra flags")
    sub.add_parser("calculate", help="recalculate from the newest run receipts")
    sub.add_parser("verify", help="recompute the newest print from receipts")
    sub.add_parser("publish", help="rewrite public/ from the newest verified bundle")

    report = sub.add_parser("report", help="operator status, activity, and TODOs (email body)")
    report.add_argument("--observation", type=Path, help="latest.json; default public/latest.json")
    report.add_argument("--out", type=Path, help="write markdown here")

    ib = sub.add_parser("internet-backyard", help="append a manual comparison record")
    ib.add_argument("action", choices=["add"])
    ib.add_argument("--file", type=Path, required=True)

    tc = sub.add_parser("technocore", help="Technocore operator commands")
    tc_sub = tc.add_subparsers(dest="tc_cmd", required=True)
    tc_sub.add_parser("doctor")
    ident = tc_sub.add_parser("identity")
    ident_sub = ident.add_subparsers(dest="ident_cmd", required=True)
    create = ident_sub.add_parser("create")
    create.add_argument("--role", choices=["owner", "agent", "recovery"], required=True)
    create.add_argument(
        "--write-dir",
        type=Path,
        help="write role.did and role.seed here; do not print the seed",
    )
    claim = tc_sub.add_parser("claim-room")
    claim.add_argument("--room", required=True)
    claim.add_argument("--owner-seed-stdin", action="store_true")
    allow = tc_sub.add_parser("allow-agent")
    allow.add_argument("--room", required=True)
    allow.add_argument("--agent-did", required=True)
    allow.add_argument("--owner-seed-stdin", action="store_true")
    revoke = tc_sub.add_parser("revoke-agent")
    revoke.add_argument("--room", required=True)
    revoke.add_argument("--agent-did", required=True)
    revoke.add_argument("--owner-seed-stdin", action="store_true")
    verify_r = tc_sub.add_parser("verify-room")
    verify_r.add_argument("--room", required=True)
    rend = tc_sub.add_parser("render")
    rend.add_argument("--observation", type=Path, required=True)
    pub = tc_sub.add_parser("publish")
    pub.add_argument("--room", required=True)
    pub.add_argument("--dry-run", action="store_true")
    pub.add_argument("--approve-once", action="store_true")
    pub.add_argument("--observation", type=Path)
    exp = tc_sub.add_parser("verify-export")
    exp.add_argument("--room", required=True)
    exp.add_argument("--file", type=Path, required=True)

    flop = sub.add_parser("flop", help="FLOP readiness and simulation")
    flop_sub = flop.add_subparsers(dest="flop_cmd", required=True)
    flop_sub.add_parser("doctor")
    plan = flop_sub.add_parser("render-participation-plan")
    plan.add_argument("--corpus", required=True)
    plan.add_argument("--budget", required=True)
    sim = flop_sub.add_parser("simulate")
    sim.add_argument("--fixture", type=Path, required=True)
    once = flop_sub.add_parser("run-once")
    once.add_argument("--official-config", type=Path, required=True)
    once.add_argument("--approve-once", action="store_true")
    rec = flop_sub.add_parser("reconcile")
    rec.add_argument("--receipt-dir", type=Path, required=True)
    ev = flop_sub.add_parser("export-evidence")
    ev.add_argument("--receipt-dir", type=Path, required=True)

    args = parser.parse_args(argv)
    try:
        if args.cmd == "run":
            return _cmd_run(args)
        if args.cmd in {"collect", "calculate", "verify", "publish"}:
            return _cmd_run(argparse.Namespace(fixtures=True, live=False, fixture_dir=None, observation_time=None))
        if args.cmd == "report":
            return _cmd_report(args)
        if args.cmd == "internet-backyard":
            return _cmd_ib(args)
        if args.cmd == "technocore":
            return _cmd_technocore(args)
        if args.cmd == "flop":
            return _cmd_flop(args)
    except (TechnocoreError, BudgetError, RuntimeError, ValueError, FileExistsError) as exc:
        print(redact(str(exc)), file=sys.stderr)
        return 1
    return 2


def _cmd_run(args: argparse.Namespace) -> int:
    bundle = run(
        fixture_dir=args.fixture_dir,
        live=bool(args.live),
        observation_time=args.observation_time,
    )
    print(f"OCB v{__version__} print {bundle['print_hash'][:16]} status ok")
    print(f"wrote public/latest.json ({bundle.get('observation_date')})")
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    settings = load_settings()
    path = args.observation or (settings.root / "public" / "latest.json")
    bundle = read_json(path)
    text = build_report(bundle, settings)
    out = args.out or (settings.root / "STATUS.txt")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    try:
        print(text)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(text.encode("utf-8"))
    return 0


def _cmd_ib(args: argparse.Namespace) -> int:
    settings = load_settings()
    dest_dir = settings.root / settings.sources["internet_backyard_manual"]["records_dir"]
    record = json.loads(args.file.read_text(encoding="utf-8"))
    dest = dest_dir / args.file.name
    write_record(dest, record)
    print(f"appended {dest}")
    return 0


def _read_seed(label: str) -> str:
    if not sys.stdin.isatty():
        seed = sys.stdin.read().strip()
    else:
        seed = getpass(f"{label} (64 hex chars, not echoed): ").strip()
    if len(seed) != 64:
        raise TechnocoreError("expected a 64-character hex seed on stdin or a masked prompt")
    return seed


def _cmd_technocore(args: argparse.Namespace) -> int:
    settings = load_settings()
    tc = settings.raw["technocore"]
    cmd = args.tc_cmd
    if cmd == "doctor":
        print("technocore doctor")
        print(f"base_url={tc['base_url']}")
        print(f"publish={settings.technocore_publish}")
        print(f"production_room={tc['production_room']}")
        print("agent_seed_configured=", bool(os.environ.get(settings.agent_seed_env)))
        print("owner_seed_in_env=false (must stay offline)")
        return 0
    if cmd == "identity" and args.ident_cmd == "create":
        seed, did = keygen()
        print(f"role={args.role}")
        print(f"did={did}")
        if args.write_dir:
            dest = Path(args.write_dir)
            dest.mkdir(parents=True, exist_ok=True)
            did_path = dest / f"{args.role}.did"
            seed_path = dest / f"{args.role}.seed"
            if did_path.exists() or seed_path.exists():
                raise TechnocoreError(f"{args.role} identity already exists in {dest}; refusing to overwrite")
            did_path.write_text(did + "\n", encoding="utf-8")
            seed_path.write_text(seed + "\n", encoding="utf-8")
            try:
                seed_path.chmod(0o600)
            except OSError:
                pass
            print(f"wrote_did={did_path}")
            print(f"wrote_seed={seed_path}")
            print("The seed is only in that file. Put owner/recovery in a password manager.")
            print("Put the agent seed in GitHub Actions as TECHNOCORE_AGENT_SEED later.")
            print("Do not paste any seed into chat, email, or git.")
            return 0
        print("seed=[printed once; store offline or in the deployment secret; never commit]")
        if args.role == "agent":
            print("Store this seed only as TECHNOCORE_AGENT_SEED. Do not paste it into chat.")
        else:
            print("Store this seed offline. Do not put it in GitHub Actions.")
        print(f"seed={seed}")
        return 0
    if cmd in {"claim-room", "allow-agent", "revoke-agent"}:
        if not args.owner_seed_stdin:
            raise TechnocoreError("owner seed must be supplied with --owner-seed-stdin")
        seed = _read_seed("owner seed")
        owner_did = did_of(key_from_seed(seed))
        if cmd == "claim-room":
            nonce = "1"
            value = owner_did
            signed = sign_note(seed, "room-owners", args.room, nonce, value)
            payload = {
                "action": "claim-room",
                "room": args.room,
                "did": owner_did,
                "nonce": nonce,
                "canonical": signed["canonical"],
                "effect": "claim ownership if absent",
            }
            print(json.dumps({k: redact(str(v)) if k != "did" else v for k, v in payload.items()}, indent=2))
            if not confirm_prompt(f"Claim {args.room} as {owner_did} with if_absent=1"):
                return 1
            print("submit this signed note via POST /kv/room-owners/<room> with if_absent=1")
            print(json.dumps({"did": signed["did"], "sig": signed["sig"], "nonce": signed["nonce"], "value": signed["value"]}))
            return 0
        agent = args.agent_did
        nonce = "2"
        value = "" if cmd == "revoke-agent" else agent
        signed = sign_note(seed, "room-allow", args.room, nonce, value or " ")
        print(f"action={cmd} room={args.room} owner={owner_did} agent={agent} nonce={nonce}")
        if not confirm_prompt(f"{cmd} on {args.room}"):
            return 1
        print(json.dumps({"did": signed["did"], "sig": signed["sig"], "nonce": signed["nonce"], "value": signed["value"]}))
        return 0
    if cmd == "verify-room":
        base = tc["base_url"]
        try:
            rooms = get_json(base, "rooms")
            print("rooms endpoint reachable")
            print(redact(str(rooms)[:400]))
        except Exception as exc:
            print(f"rooms read failed (ok for offline): {exc}")
        print(f"preferred production room: {tc['production_room']}")
        return 0
    if cmd == "render":
        bundle = read_json(args.observation)
        print(render_digest(bundle))
        return 0
    if cmd == "publish":
        bundle_path = args.observation or (load_settings().root / "public" / "latest.json")
        bundle = read_json(bundle_path)
        text = render_digest(bundle)
        seed = os.environ.get(settings.agent_seed_env)
        if not seed:
            raise TechnocoreError("TECHNOCORE_AGENT_SEED is not set; dry-run can use a temp identity")
        did = did_of(key_from_seed(seed))
        nonce = next_nonce(settings.root / tc["nonce_state_path"], args.room, did)
        signed = sign_message(seed, args.room, nonce, text)
        preview = dry_run_post(tc["base_url"], args.room, signed)
        print(json.dumps(preview, indent=2))
        if args.dry_run or not settings.technocore_publish:
            print("dry-run: not sent")
            return 0
        if not args.approve_once and not confirm_prompt(f"POST signed digest to {args.room} as {did}"):
            return 1
        response = post_signed(tc["base_url"], args.room, signed)
        print(f"status={response.status_code}")
        print(redact(response.text[:500]))
        return 0 if response.status_code < 300 else 1
    if cmd == "verify-export":
        ok = 0
        bad = 0
        for line in args.file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            if not rec.get("sig"):
                continue
            if verify_signed_text(rec.get("from") or rec.get("did"), rec["sig"], args.room, str(rec["nonce"]), rec["text"]):
                ok += 1
            else:
                bad += 1
        print(f"verified_ok={ok} verified_bad={bad}")
        return 0 if bad == 0 else 1
    return 2


def _cmd_flop(args: argparse.Namespace) -> int:
    settings = load_settings()
    if args.flop_cmd == "doctor":
        print("flop doctor")
        print(f"FLOP_PARTICIPATION={settings.flop_participation}")
        print(f"status={settings.raw['flop']['status']}")
        print("official_config_present=false")
        print("wallet_configured=false")
        return 0
    if args.flop_cmd == "render-participation-plan":
        print(
            json.dumps(
                {
                    "corpus": args.corpus,
                    "budget_test_flop": args.budget,
                    "caps": settings.raw["flop"],
                    "live": False,
                },
                indent=2,
            )
        )
        return 0
    if args.flop_cmd == "simulate":
        fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
        summary = summarize_sessions(
            fixture.get("sessions") or [],
            usd_per_flop_token=None,
            profile=None,
            simulated=True,
        )
        print(json.dumps(summary, indent=2, default=str))
        return 0
    if args.flop_cmd == "run-once":
        print("blocked: FLOP_PARTICIPATION remains false until official software is pinned")
        cfg = json.loads(args.official_config.read_text(encoding="utf-8"))
        print(f"would use official endpoint={cfg.get('endpoint')} identity={cfg.get('did')}")
        return 2
    if args.flop_cmd in {"reconcile", "export-evidence"}:
        files = sorted(args.receipt_dir.glob("*.json"))
        print(f"{args.flop_cmd} receipts={len(files)} (read-only)")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
