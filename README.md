# NYC: Construction & Street Safety (Data Engineering & Visualization - Milestone 1)

**Question:** Do ZIP codes with more construction activity also have more (or more severe) street crashes?

- **Housing dataset:** DOB NOW: Build - Job Application Filings (`w9ak-ipjd`) - https://data.cityofnewyork.us/d/w9ak-ipjd
- **Transportation dataset:** Motor Vehicle Collisions - Crashes (`h9gi-nx95`) - https://data.cityofnewyork.us/d/h9gi-nx95 (outside the catalog; the notebook explains how we found it and includes the feasibility check)
- **Period:** 1 Jan 2022 - 31 Dec 2025. **Integration level:** ZIP code x year x month.
- **Deployed website:** _paste the Vercel link here_

## Repository contents
| File | What it is |
|---|---|
| `Milestone1_NYC_Housing_Transportation.ipynb` | Full notebook: EDA, cleaning, integration, post-integration cleaning, 12 questions/charts, story |
| `charts.py` | The 12 chart functions (used by the notebook and the website) |
| `app.py` | Dash website (dropdown filters, search mode, Generate Report button, story section) |
| `data/` | Small aggregated tables used by the website (created by the notebook) |
| `api/index.py`, `vercel.json`, `requirements.txt` | Deployment files for Vercel |

## Setup (run locally)
1. `pip install -r requirements.txt` (plus `scikit-learn seaborn matplotlib jupyter` to run the notebook)
2. Run the notebook top to bottom (the first run downloads the data from NYC Open Data automatically and caches it in `cache/`). This creates `charts.py` and the files in `data/`.
3. `python app.py` and open http://127.0.0.1:8050

## Deployment (Vercel)
1. Push the repository to GitHub (make sure `data/` is committed; `cache/` is ignored).
2. In Vercel: **Add New > Project > import the GitHub repo**. Framework preset: *Other*. No build command needed.
3. Deploy, open the link, and test the filters, search box and **Generate Report** button.
4. If Vercel fails because of package size or timeouts, deploy on **Render** instead: *New Web Service*, build command `pip install -r requirements.txt`, start command `gunicorn app:server`.

## Team contributions
| Member | Contributions |
|---|---|
| Tasneem | Dataset selection & feasibility check, data loading, housing EDA, Q1 & Q2 (borough shares, construction-and-crash hotspot chart), story text, README, prompts section |
| Sara | Crash EDA, crash cleaning, Q3 & Q4 (monthly trend line, seasonality heatmaps), search-mode parser |
| Ziad | Housing cleaning (duplicates, dates, units, cost outliers), Q5 & Q6 (units vs crashes scatter, severity box plot), dropdown filters and filter logic |
| Abdelrahman | Integration (ZIP recovery, borough consistency, aggregation, join), Q7 & Q8 (delay correlation, job-type chart), data export and deployment configuration |
| Yassin | Post-integration cleaning and validation checks, Q9 & Q10 (pedestrian/cyclist ranking, cost vs severity), page layout, KPI cards, testing |
| Youssef | `charts.py` setup, Q11 & Q12 (yes/no injury-crash model, crash causes in high vs low construction ZIPs), Dash app and Generate Report callback |
