#!/usr/bin/env python3
import os

import uvicorn


def main() -> None:
    """Run the web-based ticket assistant."""
    uvicorn.run("web.app:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))


if __name__ == "__main__":
    main()

