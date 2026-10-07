#!/usr/bin/env python3
import json
import os
from datetime import datetime
from pathlib import Path
import statistics


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
        if reviews:
            first_review = parse_timestamp(reviews[0].get("submittedAt"))

        result = {
            "repo": repo,
            "number": number,
            "created": data.get("createdAt"),
            "merged": data.get("mergedAt"),
            "review_count": len(reviews),
            "has_review": len(reviews) > 0,
            "time_to_first_review_hours": calculate_hours(created, first_review),
            "time_to_first_review_days": calculate_days(created, first_review),
            "time_to_merge_hours": calculate_hours(created, merged),
            "time_to_merge_days": calculate_days(created, merged),
        }

        return result
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return None


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
    with open("/tmp/pr_timing_analysis.json", "w") as f:
        json.dump(results, f, indent=2)

    # Calculate statistics
    time_to_merge = [
        r["time_to_merge_days"] for r in results if r["time_to_merge_days"] is not None
    ]
    time_to_review = [
        r["time_to_first_review_days"]
        for r in results
        if r["time_to_first_review_days"] is not None
    ]

    print("\n=== TIME TO MERGE STATISTICS ===")
    if time_to_merge:
        print(f"Total PRs with merge data: {len(time_to_merge)}")
        print(f"Mean: {statistics.mean(time_to_merge):.2f} days")
        print(f"Median: {statistics.median(time_to_merge):.2f} days")
        print(f"Min: {min(time_to_merge):.2f} days")
        print(f"Max: {max(time_to_merge):.2f} days")
        if len(time_to_merge) > 1:
            print(f"Std Dev: {statistics.stdev(time_to_merge):.2f} days")

        # Percentiles
        sorted_merge = sorted(time_to_merge)
        p25 = sorted_merge[len(sorted_merge) // 4]
        p75 = sorted_merge[3 * len(sorted_merge) // 4]
        p90 = sorted_merge[9 * len(sorted_merge) // 10]
        p95 = sorted_merge[95 * len(sorted_merge) // 100]

        print(f"25th percentile: {p25:.2f} days")
        print(f"75th percentile: {p75:.2f} days")
        print(f"90th percentile: {p90:.2f} days")
        print(f"95th percentile: {p95:.2f} days")

    print("\n=== TIME TO FIRST REVIEW STATISTICS ===")
    if time_to_review:
        print(f"Total PRs with review data: {len(time_to_review)}")
        print(f"Mean: {statistics.mean(time_to_review):.2f} days")
        print(f"Median: {statistics.median(time_to_review):.2f} days")
        print(f"Min: {min(time_to_review):.2f} days")
        print(f"Max: {max(time_to_review):.2f} days")
        if len(time_to_review) > 1:
            print(f"Std Dev: {statistics.stdev(time_to_review):.2f} days")

        # Percentiles
        sorted_review = sorted(time_to_review)
        p25 = sorted_review[len(sorted_review) // 4]
        p75 = sorted_review[3 * len(sorted_review) // 4]
        p90 = sorted_review[9 * len(sorted_review) // 10]
        p95 = sorted_review[95 * len(sorted_review) // 100]

        print(f"25th percentile: {p25:.2f} days")
        print(f"75th percentile: {p75:.2f} days")
        print(f"90th percentile: {p90:.2f} days")
        print(f"95th percentile: {p95:.2f} days")

    prs_without_review = sum(1 for r in results if not r["has_review"])
    print(f"\n=== REVIEW STATUS ===")
    print(f"PRs with reviews: {len(time_to_review)}/{len(results)}")
    print(f"PRs without reviews: {prs_without_review}/{len(results)}")

    # Distribution buckets for merge time
    print("\n=== TIME TO MERGE DISTRIBUTION ===")
    buckets = {
        "< 1 hour": 0,
        "1-6 hours": 0,
        "6-24 hours": 0,
        "1-3 days": 0,
        "3-7 days": 0,
        "1-2 weeks": 0,
        "2-4 weeks": 0,
        "> 4 weeks": 0,
    }

    for days in time_to_merge:
        hours = days * 24
        if hours < 1:
            buckets["< 1 hour"] += 1
        elif hours < 6:
            buckets["1-6 hours"] += 1
        elif hours < 24:
            buckets["6-24 hours"] += 1
        elif days < 3:
            buckets["1-3 days"] += 1
        elif days < 7:
            buckets["3-7 days"] += 1
        elif days < 14:
            buckets["1-2 weeks"] += 1
        elif days < 28:
            buckets["2-4 weeks"] += 1
        else:
            buckets["> 4 weeks"] += 1

    for bucket, count in buckets.items():
        pct = (count / len(time_to_merge) * 100) if time_to_merge else 0
        print(f"{bucket:15s}: {count:4d} ({pct:5.1f}%)")

    # Distribution buckets for review time
    print("\n=== TIME TO FIRST REVIEW DISTRIBUTION ===")
    review_buckets = {
        "< 1 hour": 0,
        "1-6 hours": 0,
        "6-24 hours": 0,
        "1-3 days": 0,
        "3-7 days": 0,
        "1-2 weeks": 0,
        "> 2 weeks": 0,
    }

    for days in time_to_review:
        hours = days * 24
        if hours < 1:
            review_buckets["< 1 hour"] += 1
        elif hours < 6:
            review_buckets["1-6 hours"] += 1
        elif hours < 24:
            review_buckets["6-24 hours"] += 1
        elif days < 3:
            review_buckets["1-3 days"] += 1
        elif days < 7:
            review_buckets["3-7 days"] += 1
        elif days < 14:
            review_buckets["1-2 weeks"] += 1
        else:
            review_buckets["> 2 weeks"] += 1

    for bucket, count in review_buckets.items():
        pct = (count / len(time_to_review) * 100) if time_to_review else 0
        print(f"{bucket:15s}: {count:4d} ({pct:5.1f}%)")


if __name__ == "__main__":
    main()
