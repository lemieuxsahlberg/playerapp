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
.highlight-card {
    background: #ffffff;
    border-radius: 16px;
    padding: 16px 18px;
    margin-bottom: 12px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.highlight-label {
    font-size: 0.9rem;
    color: #666;
    margin-bottom: 4px;
}
.highlight-value {
    font-size: 1.2rem;
    font-weight: 700;
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
    "recent_risers_home": {"Suomi": "Viimeisimpien kisojen nousijat", "English": "Latest competition risers"},
    "avg_rank_home": {"Suomi": "Paras sijoituskeskiarvo", "English": "Best average rank"},

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

    "most_top5": {"Suomi": "Eniten Top 5 -sijoituksia", "English": "Most Top 5 finishes"},
    "best_avg_rank": {"Suomi": "Paras sijoituskeskiarvo", "English": "Best average rank"},
    "recent_improvers": {"Suomi": "Viimeisimpien kisojen nousijat", "English": "Latest competition risers"},
    "long_term_dev": {"Suomi": "Pitkän aikavälin kehitys", "English": "Long-term development"},
    "search_players": {"Suomi": "Hae pelaajaa listasta", "English": "Search player in list"},

    "select_players": {"Suomi": "Valitse pelaajat", "English": "Select players"},
    "comparison_trends": {"Suomi": "Vertailutrendit", "English": "Comparison trends"},

    "no_data": {"Suomi": "Dataa ei löytynyt.", "English": "No data found."},
    "no_matches": {"Suomi": "Ei osumia — näytetään koko lista.", "English": "No matches — showing full list."},

    "footer": {
        "Suomi": "© 2026 Greta Sahlberg – Kaikki oikeudet pidätetään.",
        "English": "© 2026 Greta Sahlberg – All rights reserved."
    },

    "top_player_now": {"Suomi": "Top-pelaaja nyt", "English": "Top player right now"},
    "hot_player": {"Suomi": "Kuumin pelaaja", "English": "Hottest player"},
    "best_avg_rank_card": {"Suomi": "Paras sijoituskeskiarvo", "English": "Best average rank"},
    "latest3_note": {
        "Suomi": "Perustuu koko datan kolmeen viimeisimpään järjestettyyn kilpailuun.",
        "English": "Based on the latest 3 competitions in the full dataset."
    },
    "starts_by_year": {"Suomi": "Kisat vuosittain", "English": "Starts by year"},
}

def t(key):
    return TEXT.get(key, {"Suomi": key, "English": key}).get(LANG, key)

# ---------- Column labels ----------
COL_LABELS = {
    "player": {"Suomi": "Pelaaja", "English": "Player"},
    "top5_finishes": {"Suomi": "Top 5", "English": "Top 5"},
    "top5_rate": {"Suomi": "Top 5 -osuus", "English": "Top 5 rate"},
    "best_rank": {"Suomi": "Paras sijoitus", "English": "Best rank"},
    "avg_rank": {"Suomi": "Sijoituskeskiarvo", "English": "Average rank"},
    "consistency": {"Suomi": "Tasaisuus", "English": "Consistency"},
    "current_form": {"Suomi": "Nykykunto", "English": "Current form"},
    "trend_slope": {"Suomi": "Trendi", "English": "Trend"},
    "recent3_form": {"Suomi": "Viim. 3 kilpailun taso", "English": "Latest 3 competition form"},
    "recent3_trend": {"Suomi": "Viim. 3 kilpailun trendi", "English": "Latest 3 competition trend"},
    "tournaments": {"Suomi": "Kilpailuja", "English": "Competitions"},
    "competition": {"Suomi": "Kilpailu-ID", "English": "Competition ID"},
    "rank": {"Suomi": "Sijoitus", "English": "Rank"},
    "year": {"Suomi": "Vuosi", "English": "Year"},
    "score": {"Suomi": "Score", "English": "Score"},
}

def localize_columns(df_in: pd.DataFrame) -> pd.DataFrame:
    df_out = df_in.copy()
    rename_map = {}
    for c in df_out.columns:
        if c in COL_LABELS:
            rename_map[c] = COL_LABELS[c][LANG]
    return df_out.rename(columns=rename_map)

# ---------- Helpers ----------
def norm_name(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return s.lower().strip()

def year_from_competition(comp):
    """
    Esim.
    24xx -> 2024
    25xx -> 2025
    26xx -> 2026
    27xx -> 2027
    """
    try:
        comp = int(comp)
        prefix = int(str(comp)[:2])
        if 20 <= prefix <= 99:
            return 2000 + prefix
        return None
    except Exception:
        return None

def score_color(value, metric_type="high"):
    """
    metric_type:
    - 'high' = suurempi parempi
    - 'low' = pienempi parempi
    """
    if pd.isna(value):
        return "#999999"

    if metric_type == "high":
        if value >= 0.80:
            return "#2563eb"  # sininen = superhyvä
        elif value >= 0.60:
            return "#16a34a"  # vihreä = hyvä
        else:
            return "#dc2626"  # punainen = huono
    else:
        if value <= 5:
            return "#2563eb"
        elif value <= 12:
            return "#16a34a"
        else:
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
def load_data(path="results.parquet", version="v30") -> pd.DataFrame:
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

    # Siivotaan nimet
    df["player"] = df["player"].astype(str).str.strip()
    df = df[df["player"].notna()].copy()
    df = df[df["player"] != ""].copy()
    df = df[df["player"].str.lower() != "nan"].copy()
    df = df[~df["player"].isin(["-", "--", "None", "null"])].copy()

    # Poistetaan todennäköiset kilpailu-/otsikkorivit
    bad_pattern = (
        r"all players|osakilpailu|masters|rahola|kirjurinluoto|updated:|teams|"
        r"general|class|qualification|matchplay|finnish adventure golf masters"
    )
    df = df[~df["player"].str.contains(bad_pattern, case=False, na=False)].copy()

    # Vain nimet joissa on kirjaimia
    df = df[df["player"].str.contains(r"[A-Za-zÅÄÖåäö]", regex=True, na=False)].copy()

    # Poistetaan Erik Hjalmarsson (molemmat mahdolliset kirjoitusjärjestykset)
    excluded_norms = {"erik hjalmarsson", "hjalmarsson erik"}
    df["player_norm"] = df["player"].apply(norm_name)
    df = df[~df["player_norm"].isin(excluded_norms)].copy()

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

def compute_recent_global_stats(dfp: pd.DataFrame):
    """
    Koko datan 3 viimeisintä järjestettyä kilpailua (suurimmat ID:t)
    ja niissä pelanneiden pelaajien recent3_form / recent3_trend.
    """
    latest3 = sorted(dfp["competition"].dropna().unique())[-3:]
    recent = dfp[dfp["competition"].isin(latest3)].copy()

    rows = []
    for pn, sub in recent.sort_values("competition").groupby("player_norm"):
        y = sub["performance_score"].to_numpy()
        comp_count = sub["competition"].nunique()

        if len(y) >= 2:
            x = np.arange(len(y))
            recent3_trend = np.polyfit(x, y, 1)[0]
        else:
            recent3_trend = 0.0

        recent3_form = float(np.mean(y)) if len(y) else np.nan

        rows.append((pn, recent3_form, recent3_trend, comp_count))

    recent_df = pd.DataFrame(
        rows,
        columns=["player_norm", "recent3_form", "recent3_trend", "recent3_comp_count"]
    )
    return recent_df, latest3

def compute_player_table(df: pd.DataFrame):
    dfp = add_performance(df)

    # Top 5
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

    # Perusluvut
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

    # Koko historian trendi + nykykunto
    trend_rows = []
    for pn, sub in dfp.sort_values("competition").groupby("player_norm"):
        y = sub["performance_score"].to_numpy()

        if len(y) >= 3:
            x = np.arange(len(y))
            trend_slope = np.polyfit(x, y, 1)[0]
        else:
            trend_slope = 0.0

        current_form = float(np.mean(y[-5:])) if len(y) else np.nan

        trend_rows.append((pn, trend_slope, current_form))

    trend_df = pd.DataFrame(
        trend_rows,
        columns=["player_norm", "trend_slope", "current_form"]
    )

    out = agg.merge(base, on="player_norm", how="left").merge(trend_df, on="player_norm", how="left")

    # Koko datan 3 viimeisintä järjestettyä kilpailua
    recent_global_df, latest3 = compute_recent_global_stats(dfp)
    out = out.merge(recent_global_df, on="player_norm", how="left")

    # Vuosikohtaiset kisamäärät
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

    # Kokonaisscore
    out["score"] = (
        0.45 * out["avg_perf"] +
        0.20 * out["top5_rate"] +
        0.20 * out["consistency"] +
        0.15 * out["trend_slope"]
    )

    return out.sort_values("score", ascending=False), latest3

def player_timeseries(df: pd.DataFrame, player_norm: str) -> pd.DataFrame:
    dfp = add_performance(df)
    sub = dfp[dfp["player_norm"] == player_norm].sort_values("competition")
    return sub[["competition", "rank", "performance_score", "year"]]

# ---------- Load ----------
df = load_data()

# Jos haluat joskus sulkea kilpailuja pois, lisää tähän esim. [2409]
exclude_ids = []
if exclude_ids:
    df = df[~df["competition"].isin(exclude_ids)].copy()

if df.empty:
    st.error(t("no_data"))
    st.stop()

players_table, latest3_comp_ids = compute_player_table(df)
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

    best_score_row = players_table.sort_values("score", ascending=False).iloc[0]

    hot_candidates = players_table[players_table["recent3_comp_count"] >= 2].copy()
    if hot_candidates.empty:
        hot_candidates = players_table.copy()

    hottest_row = hot_candidates.sort_values(
        ["recent3_form", "recent3_trend"],
        ascending=False
    ).iloc[0]

    best_avg_rank_row = players_table.sort_values("avg_rank", ascending=True).iloc[0]

    st.markdown("### Nostoja")
    c1, c2, c3 = st.columns(3)

    with c1:
        color = score_color(best_score_row["score"], metric_type="high")
        value = f"{best_score_row['player']}<br><span style='font-size:1rem;'>Score {best_score_row['score']:.3f}</span>"
        st.markdown(highlight_metric_card(t("top_player_now"), value, color), unsafe_allow_html=True)

    with c2:
        hot_value = hottest_row["recent3_form"] + hottest_row["recent3_trend"]
        color = score_color(hot_value, metric_type="high")
        if LANG == "Suomi":
            value = (
                f"{hottest_row['player']}<br>"
                f"<span style='font-size:1rem;'>Kilpailut {', '.join(str(int(x)) for x in latest3_comp_ids)}: "
                f"{hottest_row['recent3_form']:.3f} / trendi {hottest_row['recent3_trend']:+.4f}</span>"
            )
        else:
            value = (
                f"{hottest_row['player']}<br>"
                f"<span style='font-size:1rem;'>Competitions {', '.join(str(int(x)) for x in latest3_comp_ids)}: "
                f"{hottest_row['recent3_form']:.3f} / trend {hottest_row['recent3_trend']:+.4f}</span>"
            )
        st.markdown(highlight_metric_card(t("hot_player"), value, color), unsafe_allow_html=True)
        st.caption(t("latest3_note"))

    with c3:
        color = score_color(best_avg_rank_row["avg_rank"], metric_type="low")
        value = f"{best_avg_rank_row['player']}<br><span style='font-size:1rem;'>{best_avg_rank_row['avg_rank']:.2f}</span>"
        st.markdown(highlight_metric_card(t("best_avg_rank_card"), value, color), unsafe_allow_html=True)

    st.markdown("### Top 3")
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(f"#### {t('top5_home')}")
        top5_home = players_table.sort_values(["top5_finishes", "top5_rate"], ascending=False).head(3)
        st.dataframe(
            localize_columns(top5_home[["player", "top5_finishes", "top5_rate"]]),
            use_container_width=True
        )

    with c2:
        st.markdown(f"#### {t('recent_risers_home')}")
        recent_home = hot_candidates.sort_values("recent3_trend", ascending=False).head(3)
        st.dataframe(
            localize_columns(recent_home[["player", "recent3_trend", "recent3_form"]]),
            use_container_width=True
        )

    with c3:
        st.markdown(f"#### {t('avg_rank_home')}")
        avg_rank_home = players_table.sort_values("avg_rank", ascending=True).head(3)
        st.dataframe(
            localize_columns(avg_rank_home[["player", "avg_rank", "best_rank"]]),
            use_container_width=True
        )

# ---------- Player Search ----------
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

    # Dynaamiset vuosikortit
    year_cols = [c for c in row.index if str(c).startswith("starts_")]
    year_cols = sorted(year_cols, key=lambda x: int(str(x).split("_")[1]))

    if year_cols:
        st.markdown(f"### {t('starts_by_year')}")
        year_cards_cols = st.columns(min(4, len(year_cols)))
        for i, col in enumerate(year_cols):
            year = col.split("_")[1]
            label = f"Kisat {year}" if LANG == "Suomi" else f"Starts {year}"
            with year_cards_cols[i % len(year_cards_cols)]:
                st.markdown(metric_card(label, int(row.get(col, 0))), unsafe_allow_html=True)

    ts = player_timeseries(df, pn)

    st.markdown(f"### {t('player_trend')}")
    st.line_chart(ts.set_index("competition")["performance_score"])

    st.markdown(f"### {t('recent_results')}")
    st.dataframe(
        localize_columns(ts.tail(20)),
        use_container_width=True
    )

# ---------- Rankings ----------
with tabs[2]:
    st.markdown(f"## {t('rankings')}")

    st.markdown(f"### {t('most_top5')}")
    st.dataframe(
        localize_columns(
            players_table.sort_values("top5_finishes", ascending=False)[
                ["player", "top5_finishes", "top5_rate", "tournaments", "best_rank", "consistency"]
            ].head(50)
        ),
        use_container_width=True
    )

    st.markdown(f"### {t('best_avg_rank')}")
    st.dataframe(
        localize_columns(
            players_table.sort_values("avg_rank", ascending=True)[
                ["player", "avg_rank", "best_rank", "top5_rate", "consistency", "tournaments"]
            ].head(50)
        ),
        use_container_width=True
    )

    st.markdown(f"### {t('recent_improvers')}")
    st.dataframe(
        localize_columns(
            hot_candidates.sort_values("recent3_trend", ascending=False)[
                ["player", "recent3_trend", "recent3_form", "top5_rate", "consistency", "tournaments"]
            ].head(50)
        ),
        use_container_width=True
    )

    st.markdown(f"### {t('long_term_dev')}")
    ranking_query = st.text_input(t("search_players"), "")

    overall_trend = players_table.sort_values("trend_slope", ascending=False).copy()

    if ranking_query:
        qn = norm_name(ranking_query)
        overall_trend = overall_trend[
            overall_trend["player_norm"].str.contains(qn, na=False)
        ].copy()

    st.dataframe(
        localize_columns(
            overall_trend[
                ["player", "trend_slope", "current_form", "top5_rate", "consistency", "tournaments"]
            ].head(100)
        ),
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
            sub = df_perf[df_perf["player_norm"] == pn].sort_values("competition")[
                ["competition", "performance_score"]
            ].copy()
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
- **Viimeisimpien kisojen nousijat** = koko datan 3 viimeisimmän järjestetyn kilpailun perusteella  
- **Kuumin pelaaja** = perustuu samaan 3 viimeisimmän järjestetyn kilpailun joukkoon  
- **Pitkän aikavälin kehitys** = koko datan trendi  
- **Vuosi** päätellään kilpailu-ID:n kahdesta ensimmäisestä numerosta  
  - `24...` = 2024  
  - `25...` = 2025  
  - `26...` = 2026  
  - `27...` = 2027  
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
- **Latest competition risers** = based on the latest 3 competitions in the whole dataset  
- **Hottest player** = based on the same latest 3 competitions in the whole dataset  
- **Long-term development** = trend over the full dataset  
- **Year** is inferred from the first two digits of competition ID  
  - `24...` = 2024  
  - `25...` = 2025  
  - `26...` = 2026  
  - `27...` = 2027  
- **Score** = weighted combination:
  - 45% avg_perf
  - 20% top5_rate
  - 20% consistency
  - 15% trend_slope
        """)

st.markdown("---")

if LANG == "Suomi":
    st.caption("© 2026 Greta Sahlberg – Kaikki oikeudet pidätetään.")
else:
    st.caption("© 2026 Greta Sahlberg – All rights reserved.")
