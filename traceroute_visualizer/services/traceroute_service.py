from __future__ import annotations

import ipaddress
import logging
import socket
from dataclasses import asdict, dataclass
from typing import Any

from scapy.layers.inet import traceroute

logger = logging.getLogger(__name__)


@dataclass
class HopResult:
    hop_index: int
    ip: str
    rtt_ms: float | None
    status: str


def validate_target(target: str) -> str:
    target = target.strip()
    if not target:
        raise ValueError("Target cannot be empty.")
    if len(target) > 255:
        raise ValueError("Target is too long.")
    return target


def resolve_target(target: str, block_private_targets: bool = True) -> tuple[str, str]:
    validated = validate_target(target)
    try:
        ip = str(ipaddress.ip_address(validated))
        hostname = validated
    except ValueError:
        try:
            ip = socket.gethostbyname(validated)
            hostname = validated
        except socket.gaierror as exc:
            raise ValueError("Could not resolve host.") from exc

    ip_obj = ipaddress.ip_address(ip)
    if block_private_targets and (
        ip_obj.is_private
        or ip_obj.is_loopback
        or ip_obj.is_multicast
        or ip_obj.is_reserved
    ):
        raise ValueError(
            "Target resolves to an internal or reserved IP and is blocked by policy."
        )
    return hostname, ip


def run_traceroute(
    destination: str,
    max_hops: int,
    timeout: float,
    retries: int,
) -> list[dict[str, Any]]:
    logger.info(
        "starting traceroute",
        extra={
            "destination": destination,
            "max_hops": max_hops,
            "timeout": timeout,
            "retries": retries,
        },
    )
    answered, _ = traceroute(
        destination, maxttl=max_hops, timeout=timeout, retry=retries, verbose=0
    )
    by_ttl: dict[int, HopResult] = {}

    for sent_packet, recv_packet in answered:
        ttl = int(getattr(sent_packet, "ttl", 0))
        ip = str(getattr(recv_packet, "src", "Unknown"))
        sent_time = getattr(sent_packet, "sent_time", None)
        recv_time = getattr(recv_packet, "time", None)
        rtt_ms = (
            round((recv_time - sent_time) * 1000, 2)
            if sent_time and recv_time
            else None
        )
        status = "ok"
        try:
            ip_obj = ipaddress.ip_address(ip)
            if (
                ip_obj.is_private
                or ip_obj.is_loopback
                or ip_obj.is_reserved
                or ip_obj.is_multicast
            ):
                status = "private"
        except ValueError:
            status = "unknown"

        by_ttl.setdefault(
            ttl, HopResult(hop_index=ttl, ip=ip, rtt_ms=rtt_ms, status=status)
        )

    hops: list[dict[str, Any]] = []
    for hop_index in range(1, max_hops + 1):
        hop = by_ttl.get(hop_index)
        if hop:
            hops.append(asdict(hop))
        else:
            hops.append(
                asdict(
                    HopResult(
                        hop_index=hop_index, ip="*", rtt_ms=None, status="timeout"
                    )
                )
            )
    return hops
