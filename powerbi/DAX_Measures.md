# Power BI DAX Measures – OTT Subscriber & Content Engagement Dashboard

Import the five CSV files from `/data` (or connect to the SQL tables).  
Recommended model relationships:

```
users[user_id]          1 → *  subscriptions[user_id]
users[user_id]          1 → *  viewing_sessions[user_id]
content[content_id]     1 → *  viewing_sessions[content_id]
```

Create a **Date** table (or use `daily_active_users[date]`) and mark it as a date table.

---

## Core KPI Measures

### Monthly Active Users (MAU)
```dax
MAU = 
CALCULATE(
    DISTINCTCOUNT(viewing_sessions[user_id]),
    ALLEXCEPT(DateTable, DateTable[YearMonth])
)
```
Or simpler with a month column on the date table:
```dax
MAU = DISTINCTCOUNT(viewing_sessions[user_id])
```
(Use a month hierarchy / filter context.)

### Daily Active Users (DAU)
```dax
DAU = DISTINCTCOUNT(viewing_sessions[user_id])
```

### Average Watch-Time per Session (minutes)
```dax
Avg Watch Minutes = AVERAGE(viewing_sessions[watch_minutes])
```

### Total Watch Hours
```dax
Total Watch Hours = SUM(viewing_sessions[watch_minutes]) / 60
```

### Churn Rate (simplified – requires status flag)
```dax
Churned Subscribers = 
CALCULATE(
    DISTINCTCOUNT(subscriptions[user_id]),
    subscriptions[status] = "Churned"
)

Active Subscribers = 
CALCULATE(
    DISTINCTCOUNT(subscriptions[user_id]),
    subscriptions[status] = "Active"
)

Churn Rate % = 
DIVIDE([Churned Subscribers], [Churned Subscribers] + [Active Subscribers], 0)
```

For a proper monthly churn rate you will typically use a snapshot or the SQL query in `02_kpi_queries.sql` and import the result as a table.

### Completion Rate
```dax
Avg Completion % = AVERAGE(viewing_sessions[completion_pct])
```

### Sessions per User (selected period)
```dax
Sessions per MAU = 
DIVIDE(
    COUNTROWS(viewing_sessions),
    [MAU],
    0
)
```

---

## Suggested Visuals for the Dashboard

| Visual                      | Fields                                      | Purpose                              |
|----------------------------|---------------------------------------------|--------------------------------------|
| Card                       | MAU, Churn Rate %, Avg Watch Minutes        | KPI header                           |
| Line chart                 | Date + MAU / DAU                            | Trend of engagement                  |
| Clustered bar              | Plan Type + Avg Watch Minutes               | Plan-level engagement                |
| Donut                      | Device + Sessions                           | Device mix                           |
| Matrix / Heatmap           | Cohort Month × Weeks Since Signup           | Retention (import cohort matrix)     |
| Table                      | Genre + Total Watch Hours + Completion %    | Content performance                  |
| Funnel or stacked bar      | Acquisition Channel + New Users / Retention | Campaign targeting                   |

---

## Import Tips

1. Load all CSVs via **Get Data → Text/CSV**.
2. In Power Query, set correct data types (dates, decimals).
3. Create a calculated column on `viewing_sessions`:
   ```dax
   Session Month = FORMAT(viewing_sessions[session_date], "YYYY-MM")
   ```
4. For the retention heatmap, import `docs/cohort_retention_matrix.csv` as a separate table (unpivot if needed).
5. Publish to Power BI Service and share with stakeholders.
