#!/usr/bin/env python3


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

        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },

        timeout=30,
    )
    response.raise_for_status()

    payload: dict[str, Any] = response.json()

    os.replace(temp_name, path)


def main() -> int:



if __name__ == "__main__":
    raise SystemExit(main())
