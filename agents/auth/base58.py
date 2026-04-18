"""Minimal base58 helpers for Solana wallet auth."""
from __future__ import annotations

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
ALPHABET_INDEX = {char: index for index, char in enumerate(ALPHABET)}


def b58decode(value: str) -> bytes:
    """Decode a base58 string into bytes."""
    if not value:
        return b""

    num = 0
    for char in value:
        if char not in ALPHABET_INDEX:
            raise ValueError("Invalid base58 string.")
        num = num * 58 + ALPHABET_INDEX[char]

    combined = num.to_bytes((num.bit_length() + 7) // 8, byteorder="big")
    leading_zeros = len(value) - len(value.lstrip("1"))
    return b"\x00" * leading_zeros + combined
