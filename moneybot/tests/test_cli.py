import pytest

from moneybot import cli, db


@pytest.fixture(autouse=True)
def _env(tmp_path, monkeypatch):
    monkeypatch.setenv("MONEYBOT_DB", str(tmp_path / "cli.db"))
    monkeypatch.setenv("MONEYBOT_MEDIA_DIR", str(tmp_path / "media"))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("MONEYBOT_ALLOWED_SENDERS", "")


def test_send_prints_the_reply(capsys):
    assert cli.main(["send", "got", "10000", "from", "the", "collective"]) == 0
    assert "$3,700 to tax" in capsys.readouterr().out


def test_the_cli_speaks_as_the_owner(tmp_path, capsys):
    """A ledger owned by a phone number is still reachable from the terminal."""
    path = str(tmp_path / "cli.db")
    conn = db.connect(path)
    db.init(conn)
    db.set_setting(conn, "owner", "+15550001111")
    conn.close()
    assert cli.main(["send", "?"]) == 0
    out = capsys.readouterr().out
    assert "Spendable" in out
    assert "not them" not in out


def test_nag_dry_run_sends_nothing(capsys):
    cli.main(["send", "got", "10000", "from", "the", "collective", "--date", "2026-07-05"])
    assert cli.main(["nag", "--date", "2026-08-25", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "2026-Q3" in out
    assert "1 nag(s) due" in out


def test_nag_refuses_to_run_without_an_owner(tmp_path, capsys):
    assert cli.main(["nag", "--date", "2026-08-25"]) == 1
    assert "has to text the bot once" in capsys.readouterr().err


def test_export_writes_the_bundle(tmp_path, capsys):
    cli.main(["send", "got", "10000", "from", "the", "collective", "--date", "2026-03-01"])
    out_dir = tmp_path / "csv"
    assert cli.main(["export", "--year", "2026", "--out", str(out_dir)]) == 0
    assert "$10,000 income" in capsys.readouterr().out
    assert sorted(p.name for p in out_dir.iterdir()) == [
        "expenses-2026.csv", "payments-2026.csv", "summary-2026.csv"
    ]


def test_send_can_pretend_it_is_another_day(capsys):
    cli.main(["send", "got", "10000", "from", "the", "collective", "--date", "2026-02-10"])
    capsys.readouterr()
    cli.main(["send", "month", "--date", "2026-02-10"])
    assert "February" in capsys.readouterr().out
