"""charts.py - the 12 chart functions used by the notebook AND the website.
Every chart_N(h, c) gets the housing table h and the crash table c and returns a Plotly figure."""
import os
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ZIP centroids (ZIP locations) are only needed for the hotspot chart (Q2)
HERE = os.path.dirname(os.path.abspath(__file__))
ZIP_CENTROIDS = pd.read_csv(os.path.join(HERE, "data", "zip_centroids.csv"))

KEYS = ["zip_code", "borough", "year", "month"]
H_NUMBERS = ["filings", "new_building_filings", "new_units", "total_cost"]
C_NUMBERS = ["crashes", "injury_crashes", "injured", "killed", "ped_cyc_injured"]
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def no_data(message="No data for the selected filters"):
    """An empty chart with a message (shown when the filters leave nothing to draw)."""
    fig = go.Figure()
    fig.add_annotation(text=message, x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False, font=dict(size=16))
    fig.update_layout(xaxis_visible=False, yaxis_visible=False, height=420)
    return fig


def join_data(h, c):
    """One row per ZIP x year x month with housing AND crash numbers (the same join as sections 5-6)."""
    h_month = h.groupby(KEYS, as_index=False)[H_NUMBERS].sum()
    c_month = c.groupby(KEYS, as_index=False)[C_NUMBERS].sum()
    return h_month.merge(c_month, on=KEYS, how="outer").fillna(0)


def zip_table(joined):
    """One row per ZIP code (totals for the selected period)."""
    z = joined.groupby(["zip_code", "borough"], as_index=False)[H_NUMBERS + C_NUMBERS].sum()
    z["zip_label"] = z["zip_code"].astype(int).astype(str)
    return z


def add_trend_line(fig, x, y):
    """Draw a straight best-fit line on a scatter plot and return the correlation r."""
    ok = x.notna() & y.notna()
    if ok.sum() < 3 or x[ok].nunique() < 2:
        return None
    slope, intercept = np.polyfit(x[ok], y[ok], 1)
    xs = np.linspace(x[ok].min(), x[ok].max(), 50)
    fig.add_trace(go.Scatter(x=xs, y=slope * xs + intercept, mode="lines", name="Best-fit line", line=dict(color="black", dash="dash")))
    return float(np.corrcoef(x[ok], y[ok])[0, 1])


def show_r(r):
    return "n/a" if r is None or pd.isna(r) else f"{r:.2f}"


def spearman(s1, s2):
    """Spearman rank correlation using ranks (does not require scipy)."""
    return s1.rank().corr(s2.rank())


def key_findings(h, c):
    """A few plain-English findings calculated from the data on screen (used in the notebook story and on the website)."""
    joined = join_data(h, c)
    if joined.empty:
        return ["No data for the selected filters."]
    z = zip_table(joined)
    lines = [f"**{int(z['filings'].sum()):,}** construction filings and **{int(z['crashes'].sum()):,}** crashes "
             f"({int(z['injured'].sum()):,} people injured, {int(z['killed'].sum()):,} killed) in **{len(z)}** ZIP codes."]
    b = z.groupby("borough")[["filings", "crashes"]].sum()
    b = b[b["filings"] > 0]
    if not b.empty:
        ratio = (b["crashes"] / b["filings"] * 100).sort_values(ascending=False)
        lines.append(f"**{ratio.index[0].title()}** has the most crashes per 100 filings ({ratio.iloc[0]:,.0f}) and "
                     f"**{ratio.index[-1].title()}** the fewest ({ratio.iloc[-1]:,.0f}).")
    if len(z) >= 5:
        rho = spearman(z["filings"], z["crashes"])
        lines.append(f"Across ZIP codes, filings and crashes have a rank correlation of **{show_r(rho)}**. "
                     "Big, busy ZIP codes tend to have both, so this does **not** show that construction causes crashes.")
    return lines


