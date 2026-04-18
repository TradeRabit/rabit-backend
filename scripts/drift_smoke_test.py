"""Smoke test utility for Drift public connectivity and execution gate status."""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict

import aiohttp

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from config.settings import settings


def _print_result(name: str, success: bool, detail: Any) -> None:
    """Print one test result in a compact format."""
    prefix = "PASS" if success else "FAIL"
    if isinstance(detail, (dict, list)):
        rendered = json.dumps(detail, ensure_ascii=False)[:400]
    else:
        rendered = str(detail)
    print(f"[{prefix}] {name}: {rendered}")


async def _rpc_health() -> Dict[str, Any]:
    """Call Solana RPC health check."""
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(
            settings.DRIFT_RPC_URL,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getHealth",
            },
        ) as response:
            text = await response.text()
            try:
                body = json.loads(text)
            except json.JSONDecodeError:
                body = {"raw": text}
            return {
                "status": response.status,
                "body": body,
            }


async def _ws_probe(url: str) -> Dict[str, Any]:
    """Attempt a websocket handshake and close immediately."""
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.ws_connect(url, heartbeat=10) as ws:
            await ws.close()
            return {"connected": True, "url": url}


async def run_public_only() -> int:
    """Run public Drift connectivity checks."""
    failures = 0

    try:
        rpc = await _rpc_health()
        rpc_ok = rpc["status"] < 400 and "error" not in rpc["body"]
        _print_result("rpc_health", rpc_ok, rpc)
        failures += 0 if rpc_ok else 1
    except Exception as exc:
        _print_result("rpc_health", False, exc)
        failures += 1

    for name, url in [
        ("drift_ws", settings.DRIFT_WS_URL),
        ("drift_dlob_ws", settings.DRIFT_DLOB_WS_URL),
    ]:
        try:
            result = await _ws_probe(url)
            _print_result(name, True, result)
        except Exception as exc:
            _print_result(name, False, exc)
            failures += 1

    return failures


async def run_execution_disabled() -> int:
    """Validate that execution config is disabled before any live Drift tests."""
    detail = {
        "DRIFT_EXECUTION_ENABLED": settings.DRIFT_EXECUTION_ENABLED,
        "DRIFT_RPC_URL": settings.DRIFT_RPC_URL,
        "DRIFT_WS_URL": settings.DRIFT_WS_URL,
        "note": (
            "This mode never places an order. It only confirms whether the global "
            "Drift execution gate is still disabled."
        ),
    }
    ok = not settings.DRIFT_EXECUTION_ENABLED
    _print_result("execution_disabled", ok, detail)
    return 0 if ok else 1


async def main_async(mode: str) -> int:
    """Dispatch smoke test mode."""
    if mode == "public-only":
        return await run_public_only()
    if mode == "execution-disabled":
        return await run_execution_disabled()
    raise ValueError(f"Unsupported mode '{mode}'")


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Run Drift smoke tests.")
    parser.add_argument(
        "--mode",
        choices=["public-only", "execution-disabled"],
        default="public-only",
        help="Which Drift smoke test mode to run.",
    )
    args = parser.parse_args()
    failures = asyncio.run(main_async(args.mode))
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
