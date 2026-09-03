import io
import logging

from open_compute_basis.logging_utils import RedactingFormatter, assert_no_secrets, redact
from open_compute_basis.technocore import did_of, dry_run_post, key_from_seed, keygen, sign_message


def test_write_dir_does_not_print_seed(tmp_path, capsys):
    from open_compute_basis.cli import main

    dest = tmp_path / "ids"
    assert main(["technocore", "identity", "create", "--role", "owner", "--write-dir", str(dest)]) == 0
    out = capsys.readouterr().out
    seed = (dest / "owner.seed").read_text(encoding="utf-8").strip()
    assert seed
    assert seed not in out
    assert (dest / "owner.did").read_text(encoding="utf-8").startswith("did:key:")
    assert main(["technocore", "identity", "create", "--role", "owner", "--write-dir", str(dest)]) == 1


def test_logs_never_contain_seed():
    seed, did = keygen()
    signed = sign_message(seed, "d-open-compute-basis", "1", "hello world")
    preview = dry_run_post("https://technocore.chat", "d-open-compute-basis", signed)
    blob = redact(str(preview) + did)
    assert seed not in blob
    assert preview["seed"] == "[REDACTED]"
    assert preview["sent"] is False
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(RedactingFormatter("%(message)s"))
    logger = logging.getLogger("ocb-secret-test")
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    logger.info("seed was %s", seed)
    assert seed not in stream.getvalue()
    assert "[REDACTED_SEED]" in stream.getvalue()
    assert_no_secrets(stream.getvalue(), [seed])
    assert did_of(key_from_seed(seed)) == did
