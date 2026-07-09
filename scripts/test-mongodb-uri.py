"""Test MongoDB Atlas connectivity before cloud deploy."""

from __future__ import annotations

import asyncio
import os
import sys
from urllib.parse import quote_plus


def build_atlas_uri(
    username: str,
    password: str,
    cluster_host: str,
    db_name: str = "smart_inventory",
) -> str:
    """Build a URL-safe Atlas connection string."""
    host = cluster_host.removeprefix("mongodb+srv://").split("/")[0]
    if not host.endswith(".mongodb.net"):
        host = f"{host}.mongodb.net"
    user = quote_plus(username)
    pwd = quote_plus(password)
    return (
        f"mongodb+srv://{user}:{pwd}@{host}/{db_name}"
        "?retryWrites=true&w=majority&appName=smart-inventory"
    )


async def test_uri(uri: str) -> None:
    from motor.motor_asyncio import AsyncIOMotorClient

    client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=10000)
    try:
        await client.admin.command("ping")
        db_name = uri.rsplit("/", 1)[-1].split("?")[0] or "smart_inventory"
        db = client[db_name]
        await db.command("ping")
        print(f"OK: connected and authenticated (database: {db_name})")
    finally:
        client.close()


def main() -> int:
    uri = os.environ.get("MONGODB_URI", "").strip()
    if len(sys.argv) > 1:
        uri = sys.argv[1].strip()

    if not uri:
        print("Usage: py scripts/test-mongodb-uri.py <MONGODB_URI>")
        print("   or: $env:MONGODB_URI='...'; py scripts/test-mongodb-uri.py")
        return 1

    if "REPLACE_ATLAS" in uri or "<user>" in uri or "<password>" in uri:
        print("ERROR: MONGODB_URI still contains placeholder values.")
        return 1

    try:
        asyncio.run(test_uri(uri))
    except Exception as exc:
        err = str(exc)
        print(f"FAILED: {err}")
        if "bad auth" in err.lower() or "authentication failed" in err.lower():
            print()
            print("Fix Atlas auth:")
            print("  1. Atlas → Database Access → create DB user (not your login email)")
            print("  2. Reset password if unsure; URL-encode special chars (@ # : /)")
            print("  3. Atlas → Network Access → allow 0.0.0.0/0 for Render")
            print("  4. Copy connection string from Connect → Drivers")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
