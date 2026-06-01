import streamlit as st
import pandas as pd
import numpy as np
import unicodedata

st.set_page_config(
    page_title="Pelaajahaku / Player Stats",
    layout="wide"
)

# ---------- Styling ----------
st.markdown("""
<style>
.block-container {
    max-width: 1200px;
    padding-top: 2rem;
    padding-bottom: 2rem;
}
.metric-card {
    background: #f8f9fb;
    border: 1px solid #e7ebf0;
    border-radius: 16px;
    padding: 16px 18px;
    margin-bottom: 10px;
}
.metric-label {
    font-size: 0.9rem;
    color: #666;
    margin-bottom: 4px;
}
.metric-value {
    font-size: 1.6rem;
    font-weight: 700;
    color: #111;
}
.small-note {
    color: #666;
    font-size: 0.9rem;
}
</style>
""", unsafe_allow_html=True)

# ---------- Language ----------
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
    "top5_home": {"Suomi": "Eniten Top 5 -sijoituksia", "English": "Most Top 5 finishes"},
    "trend_home": {"Suomi": "Nousujohteisimmat", "English": "Most improving"},
    "avg_rank_home": {"Suomi": "Paras sijoituskeskiarvo", "English": "Best average rank"},
    "filter_name": {"Suomi": "Suodata nimeä", "English": "Filter name"},
    "select_player": {"Suomi": "Valitse pelaaja", "English": "Select player"},
    "best_rank": {"Suomi": "Paras sijoitus", "English": "Best rank"},
    "avg_rank": {"Suomi": "Sijoituskeskiarvo", "English": "Average rank"},
    "top5": {"Suomi": "Top 5", "English": "Top 5"},
    "consistency": {"Suomi": "Tasaisuus", "English": "Consistency"},
    "trend": {"Suomi": "Trendi", "English": "Trend"},
    "current_form": {"Suomi": "Nykykunto", "English": "Current form"},
    "starts_2024": {"Suomi": "Kisat 2024", "English": "Starts 2024"},
    "starts_2025": {"Suomi": "Kisat 2025", "English": "Starts 2025"},
    "starts_2026": {"Suomi": "Kisat 2026", "English": "Starts 2026"},
    "player_trend": {"Suomi": "Pelaajan trendikäyrä", "English": "Player trend chart"},
    "recent_results": {"Suomi": "Viimeisimmät kilpailut", "English": "Most recent competitions"},
    "most_top5": {"Suomi": "Eniten Top 5 -sijoituksia", "English": "Most Top 5 finishes"},
    "best_avg_perf": {"Suomi": "Paras keskimääräinen suoritus", "English": "Best average performance"},
    "best_avg_rank": {"Suomi": "Paras sijoituskeskiarvo", "English": "Best average rank"},
    "most_improving": {"Suomi": "Nousujohteisimmat", "English": "Most improving"},
    "select_players": {"Suomi": "Valitse pelaajat", "English": "Select players"},
    "comparison_trends": {"Suomi": "Vertailutrendit", "English": "Comparison trends"},
    "no_data": {"Suomi": "Dataa ei löytynyt.", "English": "No data found."},
    "no_matches": {"Suomi": "Ei osumia — näytetään koko lista.", "English": "No matches — showing full list."},
    "info_text": {"Suomi": "Tietoa datasta", "English": "Data summary"},
}

def t(key):
    return TEXT[key][LANG]

