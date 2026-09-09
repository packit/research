#!/usr/bin/env python3
import json
import os
from datetime import datetime
from pathlib import Path
import statistics

# Known bot accounts
BOT_ACCOUNTS = {
    "gemini-code-assist",
    "fullsend-ai-coder",
    "dependabot",
    "pre-commit-ci",
    "github-actions",
}


def is_bot_reviewer(login):
    """Check if a reviewer is a bot"""
    if not login:
        return False
    login_lower = login.lower()
    # Check if it's a known bot or ends with [bot] or -bot
    return (
        login in BOT_ACCOUNTS
        or login_lower.endswith("[bot]")
        or login_lower.endswith("-bot")
        or "bot" in login_lower
    )


def parse_timestamp(ts):
    """Parse ISO timestamp to datetime"""
    if not ts:
        return None
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def calculate_hours(start, end):
    """Calculate hours between two timestamps"""
    if not start or not end:
        return None
    return (end - start).total_seconds() / 3600


def calculate_days(start, end):
    """Calculate days between two timestamps"""
    if not start or not end:
        return None
    return (end - start).total_seconds() / 86400


def process_pr_file(filepath):
    """Process a single PR JSON file"""
    try:
        with open(filepath) as f:
            data = json.load(f)

        # Extract repo and number from filename
        filename = Path(filepath).stem
        parts = filename.rsplit("_", 1)
        repo = parts[0].replace("_", "/", 1)
        number = int(parts[1])

        created = parse_timestamp(data.get("createdAt"))
        merged = parse_timestamp(data.get("mergedAt"))
        reviews = data.get("reviews", [])

        first_review = None
        first_review_by = None
        first_human_review = None
        first_bot_review = None
        human_review_count = 0
        bot_review_count = 0

        for review in reviews:
            reviewer_login = review.get("author", {}).get("login", "")
            review_time = parse_timestamp(review.get("submittedAt"))

            if not review_time:
                continue

            # Track first review overall
            if first_review is None:
                first_review = review_time
                first_review_by = reviewer_login

            # Track bot vs human reviews
            if is_bot_reviewer(reviewer_login):
                bot_review_count += 1
                if first_bot_review is None:
                    first_bot_review = review_time
            else:
                human_review_count += 1
                if first_human_review is None:
                    first_human_review = review_time

        result = {
            "repo": repo,
            "number": number,
            "created": data.get("createdAt"),
            "merged": data.get("mergedAt"),
            "total_review_count": len(reviews),
            "human_review_count": human_review_count,
            "bot_review_count": bot_review_count,
            "has_review": len(reviews) > 0,
            "has_human_review": human_review_count > 0,
            "has_bot_review": bot_review_count > 0,
            "first_review_by": first_review_by,
            "first_review_is_bot": (
                is_bot_reviewer(first_review_by) if first_review_by else None
            ),
            "time_to_first_review_hours": calculate_hours(created, first_review),
            "time_to_first_review_days": calculate_days(created, first_review),
            "time_to_first_human_review_hours": calculate_hours(
                created, first_human_review
            ),
            "time_to_first_human_review_days": calculate_days(
                created, first_human_review
            ),
            "time_to_first_bot_review_hours": calculate_hours(
                created, first_bot_review
            ),
            "time_to_first_bot_review_days": calculate_days(created, first_bot_review),
            "time_to_merge_hours": calculate_hours(created, merged),
            "time_to_merge_days": calculate_days(created, merged),
        }

        return result
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return None


def print_distribution(title, time_data, buckets_def):
    """Print distribution buckets"""
    print(f"\n=== {title} ===")
    buckets = {k: 0 for k in buckets_def.keys()}

    for days in time_data:
        hours = days * 24
        for bucket_name, (min_hours, max_hours) in buckets_def.items():
            if min_hours <= hours < max_hours:
                buckets[bucket_name] += 1
                break

    for bucket, count in buckets.items():
        pct = (count / len(time_data) * 100) if time_data else 0
        print(f"{bucket:15s}: {count:4d} ({pct:5.1f}%)")


