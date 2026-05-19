import pytest
from pathlib import Path

from certpair import SelectionStrategy, find, resolve


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


def test_resolve_uses_config_dict_when_env_is_unset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PUBLIC_CERT", raising=False)
    monkeypatch.delenv("PRIVATE_KEY", raising=False)
    monkeypatch.delenv("TLS_PATH", raising=False)

    cert_file = tmp_path / "client.crt"
    key_file = tmp_path / "client.key"
    cert_file.write_text("cert")
    key_file.write_text("key")

    result = resolve({
        "public_cert": str(cert_file),
        "private_key": str(key_file),
    })

    assert result == (str(cert_file), str(key_file))


def test_resolve_prefers_env_over_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_cert = tmp_path / "config.crt"
    config_key = tmp_path / "config.key"
    env_cert = tmp_path / "env.crt"
    env_key = tmp_path / "env.key"

    config_cert.write_text("config cert")
    config_key.write_text("config key")
    env_cert.write_text("env cert")
    env_key.write_text("env key")

    monkeypatch.setenv("PUBLIC_CERT", str(env_cert))
    monkeypatch.setenv("PRIVATE_KEY", str(env_key))
    monkeypatch.delenv("TLS_PATH", raising=False)

    result = resolve({
        "public_cert": str(config_cert),
        "private_key": str(config_key),
    })

    assert result == (str(env_cert), str(env_key))


def test_resolve_prefers_env_tls_path_over_config_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_cert = tmp_path / "config.crt"
    config_key = tmp_path / "config.key"
    config_cert.write_text("config cert")
    config_key.write_text("config key")

    env_dir = tmp_path / "env_tls"
    env_dir.mkdir()
    env_cert = env_dir / "env.crt"
    env_key = env_dir / "env.key"
    env_cert.write_text("env cert")
    env_key.write_text("env key")

    monkeypatch.delenv("PUBLIC_CERT", raising=False)
    monkeypatch.delenv("PRIVATE_KEY", raising=False)
    monkeypatch.setenv("TLS_PATH", str(env_dir))

    result = resolve({
        "public_cert": str(config_cert),
        "private_key": str(config_key),
        "tls_path": str(tmp_path / "config_tls"),
    })

    assert result == (str(env_cert), str(env_key))


def test_resolve_uses_env_public_cert_and_config_private_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_cert = tmp_path / "config.crt"
    config_key = tmp_path / "config.key"
    env_cert = tmp_path / "env.crt"

    config_cert.write_text("config cert")
    config_key.write_text("config key")
    env_cert.write_text("env cert")

    monkeypatch.setenv("PUBLIC_CERT", str(env_cert))
    monkeypatch.delenv("PRIVATE_KEY", raising=False)
    monkeypatch.delenv("TLS_PATH", raising=False)

    result = resolve({
        "public_cert": str(config_cert),
        "private_key": str(config_key),
    })

    assert result == (str(env_cert), str(config_key))


def test_resolve_uses_config_public_cert_and_config_private_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_cert = tmp_path / "config1.crt"
    config_key = tmp_path / "config2.key"
    extra_cert = tmp_path / "extra.crt"
    extra_key = tmp_path / "extra.key"


    config_cert.write_text("config cert")
    config_key.write_text("config key")
    extra_cert.write_text("extra cert")
    extra_key.write_text("extra key")

    monkeypatch.delenv("PUBLIC_CERT", raising=False)
    monkeypatch.delenv("PRIVATE_KEY", raising=False)
    monkeypatch.delenv("TLS_PATH", raising=False)

    result = resolve({
        "public_cert": str(config_cert),
        "private_key": str(config_key),
        "tls_path": str(tmp_path),
    })

    assert result == (str(config_cert), str(config_key)) 


def test_resolve_from_only_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_cert = tmp_path / "a.crt"
    config_key = tmp_path / "b.key"
    extra_cert = tmp_path / "extra.crt"
    extra_key = tmp_path / "extra.key"


    config_cert.write_text("config cert")
    config_key.write_text("config key")
    extra_cert.write_text("extra cert")
    extra_key.write_text("extra key")

    monkeypatch.delenv("PUBLIC_CERT", raising=False)
    monkeypatch.delenv("PRIVATE_KEY", raising=False)
    monkeypatch.delenv("TLS_PATH", raising=False)

    result = resolve({
        "public_cert2": str(config_cert),
        "private_key": str(config_key),
        "tls_path": str(tmp_path),
    })

    assert result == (str(extra_cert), str(extra_key))