# ---------------------------------------------------------------- Q1  (Tasneem)
def chart_1(h, c):
    joined = join_data(h, c)
    b = joined.groupby("borough", as_index=False)[["new_units", "injured"]].sum()
    if b["new_units"].sum() == 0 or b["injured"].sum() == 0:
        return no_data("Not enough new-unit and injury data for these filters")
    # turn each borough's numbers into a share of the city total
    b["Share of new housing units (%)"] = b["new_units"] / b["new_units"].sum() * 100
    b["Share of people injured (%)"] = b["injured"] / b["injured"].sum() * 100
    long = b.melt(id_vars="borough", value_vars=["Share of new housing units (%)", "Share of people injured (%)"],
                  var_name="measure", value_name="share")
    return px.bar(long, x="borough", y="share", color="measure", barmode="group", text_auto=".0f",
                  labels={"share": "% of city total", "borough": "Borough", "measure": ""},
                  title="Q1 - Each borough's share of new housing units vs share of people injured")


# ---------------------------------------------------------------- Q2  (Tasneem)
def chart_2(h, c):
    z = zip_table(join_data(h, c))
    z = z.merge(ZIP_CENTROIDS, on="zip_code", how="left").dropna(subset=["latitude", "longitude"])   # ZIPs without a location are not drawn
    z = z[(z["filings"] > 0) | (z["crashes"] > 0)].copy()
    if len(z) < 8:
        return no_data("Need at least 8 ZIP codes")
    # "high" = in the top 25% of ZIP codes for that measure
    high_construction = z["filings"] >= z["filings"].quantile(0.75)
    high_crashes = z["crashes"] >= z["crashes"].quantile(0.75)
    hotspot, only_construction, only_crashes, rest = ("Hotspot: high construction AND high crashes", "High construction only",
                                                      "High crashes only", "Everything else")
    z["group"] = np.select([high_construction & high_crashes, high_construction, high_crashes],
                           [hotspot, only_construction, only_crashes], default=rest)
    fig = px.scatter(z, x="longitude", y="latitude", color="group", size="crashes", size_max=26, opacity=0.75,
                     color_discrete_map={hotspot: "#d62728", only_construction: "#1f77b4", only_crashes: "#ff7f0e", rest: "#c8c8c8"},
                     category_orders={"group": [hotspot, only_construction, only_crashes, rest]},
                     hover_name="zip_label", hover_data={"borough": True, "filings": ":,", "crashes": ":,", "longitude": False, "latitude": False},
                     labels={"group": ""}, height=620,
                     title="Q2 - ZIP-code hotspots: bubble size = crashes, colour = construction/crash group")
    # borough names at the average position of their ZIP codes, to help the reader find their way
    names = z.groupby("borough")[["longitude", "latitude"]].mean().reset_index()
    fig.add_trace(go.Scatter(x=names["longitude"], y=names["latitude"], text=names["borough"].str.title(), mode="text",
                             textfont=dict(size=13, color="black"), showlegend=False, hoverinfo="skip"))
    # keep the shape of the city right: 1 degree of latitude is about 1.32x longer than 1 degree of longitude here
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, scaleanchor="x", scaleratio=1 / np.cos(np.radians(40.7)))
    return fig


# ---------------------------------------------------------------- Q3  (Sara)
def chart_3(h, c):
    joined = join_data(h, c)
    monthly = joined.groupby(["year", "month"], as_index=False)[["filings", "crashes"]].sum()
    if len(monthly) < 3:
        return no_data("Need at least 3 months of data")
    monthly["date"] = pd.to_datetime(dict(year=monthly["year"].astype(int), month=monthly["month"].astype(int), day=1))
    monthly = monthly.sort_values("date")
    # index each series to its own average (= 100) so both fit on one axis
    monthly["Construction filings"] = monthly["filings"] / (monthly["filings"].mean() or np.nan) * 100
    monthly["Crashes"] = monthly["crashes"] / (monthly["crashes"].mean() or np.nan) * 100
    long = monthly.melt(id_vars="date", value_vars=["Construction filings", "Crashes"], var_name="measure", value_name="index")
    r = monthly["filings"].corr(monthly["crashes"])
    return px.line(long, x="date", y="index", color="measure", markers=True,
                   labels={"index": "Index (own average = 100)", "date": "Month", "measure": ""},
                   title=f"Q3 - Monthly construction filings vs crashes (correlation r = {show_r(r)})")