def main():
    data_dir = "/tmp/pr_data"
    results = []

    print("Processing PR data files...")
    for filepath in sorted(Path(data_dir).glob("*.json")):
        result = process_pr_file(filepath)
        if result:
            results.append(result)

    print(f"\nProcessed {len(results)} PRs")

    # Save results
    with open("/tmp/pr_timing_analysis_detailed.json", "w") as f:
        json.dump(results, f, indent=2)

    # Separate data by review type
    time_to_merge = [
        r["time_to_merge_days"] for r in results if r["time_to_merge_days"] is not None
    ]
    time_to_any_review = [
        r["time_to_first_review_days"]
        for r in results
        if r["time_to_first_review_days"] is not None
    ]
    time_to_human_review = [
        r["time_to_first_human_review_days"]
        for r in results
        if r["time_to_first_human_review_days"] is not None
    ]
    time_to_bot_review = [
        r["time_to_first_bot_review_days"]
        for r in results
        if r["time_to_first_bot_review_days"] is not None
    ]

    # Calculate statistics
    def print_stats(title, data):
        print(f"\n{'='*60}")
        print(f"{title}")
        print("=" * 60)
        if data:
            print(f"Total PRs: {len(data)}")
            print(
                f"Mean: {statistics.mean(data):.2f} days ({statistics.mean(data)*24:.1f} hours)"
            )
            print(
                f"Median: {statistics.median(data):.2f} days ({statistics.median(data)*24:.1f} hours)"
            )
            print(f"Min: {min(data):.2f} days ({min(data)*24:.1f} hours)")
            print(f"Max: {max(data):.2f} days ({max(data)*24:.1f} hours)")
            if len(data) > 1:
                print(f"Std Dev: {statistics.stdev(data):.2f} days")

            # Percentiles
            sorted_data = sorted(data)
            p25 = sorted_data[len(sorted_data) // 4]
            p75 = sorted_data[3 * len(sorted_data) // 4]
            p90 = sorted_data[9 * len(sorted_data) // 10]
            p95 = sorted_data[95 * len(sorted_data) // 100]

            print(f"\nPercentiles:")
            print(f"  25th: {p25:.2f} days ({p25*24:.1f} hours)")
            print(f"  75th: {p75:.2f} days ({p75*24:.1f} hours)")
            print(f"  90th: {p90:.2f} days ({p90*24:.1f} hours)")
            print(f"  95th: {p95:.2f} days ({p95*24:.1f} hours)")
        else:
            print("No data available")

    print_stats("TIME TO MERGE", time_to_merge)
    print_stats("TIME TO FIRST REVIEW (ANY)", time_to_any_review)
    print_stats("TIME TO FIRST HUMAN REVIEW", time_to_human_review)
    print_stats("TIME TO FIRST BOT REVIEW", time_to_bot_review)

    # Review status breakdown
    prs_with_human_review = sum(1 for r in results if r["has_human_review"])
    prs_with_bot_review = sum(1 for r in results if r["has_bot_review"])
    prs_without_review = sum(1 for r in results if not r["has_review"])
    prs_first_review_bot = sum(1 for r in results if r["first_review_is_bot"])
    prs_first_review_human = sum(
        1 for r in results if r["first_review_is_bot"] == False
    )

    print(f"\n{'='*60}")
    print("REVIEW STATUS BREAKDOWN")
    print("=" * 60)
    print(f"Total PRs: {len(results)}")
    print(
        f"PRs with human reviews: {prs_with_human_review} ({prs_with_human_review/len(results)*100:.1f}%)"
    )
    print(
        f"PRs with bot reviews: {prs_with_bot_review} ({prs_with_bot_review/len(results)*100:.1f}%)"
    )
    print(
        f"PRs without any review: {prs_without_review} ({prs_without_review/len(results)*100:.1f}%)"
    )
    print(
        f"\nFirst review by bot: {prs_first_review_bot} ({prs_first_review_bot/len(results)*100:.1f}%)"
    )
    print(
        f"First review by human: {prs_first_review_human} ({prs_first_review_human/len(results)*100:.1f}%)"
    )

    # Distribution buckets
    merge_buckets = {
        "< 1 hour": (0, 1),
        "1-6 hours": (1, 6),
        "6-24 hours": (6, 24),
        "1-3 days": (24, 72),
        "3-7 days": (72, 168),
        "1-2 weeks": (168, 336),
        "2-4 weeks": (336, 672),
        "> 4 weeks": (672, float("inf")),
    }

    review_buckets = {
        "< 1 hour": (0, 1),
        "1-6 hours": (1, 6),
        "6-24 hours": (6, 24),
        "1-3 days": (24, 72),
        "3-7 days": (72, 168),
        "1-2 weeks": (168, 336),
        "> 2 weeks": (336, float("inf")),
    }

    print_distribution("TIME TO MERGE DISTRIBUTION", time_to_merge, merge_buckets)
    print_distribution(
        "TIME TO FIRST REVIEW (ANY) DISTRIBUTION", time_to_any_review, review_buckets
    )
    print_distribution(
        "TIME TO FIRST HUMAN REVIEW DISTRIBUTION", time_to_human_review, review_buckets
    )
    print_distribution(
        "TIME TO FIRST BOT REVIEW DISTRIBUTION", time_to_bot_review, review_buckets
    )

    # Top bot reviewers
    print(f"\n{'='*60}")
    print("BOT REVIEWERS")
    print("=" * 60)
    bot_reviewers = {}
    for filepath in Path(data_dir).glob("*.json"):
        try:
            with open(filepath) as f:
                data = json.load(f)
            for review in data.get("reviews", []):
                reviewer = review.get("author", {}).get("login", "")
                if is_bot_reviewer(reviewer):
                    bot_reviewers[reviewer] = bot_reviewers.get(reviewer, 0) + 1
        except:
            pass

    for bot, count in sorted(bot_reviewers.items(), key=lambda x: x[1], reverse=True):
        print(f"{bot:30s}: {count:4d} reviews")


if __name__ == "__main__":
    main()
