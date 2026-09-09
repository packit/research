#!/usr/bin/env python3
import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

# Load the analysis data
with open("/tmp/pr_timing_analysis_detailed.json") as f:
    data = json.load(f)

# Extract time data
time_to_merge = [
    r["time_to_merge_days"] for r in data if r["time_to_merge_days"] is not None
]
time_to_any_review = [
    r["time_to_first_review_days"]
    for r in data
    if r["time_to_first_review_days"] is not None
]
time_to_human_review = [
    r["time_to_first_human_review_days"]
    for r in data
    if r["time_to_first_human_review_days"] is not None
]
time_to_bot_review = [
    r["time_to_first_bot_review_days"]
    for r in data
    if r["time_to_first_bot_review_days"] is not None
]

# Create figure with 2x2 subplots
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle(
    "PR Time Distributions - Packit Organization (Last 365 Days)",
    fontsize=16,
    fontweight="bold",
)

# Color scheme
color_merge = "#3498db"
color_any = "#9b59b6"
color_human = "#e74c3c"
color_bot = "#2ecc71"


def create_histogram(ax, data, title, color, xlabel, bins=50, xlim=None):
    """Create a histogram with statistics"""
    n, bins_edges, patches = ax.hist(
        data, bins=bins, color=color, alpha=0.7, edgecolor="black", linewidth=0.5
    )

    # Add median and mean lines
    median = np.median(data)
    mean = np.mean(data)

    ax.axvline(
        median, color="red", linestyle="--", linewidth=2, label=f"Median: {median:.2f}d"
    )
    ax.axvline(
        mean, color="orange", linestyle="--", linewidth=2, label=f"Mean: {mean:.2f}d"
    )

    ax.set_xlabel(xlabel, fontsize=11, fontweight="bold")
    ax.set_ylabel("Number of PRs", fontsize=11, fontweight="bold")
    ax.set_title(title, fontsize=13, fontweight="bold", pad=10)
    ax.legend(loc="upper right", fontsize=10)
    ax.grid(True, alpha=0.3, linestyle="--")

    if xlim:
        ax.set_xlim(xlim)

    # Add statistics text box
    stats_text = f"n={len(data)}\nMin: {min(data):.2f}d\nMax: {max(data):.2f}d\nStd: {np.std(data):.2f}d"
    ax.text(
        0.98,
        0.97,
        stats_text,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment="top",
        horizontalalignment="right",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
    )

    return ax


# 1. Time to Merge
create_histogram(
    ax1,
    time_to_merge,
    f"Time to Merge (n={len(time_to_merge)})",
    color_merge,
    "Days from PR Creation to Merge",
    bins=60,
    xlim=(0, min(60, max(time_to_merge))),
)

# 2. Time to First Review (Any)
create_histogram(
    ax2,
    time_to_any_review,
    f"Time to First Review - Any (n={len(time_to_any_review)})",
    color_any,
    "Days from PR Creation to First Review",
    bins=50,
    xlim=(0, min(30, max(time_to_any_review))),
)

# 3. Time to First Human Review
create_histogram(
    ax3,
    time_to_human_review,
    f"Time to First Human Review (n={len(time_to_human_review)})",
    color_human,
    "Days from PR Creation to First Human Review",
    bins=50,
    xlim=(0, min(30, max(time_to_human_review))),
)

# 4. Time to First Bot Review
create_histogram(
    ax4,
    time_to_bot_review,
    f"Time to First Bot Review (n={len(time_to_bot_review)})",
    color_bot,
    "Days from PR Creation to First Bot Review",
    bins=50,
    xlim=(0, min(10, max(time_to_bot_review))),
)

plt.tight_layout()
plt.savefig("/tmp/pr_time_distributions.png", dpi=300, bbox_inches="tight")
print("Saved: /tmp/pr_time_distributions.png")

# Create a second figure with zoomed-in views (first 24 hours)
fig2, ((ax5, ax6), (ax7, ax8)) = plt.subplots(2, 2, figsize=(16, 12))
fig2.suptitle(
    "PR Time Distributions - First 24 Hours (Zoomed In)", fontsize=16, fontweight="bold"
)


