from pathlib import Path

from certpair import SelectionStrategy, find


def test_find_selects_alice_for_alphabetical_strategy() -> None:
    result = find("tests/tls", SelectionStrategy.ALPHABETICAL)

    assert result is not None
    cert_path, key_path = result
    assert Path(cert_path).name == "alice.crt"
    assert Path(key_path).name == "alice.key"