-- ============================================================
-- Core Operational KPIs for Power BI / SQL modeling
-- ============================================================

-- 1. Monthly Active Users (MAU)
--    Distinct users who had ≥1 viewing session in the calendar month
SELECT
    DATE_TRUNC('month', session_date)::DATE AS month,
    COUNT(DISTINCT user_id) AS mau
FROM viewing_sessions
GROUP BY 1
ORDER BY 1;


-- 2. Churn Rate (monthly)
--    Users whose last subscription ended in the month /
--    Users who were active at the start of the month
WITH monthly_churn AS (
    SELECT
        DATE_TRUNC('month', end_date)::DATE AS month,
        COUNT(DISTINCT user_id) AS churned_users
    FROM subscriptions
    WHERE status = 'Churned' AND end_date IS NOT NULL
    GROUP BY 1
),
monthly_active_start AS (
    SELECT
        DATE_TRUNC('month', d.month)::DATE AS month,
        COUNT(DISTINCT s.user_id) AS active_at_start
    FROM generate_series('2023-01-01'::DATE, '2025-06-01'::DATE, '1 month') AS d(month)
    JOIN subscriptions s
      ON s.start_date < d.month
     AND (s.end_date IS NULL OR s.end_date >= d.month)
    GROUP BY 1
)
SELECT
    a.month,
    a.active_at_start,
    COALESCE(c.churned_users, 0) AS churned_users,
    ROUND(100.0 * COALESCE(c.churned_users, 0) / NULLIF(a.active_at_start, 0), 2) AS churn_rate_pct
FROM monthly_active_start a
LEFT JOIN monthly_churn c ON a.month = c.month
ORDER BY 1;


-- 3. Average Watch-Time per Session
SELECT
    ROUND(AVG(watch_minutes), 1) AS avg_watch_minutes_per_session,
    ROUND(AVG(completion_pct), 1) AS avg_completion_pct
FROM viewing_sessions;


-- 4. Watch-Time per Session by Plan (join via active subscription)
SELECT
    s.plan_type,
    COUNT(v.session_id) AS sessions,
    ROUND(AVG(v.watch_minutes), 1) AS avg_watch_min,
    ROUND(AVG(v.completion_pct), 1) AS avg_completion_pct
FROM viewing_sessions v
JOIN subscriptions s
  ON v.user_id = s.user_id
 AND v.session_date >= s.start_date
 AND (s.end_date IS NULL OR v.session_date <= s.end_date)
GROUP BY s.plan_type
ORDER BY avg_watch_min DESC;


-- 5. Content Engagement – Top Genres by Watch Minutes
SELECT
    c.genre,
    COUNT(v.session_id) AS sessions,
    SUM(v.watch_minutes) AS total_watch_minutes,
    ROUND(AVG(v.completion_pct), 1) AS avg_completion
FROM viewing_sessions v
JOIN content c ON v.content_id = c.content_id
GROUP BY c.genre
ORDER BY total_watch_minutes DESC;


-- 6. Device Split of Engagement
SELECT
    device,
    COUNT(*) AS sessions,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_of_sessions,
    ROUND(AVG(watch_minutes), 1) AS avg_watch_min
FROM viewing_sessions
GROUP BY device
ORDER BY sessions DESC;


-- 7. New Subscriber Acquisition by Channel (cohort base)
SELECT
    DATE_TRUNC('month', u.signup_date)::DATE AS signup_month,
    u.acquisition_channel,
    COUNT(*) AS new_users
FROM users u
GROUP BY 1, 2
ORDER BY 1, 3 DESC;
