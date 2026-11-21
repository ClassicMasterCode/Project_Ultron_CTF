#!/usr/bin/env python3
"""
ULTRON Recovery Infrastructure - Second Factor Utility
Implements standard RFC 6238 TOTP (Time-Based One-Time Password).
Compatible with Python 3.8+ with zero external dependencies.
"""
import sys
import os
import time
import hmac
import hashlib
import struct
import base64
import argparse

def get_totp_code(secret_b32: str, interval: int = 30, digits: int = 6, for_time: int = None) -> str:
    """Generate RFC 6238 TOTP code."""
    # Clean up base32 secret
    cleaned = secret_b32.strip().replace(" ", "").upper()
    # Add padding if needed
    padding = len(cleaned) % 8
    if padding != 0:
        cleaned += "=" * (8 - padding)
    key = base64.b32decode(cleaned, casefold=True)

    current_t = int(for_time if for_time is not None else time.time())
    counter = current_t // interval

    # Pack 64-bit integer
    msg = struct.pack(">Q", counter)
    h = hmac.new(key, msg, hashlib.sha1).digest()

    offset = h[-1] & 0x0F
    code_int = struct.unpack(">I", h[offset:offset + 4])[0] & 0x7FFFFFFF
    code = code_int % (10 ** digits)
    return f"{code:0{digits}d}"

def time_remaining(interval: int = 30) -> int:
    return interval - (int(time.time()) % interval)

def main():
    parser = argparse.ArgumentParser(description="Stark Systems ULTRON Authentication Helper")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    totp_parser = subparsers.add_parser("totp", help="Generate TOTP code")
    totp_parser.add_argument("--seed", "-s", help="Base32 seed string")
    totp_parser.add_argument("--seed-file", "-f", help="Path to seed file")
    totp_parser.add_argument("--interval", "-i", type=int, default=30, help="Time step (default: 30s)")
    totp_parser.add_argument("--digits", "-d", type=int, default=6, help="Digits (default: 6)")

    args = parser.parse_args()

    if args.command == "totp":
        seed = None
        if args.seed:
            seed = args.seed
        elif args.seed_file:
            if not os.path.exists(args.seed_file):
                print(f"Error: Seed file not found: {args.seed_file}", file=sys.stderr)
                sys.exit(1)
            with open(args.seed_file, "r") as f:
                seed = f.read().strip()
        else:
            print("Error: Specify either --seed or --seed-file", file=sys.stderr)
            sys.exit(1)

        code = get_totp_code(seed, interval=args.interval, digits=args.digits)
        rem = time_remaining(args.interval)
        print(f"[ULTRON AUTH] Active TOTP Code: {code}  (valid for {rem}s)")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
