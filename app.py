"""app.py - the interactive website (Dash).
Authors: Youssef (app + Generate Report), Ziad (dropdowns + filters), Sara (search mode),
         Yassin (layout, KPI cards, testing), Tasneem (story text).
Run locally:  python app.py   then open http://127.0.0.1:8050
"""
import os
import re
import pandas as pd
from dash import Dash, dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate

import charts

# ------------------------------------------------------------ data (small tables created by the notebook)
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
H = pd.read_csv(os.path.join(DATA_DIR, "housing_agg.csv.gz"))
C = pd.read_csv(os.path.join(DATA_DIR, "crash_agg.csv.gz"))

YEARS = sorted(set(H["year"]) | set(C["year"]))
BOROUGHS = sorted(set(H["borough"]) | set(C["borough"]))
JOB_TYPES = sorted(H["job_type"].unique())
FACTORS = sorted(C["factor"].unique())

# the 12 charts: (number, team member, question, function)
CHARTS = [
    (1, "Tasneem", "Does each borough's share of new housing match its share of people injured in crashes?", charts.chart_1),
    (2, "Tasneem", "Which ZIP codes are hotspots for both construction and crashes, and where are they?", charts.chart_2),
    (3, "Sara", "Do monthly construction filings and monthly crashes move together over time?", charts.chart_3),
    (4, "Sara", "Which months of the year are busiest for filings and for injury crashes?", charts.chart_4),
    (5, "Ziad", "Do ZIP codes with more new housing units also have more crashes?", charts.chart_5),
    (6, "Ziad", "Are crashes more severe in ZIP codes with more construction?", charts.chart_6),
    (7, "Abdelrahman", "Do crashes rise in the months after a spike in construction filings?", charts.chart_7),
    (8, "Abdelrahman", "Which types of construction jobs are filed in the most crash-prone ZIP codes?", charts.chart_8),
    (9, "Yassin", "Which ZIP codes have the most pedestrian and cyclist injuries, and how much construction do they have?", charts.chart_9),
    (10, "Yassin", "Do ZIP codes with bigger (costlier) construction projects have more severe crashes?", charts.chart_10),
    (11, "Youssef", "Can a month's construction filings predict whether a ZIP code has an injury crash that month?", charts.chart_11),
    (12, "Youssef", "Are the main crash causes different in high- vs low-construction ZIP codes?", charts.chart_12),
]

# ------------------------------------------------------------ filters (Ziad)
def apply_filters(boroughs, years, job_types, factors):
    """Filter the housing table (borough, year, job type) and the crash table (borough, year, factor). Empty = no filter."""
    h, c = H, C
    if boroughs:
        h, c = h[h["borough"].isin(boroughs)], c[c["borough"].isin(boroughs)]
    if years:
        h, c = h[h["year"].isin(years)], c[c["year"].isin(years)]
    if job_types:
        h = h[h["job_type"].isin(job_types)]
    if factors:
        c = c[c["factor"].isin(factors)]
    return h, c


# ------------------------------------------------------------ search mode (Sara)
FACTOR_WORDS = {"speed": "speed", "distract": "distraction", "alcohol": "alcohol", "following": "following", "yield": "yield"}

def parse_search(text, years, job_types, factors):
    """Turn a query like 'Brooklyn 2022 new buildings speeding' into dropdown choices."""
    t = text.lower().replace("new construction", "new building")
    found_boroughs = [b for b in BOROUGHS if b.lower().split()[0] in t]                 # 'staten' finds STATEN ISLAND
    found_years = [int(y) for y in re.findall(r"\b(20\d{2})\b", t) if int(y) in years]
    found_jobs = [j for j in job_types if j.lower() in t]                              # 'new buildings' contains 'new building'
    found_factors = [f for f in factors if any(word in t and needle in f.lower() for word, needle in FACTOR_WORDS.items())]
    return {"boroughs": found_boroughs, "years": found_years, "job_types": found_jobs, "factors": found_factors}


