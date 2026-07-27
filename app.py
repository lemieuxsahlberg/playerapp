import re
import unicodedata

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Pelaajahaku / Player Stats", layout="wide")

st.markdown(
    """
<style>
.block-container { max-width: 1200px; padding-top: 2rem; padding-bottom: 2rem; }
.metric-card { background: #f8f9fb; border: 1px solid #e7ebf0; border-radius: 16px; padding: 16px 18px; margin-bottom: 10px; }
.metric-label { font-size: 0.9rem; color: #666; margin-bottom: 4px; }
.metric-value { font-size: 1.6rem; font-weight: 700; color: #111; }
.highlight-card { background: #fff; border-radius: 16px; padding: 16px 18px; margin-bottom: 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.highlight-label { font-size: 0.9rem; color: #666; margin-bottom: 4px; }
.highlight-value { font-size: 1.2rem; font-weight: 700; }
</style>
""",
    unsafe_allow_html=True,
)

LANG = st.radio("Kieli / Language", ["Suomi", "English"], horizontal=True)

TEXT = {
    "title": {"Suomi": "Pelaajahaku & tilastot", "English": "Player Search & Statistics"},
    "overview": {"Suomi": "Etusivu", "English": "Overview"},
    "player_search": {"Suomi": "Pelaajahaku", "English": "Player Search"},
    "rankings": {"Suomi": "Top-listat", "English": "Rankings"},
    "trends": {"Suomi": "Trendit", "English": "Trends"},
    "calculation": {"Suomi": "Laskentaperusteet", "English": "How the numbers are calculated"},
    "players": {"Suomi": "Pelaajia", "English": "Players"},
    "competitions": {"Suomi": "Kilpailuja", "English": "Competitions"},
    "rows": {"Suomi": "Tulosrivejä", "English": "Result rows"},
    "score_home": {"Suomi": "Score", "English": "Score"},
    "active_home": {"Suomi": "Aktiivisuus", "English": "Activity"},
    "top5_home": {"Suomi": "Eniten Top 5 -sijoituksia", "English": "Most Top 5 finishes"},
    "hot_now": {"Suomi": "Tämän hetken kuumimmat pelaajat", "English": "Hottest players right now"},
    "hot_now_note": {"Suomi": "Laskettu koko datan viidestä viimeisimmästä järjestetystä kilpailusta. Mukaan nostetaan ensisijaisesti pelaajat, joilla on vähintään 2 kilpailua näistä viidestä.", "English": "Calculated from the latest five competitions in the dataset. Players with at least 2 starts in those five are prioritized."},
    "open_player": {"Suomi": "Avaa pelaajan tiedot", "English": "Open player details"},
    "filter_name": {"Suomi": "Suodata nimeä", "English": "Filter name"},
    "select_player": {"Suomi": "Valitse pelaaja", "English": "Select player"},
    "best_rank": {"Suomi": "Paras sijoitus", "English": "Best rank"},
    "avg_rank": {"Suomi": "Sijoituskeskiarvo", "English": "Average rank"},
    "top5": {"Suomi": "Top 5", "English": "Top 5"},
    "consistency": {"Suomi": "Tasaisuus", "English": "Consistency"},
    "trend": {"Suomi": "Trendi", "English": "Trend"},
    "current_form": {"Suomi": "Nykykunto", "English": "Current form"},
    "player_trend": {"Suomi": "Kehityssuunta", "English": "Performance trend"},
    "recent_results": {"Suomi": "Viimeisimmät kilpailut", "English": "Most recent competitions"},
    "starts_by_year": {"Suomi": "Kisat vuosittain", "English": "Starts by year"},
    "score_label": {"Suomi": "Score-järjestys", "English": "Score ranking"},
    "min_starts_label": {"Suomi": "Minimikisamäärä top-listoille", "English": "Minimum starts for rankings"},
    "min_starts_help": {"Suomi": "Suodattaa pois pelaajat, joilla on liian vähän kilpailuja. Suositus: 3.", "English": "Filters out players with too few competitions. Recommendation: 3."},
    "qualified_note": {"Suomi": "Listoissa näkyy vain pelaajat, joilla on vähintään valittu määrä kilpailuja.", "English": "Rankings only include players with at least the selected number of competitions."},
    "yearly_top": {"Suomi": "Vuosittaiset top-listat", "English": "Yearly top lists"},
    "yearly_top_note": {"Suomi": "Näyttää uusimman datavuoden sekä kolme sitä edeltävää vuotta, jos dataa löytyy.", "English": "Shows the latest data year and the three preceding years when data exists."},
    "most_top5": {"Suomi": "Eniten Top 5 -sijoituksia", "English": "Most Top 5 finishes"},
    "best_avg_rank": {"Suomi": "Paras sijoituskeskiarvo", "English": "Best average rank"},
    "most_active": {"Suomi": "Eniten kilpailuja", "English": "Most competitions"},
    "long_term_dev": {"Suomi": "Pitkän aikavälin kehitys", "English": "Long-term development"},
    "search_players": {"Suomi": "Hae pelaajaa listasta", "English": "Search player in list"},
    "select_players": {"Suomi": "Valitse pelaajat", "English": "Select players"},
    "comparison_trends": {"Suomi": "Vertailutrendit", "English": "Comparison trends"},
    "no_data": {"Suomi": "Dataa ei löytynyt.", "English": "No data found."},
    "no_matches": {"Suomi": "Ei osumia — näytetään koko lista.", "English": "No matches — showing full list."},
    "footer": {"Suomi": "© 2026 Greta Sahlberg – Kaikki oikeudet pidätetään.", "English": "© 2026 Greta Sahlberg – All rights reserved."},
    "top_player_now": {"Suomi": "Paras score", "English": "Best score"},
    "most_active_card": {"Suomi": "Aktiivisin pelaaja", "English": "Most active player"},
    "most_top5_card": {"Suomi": "Eniten Top 5 -sijoituksia", "English": "Most Top 5 finishes"},
}