def test_resolve_from_only_config2(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_cert = tmp_path / "a.crt"
    config_key = tmp_path / "b.key"
    extra_cert = tmp_path / "extra.crt"
    extra_key = tmp_path / "extra.key"


    config_cert.write_text("config cert")
    config_key.write_text("config key")
    extra_cert.write_text("extra cert")
    extra_key.write_text("extra key")

    monkeypatch.delenv("PUBLIC_CERT", raising=False)
    monkeypatch.delenv("PRIVATE_KEY", raising=False)
    monkeypatch.delenv("TLS_PATH", raising=False)

    result = resolve({
        "public_cert": str(config_cert),
        "private_key2": str(config_key),
        "tls_path": str(tmp_path),
    })

    assert result == (str(extra_cert), str(extra_key))


def test_resolve_from_only_config2(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_cert = tmp_path / "a.crt"
    config_key = tmp_path / "b.key"
    extra_cert = tmp_path / "extra.crt"
    extra_key = tmp_path / "extra.key"


    config_cert.write_text("config cert")
    config_key.write_text("config key")
    extra_cert.write_text("extra cert")
    extra_key.write_text("extra key")

    monkeypatch.delenv("PUBLIC_CERT", raising=False)
    monkeypatch.delenv("PRIVATE_KEY", raising=False)
    monkeypatch.delenv("TLS_PATH", raising=False)

    result = resolve({
        "tls_path": str(tmp_path),
    })

    assert result == (str(extra_cert), str(extra_key))


def test_resolve_raises_value_error_for_invalid_config_tls_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Provide an env tls path that doesn't have a matching cert/key pair, but has non-matching certs and keys.

    provide a config tls path that has a matching cert/key pair.

    Make sure that we raise a ValueError for the env tls path, and that we don't use the config tls path's cert/key pair.

    We're trying to help the user in case they attempted to specify the tls path using the env var, but something is wrong.
    
    We want to make sure they get an error instead of silently falling back to a different tls path that has valid certs and keys.
    """
    config_cert = tmp_path / "a.crt"
    config_key = tmp_path / "b.key"
    env_dir = tmp_path / "env_tls"
    env_dir.mkdir()
    env_dir_cert = env_dir / "env1.crt"
    env_dir_key = env_dir / "env2.key"

    config_dir = tmp_path / "config_tls"
    config_dir.mkdir()
    config_dir_cert = config_dir / "config_dir.crt"
    config_dir_key = config_dir / "config_dir.key"



    config_cert.write_text("config cert")
    config_key.write_text("config key")
    env_dir_cert.write_text("env cert")
    env_dir_key.write_text("env key")
    config_dir_cert.write_text("config dir cert")
    config_dir_key.write_text("config dir key")

    monkeypatch.delenv("PUBLIC_CERT", raising=False)
    monkeypatch.delenv("PRIVATE_KEY", raising=False)
    monkeypatch.setenv("TLS_PATH", str(env_dir))

    monkeypatch.delenv("TLS_PATH", raising=False)

    with pytest.raises(ValueError, match="Invalid config"):
        resolve({
            "tls_path": str(tmp_path),
        })

def test_resolve_raises_value_error_for_invalid_config_tls_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    provide an env cert path that doesn't lead to a real file
    provide a config cert path that works
    provide a config key path that works
    provide a config tls path that has a matching cert/key pair.

    Make sure that we raise a ValueError. The user provided both a cert path and a key path, but one is invalid.
    We should raise an error instead of silently falling back to the config tls path's cert/key pair.
    """
    env_cert = tmp_path / "env.crt"
    config_cert = tmp_path / "a.crt"
    config_key = tmp_path / "b.key"

    config_dir = tmp_path / "config_tls"
    config_dir.mkdir()
    config_dir_cert = config_dir / "config_dir.crt"
    config_dir_key = config_dir / "config_dir.key"



    # env_cert.write_text("env cert")
    config_cert.write_text("config cert")
    config_key.write_text("config key")
    config_dir_cert.write_text("config dir cert")
    config_dir_key.write_text("config dir key")

    monkeypatch.setenv("PUBLIC_CERT", str(env_cert))
    monkeypatch.delenv("PRIVATE_KEY", raising=False)
    monkeypatch.delenv("TLS_PATH", raising=False)


    with pytest.raises(ValueError, match="Invalid config"):
        resolve({
            "public_cert": str(config_cert),
            "private_key": str(config_key),
            "tls_path": str(tmp_path),
        })


def test_resolve_to_working_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    do not provide env vars
    do not provide config

    put a cert and key in the current working directory
    """
    cert_file = tmp_path / "working.crt"
    key_file = tmp_path / "working.key"
    cert_file.write_text("working cert")
    key_file.write_text("working key")

    monkeypatch.delenv("PUBLIC_CERT", raising=False)
    monkeypatch.delenv("PRIVATE_KEY", raising=False)
    monkeypatch.delenv("TLS_PATH", raising=False)
    monkeypatch.chdir(tmp_path)

    result = resolve()

    assert result == (str(cert_file), str(key_file))