# ------------------------------------------------------------ page layout (Yassin)
BLUE = "#1f4e79"
CARD = {"background": "white", "borderRadius": "10px", "padding": "14px", "boxShadow": "0 1px 4px rgba(0,0,0,0.12)"}

def dropdown(component_id, label, options):
    return html.Div([html.Label(label, style={"fontWeight": "600"}),
                     dcc.Dropdown(id=component_id, options=[{"label": str(o), "value": o} for o in options], multi=True, placeholder="All")],
                    style={"flex": "1", "minWidth": "220px"})

def kpi_card(title, value):
    return html.Div([html.Div(title, style={"fontSize": "13px", "color": "#555"}),
                     html.Div(f"{value:,}", style={"fontSize": "26px", "fontWeight": "700", "color": BLUE})],
                    style={**CARD, "flex": "1", "minWidth": "150px", "textAlign": "center"})

STORY_TOP = """
### The question
Do the parts of New York City with more **construction activity** also have more (or more severe) **street crashes**?
The city approves tens of thousands of construction jobs every year while trying to reduce traffic injuries (Vision Zero).

### The data
**Housing:** DOB NOW: Build - Job Application Filings. **Transportation:** Motor Vehicle Collisions - Crashes (2022-2025).
Both are summed to **ZIP code x month**, so we compare places and months, never single filings with single crashes.
Pick filters (or use the search box), then press **Generate Report**.
"""

STORY_BOTTOM = """
### The limits
- **Correlation is not causation.** Busy, dense ZIP codes have more construction *and* more traffic, so both counts are higher there.
- We have **no traffic, population or road-length data**, so counts are not per person or per mile.
- A **filing is an application**, not proof that a building was built or when work happened.
- Crash data is **police-reported**; ZIP codes are a coarse area; some ZIPs were recovered from coordinates (within 500 m).

### Benefit to New York
- **Planners:** see where housing growth and street danger overlap before approving more development.
- **DOT / Vision Zero:** prioritise safety reviews in ZIP codes that are high on both construction and crashes, and for pedestrian/cyclist injuries.
- **Department of Buildings:** coordinate site-safety checks with local crash patterns.
- **Communities and advocates:** ask the same questions about their own borough and year.
"""

app = Dash(__name__, title="NYC Construction & Street Safety")
server = app.server          # needed by Vercel / gunicorn

app.layout = html.Div(style={"background": "#f4f7fa", "minHeight": "100vh", "fontFamily": "Arial, sans-serif"}, children=[
    html.Div([html.H1("NYC: Construction & Street Safety", style={"margin": "0"}),
              html.P("Do places with more construction filings also have more crashes? (2022-2025)", style={"margin": "4px 0 0 0"})],
             style={"background": "#12263a", "color": "white", "padding": "22px 32px"}),

    html.Div(style={"maxWidth": "1400px", "margin": "0 auto", "padding": "20px"}, children=[
        html.Div(dcc.Markdown(STORY_TOP), style={**CARD, "marginBottom": "16px"}),

        # filters, search box and the Generate Report button
        html.Div([
            html.Div([dropdown("borough-dd", "Borough", BOROUGHS), dropdown("year-dd", "Year", YEARS),
                      dropdown("job-dd", "Housing: job type", JOB_TYPES), dropdown("factor-dd", "Transport: contributing factor", FACTORS)],
                     style={"display": "flex", "gap": "14px", "flexWrap": "wrap"}),
            html.Div([
                dcc.Input(id="search-box", type="text", debounce=True, n_submit=0,
                          placeholder='Search mode - try: "Brooklyn 2022 new buildings" or "Queens 2024 speeding"',
                          style={"flex": "1", "minWidth": "320px", "padding": "10px"}),
                html.Button("Search", id="search-btn", n_clicks=0, style={"padding": "10px 18px"}),
                html.Button("Generate Report", id="generate-btn", n_clicks=0,
                            style={"padding": "10px 24px", "background": BLUE, "color": "white", "fontWeight": "700", "border": "none", "borderRadius": "6px"}),
            ], style={"display": "flex", "gap": "10px", "marginTop": "14px", "flexWrap": "wrap"}),
            html.Div(id="search-status", style={"marginTop": "8px", "fontSize": "13px"}),
        ], style={**CARD, "marginBottom": "16px"}),

        html.Div(id="status", style={"margin": "0 0 8px 4px", "fontSize": "13px"}),
        html.Div(id="kpis", style={"display": "flex", "gap": "12px", "flexWrap": "wrap", "marginBottom": "16px"}),
        html.Div([html.H3("Key findings for the current selection", style={"marginTop": "0"}), dcc.Markdown(id="findings")],
                 style={**CARD, "marginBottom": "16px"}),

        # one card per research question
        html.Div([
            html.Div([html.H4(f"Q{number}", style={"margin": "0", "color": BLUE}),
                      html.P(question, style={"margin": "4px 0", "fontWeight": "600"}),
                      html.Small(f"Research question by {member}", style={"color": "#777"}),
                      dcc.Graph(id=f"graph-{number}")], style=CARD)
            for number, member, question, _ in CHARTS
        ], style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(520px, 1fr))", "gap": "16px"}),

        html.Div(dcc.Markdown(STORY_BOTTOM), style={**CARD, "marginTop": "16px"}),
        html.P("Data: NYC Open Data. GIU Data Engineering & Visualization, Winter 2026.",
               style={"fontSize": "12px", "color": "#777", "textAlign": "center", "marginTop": "16px"}),
    ]),
])