def create_zoomed_histogram(ax, data, title, color, xlabel, max_hours=24):
    """Create a histogram showing only first 24 hours in hours"""
    # Convert to hours and filter
    data_hours = [d * 24 for d in data if d * 24 <= max_hours]

    if not data_hours:
        ax.text(
            0.5,
            0.5,
            "No data in range",
            ha="center",
            va="center",
            transform=ax.transAxes,
        )
        return

    bins = np.arange(0, max_hours + 1, 1)  # 1-hour bins
    n, bins_edges, patches = ax.hist(
        data_hours, bins=bins, color=color, alpha=0.7, edgecolor="black", linewidth=0.5
    )

    # Add median and mean lines
    if data_hours:
        median = np.median(data_hours)
        mean = np.mean(data_hours)

        ax.axvline(
            median,
            color="red",
            linestyle="--",
            linewidth=2,
            label=f"Median: {median:.1f}h",
        )
        ax.axvline(
            mean,
            color="orange",
            linestyle="--",
            linewidth=2,
            label=f"Mean: {mean:.1f}h",
        )

    ax.set_xlabel(xlabel, fontsize=11, fontweight="bold")
    ax.set_ylabel("Number of PRs", fontsize=11, fontweight="bold")
    ax.set_title(title, fontsize=13, fontweight="bold", pad=10)
    ax.legend(loc="upper right", fontsize=10)
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.set_xlim(0, max_hours)

    # Add statistics text box
    pct = len(data_hours) / len(data) * 100
    stats_text = f"{len(data_hours)}/{len(data)} PRs\n({pct:.1f}%)"
    ax.text(
        0.98,
        0.97,
        stats_text,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="top",
        horizontalalignment="right",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
    )


create_zoomed_histogram(
    ax5,
    time_to_merge,
    "Time to Merge (First 24 Hours)",
    color_merge,
    "Hours from PR Creation to Merge",
)

create_zoomed_histogram(
    ax6,
    time_to_any_review,
    "Time to First Review - Any (First 24 Hours)",
    color_any,
    "Hours from PR Creation to First Review",
)

create_zoomed_histogram(
    ax7,
    time_to_human_review,
    "Time to First Human Review (First 24 Hours)",
    color_human,
    "Hours from PR Creation to First Human Review",
)

create_zoomed_histogram(
    ax8,
    time_to_bot_review,
    "Time to First Bot Review (First 24 Hours)",
    color_bot,
    "Hours from PR Creation to First Bot Review",
    max_hours=6,
)  # Bot reviews are so fast, show only 6 hours

plt.tight_layout()
plt.savefig("/tmp/pr_time_distributions_zoomed.png", dpi=300, bbox_inches="tight")
print("Saved: /tmp/pr_time_distributions_zoomed.png")

# Create a third figure comparing bot vs human review times
fig3, ax9 = plt.subplots(1, 1, figsize=(14, 8))

# Create overlapping histograms
bins = np.arange(0, 10, 0.2)  # 0-10 days in 0.2 day increments
ax9.hist(
    time_to_bot_review,
    bins=bins,
    color=color_bot,
    alpha=0.5,
    label=f"Bot Reviews (n={len(time_to_bot_review)})",
    edgecolor="black",
    linewidth=0.5,
)
ax9.hist(
    time_to_human_review,
    bins=bins,
    color=color_human,
    alpha=0.5,
    label=f"Human Reviews (n={len(time_to_human_review)})",
    edgecolor="black",
    linewidth=0.5,
)

# Add median lines
bot_median = np.median(time_to_bot_review)
human_median = np.median(time_to_human_review)
ax9.axvline(
    bot_median,
    color=color_bot,
    linestyle="--",
    linewidth=2,
    label=f"Bot Median: {bot_median:.3f}d ({bot_median*24:.1f}h)",
)
ax9.axvline(
    human_median,
    color=color_human,
    linestyle="--",
    linewidth=2,
    label=f"Human Median: {human_median:.3f}d ({human_median*24:.1f}h)",
)

