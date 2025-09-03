#!/usr/bin/env python3
from rich.console import Console

from core.work_assistant import WorkAssistant

console = Console()


def main() -> None:
    """Entry point for the personal ticket assistant."""
    try:
        assistant = WorkAssistant()
        assistant.start_session()
    except KeyboardInterrupt:
        console.print("\n👋 Session ended", style="yellow")
    except Exception as e:
        console.print(f"\n❌ Error: {e}", style="red")


if __name__ == "__main__":
    main()