# ---------- Helpers ----------
def norm_name(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return s.lower().strip()

def year_from_competition(comp):
    try:
        comp = int(comp)
        prefix = str(comp)[:2]
        if prefix == "24":
            return 2024
        if prefix == "25":
            return 2025
        if prefix == "26":
            return 2026
        return None
    except Exception:
        return None

@st.cache_data
def load_data(path="results.parquet", version="v8") -> pd.DataFrame:
    df = pd.read_parquet(path).copy()

    df["rank"] = pd.to_numeric(df["rank"], errors="coerce")

    if "competition" in df.columns:
        df["competition"] = pd.to_numeric(df["competition"], errors="coerce")
    elif "source" in df.columns:
        df["competition"] = pd.to_numeric(
            df["source"].astype(str).str.extract(r"/(\d+)/")[0],
            errors="coerce"
        )
    else:
        df["competition"] = np.nan

    # Siivotaan pelaajanimet
    df["player"] = df["player"].astype(str).str.strip()
    df = df[df["player"].notna()].copy()
    df = df[df["player"] != ""].copy()
    df = df[df["player"].str.lower() != "nan"].copy()
    df = df[~df["player"].isin(["-", "--", "None", "null"])].copy()

    df["player_norm"] = df["player"].apply(norm_name)
    df["year"] = df["competition"].apply(year_from_competition)

    return df
def add_performance(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    field_sizes = (
        df.groupby("competition")["rank"]
        .max()
        .reset_index(name="field_size")
    )

    df = df.merge(field_sizes, on="competition", how="left")

    df["performance_score"] = 1 - ((df["rank"] - 1) / (df["field_size"] - 1))
    df["performance_score"] = df["performance_score"].fillna(1.0)

    return df

def compute_player_table(df: pd.DataFrame) -> pd.DataFrame:
    dfp = add_performance(df)

    top5 = (
        dfp[dfp["rank"] <= 5]
        .groupby("player_norm")
        .size()
        .reset_index(name="top5_finishes")
    )

    total = (
        dfp.groupby("player_norm")
        .size()
        .reset_index(name="starts")
    )

    base = total.merge(top5, on="player_norm", how="left").fillna({"top5_finishes": 0})
    base["top5_rate"] = base["top5_finishes"] / base["starts"]

    agg = (
        dfp.groupby("player_norm")
        .agg(
            player=("player", "first"),
            tournaments=("competition", "count"),
            avg_rank=("rank", "mean"),
            best_rank=("rank", "min"),
            avg_perf=("performance_score", "mean"),
            std_perf=("performance_score", "std"),
        )
        .reset_index()
    )

    agg["consistency"] = (1 - agg["std_perf"]).fillna(0)

    trends = []
    for pn, sub in dfp.sort_values("competition").groupby("player_norm"):
        y = sub["performance_score"].to_numpy()
        if len(y) >= 3:
            x = np.arange(len(y))
            slope = np.polyfit(x, y, 1)[0]
        else:
            slope = 0.0
        current_form = float(np.mean(y[-5:])) if len(y) else np.nan
        trends.append((pn, slope, current_form))

    trend_df = pd.DataFrame(trends, columns=["player_norm", "trend_slope", "current_form"])

    out = agg.merge(base, on="player_norm", how="left").merge(trend_df, on="player_norm", how="left")

    # yearly starts
    yearly = (
        dfp.groupby(["player_norm", "year"])["competition"]
        .nunique()
        .reset_index(name="starts_year")
    )

    ypivot = yearly.pivot(index="player_norm", columns="year", values="starts_year").fillna(0).reset_index()
    ypivot.columns = [
        f"starts_{int(c)}" if isinstance(c, (int, float)) and not pd.isna(c) else c
        for c in ypivot.columns
    ]

    out = out.merge(ypivot, on="player_norm", how="left")

    out["score"] = (
        0.45 * out["avg_perf"] +
        0.20 * out["top5_rate"] +
        0.20 * out["consistency"] +
        0.15 * out["trend_slope"]
    )

    return out.sort_values("score", ascending=False)

def player_timeseries(df: pd.DataFrame, player_norm: str) -> pd.DataFrame:
    dfp = add_performance(df)
    sub = dfp[dfp["player_norm"] == player_norm].sort_values("competition")
    return sub[["competition", "rank", "performance_score", "year"]]

def metric_card(label, value):
    return f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
    </div>
    """

# ---------- Load ----------
df = load_data()

# Halutessa voit sulkea kilpailuja pois tästä:
exclude_ids = []
if exclude_ids:
    df = df[~df["competition"].isin(exclude_ids)].copy()

if df.empty:
    st.error(t("no_data"))
    st.stop()

players_table = compute_player_table(df)
df_perf = add_performance(df)

# ---------- Page ----------
st.title(t("title"))

tabs = st.tabs([
    t("overview"),
    t("player_search"),
    t("rankings"),
    t("trends"),
    t("calculation")
])

# ---------- Overview ----------
with tabs[0]:
    st.markdown(f"## {t('overview')}")

    total_players = df["player"].nunique()
    total_competitions = df["competition"].nunique()
    total_rows = len(df)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(metric_card(t("players"), total_players), unsafe_allow_html=True)
    with c2:
        st.markdown(metric_card(t("competitions"), total_competitions), unsafe_allow_html=True)
    with c3:
        st.markdown(metric_card(t("rows"), total_rows), unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(f"### {t('top5_home')}")
        top5_home = players_table.sort_values(["top5_finishes", "top5_rate"], ascending=False).head(3)
        st.dataframe(
            top5_home[["player", "top5_finishes", "top5_rate"]],
            use_container_width=True
        )

    with c2:
        st.markdown(f"### {t('trend_home')}")
        trend_home = players_table.sort_values("trend_slope", ascending=False).head(3)
        st.dataframe(
            trend_home[["player", "trend_slope", "current_form"]],
            use_container_width=True
        )

    with c3:
        st.markdown(f"### {t('avg_rank_home')}")
        avg_rank_home = players_table.sort_values("avg_rank", ascending=True).head(3)
        st.dataframe(
            avg_rank_home[["player", "avg_rank", "best_rank"]],
            use_container_width=True
        )

# ---------- Player search ----------
with tabs[1]:
    st.markdown(f"## {t('player_search')}")

    q = st.text_input(t("filter_name"), "")
    if q:
        qn = norm_name(q)
        options = players_table[
            players_table["player_norm"].str.contains(qn, na=False)
        ]["player"].tolist()
        if not options:
            options = players_table["player"].tolist()
            st.info(t("no_matches"))
    else:
        options = players_table["player"].tolist()

    chosen = st.selectbox(t("select_player"), options=options, index=0)
    pn = norm_name(chosen)
    row = players_table[players_table["player_norm"] == pn].iloc[0]

    c1, c2, c3 = st.columns(3)
    c4, c5, c6 = st.columns(3)
    c7, c8, c9 = st.columns(3)

    with c1:
        st.markdown(metric_card(t("best_rank"), int(row["best_rank"])), unsafe_allow_html=True)
    with c2:
        st.markdown(metric_card(t("avg_rank"), f"{row['avg_rank']:.2f}"), unsafe_allow_html=True)
    with c3:
        st.markdown(metric_card(t("top5"), f"{int(row['top5_finishes'])} ({row['top5_rate']*100:.1f}%)"), unsafe_allow_html=True)

    with c4:
        st.markdown(metric_card(t("consistency"), f"{row['consistency']:.3f}"), unsafe_allow_html=True)
    with c5:
        st.markdown(metric_card(t("trend"), f"{row['trend_slope']:+.4f}"), unsafe_allow_html=True)
    with c6:
        st.markdown(metric_card(t("current_form"), f"{row['current_form']:.3f}"), unsafe_allow_html=True)

    with c7:
        st.markdown(metric_card(t("starts_2024"), int(row.get("starts_2024", 0))), unsafe_allow_html=True)
    with c8:
        st.markdown(metric_card(t("starts_2025"), int(row.get("starts_2025", 0))), unsafe_allow_html=True)
    with c9:
        st.markdown(metric_card(t("starts_2026"), int(row.get("starts_2026", 0))), unsafe_allow_html=True)

    ts = player_timeseries(df, pn)

    st.markdown(f"### {t('player_trend')}")
    st.line_chart(ts.set_index("competition")["performance_score"])

    st.markdown(f"### {t('recent_results')}")
    st.dataframe(ts.tail(20), use_container_width=True)

# ---------- Rankings ----------
with tabs[2]:
    st.markdown(f"## {t('rankings')}")

    st.markdown(f"### {t('most_top5')}")
    st.dataframe(
        players_table.sort_values("top5_finishes", ascending=False)[
            ["player", "top5_finishes", "top5_rate", "tournaments", "best_rank", "consistency"]
        ].head(50),
        use_container_width=True
    )

    st.markdown(f"### {t('best_avg_rank')}")
    st.dataframe(
        players_table.sort_values("avg_rank", ascending=True)[
            ["player", "avg_rank", "best_rank", "top5_rate", "consistency", "tournaments"]
        ].head(50),
        use_container_width=True
    )

    st.markdown(f"### {t('most_improving')}")
    st.dataframe(
        players_table.sort_values("trend_slope", ascending=False)[
            ["player", "trend_slope", "current_form", "top5_rate", "consistency", "tournaments"]
        ].head(50),
        use_container_width=True
    )

# ---------- Trends ----------
with tabs[3]:
    st.markdown(f"## {t('comparison_trends')}")

    options = players_table["player"].tolist()
    selected = st.multiselect(t("select_players"), options=options, default=options[:2])

    if selected:
        chart_df = []
        for p in selected:
            pn = norm_name(p)
            sub = df_perf[df_perf["player_norm"] == pn].sort_values("competition")[["competition", "performance_score"]].copy()
            sub["player"] = p
            chart_df.append(sub)

        if chart_df:
            chart_df = pd.concat(chart_df, ignore_index=True)
            pivot = chart_df.pivot(index="competition", columns="player", values="performance_score").sort_index()
            st.line_chart(pivot)

# ---------- Calculations ----------
with tabs[4]:
    st.markdown(f"## {t('calculation')}")

    if LANG == "Suomi":
        st.markdown("""
- **Paras sijoitus** = pienin rank  
- **Sijoituskeskiarvo** = sijoitusten keskiarvo  
- **Top 5** = montako kertaa rank ≤ 5  
- **Top 5 -osuus** = top5 / starts  
- **Performance score** = `1 − (rank−1)/(field_size−1)`  
- **Tasaisuus** = `1 − std(performance_score)`  
- **Trendi** = lineaarinen trendi performance_scorelle  
- **Nykykunto** = viimeisten 5 kilpailun performance_score-keskiarvo  
- **Vuosi** päätellään kilpailu-ID:n kahdesta ensimmäisestä numerosta:  
  - `24...` = 2024  
  - `25...` = 2025  
  - `26...` = 2026  
- **Score** = painotettu yhdistelmä:
  - 45 % avg_perf
  - 20 % top5_rate
  - 20 % consistency
  - 15 % trend_slope
        """)
    else:
        st.markdown("""
- **Best rank** = lowest rank  
- **Average rank** = mean rank  
- **Top 5** = number of times rank ≤ 5  
- **Top 5 rate** = top5 / starts  
- **Performance score** = `1 − (rank−1)/(field_size−1)`  
- **Consistency** = `1 − std(performance_score)`  
- **Trend** = linear slope of performance_score  
- **Current form** = mean performance_score of last 5 competitions  
- **Year** is inferred from the first two digits of competition ID:  
  - `24...` = 2024  
  - `25...` = 2025  
  - `26...` = 2026  
- **Score** = weighted combination:
  - 45% avg_perf
  - 20% top5_rate
  - 20% consistency
  - 15% trend_slope
        """)
