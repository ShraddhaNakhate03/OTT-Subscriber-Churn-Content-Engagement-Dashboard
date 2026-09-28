#!/usr/bin/env python3
"""
OTT Subscriber & Content Engagement Dashboard
Synthetic data generator for 100K+ streaming + subscription records.

Produces:
  - users.csv
  - subscriptions.csv
  - content.csv
  - viewing_sessions.csv  (>100k rows)
  - daily_active_users.csv (pre-aggregated for Power BI)

Designed so the resulting CSVs can be loaded directly into Power BI
or used with the accompanying SQL scripts and cohort analysis.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import random

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------
SEED = 42
np.random.seed(SEED)
random.seed(SEED)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

N_USERS = 25_000
N_CONTENT = 2_500
N_VIEWING_SESSIONS = 120_000          # >100k target
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2025, 6, 30)

PLANS = ["Basic", "Standard", "Premium"]
PLAN_PRICES = {"Basic": 9.99, "Standard": 15.99, "Premium": 19.99}
COUNTRIES = ["US", "IN", "UK", "CA", "AU", "BR", "DE", "FR", "JP", "MX"]
AGE_GROUPS = ["18-24", "25-34", "35-44", "45-54", "55+"]
DEVICES = ["Mobile", "Smart TV", "Laptop", "Tablet", "Desktop"]
GENRES = [
    "Action", "Comedy", "Drama", "Thriller", "Sci-Fi",
    "Romance", "Horror", "Documentary", "Animation", "Crime"
]
CONTENT_TYPES = ["Movie", "Series", "Documentary", "Special"]


def random_dates(n, start=START_DATE, end=END_DATE):
    """Return n random datetime objects between start and end."""
    delta = (end - start).total_seconds()
    return [start + timedelta(seconds=random.uniform(0, delta)) for _ in range(n)]


def generate_users(n=N_USERS):
    print(f"Generating {n:,} users...")
    user_ids = [f"U{str(i).zfill(6)}" for i in range(1, n + 1)]
    signup_dates = sorted(random_dates(n))
    countries = np.random.choice(COUNTRIES, n, p=[0.35, 0.20, 0.10, 0.08, 0.07, 0.05, 0.05, 0.04, 0.03, 0.03])
    age_groups = np.random.choice(AGE_GROUPS, n, p=[0.22, 0.30, 0.22, 0.15, 0.11])
    preferred_device = np.random.choice(DEVICES, n, p=[0.40, 0.25, 0.18, 0.10, 0.07])

    df = pd.DataFrame({
        "user_id": user_ids,
        "signup_date": [d.date() for d in signup_dates],
        "country": countries,
        "age_group": age_groups,
        "preferred_device": preferred_device,
        "acquisition_channel": np.random.choice(
            ["Organic", "Paid Social", "Referral", "Partner", "Email"],
            n, p=[0.40, 0.25, 0.15, 0.12, 0.08]
        )
    })
    return df


def generate_content(n=N_CONTENT):
    print(f"Generating {n:,} content titles...")
    content_ids = [f"C{str(i).zfill(5)}" for i in range(1, n + 1)]
    titles = [f"Title_{i}" for i in range(1, n + 1)]  # placeholder; real titles not needed
    genres = np.random.choice(GENRES, n)
    content_types = np.random.choice(CONTENT_TYPES, n, p=[0.45, 0.40, 0.10, 0.05])
    durations = np.where(
        content_types == "Movie",
        np.random.randint(80, 180, n),
        np.where(
            content_types == "Series",
            np.random.randint(20, 60, n),          # episode length
            np.random.randint(40, 120, n)
        )
    )
    release_dates = random_dates(n, datetime(2018, 1, 1), END_DATE)

    df = pd.DataFrame({
        "content_id": content_ids,
        "title": titles,
        "genre": genres,
        "content_type": content_types,
        "duration_minutes": durations,
        "release_date": [d.date() for d in release_dates],
        "is_original": np.random.choice([True, False], n, p=[0.35, 0.65])
    })
    return df


def generate_subscriptions(users_df):
    print("Generating subscriptions (lifecycle)...")
    records = []
    for _, user in users_df.iterrows():
        user_id = user["user_id"]
        signup = pd.Timestamp(user["signup_date"])
        # Most users start with one plan; some upgrade/downgrade or churn and rejoin
        n_subs = np.random.choice([1, 2, 3], p=[0.70, 0.22, 0.08])
        current_start = signup

        for i in range(n_subs):
            plan = np.random.choice(PLANS, p=[0.40, 0.35, 0.25])
            # Tenure in months (realistic churn)
            tenure_months = max(1, int(np.random.exponential(8)))
            end = current_start + pd.DateOffset(months=tenure_months)
            if end > pd.Timestamp(END_DATE):
                end = pd.Timestamp(END_DATE)
                status = "Active"
            else:
                # Churn probability increases with tenure
                status = "Churned" if random.random() < 0.65 else "Active"
                if status == "Active":
                    end = pd.Timestamp(END_DATE)

            records.append({
                "subscription_id": f"S{len(records)+1:07d}",
                "user_id": user_id,
                "plan_type": plan,
                "plan_price": PLAN_PRICES[plan],
                "start_date": current_start.date(),
                "end_date": end.date() if status == "Churned" else None,
                "status": status,
                "billing_cycle": np.random.choice(["Monthly", "Annual"], p=[0.85, 0.15])
            })

            if status == "Churned":
                # Possible gap before next subscription
                gap = timedelta(days=int(np.random.exponential(30)))
                current_start = end + gap
                if current_start > pd.Timestamp(END_DATE):
                    break
            else:
                break  # still active

    df = pd.DataFrame(records)
    return df


def generate_viewing_sessions(users_df, content_df, n=N_VIEWING_SESSIONS):
    """Vectorized generation for speed (~120k rows in a few seconds)."""
    print(f"Generating {n:,} viewing sessions (vectorized)...")
    user_ids = users_df["user_id"].values
    content_ids = content_df["content_id"].values
    durations = content_df["duration_minutes"].values
    signup_dates = pd.to_datetime(users_df["signup_date"]).values

    # Sample users (with replacement)
    user_idx = np.random.randint(0, len(user_ids), size=n)
    chosen_users = user_ids[user_idx]
    chosen_signups = signup_dates[user_idx]

    # Days since signup (clip at least 1)
    end_np = np.datetime64(END_DATE)
    days_available = ((end_np - chosen_signups) / np.timedelta64(1, "D")).astype(int)
    days_available = np.maximum(days_available, 1)
    offset_days = (np.random.rand(n) * days_available).astype(int)
    session_dates = chosen_signups + offset_days.astype("timedelta64[D]")

    # Hours (evening peak)
    hour_probs = np.array([0.015]*6 + [0.025]*4 + [0.055]*6 + [0.085]*5 + [0.045]*3)
    hour_probs /= hour_probs.sum()
    hours = np.random.choice(24, size=n, p=hour_probs)
    minutes = np.random.randint(0, 60, size=n)

    # Build datetime
    session_start = pd.to_datetime(session_dates) + pd.to_timedelta(hours, unit="h") + pd.to_timedelta(minutes, unit="m")

    # Content & watch time
    content_idx = np.random.randint(0, len(content_ids), size=n)
    chosen_content = content_ids[content_idx]
    max_dur = durations[content_idx]
    watch_pct = np.clip(np.random.beta(2, 1.5, size=n), 0.05, 1.0)
    watch_minutes = np.maximum(1, (max_dur * watch_pct).astype(int))

    devices = np.random.choice(DEVICES, size=n, p=[0.42, 0.23, 0.18, 0.10, 0.07])

    df = pd.DataFrame({
        "session_id": [f"VS{i+1:07d}" for i in range(n)],
        "user_id": chosen_users,
        "content_id": chosen_content,
        "session_start": session_start,
        "watch_minutes": watch_minutes,
        "device": devices,
        "completion_pct": np.round(watch_pct * 100, 1)
    })
    df["session_date"] = df["session_start"].dt.date
    return df


def precompute_daily_active(users_df, sessions_df, subs_df):
    """Lightweight daily aggregates useful for Power BI MAU / DAU calculations."""
    print("Pre-computing daily active users & watch metrics...")
    sessions_df = sessions_df.copy()
    sessions_df["session_date"] = pd.to_datetime(sessions_df["session_date"])

    daily = (
        sessions_df
        .groupby("session_date")
        .agg(
            dau=("user_id", "nunique"),
            total_sessions=("session_id", "count"),
            total_watch_minutes=("watch_minutes", "sum"),
            avg_watch_per_session=("watch_minutes", "mean")
        )
        .reset_index()
        .rename(columns={"session_date": "date"})
    )
    daily["avg_watch_per_session"] = daily["avg_watch_per_session"].round(1)
    return daily


def main():
    print("=" * 60)
    print("OTT Subscriber & Content Engagement – Data Generator")
    print("=" * 60)

    users = generate_users()
    content = generate_content()
    subscriptions = generate_subscriptions(users)
    sessions = generate_viewing_sessions(users, content)
    daily = precompute_daily_active(users, sessions, subscriptions)

    # Write CSVs
    users.to_csv(OUTPUT_DIR / "users.csv", index=False)
    content.to_csv(OUTPUT_DIR / "content.csv", index=False)
    subscriptions.to_csv(OUTPUT_DIR / "subscriptions.csv", index=False)
    sessions.to_csv(OUTPUT_DIR / "viewing_sessions.csv", index=False)
    daily.to_csv(OUTPUT_DIR / "daily_active_users.csv", index=False)

    print("\n" + "=" * 60)
    print("Files written to:", OUTPUT_DIR)
    print(f"  users.csv              : {len(users):,} rows")
    print(f"  content.csv            : {len(content):,} rows")
    print(f"  subscriptions.csv      : {len(subscriptions):,} rows")
    print(f"  viewing_sessions.csv   : {len(sessions):,} rows  ← 100K+ target")
    print(f"  daily_active_users.csv : {len(daily):,} rows")
    print("=" * 60)
    print("Ready for SQL modeling, cohort analysis & Power BI import.")


if __name__ == "__main__":
    main()
