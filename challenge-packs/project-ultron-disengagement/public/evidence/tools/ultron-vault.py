#!/usr/bin/env python3
"""
ULTRON Recovery Infrastructure - Encrypted Vault Utility
Supports encryption and decryption of ULTRON .vault recovery archives.
Zero external dependencies (uses standard library PBKDF2-HMAC-SHA256 + CTR keystream).
"""
import sys
import os
import json
import base64
import hashlib
import hmac
import struct
import argparse

MAGIC = b"ULTRON-VAULT-v1\n"
SALT_LEN = 16
ITERATIONS = 100_000

def _derive_keystream(key: bytes, length: int) -> bytes:
    """Generate deterministic CTR keystream from key using HMAC-SHA256."""
    blocks = []
    counter = 0
    generated = 0
    while generated < length:
        block = hmac.new(key, struct.pack(">Q", counter), hashlib.sha256).digest()
        blocks.append(block)
        generated += len(block)
        counter += 1
    return b"".join(blocks)[:length]

def encrypt_vault(data: bytes, passphrase: str, metadata: dict = None) -> bytes:
    """Encrypt payload into .vault container."""
    salt = os.urandom(SALT_LEN)
    key = hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, ITERATIONS, dklen=32)
    keystream = _derive_keystream(key, len(data))
    ciphertext = bytes(a ^ b for a, b in zip(data, keystream))
    auth_tag = hmac.new(key, ciphertext, hashlib.sha256).digest()

    header = {
        "format": "ULTRON-VAULT-1.0",
        "iterations": ITERATIONS,
        "salt": base64.b64encode(salt).decode("ascii"),
        "auth_tag": base64.b64encode(auth_tag).decode("ascii"),
        "meta": metadata or {}
    }
    header_bytes = json.dumps(header).encode("utf-8")
    return MAGIC + struct.pack(">I", len(header_bytes)) + header_bytes + ciphertext

def decrypt_vault(vault_bytes: bytes, passphrase: str) -> tuple[bytes, dict]:
    """Decrypt .vault container with passphrase."""
    if not vault_bytes.startswith(MAGIC):
        raise ValueError("Invalid vault format or magic header missing")

    offset = len(MAGIC)
    header_len = struct.unpack(">I", vault_bytes[offset:offset+4])[0]
    offset += 4
    header_json = vault_bytes[offset:offset+header_len].decode("utf-8")
    header = json.loads(header_json)
    offset += header_len

    salt = base64.b64decode(header["salt"])
    expected_tag = base64.b64decode(header["auth_tag"])
    iterations = header.get("iterations", ITERATIONS)
    ciphertext = vault_bytes[offset:]

    key = hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, iterations, dklen=32)
    computed_tag = hmac.new(key, ciphertext, hashlib.sha256).digest()

    if not hmac.compare_digest(expected_tag, computed_tag):
        raise ValueError("Decryption failed: incorrect passphrase or corrupted vault archive")

    keystream = _derive_keystream(key, len(ciphertext))
    plaintext = bytes(a ^ b for a, b in zip(ciphertext, keystream))
    return plaintext, header.get("meta", {})

def main():
    parser = argparse.ArgumentParser(description="Stark Systems ULTRON Vault Utility")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    decrypt_p = subparsers.add_parser("decrypt", help="Decrypt a .vault archive")
    decrypt_p.add_argument("file", help="Path to .vault file")
    decrypt_p.add_argument("--passphrase", "-p", required=True, help="Unlock phrase")
    decrypt_p.add_argument("--output", "-o", help="Optional output file path")

    inspect_p = subparsers.add_parser("inspect", help="Inspect .vault metadata")
    inspect_p.add_argument("file", help="Path to .vault file")

    args = parser.parse_args()

    if args.command == "inspect":
        if not os.path.exists(args.file):
            print(f"Error: Vault file not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        with open(args.file, "rb") as f:
            data = f.read()
        if not data.startswith(MAGIC):
            print("Error: Invalid vault file header", file=sys.stderr)
            sys.exit(1)
        offset = len(MAGIC)
        header_len = struct.unpack(">I", data[offset:offset+4])[0]
        offset += 4
        header = json.loads(data[offset:offset+header_len].decode("utf-8"))
        print(f"[ULTRON VAULT] File: {os.path.basename(args.file)}")
        print(f"Format: {header.get('format')}")
        print(f"Metadata: {json.dumps(header.get('meta', {}), indent=2)}")

    elif args.command == "decrypt":
        if not os.path.exists(args.file):
            print(f"Error: Vault file not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        with open(args.file, "rb") as f:
            raw = f.read()
        try:
            plaintext, meta = decrypt_vault(raw, args.passphrase)
            print(f"[ULTRON VAULT] Archive unlocked successfully. (Archive ID: {meta.get('archive_id', 'UNKNOWN')})")
            if args.output:
                with open(args.output, "wb") as f:
                    f.write(plaintext)
                print(f"[ULTRON VAULT] Extracted contents written to: {args.output}")
            else:
                try:
                    text = plaintext.decode("utf-8")
                    print("\n--- EXTRACTED CONTENT ---")
                    print(text)
                    print("-------------------------\n")
                except UnicodeDecodeError:
                    print(f"[ULTRON VAULT] Extracted {len(plaintext)} binary bytes.")
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
