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
FOLLOWERS_PER_ROW = 6
README_PATH = Path("README.md")
START_MARKER = "<!-- FOLLOWERS_START -->"
END_MARKER = "<!-- FOLLOWERS_END -->"


def fetch_followers(token: str) -> list[dict[str, str]]:
    """Fetch newest followers for the configured GitHub user."""
    query = """
    query($username: String!, $count: Int!) {
      user(login: $username) {
        followers(
          first: $count
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
        json={"query": query, "variables": {"username": TARGET_USERNAME, "count": FOLLOWER_COUNT}},
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=30,
    )
    response.raise_for_status()

    payload: dict[str, Any] = response.json()
    if "errors" in payload:
        raise RuntimeError(f"GraphQL returned errors: {payload['errors']}")

    user_data = payload.get("data", {}).get("user")
    if not user_data:
        raise RuntimeError(f"GitHub user '{TARGET_USERNAME}' was not found.")

    followers = user_data.get("followers", {}).get("nodes", [])
    cleaned: list[dict[str, str]] = []
    for follower in followers:
        if follower and follower.get("login") and follower.get("avatarUrl") and follower.get("url"):
            cleaned.append(
                {
                    "login": follower["login"],
                    "avatarUrl": follower["avatarUrl"],
                    "url": follower["url"],
                }
            )
    return cleaned


def build_followers_block(followers: list[dict[str, str]]) -> str:
    """Build markdown/html block for followers section."""
    lines = [
        "## ✨ Latest Followers",
        "",
        '<div align="center">',
        '  <table align="center" style="border-collapse:separate; border-spacing:8px; margin:0 auto;">',
        "    <tr>",
        '      <td style="vertical-align:middle; padding-right:8px;">',
        '        <span style="font-size:24px;">⭐</span>',
        "      </td>",
        '      <td style="padding:10px 14px; border:1px solid #d0d7de; border-radius:12px; background:#f6f8fa;">',
        '        <table align="center" style="border-collapse:separate; border-spacing:0;">',
    ]

    if not followers:
        lines.extend(
            [
                "          <tr>",
                '            <td align="center" style="padding:16px; color:#57606a;">No followers to display right now.</td>',
                "          </tr>",
            ]
        )
    else:
        for i in range(0, len(followers), FOLLOWERS_PER_ROW):
            row_followers = followers[i : i + FOLLOWERS_PER_ROW]
            lines.append("          <tr>")
            for follower in row_followers:
                lines.extend(
                    [
                        '            <td align="center" style="padding:14px 12px; min-width:100px;">',
                        f'              <a href="{follower["url"]}" style="text-decoration:none; color:#24292f; font-size:14px; font-weight:600;">',
                        f'                <img src="{follower["avatarUrl"]}" width="80" style="border-radius:50%; border:2px solid #d0d7de;" /><br/>',
                        f'                <span style="display:inline-block; margin-top:8px;">{follower["login"]}</span>',
                        "              </a>",
                        "            </td>",
                    ]
                )
            lines.append("          </tr>")

    lines.extend(
        [
            "        </table>",
            "      </td>",
            '      <td style="vertical-align:middle; padding-left:8px;">',
            '        <span style="font-size:24px;">⭐</span>',
            "      </td>",
            "    </tr>",
            "  </table>",
            "</div>",
        ]
    )
    return "\n".join(lines).strip()


def replace_followers_section(readme_text: str, followers_block: str) -> str:
    """Replace content between markers in README."""
    if START_MARKER not in readme_text or END_MARKER not in readme_text:
        raise RuntimeError(f"README must contain both {START_MARKER} and {END_MARKER} markers.")

    start_index = readme_text.index(START_MARKER) + len(START_MARKER)
    end_index = readme_text.index(END_MARKER)
    if start_index > end_index:
        raise RuntimeError("Followers markers are in invalid order.")

    replacement = f"\n\n{followers_block}\n\n"
    return f"{readme_text[:start_index]}{replacement}{readme_text[end_index:]}"


def safe_write(path: Path, content: str) -> None:
    """Write file content atomically."""
    with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent) as temp_file:
        temp_file.write(content)
        temp_name = temp_file.name

    os.replace(temp_name, path)


def main() -> int:
    token = os.getenv("GH_TOKEN")
    if not token:
        print("Error: GH_TOKEN environment variable is required.", file=sys.stderr)
        return 1

    if not README_PATH.exists():
        print(f"Error: {README_PATH} does not exist.", file=sys.stderr)
        return 1

    try:
        followers = fetch_followers(token)
        followers_block = build_followers_block(followers)
        current_readme = README_PATH.read_text(encoding="utf-8")
        updated_readme = replace_followers_section(current_readme, followers_block)

        if updated_readme == current_readme:
            print("README is already up to date. No changes made.")
            return 0

        safe_write(README_PATH, updated_readme)
        print(f"README updated successfully with {len(followers)} followers.")
        return 0
    except requests.RequestException as exc:
        print(f"Network/API error while fetching followers: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
