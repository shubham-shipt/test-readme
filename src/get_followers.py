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
    """Fetch newest followers for the configured GitHub user."""

    query = """
    query($username: String!, $count: Int!) {
      user(login: $username) {
        followers(
          first: $count,
          orderBy: { field: FOLLOWED_AT, direction: DESC }
        ) {
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
        raise RuntimeError(f"GraphQL returned errors: {payload['errors']}")

    user_data = payload.get("data", {}).get("user")
    if not user_data:
        raise RuntimeError(f"GitHub user '{TARGET_USERNAME}' not found.")

    followers = user_data.get("followers", {}).get("nodes", [])

    cleaned: list[dict[str, str]] = []
    for follower in followers:
        if follower:
            cleaned.append(
                {
                    "login": follower["login"],
                    "avatarUrl": follower["avatarUrl"],
                    "url": follower["url"],
                }
            )

    return cleaned


def build_followers_block(followers: list[dict[str, str]]) -> str:
    """Build markdown table block for followers section."""

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
    """Replace content between markers in README."""

    if START_MARKER not in readme_text or END_MARKER not in readme_text:
        raise RuntimeError("README missing follower markers.")

    start_index = readme_text.index(START_MARKER) + len(START_MARKER)
    end_index = readme_text.index(END_MARKER)

    replacement = f"\n\n{followers_block}\n\n"

    return (
        readme_text[:start_index]
        + replacement
        + readme_text[end_index:]
    )


def safe_write(path: Path, content: str) -> None:
    """Write file content atomically."""

    with NamedTemporaryFile(
        "w", encoding="utf-8", delete=False, dir=path.parent
    ) as temp_file:
        temp_file.write(content)
        temp_name = temp_file.name

    os.replace(temp_name, path)


def main() -> int:
    token = os.getenv("GH_TOKEN")

    if not token:
        print("Error: GH_TOKEN environment variable required.", file=sys.stderr)
        return 1

    if not README_PATH.exists():
        print("Error: README.md not found.", file=sys.stderr)
        return 1

    try:
        followers = fetch_followers(token)
        followers_block = build_followers_block(followers)

        current_readme = README_PATH.read_text(encoding="utf-8")
        updated_readme = replace_followers_section(
            current_readme,
            followers_block,
        )

        if updated_readme == current_readme:
            print("README already up to date.")
            return 0

        safe_write(README_PATH, updated_readme)

        print(f"README updated with {len(followers)} followers.")
        return 0

    except requests.RequestException as exc:
        print(f"API error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
