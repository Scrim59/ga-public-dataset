# =========================
#import libraries
import pandas as pd
import re
from pandasql import sqldf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
# =========================
# load data to dataframe ga360
ga360 = pd.read_csv("solution/input_csv/ga_public_dataset.csv")

# =========================
#POINT 3 - QUERIES 

#Q1:select the sum of visits( use  alias totalVisits), the sum of transactions (use alias totalTransaction), the sum of bounces(use totalBounce) 
#    for the cities located in the US and EU and order by transaction in descending order and limit to 20 the results.
q1 = """
SELECT
    city,
    SUM(visits) AS totalVisits,
    SUM(transactions) AS totalTransaction,
    SUM(bounces) AS totalBounce
FROM ga360
WHERE
    country = 'United States'
    OR continent = 'Europe'
GROUP BY city
ORDER BY totalTransaction DESC
LIMIT 20
"""

city_agg = sqldf(q1, {"ga360": ga360})

print("\n--- Top cities (US + EU) ---")
print(city_agg)

#Output has undefined cities - we can celan data to have meaningful dataframe:

# clean city column
ga360_clean = ga360.copy()
ga360_clean = ga360_clean[ga360_clean["city"].notna()]
ga360_clean = ga360_clean[~ga360_clean["city"].isin(["(not set)", "not available in demo dataset"])]
city_agg_df = sqldf(q1, {"ga360": ga360_clean})

print("\n--- Top cities (US + EU) ---")
print(city_agg_df)

#Q2:find out the most used browsers by city in the US and EU, order by browser count in descending order and limit by 20 results.
q2 = """
SELECT
    city,
    browser,
    COUNT(*) AS browserCount
FROM ga360
WHERE
    country = 'United States'
    OR continent = 'Europe'
GROUP BY city, browser
ORDER BY browserCount DESC
LIMIT 20
"""

browser_city_df = sqldf(q2, {"ga360": ga360_clean})

print("\n--- Top browsers by city (US + EU) ---")
print(browser_city_df)
# =========================
#POINT 4 - DATE
# convert date from YYYYMMDD -> datetime YYYY-MM-DD
ga_360_elt = ga360.copy()

ga_360_elt["date"] = pd.to_datetime(
    ga_360_elt["date"],
    format="%Y%m%d",
    errors="coerce"
)

print("\n--- ELT dataframe date check ---")
print(ga_360_elt["date"].head())
print("date dtype:", ga_360_elt["date"].dtype)

# =========================
#POINT 5 - EMAIL
#add a new column to the ga_360_elt datafreame. The new field name is "personal_information". 
email_regex = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

def detect_pii(value):
    if pd.isna(value):
        return "no pii"
    if email_regex.search(str(value)):
        return "pii found"
    return "no pii"

ga_360_elt["personal_information"] = ga_360_elt["fullVisitorId"].apply(detect_pii)

print("\n--- PII column check ---")
print(ga_360_elt["personal_information"].value_counts())

# =========================
# POINT 6 — EXPORT CSV


output_path = "solution/output_csv/transformed_df.csv"

ga_360_elt.to_csv(
    output_path,
    sep=";",
    encoding="utf-8",
    index=False
)

print("\nExported transformed dataframe to:")
print(output_path)

# =========================
# POINT 7 — PLOTLY

# highlight max values
max_tx = city_agg_df["totalTransaction"].max()
tx_colors = [
    "#0d3b66" if v == max_tx else "#9bbcd1"
    for v in city_agg_df["totalTransaction"]
]

max_browser = browser_city_df["browserCount"].max()
browser_colors = [
    "#e76f51" if v == max_browser else "#ffb703"
    for v in browser_city_df["browserCount"]
]

fig = make_subplots(
    rows=1,
    cols=2,
    subplot_titles=[
        "Transactions by City (US + EU)",
        "Most Used Browsers by City (US + EU)"
    ]
)

# first chart 
fig.add_trace(
    go.Bar(
        x=city_agg_df["totalTransaction"],
        y=city_agg_df["city"],
        orientation="h",
        marker_color=tx_colors,
        name="Transactions"
    ),
    row=1,
    col=1
)

# second chart
fig.add_trace(
    go.Bar(
        x=browser_city_df["city"] + " - " + browser_city_df["browser"],
        y=browser_city_df["browserCount"],
        marker_color=browser_colors,
        name="Browser usage"
    ),
    row=1,
    col=2
)

fig.update_layout(
    plot_bgcolor="white",
    paper_bgcolor="white",
    font=dict(color="black"),
    height=600,
    showlegend=False
)

fig.update_xaxes(
    showgrid=True,
    gridcolor="rgba(0,0,0,0.15)",
    linecolor="black"
)

fig.update_yaxes(
    showgrid=True,
    gridcolor="rgba(0,0,0,0.15)",
    linecolor="black"
)

fig.write_html("solution/output_csv/query_results.html")

# =========================
# POINT 8 — PLOTLY BAR 

pii_counts = (
    ga_360_elt["personal_information"]
    .value_counts()
    .reset_index()
)

pii_counts.columns = ["personal_information", "count"]

pii_color_map = {
    "no pii": "#f4a6a6",      # red
    "pii found": "#a8ddb5"    # green
}

fig_pii = go.Figure(
    data=[
        go.Bar(
            x=pii_counts["personal_information"],
            y=pii_counts["count"],
            marker_color=[
                pii_color_map[val] for val in pii_counts["personal_information"]
            ]
        )
    ]
)

fig_pii.update_layout(
    title="Personal Information Detection",
    plot_bgcolor="white",
    paper_bgcolor="white",
    font=dict(color="black")
)

fig_pii.update_xaxes(
    showgrid=True,
    gridcolor="rgba(0,0,0,0.15)",
    linecolor="black"
)

fig_pii.update_yaxes(
    showgrid=True,
    gridcolor="rgba(0,0,0,0.15)",
    linecolor="black"
)

fig_pii.write_html("solution/output_csv/pii_counts.html")

print("DONE — all outputs saved to solution/output_csv/")