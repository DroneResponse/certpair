import pytest
from pathlib import Path

from certpair import SelectionStrategy, find


def test_find_selects_alice_for_alphabetical_strategy() -> None:
    result = find("tests/tls", SelectionStrategy.ALPHABETICAL)

    assert result is not None
    cert_path, key_path = result
    assert Path(cert_path).name == "alice.crt"
    assert Path(key_path).name == "alice.key"


def test_expand_home_dir() -> None:
    if not Path.cwd().is_relative_to(Path.home()):
        pytest.skip("Current working directory is not relative to home directory, so cannot test ~ expansion.")
        return

    rel_path = str(Path.cwd().relative_to(Path.home()))
    tls_dir = Path(f"~/{rel_path}/tests/tls")

    result = find(tls_dir, SelectionStrategy.ALPHABETICAL)

    assert result is not None
    cert_path, key_path = result
    assert Path(cert_path).name == "alice.crt"
    assert Path(key_path).name == "alice.key"
