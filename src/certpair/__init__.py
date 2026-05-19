import os

from collections import ChainMap
from enum import Enum
from pathlib import Path
from typing import Union
from unittest import result


class SelectionStrategy(Enum):
    ALPHABETICAL = "alphabetical"
    NEWEST = "newest"


# Canonical config dictionary keys used by this library when reading
# certificate settings, regardless of whether the config came from a file,
# config dict, or another source.
#
# For example, when reading a ``config.json`` file, the library will look for
# these keys in the JSON data.
PUBLIC_CERT_KEY = 'public_cert'
PRIVATE_KEY_KEY = 'private_key'
TLS_PATH_KEY = 'tls_path'


def resolve(config: dict | None = None) -> tuple[str, str] | None:
    """Resolve the certificate and private key pair for an application.

    The returned tuple is in the form ``(cert_file, key_file)`` so it can be
    passed directly to libraries such as ``requests`` that expect a client
    certificate pair.

    This is the main entry point for downstream programs that have already
    loaded their application config into a dictionary.

    This function finds the certificate and private key pair by checking
    multiple sources. Here is the order of precedence for finding the
    certificate/key pair:
    
    1. Environment variables.
    2. The supplied config dictionary.
    3. If no valid pair is found, return ``None``.

    
    For each source, Built-in discovery within the selected config source:
       ``public_cert`` and ``private_key`` are preferred over ``tls_path``.

    Args:
        config (dict | None): Application config values using this library's
            canonical config keys. Pass ``None`` to resolve from environment
            variables only.

    Returns:
        tuple[str, str] | None: The matching certificate and key paths, or
        ``None`` if no matching pair is found. The returned tuple is in the form
        ``(cert_file, key_file)`` so it can be passed directly to the``requests``
        library.
    """
    if config is None:
        config = {}

    env_conf = _env_config()
    if env_conf:
        result = _from_dict(env_conf)
        if result:
            return result
        # if we were given a "complete config" via the environment variables but we didn't find a valid cert/key pair, then we should fail fast instead of falling back to the config dict...
        # This is because if the environment variables are set then that's a strong signal that the user intended to use them, and if we silently ignore them and fall back to other sources then that could lead to confusion and make it harder for users to debug issues with their environment variable configuration.
        # to determine if a dict is "complete" we check if it has both the PUBLIC_CERT_KEY and PRIVATE_KEY_KEY keys, or if it has the TLS_PATH_KEY key. If it has either of those then we consider it complete enough that if we don't find a valid cert/key pair then we should raise an error instead of falling back to the config dict.
        if PUBLIC_CERT_KEY in env_conf and PRIVATE_KEY_KEY in env_conf:
            raise ValueError(f"Invalid environment variables: {env_conf[PUBLIC_CERT_KEY]}, {env_conf[PRIVATE_KEY_KEY]}. Do these files exist?")
        if TLS_PATH_KEY in env_conf:
            raise ValueError(f"Invalid environment variables: {env_conf[TLS_PATH_KEY]}, does this directory exist and does it contain a cert/key pair?")

    # if we made it this far then either there were no relevant environment variables set, or the environment variables that were set didn't lead to a complete config so now we'll combine the environment config with the supplied config dict and try to resolve a cert/key pair from that.
    #  The environment variables take priority over the supplied config dict.
    overall_config = ChainMap(env_conf, config)
    result = _from_dict(overall_config)
    if result:
        return result
    # if we have a complete overall config but we didn't find a valid cert/key pair, then we should fail fast instead of returning None, because the user provided a complete config.
    # The user might have made a mistake in their config, and falling back to another source or returning None would make it harder for them to debug the issue with their config.
    if (PUBLIC_CERT_KEY in overall_config and PRIVATE_KEY_KEY in overall_config):
        raise ValueError(f"Invalid config: {overall_config[PUBLIC_CERT_KEY]}, {overall_config[PRIVATE_KEY_KEY]}. Do these files exist?")
    if TLS_PATH_KEY in overall_config:
        raise ValueError(f"Invalid config: {overall_config[TLS_PATH_KEY]}, does this directory exist and does it contain a cert/key pair?")

    # final fallback: try to find a cert/key pair in the current working directory. This allows users to just drop cert/key files into the working directory without having to set any config or environment variables, and the library will pick them up automatically.
    return find()


def _env_config() -> dict:
    """Return a configuration dictionary from environment variables.

    Environment variables:
        PUBLIC_CERT: Path to the public certificate file.
        PRIVATE_KEY: Path to the private key file.
        TLS_PATH: A directory to search for matching certificate/key pairs.

    Returns:
        dict: A configuration dictionary containing the keys 'public_cert',
        'private_key', and 'tls_path' with paths to the certificate and private
        key files, or ``None`` if no valid configuration is found.
    """

    config = {
        PUBLIC_CERT_KEY: os.getenv('PUBLIC_CERT'),
        PRIVATE_KEY_KEY: os.getenv('PRIVATE_KEY'),
        TLS_PATH_KEY: os.getenv('TLS_PATH'),
    }
    # Remove keys with None values to clean up the config dictionary.
    # This enables us to use this dict with a ChainMap.
    config = {k: v for k, v in config.items() if v is not None}
    return config