COL_LABELS = {
    "player": {"Suomi": "Pelaaja", "English": "Player"},
    "top5_finishes": {"Suomi": "Top 5", "English": "Top 5"},
    "top5_rate": {"Suomi": "Top 5 -osuus", "English": "Top 5 rate"},
    "best_rank": {"Suomi": "Paras sijoitus", "English": "Best rank"},
    "avg_rank": {"Suomi": "Sijoituskeskiarvo", "English": "Average rank"},
    "consistency": {"Suomi": "Tasaisuus", "English": "Consistency"},
    "current_form": {"Suomi": "Nykykunto", "English": "Current form"},
    "trend_slope": {"Suomi": "Trendi", "English": "Trend"},
    "tournaments": {"Suomi": "Kilpailuja", "English": "Competitions"},
    "competition_raw": {"Suomi": "Kilpailu", "English": "Competition"},
    "competition": {"Suomi": "Kilpailu-ID", "English": "Competition ID"},
    "rank": {"Suomi": "Sijoitus", "English": "Rank"},
    "year": {"Suomi": "Vuosi", "English": "Year"},
    "score": {"Suomi": "Score", "English": "Score"},
    "performance_score": {"Suomi": "Performance score", "English": "Performance score"},
    "hot_score": {"Suomi": "Hot score", "English": "Hot score"},
    "last5_form": {"Suomi": "Viim. 5 form", "English": "Latest 5 form"},
    "last5_trend": {"Suomi": "Viim. 5 trendi", "English": "Latest 5 trend"},
    "last5_starts": {"Suomi": "Kisoja", "English": "Starts"},
    "last5_top5": {"Suomi": "Top 5", "English": "Top 5"},
    "last5_best_rank": {"Suomi": "Paras sijoitus", "English": "Best rank"},
}


def t(key: str) -> str:
    return TEXT.get(key, {"Suomi": key, "English": key}).get(LANG, key)


def localize_columns(df_in: pd.DataFrame) -> pd.DataFrame:
    return df_in.rename(columns={c: COL_LABELS[c][LANG] for c in df_in.columns if c in COL_LABELS})


