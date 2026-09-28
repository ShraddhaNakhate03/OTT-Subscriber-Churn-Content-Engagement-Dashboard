#!/usr/bin/env python3
"""
Cohort Analysis – OTT Subscriber Retention
Identifies early drop-off patterns and surfaces recommendations
to improve 30-day retention via segmented promotional campaigns.

Outputs:
  - cohort_retention_matrix.csv
  - cohort_summary.csv
  - retention_heatmap.png (optional)
  - Printed recommendations
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "docs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_data():
    users = pd.read_csv(DATA_DIR / "users.csv", parse_dates=["signup_date"])
    sessions = pd.read_csv(DATA_DIR / "viewing_sessions.csv", parse_dates=["session_start", "session_date"])
    subs = pd.read_csv(DATA_DIR / "subscriptions.csv", parse_dates=["start_date", "end_date"])
    return users, sessions, subs


def build_activity_cohorts(users, sessions):
    """
    Classic retention cohort:
    Cohort = signup month
    Period = weeks since signup (0, 1, 2, … 8)
    Metric  = % of cohort that had ≥1 session in that week
    """
    # First activity date per user (should be close to signup)
    first_activity = (
        sessions.groupby("user_id")["session_date"]
        .min()
        .reset_index()
        .rename(columns={"session_date": "first_activity"})
    )
    users = users.merge(first_activity, on="user_id", how="left")

    # Only keep users who had at least one session
    active_users = users.dropna(subset=["first_activity"]).copy()
    active_users["cohort_month"] = active_users["signup_date"].dt.to_period("M")

    # Expand sessions with cohort info
    sessions_enriched = sessions.merge(
        active_users[["user_id", "cohort_month", "signup_date"]],
        on="user_id",
        how="inner"
    )
    sessions_enriched["weeks_since_signup"] = (
        (sessions_enriched["session_date"] - sessions_enriched["signup_date"]).dt.days // 7
    ).clip(lower=0)

    # Keep first 9 weeks (0–8) for matrix
    sessions_w = sessions_enriched[sessions_enriched["weeks_since_signup"] <= 8]

    # Distinct users active in each cohort × week
    cohort_size = active_users.groupby("cohort_month")["user_id"].nunique()
    retained = (
        sessions_w.groupby(["cohort_month", "weeks_since_signup"])["user_id"]
        .nunique()
        .reset_index(name="active_users")
    )
    retained = retained.merge(
        cohort_size.rename("cohort_size"),
        left_on="cohort_month",
        right_index=True
    )
    retained["retention_pct"] = (
        100.0 * retained["active_users"] / retained["cohort_size"]
    ).round(1)

    # Pivot to matrix
    matrix = retained.pivot(
        index="cohort_month",
        columns="weeks_since_signup",
        values="retention_pct"
    ).fillna(0)

    return matrix, retained, active_users, sessions_enriched


def early_dropoff_insights(matrix, active_users, sessions):
    """Identify patterns that drive early (week-0 → week-4) drop-off."""
    insights = []

    # Overall 30-day (≈ week 4) retention
    if 4 in matrix.columns:
        avg_w4 = matrix[4].mean()
        insights.append(f"Average Week-4 retention across cohorts: {avg_w4:.1f}%")

    # Segment by acquisition channel
    users_with_channel = active_users.copy()
    channel_retention = []
    for channel, grp in users_with_channel.groupby("acquisition_channel"):
        channel_users = set(grp["user_id"])
        # Users still active in week 4
        w4_active = set(
            sessions[
                (sessions["user_id"].isin(channel_users)) &
                (sessions["weeks_since_signup"] == 4)
            ]["user_id"]
        )
        ret = 100.0 * len(w4_active) / len(channel_users) if channel_users else 0
        channel_retention.append((channel, ret, len(channel_users)))

    channel_retention.sort(key=lambda x: x[1])
    worst = channel_retention[0]
    best = channel_retention[-1]
    insights.append(
        f"Lowest 30-day retention channel: {worst[0]} ({worst[1]:.1f}%) – "
        f"consider targeted onboarding campaigns."
    )
    insights.append(
        f"Highest 30-day retention channel: {best[0]} ({best[1]:.1f}%)."
    )

    # Age group
    age_ret = []
    for age, grp in users_with_channel.groupby("age_group"):
        age_users = set(grp["user_id"])
        w4_active = set(
            sessions[
                (sessions["user_id"].isin(age_users)) &
                (sessions["weeks_since_signup"] == 4)
            ]["user_id"]
        )
        ret = 100.0 * len(w4_active) / len(age_users) if age_users else 0
        age_ret.append((age, ret))
    age_ret.sort(key=lambda x: x[1])
    insights.append(
        f"Age group with earliest drop-off: {age_ret[0][0]} "
        f"({age_ret[0][1]:.1f}% week-4 retention)."
    )

    return insights, channel_retention


def recommendations(insights, channel_retention):
    recs = [
        "1. Segment promotional campaigns by acquisition channel – "
        "especially nurture the lowest-retention channel with personalized "
        "content recommendations in the first 7 days.",
        "2. Launch a 'First 30 Days' engagement series (email + in-app) "
        "that highlights trending titles in the user's preferred genre.",
        "3. Offer a limited-time plan upgrade or free add-on for users "
        "who have not watched in the last 10 days of their first month.",
        "4. A/B test onboarding flows that push users to complete at least "
        "3 sessions in week 0 – strong predictor of 30-day retention.",
        "5. Create age-specific content playlists and surface them "
        "prominently for the age band showing the steepest early drop-off."
    ]
    return recs


def plot_heatmap(matrix, path):
    plt.figure(figsize=(12, 8))
    sns.heatmap(
        matrix,
        annot=True,
        fmt=".0f",
        cmap="YlGnBu",
        linewidths=0.5,
        cbar_kws={"label": "Retention %"}
    )
    plt.title("OTT Subscriber Retention Cohort (Week 0–8)")
    plt.xlabel("Weeks Since Signup")
    plt.ylabel("Signup Cohort (Month)")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"Heatmap saved → {path}")


def main():
    print("=" * 60)
    print("OTT Cohort Analysis – Early Drop-off & 30-Day Retention")
    print("=" * 60)

    users, sessions, subs = load_data()
    matrix, retained, active_users, sessions_enriched = build_activity_cohorts(users, sessions)

    # Save matrix
    matrix.to_csv(OUTPUT_DIR / "cohort_retention_matrix.csv")
    retained.to_csv(OUTPUT_DIR / "cohort_summary.csv", index=False)

    insights, channel_ret = early_dropoff_insights(matrix, active_users, sessions_enriched)
    recs = recommendations(insights, channel_ret)

    print("\n--- Key Insights ---")
    for i in insights:
        print("•", i)

    print("\n--- Recommendations to Boost 30-Day Retention ---")
    for r in recs:
        print(r)

    # Optional visual
    try:
        plot_heatmap(matrix, OUTPUT_DIR / "retention_heatmap.png")
    except Exception as e:
        print("Could not generate heatmap:", e)

    print("\nFiles written to docs/:")
    print("  cohort_retention_matrix.csv")
    print("  cohort_summary.csv")
    print("  retention_heatmap.png (if matplotlib available)")
    print("=" * 60)


if __name__ == "__main__":
    main()