# ---------------------------------------------------------------- Q4  (Sara)
def chart_4(h, c):
    joined = join_data(h, c)
    if joined.empty:
        return no_data()
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Construction filings", "Crashes with injuries"), horizontal_spacing=0.14)
    for position, (column, colours) in enumerate([("filings", "Blues"), ("injury_crashes", "Reds")], start=1):
        table = joined.pivot_table(index="year", columns="month", values=column, aggfunc="sum").reindex(columns=range(1, 13))
        fig.add_trace(go.Heatmap(z=table.values, x=MONTH_NAMES, y=[str(y) for y in table.index], colorscale=colours,
                                 colorbar=dict(x=0.43 if position == 1 else 1.02, len=0.9),
                                 hovertemplate="%{y} %{x}: %{z:,.0f}<extra></extra>"), row=1, col=position)
    fig.update_yaxes(type="category")
    fig.update_layout(title="Q4 - Busiest months: filings (left) and injury crashes (right)")
    return fig


# ---------------------------------------------------------------- Q5  (Ziad)
def chart_5(h, c):
    z = zip_table(join_data(h, c))
    z = z[(z["crashes"] > 0) | (z["new_units"] > 0)]
    if len(z) < 3:
        return no_data()
    fig = px.scatter(z, x="new_units", y="crashes", color="borough", hover_name="zip_label",
                     hover_data={"filings": ":,", "new_units": ":,", "crashes": ":,"},
                     labels={"new_units": "Net new dwelling units filed", "crashes": "Crashes"})
    r = add_trend_line(fig, z["new_units"], z["crashes"])
    rho = spearman(z["new_units"], z["crashes"])
    fig.update_layout(title=f"Q5 - New housing units vs crashes per ZIP (r = {show_r(r)}, Spearman = {show_r(rho)})")
    return fig


# ---------------------------------------------------------------- Q6  (Ziad)
def chart_6(h, c):
    z = zip_table(join_data(h, c))
    z = z[z["crashes"] >= 10].copy()
    if len(z) < 8:
        return no_data("Need at least 8 ZIP codes with 10 or more crashes")
    z["injured_per_100_crashes"] = z["injured"] / z["crashes"] * 100
    # four equal groups of ZIP codes, from least to most construction
    z["construction_level"] = pd.qcut(z["filings"].rank(method="first"), 4, labels=["1 (lowest)", "2", "3", "4 (highest)"])
    fig = px.box(z, x="construction_level", y="injured_per_100_crashes", color="construction_level", points="all",
                 hover_name="zip_label", hover_data={"borough": True, "filings": ":,", "construction_level": False},
                 labels={"construction_level": "Construction filings (ZIP group)", "injured_per_100_crashes": "People injured per 100 crashes"},
                 title="Q6 - Are crashes more severe in ZIP codes with more construction?")
    fig.update_layout(showlegend=False)
    return fig


# ---------------------------------------------------------------- Q7  (Abdelrahman)
def chart_7(h, c):
    joined = join_data(h, c)
    monthly = joined.groupby(["year", "month"], as_index=False)[["filings", "crashes"]].sum()
    if len(monthly) < 10:
        return no_data("Need at least 10 months of data")
    monthly["date"] = pd.to_datetime(dict(year=monthly["year"].astype(int), month=monthly["month"].astype(int), day=1))
    monthly = monthly.set_index("date").sort_index().asfreq("MS", fill_value=0)       # one row for every month
    rows = []
    for delay in range(0, 7):
        # shift(-delay) moves the crash numbers `delay` months earlier, so each row pairs filings with LATER crashes
        rows.append({"months_later": delay, "correlation": monthly["filings"].corr(monthly["crashes"].shift(-delay))})
    result = pd.DataFrame(rows)
    fig = px.bar(result, x="months_later", y="correlation", text_auto=".2f",
                 labels={"months_later": "Crashes measured this many months after the filings", "correlation": "Correlation"},
                 title="Q7 - Do crashes follow construction filings? (citywide monthly correlation by delay)")
    fig.update_xaxes(dtick=1)
    return fig


