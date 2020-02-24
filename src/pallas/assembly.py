from __future__ import annotations

import os
from typing import Mapping, Optional

from pallas.base import Athena
from pallas.caching import AthenaCachingWrapper
from pallas.proxies import AthenaProxy
from pallas.storage import storage_from_uri
from pallas.usability import AthenaKillOnInterruptWrapper, AthenaNormalizationWrapper


def setup(
    *,
    database: Optional[str] = None,
    workgroup: Optional[str] = None,
    output_location: Optional[str] = None,
    region: Optional[str] = None,
    cache_remote: Optional[str] = None,
    cache_local: Optional[str] = None,
    normalize: bool = True,
    kill_on_interrupt: bool = True,
) -> Athena:
    """
    Assembly :class:`.Athena` instance.

    Initializes :class:`.AthenaProxy` and decorates it by caching wrappers.

    :param environ: Mapping to use instead of ``os.environ``.
        Set to empty dict to ignore environment variables.
    :param environ_prefix: Prefix of environment variables.
    :param database: a name of Athena database.
        If omitted, database should be specified in SQL.
    :param workgroup: a name of Athena workgroup.
        If omitted, default workgroup will be used.
    :param output_location: an output location at S3 for query results.
        Optional if a default location is specified for the *workgroup*.
    :param region: an AWS region.
        By default, region from AWS config is used.
    :param cache_remote: an URI of a remote cache.
        Query execution IDs without results are stored to the remote cache.
    :param cache_local: an URI of a local cache.
        Both results and query execution IDs are stored to the local cache.
    :param normalize: whether to normalize SQL
        Normalizes whitespace to improve caching.
    :param kill_on_interrupt: whether to kill queries on KeyboardInterrupt
        Kills query when interrupted during waiting.
    :return: an Athena instance
        A :class:`.AthenaProxy` instance wrapped necessary in decorators.
    """

    athena: Athena
    athena = AthenaProxy(
        database=database,
        workgroup=workgroup,
        output_location=output_location,
        region=region,
    )
    if cache_remote is not None:
        storage = storage_from_uri(cache_remote)
        athena = AthenaCachingWrapper(athena, storage=storage, cache_results=False)
    if cache_local is not None:
        storage = storage_from_uri(cache_local)
        athena = AthenaCachingWrapper(athena, storage=storage, cache_results=True)
    if normalize:
        athena = AthenaNormalizationWrapper(athena)
    if kill_on_interrupt:
        athena = AthenaKillOnInterruptWrapper(athena)
    return athena


def environ_setup(
    environ: Optional[Mapping[str, str]] = None, *, prefix: str = "PALLAS"
) -> Athena:
    if environ is None:
        environ = os.environ
    config = _EnvironConfig(environ, prefix)
    return setup(
        database=config.get_str("DATABASE"),
        workgroup=config.get_str("WORKGROUP"),
        output_location=config.get_str("OUTPUT_LOCATION"),
        region=config.get_str("REGION"),
        cache_remote=config.get_str("CACHE_REMOTE"),
        cache_local=config.get_str("CACHE_LOCAL"),
        normalize=config.get_bool("NORMALIZE", True),
        kill_on_interrupt=config.get_bool("KILL_ON_INTERRUPT", True),
    )


class _EnvironConfig:
    def __init__(self, environ: Mapping[str, str], prefix: str) -> None:
        self._environ = environ
        self._prefix = prefix

    def get_str(self, key: str, default: Optional[str] = None) -> Optional[str]:
        v = self._get(key)
        if not v:
            return default
        return v

    def get_bool(self, key: str, default: bool = False) -> bool:
        v = self._get(key)
        if not v:
            return default
        v = str(v).lower()
        if v in ("1", "true", "on", "yes"):
            return True
        if v in ("0", "false", "off", "no"):
            return False
        raise ValueError(f"Invalid boolean value: {key}")

    def _get(self, key: str) -> str:
        return self._environ.get(f"{self._prefix}_{key}", "")