ax9.set_xlabel("Days from PR Creation to First Review", fontsize=12, fontweight="bold")
ax9.set_ylabel("Number of PRs", fontsize=12, fontweight="bold")
ax9.set_title(
    "Bot vs Human Review Time Comparison", fontsize=14, fontweight="bold", pad=15
)
ax9.legend(loc="upper right", fontsize=11)
ax9.grid(True, alpha=0.3, linestyle="--")
ax9.set_xlim(0, 10)

plt.tight_layout()
plt.savefig("/tmp/pr_bot_vs_human_comparison.png", dpi=300, bbox_inches="tight")
print("Saved: /tmp/pr_bot_vs_human_comparison.png")

# Create stacked bar chart showing distribution buckets
fig4, ((ax10, ax11), (ax12, ax13)) = plt.subplots(2, 2, figsize=(16, 10))
fig4.suptitle(
    "Time Distribution Buckets - Percentage View", fontsize=16, fontweight="bold"
)


def create_bucket_chart(ax, data, title, color, buckets):
    """Create a bar chart of time buckets"""
    counts = {k: 0 for k in buckets.keys()}

    for days in data:
        hours = days * 24
        for bucket_name, (min_h, max_h) in buckets.items():
            if min_h <= hours < max_h:
                counts[bucket_name] += 1
                break

    labels = list(counts.keys())
    values = list(counts.values())
    percentages = [v / len(data) * 100 for v in values]

    bars = ax.bar(
        range(len(labels)),
        percentages,
        color=color,
        alpha=0.7,
        edgecolor="black",
        linewidth=1,
    )
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_ylabel("Percentage of PRs (%)", fontsize=11, fontweight="bold")
    ax.set_title(title, fontsize=12, fontweight="bold", pad=10)
    ax.grid(True, alpha=0.3, linestyle="--", axis="y")

    # Add percentage labels on bars
    for i, (bar, pct, count) in enumerate(zip(bars, percentages, values)):
        if pct > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1,
                f"{pct:.1f}%\n({count})",
                ha="center",
                va="bottom",
                fontsize=8,
                fontweight="bold",
            )


merge_buckets = {
    "< 1h": (0, 1),
    "1-6h": (1, 6),
    "6-24h": (6, 24),
    "1-3d": (24, 72),
    "3-7d": (72, 168),
    "1-2w": (168, 336),
    "2-4w": (336, 672),
    "> 4w": (672, float("inf")),
}

review_buckets = {
    "< 1h": (0, 1),
    "1-6h": (1, 6),
    "6-24h": (6, 24),
    "1-3d": (24, 72),
    "3-7d": (72, 168),
    "1-2w": (168, 336),
    "> 2w": (336, float("inf")),
}

create_bucket_chart(
    ax10,
    time_to_merge,
    f"Time to Merge (n={len(time_to_merge)})",
    color_merge,
    merge_buckets,
)
create_bucket_chart(
    ax11,
    time_to_any_review,
    f"Time to Any Review (n={len(time_to_any_review)})",
    color_any,
    review_buckets,
)
create_bucket_chart(
    ax12,
    time_to_human_review,
    f"Time to Human Review (n={len(time_to_human_review)})",
    color_human,
    review_buckets,
)
create_bucket_chart(
    ax13,
    time_to_bot_review,
    f"Time to Bot Review (n={len(time_to_bot_review)})",
    color_bot,
    review_buckets,
)

plt.tight_layout()
plt.savefig("/tmp/pr_distribution_buckets.png", dpi=300, bbox_inches="tight")
print("Saved: /tmp/pr_distribution_buckets.png")

print("\nAll histograms created successfully!")
print("Files saved:")
print("  1. /tmp/pr_time_distributions.png - Full distribution histograms")
print("  2. /tmp/pr_time_distributions_zoomed.png - First 24 hours (zoomed)")
print("  3. /tmp/pr_bot_vs_human_comparison.png - Bot vs Human overlay")
print("  4. /tmp/pr_distribution_buckets.png - Bucket percentage charts")