# ---------------------------------------------------------------- Q8  (Abdelrahman)
def chart_8(h, c):
    if h.empty or c.empty:
        return no_data()
    filings = h.groupby(["zip_code", "year", "job_type"], as_index=False)["filings"].sum()
    crashes = c.groupby(["zip_code", "year"], as_index=False)["crashes"].sum()
    both = filings.merge(crashes, on=["zip_code", "year"], how="left").fillna({"crashes": 0})
    # average crashes per filing of each job type (a ZIP-year with more filings counts more)
    both["crashes_x_filings"] = both["crashes"] * both["filings"]
    result = both.groupby("job_type", as_index=False)[["crashes_x_filings", "filings"]].sum()
    result["avg_crashes"] = result["crashes_x_filings"] / result["filings"]
    result = result.sort_values("avg_crashes")
    return px.bar(result, x="avg_crashes", y="job_type", orientation="h", text_auto=".0f", hover_data={"filings": ":,"},
                  labels={"avg_crashes": "Average crashes in the same ZIP and year", "job_type": "Job type"},
                  title="Q8 - Which kinds of jobs are filed in the most crash-prone ZIP codes?")


# ---------------------------------------------------------------- Q9  (Yassin)
def chart_9(h, c):
    z = zip_table(join_data(h, c))
    z = z[z["ped_cyc_injured"] > 0].nlargest(15, "ped_cyc_injured")
    if z.empty:
        return no_data()
    fig = px.bar(z, x="zip_label", y="ped_cyc_injured", color="filings", color_continuous_scale="Viridis",
                 hover_data={"borough": True, "crashes": ":,", "filings": ":,", "zip_label": False},
                 labels={"zip_label": "ZIP code", "ped_cyc_injured": "Pedestrians + cyclists injured", "filings": "Construction filings"},
                 title="Q9 - Top 15 ZIP codes for pedestrian and cyclist injuries (colour = construction filings)")
    fig.update_xaxes(type="category")
    return fig


# ---------------------------------------------------------------- Q10  (Yassin)
def chart_10(h, c):
    z = zip_table(join_data(h, c))
    z = z[(z["filings"] >= 5) & (z["crashes"] >= 10)].copy()
    z["avg_cost_per_filing"] = z["total_cost"] / z["filings"]
    z["injured_per_100_crashes"] = z["injured"] / z["crashes"] * 100
    z = z[z["avg_cost_per_filing"] > 0]
    if len(z) < 3:
        return no_data("Need ZIP codes with 5+ filings and 10+ crashes")
    rho = spearman(z["avg_cost_per_filing"], z["injured_per_100_crashes"])
    return px.scatter(z, x="avg_cost_per_filing", y="injured_per_100_crashes", size="crashes", color="borough", log_x=True,
                      hover_name="zip_label", size_max=30, hover_data={"filings": ":,", "crashes": ":,"},
                      labels={"avg_cost_per_filing": "Average project cost per filing ($, log scale)",
                              "injured_per_100_crashes": "People injured per 100 crashes"},
                      title=f"Q10 - Project size vs crash severity (Spearman = {show_r(rho)})")


# ---------------------------------------------------------------- Q11  (Youssef)
def train_logistic(X, y, steps=500, learning_rate=0.1):
    """Logistic regression with gradient descent. Returns weights w and bias b."""
    w, b = np.zeros(X.shape[1]), 0.0
    for _ in range(steps):
        p = 1 / (1 + np.exp(-(X @ w + b)))                 # predicted probability of "yes"
        w -= learning_rate * (X.T @ (p - y)) / len(y)      # move the weights downhill
        b -= learning_rate * (p - y).mean()
    return w, b


