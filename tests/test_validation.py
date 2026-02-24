import pytest

from traceroute_visualizer.services.traceroute_service import (
    resolve_target,
    validate_target,
)


def test_validate_empty_target() -> None:
    with pytest.raises(ValueError):
        validate_target("   ")


def test_resolve_domain() -> None:
    hostname, ip = resolve_target("example.com", block_private_targets=False)
    assert hostname == "example.com"
    assert ip


def test_block_private_ip() -> None:
    with pytest.raises(ValueError):
        resolve_target("127.0.0.1", block_private_targets=True)