def norm_name(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return s.lower().strip()


def make_search_key(normed: str) -> str:
    parts = str(normed).split()
    if len(parts) >= 2:
        return f"{normed} {' '.join(parts[::-1])}"
    return str(normed)


def numeric_comp(value):
    m = re.search(r"(\d+)", str(value))
    return int(m.group(1)) if m else np.nan


def year_from_competition(value):
    m = re.search(r"(\d+)", str(value))
    if not m:
        return np.nan
    digits = str(m.group(1)).zfill(4)
    return 2000 + int(digits[:2])


def score_color(value, metric_type="high"):
    if pd.isna(value):
        return "#999999"
    if metric_type == "high":
        if value >= 0.80:
            return "#2563eb"
        if value >= 0.60:
            return "#16a34a"
        return "#dc2626"
    if value <= 5:
        return "#2563eb"
    if value <= 12:
        return "#16a34a"
    return "#dc2626"


def metric_card(label, value):
    return f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
    </div>
    """


def highlight_metric_card(label, value_html, color):
    return f"""
    <div class="highlight-card" style="border: 2px solid {color}; border-left: 8px solid {color};">
        <div class="highlight-label">{label}</div>
        <div class="highlight-value" style="color: {color};">{value_html}</div>
    </div>
    """


@st.cache_data
def load_data(path="results.parquet", version="hot_players_v1") -> pd.DataFrame:
    df = pd.read_parquet(path).copy()
    required = {"player", "rank"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"results.parquetista puuttuu sarakkeet: {sorted(missing)}")

    df["rank"] = pd.to_numeric(df["rank"], errors="coerce")
    df = df[df["rank"].notna()].copy()
    df = df[df["rank"] >= 1].copy()

    if "competition_raw" not in df.columns:
        if "competition" in df.columns:
            df["competition_raw"] = df["competition"].astype(str)
        elif "source" in df.columns:
            df["competition_raw"] = df["source"].astype(str).str.extract(r"/([^/]+)/tulokset")[0]
        else:
            df["competition_raw"] = np.nan

    df["competition_raw"] = df["competition_raw"].astype(str).str.replace(r"\.0$", "", regex=True)
    df["competition"] = pd.to_numeric(df["competition_raw"].apply(numeric_comp), errors="coerce")
    df["year"] = pd.to_numeric(df["competition_raw"].apply(year_from_competition), errors="coerce")

    df["player"] = df["player"].astype(str).str.strip()
    df = df[df["player"].notna()].copy()
    df = df[df["player"] != ""].copy()
    df = df[df["player"].str.lower() != "nan"].copy()
    df = df[~df["player"].isin(["-", "--", "None", "null"])].copy()

    bad_pattern = (
        r"all players|osakilpailu|masters|rahola|kirjurinluoto|updated:|teams|"
        r"general|class|qualification|matchplay|finnish adventure golf masters"
    )
    df = df[~df["player"].str.contains(bad_pattern, case=False, na=False)].copy()
    df = df[df["player"].str.contains(r"[A-Za-zÅÄÖåäö]", regex=True, na=False)].copy()

    # Poistetaan joukkue-/parikisojen ja parserivirheiden tulosrivit.
    team_or_score_pattern = r"\d|=|/|\bH\s+\d|\bE\s+\d|\bB\s+\d|\bC\s+\d"
    df = df[~df["player"].str.contains(team_or_score_pattern, regex=True, case=False, na=False)].copy()
    df = df[df["player"].str.len() <= 45].copy()

    df["player_norm"] = df["player"].apply(norm_name)
    alias_map = {
        "koski greta": "sahlberg greta",
        "greta koski": "sahlberg greta",
        "wedman greta": "sahlberg greta",
        "greta wedman": "sahlberg greta",
        "sahlberg greta": "sahlberg greta",
        "greta sahlberg": "sahlberg greta",
        "peltola pekka": "remes pekka",
        "pekka peltola": "remes pekka",
        "remes pekka": "remes pekka",
        "pekka remes": "remes pekka",
        "paavola mia": "vuorihovi mia",
        "mia paavola": "vuorihovi mia",
        "vuorihovi mia": "vuorihovi mia",
        "mia vuorihovi": "vuorihovi mia",
        "raesola kosti": "salonen kosti",
        "kosti raesola": "salonen kosti",
        "salonen kosti": "salonen kosti",
        "kosti salonen": "salonen kosti",
    }
    df["player_norm"] = df["player_norm"].replace(alias_map)
    df.loc[df["player_norm"] == "sahlberg greta", "player"] = "Greta Sahlberg"
    df.loc[df["player_norm"] == "remes pekka", "player"] = "Pekka Remes"
    df.loc[df["player_norm"] == "vuorihovi mia", "player"] = "Mia Vuorihovi"
    df.loc[df["player_norm"] == "salonen kosti", "player"] = "Kosti Salonen"

    excluded_norms = {"erik hjalmarsson", "hjalmarsson erik"}
    df = df[~df["player_norm"].isin(excluded_norms)].copy()
    df["player_search_key"] = df["player_norm"].apply(make_search_key)
    df = df.drop_duplicates(subset=["player_norm", "competition_raw", "rank"], keep="first").copy()
    return df


def add_performance(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["rank"] = pd.to_numeric(df["rank"], errors="coerce")
    comp_col = "competition_raw" if "competition_raw" in df.columns else "competition"
    field_sizes = df.groupby(comp_col)["rank"].max().reset_index(name="field_size")
    df = df.merge(field_sizes, on=comp_col, how="left")
    denom = df["field_size"] - 1
    df["performance_score"] = np.where(denom > 0, 1 - ((df["rank"] - 1) / denom), 1.0)
    df["performance_score"] = pd.to_numeric(df["performance_score"], errors="coerce").fillna(1.0)
    return df


def safe_slope(values) -> float:
    y = pd.Series(values).dropna().to_numpy()
    if len(y) >= 3:
        x = np.arange(len(y))
        return float(np.polyfit(x, y, 1)[0])
    return 0.0


def trend_readable(slope: float) -> str:
    if pd.isna(slope):
        return "-"
    pp = slope * 100
    if slope >= 0.02:
        label = "selvästi nousussa" if LANG == "Suomi" else "clearly rising"
    elif slope >= 0.005:
        label = "lievästi nousussa" if LANG == "Suomi" else "slightly rising"
    elif slope <= -0.02:
        label = "selvästi laskussa" if LANG == "Suomi" else "clearly declining"
    elif slope <= -0.005:
        label = "lievästi laskussa" if LANG == "Suomi" else "slightly declining"
    else:
        label = "tasainen" if LANG == "Suomi" else "stable"
    return f"{label} ({pp:+.1f} %-yks./kisa)" if LANG == "Suomi" else f"{label} ({pp:+.1f} pp/start)"


def compute_player_table(df: pd.DataFrame) -> pd.DataFrame:
    dfp = add_performance(df)
    top5 = dfp[dfp["rank"] <= 5].groupby("player_norm").size().reset_index(name="top5_finishes")
    total = dfp.groupby("player_norm")["competition_raw"].nunique().reset_index(name="starts")
    search_key = dfp.groupby("player_norm")["player_search_key"].first().reset_index(name="player_search_key")
    base = total.merge(top5, on="player_norm", how="left").fillna({"top5_finishes": 0})
    base["top5_rate"] = base["top5_finishes"] / base["starts"]

    agg = (
        dfp.groupby("player_norm")
        .agg(
            player=("player", "first"),
            tournaments=("competition_raw", "nunique"),
            avg_rank=("rank", "mean"),
            best_rank=("rank", "min"),
            avg_perf=("performance_score", "mean"),
            std_perf=("performance_score", "std"),
        )
        .reset_index()
    )
    agg["consistency"] = (1 - agg["std_perf"]).fillna(0)

    trend_rows = []
    for pn, sub in dfp.sort_values(["competition", "competition_raw"]).groupby("player_norm"):
        y = sub["performance_score"].to_numpy()
        trend_rows.append((pn, safe_slope(y), float(np.mean(y[-5:])) if len(y) else np.nan))
    trend_df = pd.DataFrame(trend_rows, columns=["player_norm", "trend_slope", "current_form"])

    out = agg.merge(base, on="player_norm", how="left").merge(trend_df, on="player_norm", how="left").merge(search_key, on="player_norm", how="left")
    yearly = (
        dfp.dropna(subset=["year"])
        .groupby(["player_norm", "year"])["competition_raw"]
        .nunique()
        .reset_index(name="starts_year")
    )
    if not yearly.empty:
        ypivot = yearly.pivot(index="player_norm", columns="year", values="starts_year").fillna(0).reset_index()
        ypivot.columns = [f"starts_{int(c)}" if isinstance(c, (int, float, np.integer, np.floating)) and not pd.isna(c) else c for c in ypivot.columns]
        out = out.merge(ypivot, on="player_norm", how="left")

    out["score"] = 0.45 * out["avg_perf"] + 0.20 * out["top5_rate"] + 0.20 * out["consistency"] + 0.15 * out["trend_slope"]
    return out.sort_values("score", ascending=False)


def player_timeseries(df: pd.DataFrame, player_norm: str) -> pd.DataFrame:
    dfp = add_performance(df)
    sub = dfp[dfp["player_norm"] == player_norm].sort_values(["competition", "competition_raw"])
    cols = ["competition_raw", "competition", "year", "rank", "performance_score", "player"]
    return sub[[c for c in cols if c in sub.columns]]


def recent_years_from_data(df: pd.DataFrame, count: int = 4) -> list[int]:
    years = pd.to_numeric(df.get("year"), errors="coerce").dropna().astype(int).unique().tolist()
    return sorted(years, reverse=True)[:count]


def hot_players_last_competitions(df: pd.DataFrame, latest_count: int = 5, min_starts: int = 2) -> tuple[pd.DataFrame, list[str]]:
    dfp = add_performance(df)
    comp_lookup = dfp[["competition_raw", "competition"]].drop_duplicates().copy()
    comp_lookup["competition"] = pd.to_numeric(comp_lookup["competition"], errors="coerce")
    comp_lookup = comp_lookup.dropna(subset=["competition"]).sort_values(["competition", "competition_raw"])
    latest_raw = comp_lookup["competition_raw"].tail(latest_count).tolist()
    recent = dfp[dfp["competition_raw"].isin(latest_raw)].copy()

    rows = []
    for pn, sub in recent.sort_values(["competition", "competition_raw"]).groupby("player_norm"):
        y = sub["performance_score"].to_numpy()
        starts = sub["competition_raw"].nunique()
        avg_perf = float(np.mean(y)) if len(y) else np.nan
        trend = safe_slope(y)
        top5 = int((sub["rank"] <= 5).sum())
        top5_rate = top5 / starts if starts else 0
        latest3_raw = latest_raw[-3:]
        sub_last3 = sub[sub["competition_raw"].isin(latest3_raw)].copy()
        last3_starts = sub_last3["competition_raw"].nunique()
        last3_top5 = int((sub_last3["rank"] <= 5).sum())
        best_rank = float(sub["rank"].min()) if len(sub) else np.nan
        avg_rank = float(sub["rank"].mean()) if len(sub) else np.nan
        hot_score = 0.65 * avg_perf + 0.25 * trend + 0.10 * top5_rate
        rows.append({
            "player_norm": pn,
            "player": sub["player"].iloc[0],
            "hot_score": hot_score,
            "last5_form": avg_perf,
            "last5_trend": trend,
            "last5_starts": starts,
            "last5_top5": top5,
            "last3_top5": last3_top5,
            "last3_starts": last3_starts,
            "last5_best_rank": best_rank,
            "last5_avg_rank": avg_rank,
        })

    hot_df = pd.DataFrame(rows)
    if hot_df.empty:
        return hot_df, latest_raw
    qualified = hot_df[hot_df["last5_starts"] >= min_starts].copy()
    if qualified.empty:
        qualified = hot_df.copy()
    return qualified.sort_values(["hot_score", "last5_form", "last5_trend"], ascending=False), latest_raw


def render_player_profile(df: pd.DataFrame, players_table: pd.DataFrame, player_norm: str) -> None:
    match = players_table[players_table["player_norm"] == player_norm]
    if match.empty:
        st.info("Pelaajan tietoja ei löytynyt." if LANG == "Suomi" else "Player details not found.")
        return
    row = match.iloc[0]
    st.markdown(f"### {row['player']}")
    c1, c2, c3 = st.columns(3)
    c4, c5, c6 = st.columns(3)
    with c1:
        st.markdown(metric_card(t("best_rank"), int(row["best_rank"])), unsafe_allow_html=True)
    with c2:
        st.markdown(metric_card(t("avg_rank"), f"{row['avg_rank']:.2f}"), unsafe_allow_html=True)
    with c3:
        st.markdown(metric_card(t("top5"), f"{int(row['top5_finishes'])} ({row['top5_rate'] * 100:.1f}%)"), unsafe_allow_html=True)
    with c4:
        st.markdown(metric_card(t("consistency"), f"{row['consistency']:.3f}"), unsafe_allow_html=True)
    with c5:
        st.markdown(metric_card(t("trend"), f"{row['trend_slope']:+.4f}"), unsafe_allow_html=True)
    with c6:
        st.markdown(metric_card(t("current_form"), f"{row['current_form']:.3f}"), unsafe_allow_html=True)

    year_cols = sorted([c for c in row.index if str(c).startswith("starts_")], key=lambda x: int(str(x).split("_")[1]))
    if year_cols:
        st.markdown(f"#### {t('starts_by_year')}")
        year_card_cols = st.columns(min(4, len(year_cols)))
        for i, col in enumerate(year_cols):
            year = col.split("_")[1]
            label = f"Kisat {year}" if LANG == "Suomi" else f"Starts {year}"
            with year_card_cols[i % len(year_card_cols)]:
                st.markdown(metric_card(label, int(row.get(col, 0))), unsafe_allow_html=True)

    ts = player_timeseries(df, player_norm)
    st.markdown(f"#### {t('player_trend')}")
    if not ts.empty:
        st.line_chart(ts.set_index("competition")["performance_score"])
    st.markdown(f"#### {t('recent_results')}")
    st.dataframe(localize_columns(ts.tail(30)), use_container_width=True)


try:
    df = load_data()
except Exception as exc:
    st.error("Datan lataus epäonnistui. Tarkista, että GitHubissa on oikea results.parquet.")
    st.exception(exc)
    st.stop()

if df.empty:
    st.error(t("no_data"))
    st.stop()

players_table = compute_player_table(df)
df_perf = add_performance(df)

st.title(t("title"))
tabs = st.tabs([t("overview"), t("player_search"), t("rankings"), t("trends"), t("calculation")])

with tabs[0]:
    st.markdown(f"## {t('overview')}")
    total_players = df["player_norm"].nunique()
    total_competitions = df["competition_raw"].nunique()
    total_rows = len(df)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(metric_card(t("players"), total_players), unsafe_allow_html=True)
    with c2:
        st.markdown(metric_card(t("competitions"), total_competitions), unsafe_allow_html=True)
    with c3:
        st.markdown(metric_card(t("rows"), total_rows), unsafe_allow_html=True)

    overview_qualified = players_table[players_table["tournaments"] >= 3].copy()
    if overview_qualified.empty:
        overview_qualified = players_table.copy()

    best_score_row = overview_qualified.sort_values("score", ascending=False).iloc[0]
    most_active_row = players_table.sort_values("tournaments", ascending=False).iloc[0]
    most_top5_row = overview_qualified.sort_values(["top5_finishes", "top5_rate"], ascending=False).iloc[0]

    st.markdown("### Nostoja")
    c1, c2, c3 = st.columns(3)
    with c1:
        color = score_color(best_score_row["score"], "high")
        value = f"{best_score_row['player']}<br><span style='font-size:1rem;'>Score {best_score_row['score']:.3f}</span>"
        st.markdown(highlight_metric_card(t("top_player_now"), value, color), unsafe_allow_html=True)
    with c2:
        color = score_color(most_active_row["tournaments"], "high")
        label = "kilpailua" if LANG == "Suomi" else "competitions"
        value = f"{most_active_row['player']}<br><span style='font-size:1rem;'>{int(most_active_row['tournaments'])} {label}</span>"
        st.markdown(highlight_metric_card(t("most_active_card"), value, color), unsafe_allow_html=True)
    with c3:
        color = score_color(most_top5_row["top5_rate"], "high")
        label = "Top 5 -sijoitusta" if LANG == "Suomi" else "Top-5 finishes"
        value = f"{most_top5_row['player']}<br><span style='font-size:1rem;'>{int(most_top5_row['top5_finishes'])} {label}</span>"
        st.markdown(highlight_metric_card(t("most_top5_card"), value, color), unsafe_allow_html=True)

    st.markdown("### Top 3")
    st.caption("Vähintään 3 kilpailua / Minimum 3 competitions")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"#### {t('score_home')}")
        score_home = overview_qualified.sort_values("score", ascending=False).head(3)
        st.dataframe(localize_columns(score_home[["player", "score", "best_rank"]]), use_container_width=True)
    with c2:
        st.markdown(f"#### {t('active_home')}")
        active_home = players_table.sort_values("tournaments", ascending=False).head(3)
        st.dataframe(localize_columns(active_home[["player", "tournaments", "best_rank"]]), use_container_width=True)
    with c3:
        st.markdown(f"#### {t('top5_home')}")
        top5_home = overview_qualified.sort_values(["top5_finishes", "top5_rate"], ascending=False).head(3)
        st.dataframe(localize_columns(top5_home[["player", "top5_finishes", "top5_rate"]]), use_container_width=True)

    st.markdown(f"### {t('hot_now')}")
    hot_df, latest_hot_competitions = hot_players_last_competitions(df, latest_count=5, min_starts=2)
    if latest_hot_competitions:
        st.caption(t("hot_now_note") + " " + ("Kilpailut: " if LANG == "Suomi" else "Competitions: ") + ", ".join(map(str, latest_hot_competitions)))
    if hot_df.empty:
        st.info("Kuumimpien pelaajien laskentaan ei löytynyt dataa." if LANG == "Suomi" else "No data available for hottest players.")
    else:
        for _, hot_row in hot_df.head(5).iterrows():
            with st.container(border=True):
                left, right = st.columns([2, 3])
                with left:
                    if st.button(str(hot_row["player"]), key=f"hot_open_{hot_row['player_norm']}", help=t("open_player")):
                        st.session_state["selected_player_norm"] = hot_row["player_norm"]
                    st.caption(t("open_player"))
                with right:
                    h1, h2, h3 = st.columns(3)
                    with h1:
                        st.metric("Kunto" if LANG == "Suomi" else "Form", f"{hot_row['last5_form']:.3f}")
                    with h2:
                        st.metric(t("trend"), trend_readable(float(hot_row["last5_trend"])))
                    with h3:
                        st.metric("Top 5 / 3 viim." if LANG == "Suomi" else "Top 5 / last 3", f"{int(hot_row['last3_top5'])}/{int(hot_row['last3_starts'])}")
                    st.caption(("Paras sijoitus viidessä viimeisimmässä kisassa: " if LANG == "Suomi" else "Best rank in latest five competitions: ") + str(int(hot_row["last5_best_rank"])))

    if "selected_player_norm" in st.session_state:
        st.markdown("---")
        render_player_profile(df, players_table, st.session_state["selected_player_norm"])

with tabs[1]:
    st.markdown(f"## {t('player_search')}")
    q = st.text_input(t("filter_name"), "")
    if q:
        qn = norm_name(q)
        options = players_table[players_table["player_search_key"].str.contains(qn, na=False)]["player"].tolist()
        if not options:
            options = players_table["player"].tolist()
            st.info(t("no_matches"))
    else:
        options = players_table["player"].tolist()

    default_index = 0
    if "selected_player_norm" in st.session_state:
        selected_names = players_table.loc[players_table["player_norm"] == st.session_state["selected_player_norm"], "player"].tolist()
        if selected_names and selected_names[0] in options:
            default_index = options.index(selected_names[0])
    chosen = st.selectbox(t("select_player"), options=options, index=default_index)
    pn = players_table.loc[players_table["player"] == chosen, "player_norm"].iloc[0]
    st.session_state["selected_player_norm"] = pn
    render_player_profile(df, players_table, pn)

with tabs[2]:
    st.markdown(f"## {t('rankings')}")
    min_starts = st.number_input(t("min_starts_label"), min_value=1, max_value=50, value=3, step=1, help=t("min_starts_help"))
    qualified_players = players_table[players_table["tournaments"] >= min_starts].copy()
    if qualified_players.empty:
        st.warning("Ei pelaajia tällä minimikisamäärällä. Näytetään kaikki pelaajat." if LANG == "Suomi" else "No players match this minimum. Showing all players.")
        qualified_players = players_table.copy()
    st.caption(t("qualified_note"))

    st.markdown(f"### {t('score_label')}")
    st.dataframe(localize_columns(qualified_players.sort_values("score", ascending=False)[["player", "score", "avg_rank", "top5_rate", "consistency", "tournaments"]].head(50)), use_container_width=True)

    st.markdown(f"### {t('yearly_top')}")
    st.caption(t("yearly_top_note"))
    recent_years = recent_years_from_data(df, count=4)
    if recent_years:
        year_tabs = st.tabs([str(y) for y in recent_years])
        for year_tab, year in zip(year_tabs, recent_years):
            with year_tab:
                year_df = df[pd.to_numeric(df["year"], errors="coerce") == year].copy()
                year_players = compute_player_table(year_df)
                year_players = year_players[year_players["tournaments"] >= min_starts].copy()
                if year_players.empty:
                    st.info(("Ei pelaajia minimikisamäärällä " + str(min_starts) + " tällä vuodella.") if LANG == "Suomi" else ("No players with minimum " + str(min_starts) + " starts for this year."))
                    continue
                y1, y2, y3 = st.columns(3)
                with y1:
                    st.markdown("#### Score")
                    st.dataframe(localize_columns(year_players.sort_values("score", ascending=False)[["player", "score", "avg_rank", "top5_rate", "tournaments"]].head(10)), use_container_width=True)
                with y2:
                    st.markdown(f"#### {t('most_top5')}")
                    st.dataframe(localize_columns(year_players.sort_values(["top5_finishes", "top5_rate"], ascending=False)[["player", "top5_finishes", "top5_rate", "tournaments"]].head(10)), use_container_width=True)
                with y3:
                    st.markdown(f"#### {t('best_avg_rank')}")
                    st.dataframe(localize_columns(year_players.sort_values("avg_rank", ascending=True)[["player", "avg_rank", "best_rank", "tournaments"]].head(10)), use_container_width=True)
    else:
        st.info("Vuositietoa ei löytynyt datasta.")

    st.markdown(f"### {t('most_top5')}")
    st.dataframe(localize_columns(qualified_players.sort_values("top5_finishes", ascending=False)[["player", "top5_finishes", "top5_rate", "tournaments", "best_rank", "consistency"]].head(50)), use_container_width=True)
    st.markdown(f"### {t('best_avg_rank')}")
    st.dataframe(localize_columns(qualified_players.sort_values("avg_rank", ascending=True)[["player", "avg_rank", "best_rank", "top5_rate", "consistency", "tournaments"]].head(50)), use_container_width=True)
    st.markdown(f"### {t('most_active')}")
    st.dataframe(localize_columns(players_table.sort_values("tournaments", ascending=False)[["player", "tournaments", "best_rank", "avg_rank", "top5_rate"]].head(50)), use_container_width=True)
    st.markdown(f"### {t('long_term_dev')}")
    ranking_query = st.text_input(t("search_players"), "")
    overall_trend = qualified_players.sort_values("trend_slope", ascending=False).copy()
    if ranking_query:
        qn = norm_name(ranking_query)
        overall_trend = overall_trend[overall_trend["player_search_key"].str.contains(qn, na=False)].copy()
    st.dataframe(localize_columns(overall_trend[["player", "trend_slope", "current_form", "top5_rate", "consistency", "tournaments"]].head(100)), use_container_width=True)

with tabs[3]:
    st.markdown(f"## {t('comparison_trends')}")
    options = players_table["player"].tolist()
    selected = st.multiselect(t("select_players"), options=options, default=options[:2])
    if selected:
        chart_df = []
        for player in selected:
            pn = players_table.loc[players_table["player"] == player, "player_norm"].iloc[0]
            sub = df_perf[df_perf["player_norm"] == pn].sort_values("competition")[["competition", "performance_score"]].copy()
            sub["player"] = player
            chart_df.append(sub)
        if chart_df:
            chart_df = pd.concat(chart_df, ignore_index=True)
            pivot = chart_df.pivot(index="competition", columns="player", values="performance_score").sort_index()
            st.line_chart(pivot)

with tabs[4]:
    st.markdown(f"## {t('calculation')}")
    if LANG == "Suomi":
        st.markdown(
            """
- **Paras sijoitus** = pienin rank
- **Sijoituskeskiarvo** = sijoitusten keskiarvo
- **Top 5** = montako kertaa rank ≤ 5
- **Top 5 -osuus** = top5 / starts
- **Performance score** = `1 − (rank−1)/(field_size−1)`
- **Tasaisuus** = `1 − std(performance_score)`
- **Trendi** = lineaarinen trendi performance_scorelle
- **Nykykunto** = viimeisten 5 kilpailun performance_score-keskiarvo
- **Eniten kilpailuja** = suurin kilpailumäärä
- **Top-listoissa oletusminimi on 3 kilpailua**, jotta 1–2 kisan pelaajat eivät nouse listojen kärkeen liian kevyellä otannalla.
- **Tämän hetken kuumimmat pelaajat** = viiden viimeisimmän järjestetyn kilpailun perusteella laskettu yhdistelmä: form, trendi ja Top 5 -osumat.
- **Pitkän aikavälin kehitys** = koko datan trendi
- **Vuosi** päätellään kilpailu-ID:n kahdesta ensimmäisestä numerosta.
- **Score** = painotettu yhdistelmä:
  - 45 % avg_perf
  - 20 % top5_rate
  - 20 % consistency
  - 15 % trend_slope
            """
        )
    else:
        st.markdown(
            """
- **Best rank** = lowest rank
- **Average rank** = mean rank
- **Top 5** = number of times rank ≤ 5
- **Top 5 rate** = top5 / starts
- **Performance score** = `1 − (rank−1)/(field_size−1)`
- **Consistency** = `1 − std(performance_score)`
- **Trend** = linear slope of performance_score
- **Current form** = mean performance_score of last 5 competitions
- **Most competitions** = highest competition count
- **Ranking lists default to a minimum of 3 competitions** so players with only 1–2 starts do not dominate the lists too easily.
- **Hottest players right now** = based on a combination of form, trend and Top 5 finishes in the five most recent competitions.
- **Long-term development** = trend over the full dataset
- **Score** = weighted combination:
  - 45% avg_perf
  - 20% top5_rate
  - 20% consistency
  - 15% trend_slope
            """
        )

st.markdown("---")
st.caption(t("footer"))