def chart_11(h, c):
    joined = join_data(h, c)
    if joined.empty:
        return no_data()
    joined["date"] = pd.to_datetime(dict(year=joined["year"].astype(int), month=joined["month"].astype(int), day=1))
    # 1) one row for every ZIP in every month (months with no events become zeros)
    grid = pd.MultiIndex.from_product([joined["zip_code"].unique(), pd.date_range(joined["date"].min(), joined["date"].max(), freq="MS")],
                                      names=["zip_code", "date"]).to_frame(index=False)
    monthly = joined.groupby(["zip_code", "date"], as_index=False)[["filings", "new_building_filings", "new_units", "injury_crashes"]].sum()
    data = grid.merge(monthly, on=["zip_code", "date"], how="left").fillna(0)
    # 2) target and inputs
    y = (data["injury_crashes"] > 0).astype(float).values
    if len(data) < 200 or y.min() == y.max():
        return no_data("Need more months/ZIP codes (and both yes and no cases) for the model")
    X = np.log1p(data[["filings", "new_building_filings", "new_units"]].values)
    X = (X - X.mean(axis=0)) / np.where(X.std(axis=0) == 0, 1, X.std(axis=0))
    # 3) 80% train / 20% test (fixed seed so the result is repeatable)
    order = np.random.default_rng(42).permutation(len(data))
    cut = int(0.8 * len(data))
    train, test = order[:cut], order[cut:]
    w, b = train_logistic(X[train], y[train])
    probability = 1 / (1 + np.exp(-(X[test] @ w + b)))
    accuracy = ((probability > 0.5) == (y[test] == 1)).mean()
    baseline = max(y[test].mean(), 1 - y[test].mean())
    # 4) compare actual vs predicted share by number of filings
    result = pd.DataFrame({"filings": data["filings"].values[test], "actual": y[test], "predicted": probability})
    result["filings_group"] = pd.cut(result["filings"], [-1, 0, 1, 3, 6, np.inf], labels=["0", "1", "2-3", "4-6", "7+"])
    summary = result.groupby("filings_group", observed=True)[["actual", "predicted"]].mean() * 100
    long = summary.reset_index().melt(id_vars="filings_group", var_name="what", value_name="share")
    long["what"] = long["what"].map({"actual": "Actual share with an injury crash", "predicted": "Model's predicted share"})
    return px.bar(long, x="filings_group", y="share", color="what", barmode="group", text_auto=".0f",
                  labels={"filings_group": "Construction filings in the ZIP that month", "share": "% of ZIP-months", "what": ""},
                  title=f"Q11 - Predicting an injury crash from filings: accuracy {accuracy:.0%} vs {baseline:.0%} for always guessing the common answer")


# ---------------------------------------------------------------- Q12  (Youssef)
def chart_12(h, c):
    z = zip_table(join_data(h, c))
    z = z[(z["filings"] > 0) | (z["crashes"] > 0)]
    if len(z) < 8:
        return no_data("Need at least 8 ZIP codes")
    # label each ZIP: more filings than the median ZIP = high construction
    z["group"] = np.where(z["filings"] > z["filings"].median(), "High-construction ZIPs", "Low-construction ZIPs")
    c = c.copy()
    c["group"] = c["zip_code"].map(z.set_index("zip_code")["group"])
    by_cause = c.dropna(subset=["group"]).groupby(["group", "factor"], as_index=False)["crashes"].sum()
    by_cause["share"] = by_cause["crashes"] / by_cause.groupby("group")["crashes"].transform("sum") * 100
    by_cause = by_cause[~by_cause["factor"].isin(["Unspecified", "Other", "Does Not Apply"])]
    top_causes = by_cause.groupby("factor")["crashes"].sum().nlargest(6).index
    by_cause = by_cause[by_cause["factor"].isin(top_causes)]
    if by_cause.empty:
        return no_data()
    return px.bar(by_cause, x="factor", y="share", color="group", barmode="group", text_auto=".1f",
                  labels={"factor": "Contributing factor (vehicle 1)", "share": "% of the group's crashes", "group": ""},
                  title="Q12 - Main crash causes in high- vs low-construction ZIP codes")
