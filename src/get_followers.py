#!/usr/bin/env python3
"""Update README.md with the latest GitHub followers using GraphQL."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import requests

GITHUB_GRAPHQL_API = "https://api.github.com/graphql"
TARGET_USERNAME = "shubham-shipt"
FOLLOWER_COUNT = 24

README_PATH = Path("README.md")
START_MARKER = "<!-- FOLLOWERS_START -->"
END_MARKER = "<!-- FOLLOWERS_END -->"


def fetch_followers(token: str) -> list[dict[str, str]]:
    """Fetch newest followers."""

    query = """
    query($username: String!, $count: Int!) {
      user(login: $username) {
        followers(first: $count, orderBy: {field: FOLLOWED_AT, direction: DESC}) {
          nodes {
            login
            avatarUrl
            url
          }
        }
      }
    }
    """

    response = requests.post(
        GITHUB_GRAPHQL_API,
        json={
            "query": query,
            "variables": {
                "username": TARGET_USERNAME,
                "count": FOLLOWER_COUNT,
            },
        },
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )
    response.raise_for_status()

    payload: dict[str, Any] = response.json()

    if "errors" in payload:
        raise RuntimeError(payload["errors"])

    return payload["data"]["user"]["followers"]["nodes"]


def build_followers_block(followers: list[dict[str, str]]) -> str:
    lines = []
    lines.append("## ✨ Latest Followers\n")
    lines.append("| Avatar | Username |")
    lines.append("|--------|----------|")

    for f in followers:
        avatar = f'<img src="{f["avatarUrl"]}" width="60" style="border-radius:50%;" />'
        username = f'[{f["login"]}]({f["url"]})'
        lines.append(f"| {avatar} | {username} |")

    return "\n".join(lines)


def replace_followers_section(readme_text: str, followers_block: str) -> str:
    start = readme_text.index(START_MARKER) + len(START_MARKER)
    end = readme_text.index(END_MARKER)
    return readme_text[:start] + "\n\n" + followers_block + "\n\n" + readme_text[end:]


def safe_write(path: Path, content: str) -> None:
    with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent) as tmp:
        tmp.write(content)
        temp_name = tmp.name
    os.replace(temp_name, path)


def main() -> int:
    token = os.getenv("GH_TOKEN")
    if not token:
        print("GH_TOKEN missing", file=sys.stderr)
        return 1

    followers = fetch_followers(token)
    followers_block = build_followers_block(followers)

    current = README_PATH.read_text(encoding="utf-8")
    updated = replace_followers_section(current, followers_block)

    if updated != current:
        safe_write(README_PATH, updated)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