def _from_dict(config: dict) -> tuple[str, str] | None:
    """Return a certificate and private key pair from a configuration dictionary.

    The returned tuple is in the form ``(cert_file, key_file)`` so it can be
    passed directly to libraries such as ``requests`` that expect a client
    certificate pair.

    Order of precedence for finding the certificate/key pair:
    1. If both 'public_cert' and 'private_key' are specified in the configuration and point to valid files, return that pair.
    2. If 'tls_path' is specified, search that directory for matching pairs and return the pair with the most recently modified certificate.
    3. If no valid pair is found, return ``None``.

    Args:
        config (dict): A configuration dictionary containing the keys 'public_cert', 'private_key' with paths to the certificate and private key files.

    Returns:
        tuple[str, str] | None: The matching certificate and key paths, or
        ``None`` if no matching pair is found. The returned tuple is in the form
        ``(cert_file, key_file)`` so it can be passed directly to the``requests``
        library.
    """
    paths_specified = [
        _has_string_value(config, PUBLIC_CERT_KEY),
        _has_string_value(config, PRIVATE_KEY_KEY),
    ]
    if all(paths_specified):
        cert_path = config.get(PUBLIC_CERT_KEY)
        key_path = config.get(PRIVATE_KEY_KEY)
        cert_file = Path(cert_path)
        key_file = Path(key_path)
        if cert_file.is_file() and key_file.is_file():
            return str(cert_file), str(key_file)

    if _has_string_value(config, TLS_PATH_KEY):
        tls_path = Path(config[TLS_PATH_KEY])
        result = find(tls_path)
        if result:
            return result

    return None


def _has_string_value(config: dict, key: str) -> bool:
    return key in config and isinstance(config.get(key), str)


def find(path: Union[Path, str, None] = None, strategy: SelectionStrategy = SelectionStrategy.NEWEST) -> tuple[str, str] | None:
    """Return a matching certificate and private key pair.

    The returned tuple is in the form ``(cert_file, key_file)`` so it can be
    passed directly to libraries such as ``requests`` that expect a client
    certificate pair.

    If ``path`` is omitted, the current working directory is searched. When a
    directory contains more than one matching pair, ``strategy`` controls which
    pair is selected.

    Args:
        path (Union[Path, str, None], optional): A certificate file, key file,
            or directory to search. If omitted, the current working directory is
            used.
        strategy (SelectionStrategy, optional): How to choose a pair when more
            than one matching certificate/key pair is found in a directory.
            ``SelectionStrategy.NEWEST`` picks the most recently modified
            certificate. ``SelectionStrategy.ALPHABETICAL`` picks the pair whose
            certificate filename sorts first.

    Returns:
        tuple[str, str] | None: The matching certificate and key paths, or
        ``None`` if no matching pair is found. The returned tuple is in the form
        ``(cert_file, key_file)`` so it can be passed directly to the``requests``
        library.
    """
    if path is None:
        path = Path.cwd()

    if isinstance(path, str):
        path = Path(path)
    
    if "~" in str(path):
        path = path.expanduser()

    if path.is_file():
        cert_file = path.with_suffix('.crt')
        key_file = path.with_suffix('.key')
        if key_file.is_file() and cert_file.is_file():
            return str(cert_file), str(key_file)
    elif path.is_dir():
        candidates = find_all(path)
        if len(candidates) == 0:
            return None
        if len(candidates) == 1:
            cert, key = candidates[0]
            return str(cert), str(key)
        # If we made it this far then there are multiple candidates. We need to apply the selection strategy to pick one.
        if strategy == SelectionStrategy.ALPHABETICAL:
            candidates.sort(key=lambda pair: pair[0].name)
        elif strategy == SelectionStrategy.NEWEST:
            # The 'NEWEST' strategy selects the most recently modified certificate file.
            # We check the cert file because that's the one that can expire and is more likely to be updated.
            candidates.sort(key=lambda pair: pair[0].stat().st_mtime, reverse=True)
        cert, key = candidates[0]
        return str(cert), str(key)
    return None


def find_all(path: Union[Path, str, None] = None) -> list[tuple[Path, Path]]:
    """Return all matching certificate and private key pairs in a directory.

    The returned list contains tuples in the form ``(cert_file, key_file)`` so
    they can be passed directly to libraries such as ``requests`` that expect
    client certificate pairs.

    If ``path`` is omitted, the current working directory is searched.

    Args:
        path (Union[Path, str, None], optional): A directory to search. If
            omitted, the current working directory is used.

    Returns:
        list[tuple[Path, Path]]: A list of matching certificate and key paths. Each
        tuple is in the form ``(cert_file, key_file)`` so it can be passed directly
        to libraries such as ``requests`` that expect client certificate pairs.
    """
    if path is None:
        path = Path.cwd()

    if isinstance(path, str):
        path = Path(path)
    
    if "~" in str(path):
        path = path.expanduser()

    if not path.is_dir():
        return []

    candidates = []
    for file in path.iterdir():
        if not file.is_file():
            continue
        if file.name == "CAs.crt":
            continue
        if file.suffix == '.crt':
            cert_file = file
            key_file = file.with_suffix('.key')
            if key_file.is_file() and cert_file.is_file():
                pair = cert_file, key_file
                candidates.append(pair)
    return candidates


def from_env() -> tuple[str, str] | None:
    """Return a certificate and private key pair from environment variables.

    The returned tuple is in the form ``(cert_file, key_file)`` so it can be
    passed directly to libraries such as ``requests`` that expect a client
    certificate pair.

    Environment variables:
        PUBLIC_CERT: Path to the public certificate file.
        PRIVATE_KEY: Path to the private key file.
        TLS_PATH: A directory to search for matching certificate/key pairs.

    Returns:
        tuple[str, str] | None: The matching certificate and key paths, or
        ``None`` if no matching pair is found. The returned tuple is in the form
        ``(cert_file, key_file)`` so it can be passed directly to the``requests``
        library.
    """
    config = _env_config()
    return _from_dict(config)