# ------------------------------------------------------------ search button -> fills the dropdowns (Sara)
@app.callback(
    Output("borough-dd", "value"), Output("year-dd", "value"), Output("job-dd", "value"), Output("factor-dd", "value"),
    Output("search-status", "children"),
    Input("search-btn", "n_clicks"), Input("search-box", "n_submit"), State("search-box", "value"),
    prevent_initial_call=True,
)
def apply_search(n_clicks, n_submit, text):
    if not text or not text.strip():
        raise PreventUpdate
    found = parse_search(text, YEARS, JOB_TYPES, FACTORS)
    if any(found.values()):
        message = "Filters applied - now press Generate Report."
    else:
        message = "No known borough, year, job type or cause found in your search - showing all data."
    return found["boroughs"], found["years"], found["job_types"], found["factors"], message


# ------------------------------------------------------------ Generate Report -> updates everything (Youssef)
@app.callback(
    [Output(f"graph-{number}", "figure") for number, _, _, _ in CHARTS] +
    [Output("kpis", "children"), Output("findings", "children"), Output("status", "children")],
    Input("generate-btn", "n_clicks"),
    State("borough-dd", "value"), State("year-dd", "value"), State("job-dd", "value"), State("factor-dd", "value"),
)
def generate_report(n_clicks, boroughs, years, job_types, factors):
    h, c = apply_filters(boroughs, years, job_types, factors)
    figures = []
    for number, member, question, make_chart in CHARTS:
        try:
            figures.append(make_chart(h, c))
        except Exception as error:                 # one broken chart should not break the whole report
            figures.append(charts.no_data(f"Could not draw this chart: {error}"))
    kpis = [kpi_card("Construction filings", int(h["filings"].sum())),
            kpi_card("New dwelling units", int(h["new_units"].sum())),
            kpi_card("Crashes", int(c["crashes"].sum())),
            kpi_card("People injured", int(c["injured"].sum())),
            kpi_card("People killed", int(c["killed"].sum()))]
    findings = "\n".join("- " + line for line in charts.key_findings(h, c))
    chosen = [f"{name}: {', '.join(map(str, values))}" for name, values in
              [("Borough", boroughs), ("Year", years), ("Job type", job_types), ("Factor", factors)] if values]
    status = "Report generated for: " + (" | ".join(chosen) if chosen else "all data")
    return figures + [kpis, findings, status]


if __name__ == "__main__":
    app.run(debug=False, port=8050)
