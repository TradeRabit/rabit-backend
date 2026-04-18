"""Smoke test utility for Backpack public and private connectivity."""
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

from agents.backpack_execution.client import BackpackClient, BackpackClientError
from config.settings import settings


def _print_result(name: str, success: bool, detail: Any) -> None:
    """Print one test result in a compact format."""
    prefix = "PASS" if success else "FAIL"
    if isinstance(detail, (dict, list)):
        rendered = json.dumps(detail, ensure_ascii=False)[:400]
    else:
        rendered = str(detail)
    print(f"[{prefix}] {name}: {rendered}")


async def _public_get(url: str) -> Dict[str, Any]:
    """Fetch one public endpoint."""
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as response:
            text = await response.text()
            return {
                "status": response.status,
                "content_type": response.headers.get("content-type", ""),
                "body": text[:200],
            }


async def run_public_only() -> int:
    """Run public reachability checks that do not require credentials."""
    checks = [
        ("docs", "https://docs.backpack.exchange/"),
        ("api_time", f"{settings.BACKPACK_API_URL.rstrip('/')}/api/v1/time"),
        ("api_ping", f"{settings.BACKPACK_API_URL.rstrip('/')}/api/v1/ping"),
    ]

    failures = 0
    for name, url in checks:
        try:
            result = await _public_get(url)
            ok = result["status"] < 400
            _print_result(name, ok, result)
            failures += 0 if ok else 1
        except Exception as exc:
            _print_result(name, False, exc)
            failures += 1
    return failures


async def run_private_readonly() -> int:
    """Run private read-only checks using Backpack credentials."""
    client = BackpackClient()
    failures = 0

    for name, fn in [
        ("get_balances", client.get_balances),
        ("get_collateral", client.get_collateral),
        ("get_open_orders", client.get_open_orders),
    ]:
        try:
            result = await fn()
            _print_result(name, True, result)
        except BackpackClientError as exc:
            _print_result(name, False, exc)
            failures += 1
        except Exception as exc:
            _print_result(name, False, exc)
            failures += 1
    return failures


async def run_execution_disabled() -> int:
    """Validate that execution config is disabled before any live order tests."""
    detail = {
        "BACKPACK_EXECUTION_ENABLED": settings.BACKPACK_EXECUTION_ENABLED,
        "api_key_present": bool(settings.BACKPACK_API_KEY),
        "api_secret_present": bool(settings.BACKPACK_API_SECRET),
        "note": (
            "This mode never places an order. It only confirms whether credentials exist "
            "and whether the global execution gate is still disabled."
        ),
    }
    ok = not settings.BACKPACK_EXECUTION_ENABLED
    _print_result("execution_disabled", ok, detail)
    return 0 if ok else 1


async def main_async(mode: str) -> int:
    """Dispatch smoke test mode."""
    if mode == "public-only":
        return await run_public_only()
    if mode == "private-readonly":
        return await run_private_readonly()
    if mode == "execution-disabled":
        return await run_execution_disabled()
    raise ValueError(f"Unsupported mode '{mode}'")


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Run Backpack smoke tests.")
    parser.add_argument(
        "--mode",
        choices=["public-only", "private-readonly", "execution-disabled"],
        default="public-only",
        help="Which Backpack smoke test mode to run.",
    )
    args = parser.parse_args()
    failures = asyncio.run(main_async(args.mode))
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
