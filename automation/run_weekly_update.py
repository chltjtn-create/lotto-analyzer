"""CLI wrapper for the weekly automation workflow."""

from __future__ import annotations

import argparse
import json

from lotto_analyzer.automation.weekly_update import run_weekly_update


def main() -> int:
    """Run weekly automation from command line."""
    parser = argparse.ArgumentParser(description="Run weekly Lotto automation")
    parser.add_argument("--no-email", action="store_true", help="Run without sending email")
    parser.add_argument("--count", type=int, help="Recommendation count")
    parser.add_argument("--strategy", help="Recommendation strategy")
    args = parser.parse_args()

    result = run_weekly_update(
        recommendation_count=args.count,
        strategy=args.strategy,
        send_mail=not args.no_email,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 1 if result.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
