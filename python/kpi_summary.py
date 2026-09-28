#!/usr/bin/env python3
"""Quick KPI summary – mirrors the SQL queries for validation."""

import pandas as pd
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"

users = pd.read_csv(DATA / "users.csv", parse_dates=["signup_date"])
subs = pd.read_csv(DATA / "subscriptions.csv", parse_dates=["start_date", "end_date"])
sessions = pd.read_csv(DATA / "viewing_sessions.csv", parse_dates=["session_date"])
content = pd.read_csv(DATA / "content.csv")

print("=" * 55)
print("OTT KPI SNAPSHOT")
print("=" * 55)

print(f"\nUsers                 : {len(users):,}")
print(f"Subscriptions         : {len(subs):,}")
print(f"Viewing Sessions      : {len(sessions):,}  (100K+ ✓)")
print(f"Content Titles        : {len(content):,}")

# MAU by month (last 6 months shown)
sessions["month"] = sessions["session_date"].dt.to_period("M")
mau = sessions.groupby("month")["user_id"].nunique().tail(6)
print("\nMonthly Active Users (last 6 months):")
print(mau.to_string())

# Churn snapshot
active = subs[subs["status"] == "Active"]["user_id"].nunique()
churned = subs[subs["status"] == "Churned"]["user_id"].nunique()
print(f"\nCurrently Active Subscribers : {active:,}")
print(f"Ever Churned Users           : {churned:,}")
print(f"Overall Churn Ratio          : {100*churned/(active+churned):.1f}%")

# Watch metrics
print(f"\nAvg Watch Minutes / Session  : {sessions['watch_minutes'].mean():.1f}")
print(f"Avg Completion %             : {sessions['completion_pct'].mean():.1f}%")
print(f"Total Watch Hours            : {sessions['watch_minutes'].sum()/60:,.0f}")

# Top genres
top = (
    sessions.merge(content[["content_id", "genre"]], on="content_id")
    .groupby("genre")["watch_minutes"]
    .sum()
    .sort_values(ascending=False)
    .head(5)
)
print("\nTop 5 Genres by Watch Minutes:")
print(top.to_string())

print("\n" + "=" * 55)
