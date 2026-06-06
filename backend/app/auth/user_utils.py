"""Helpers for reading user documents from MongoDB."""


def get_stored_password_hash(doc: dict) -> str | None:
    """Support legacy `hashed_password` and spec `password_hash` field names."""
    return doc.get("password_hash") or doc.get("hashed_password")
