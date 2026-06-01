import streamlit as st
import pandas as pd
import numpy as np
import unicodedata

st.set_page_config(page_title="Pelaajahaku & tilastot", layout="wide")

# ---------- Utils ----------
def norm_name(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return s.lower().strip()

@st.cache_data
def load_data(path="results.parquet", version="v4") -> pd.DataFrame:
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

    df["player_norm"] = df["player"].apply(norm_name)
    return df

def parse_range_text(range_text: str):
    ids = []
    parts = [p.strip() for p in range_text.split(",") if p.strip()]
    for part in parts:
        if "-" in part:
            a, b = part.split("-", 1)
            a = int(a.strip())
            b = int(b.strip())
            if a > b:
                a, b = b, a
            ids.extend(range(a, b + 1))
        else:
            ids.append(int(part))
    return sorted(set(ids))

def add_performance(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    field_sizes = df.groupby("competition")["rank"].max().reset_index(name="field_size")
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

    total = dfp.groupby("player_norm").size().reset_index(name="starts")
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
    return sub[["competition", "rank", "performance_score"]]

# ---------- Load ----------
df = load_data()

# ---------- Page ----------
st.title("Pelaajahaku & tilastot")

# --- Kisarajaus ---
st.markdown("## Valitse kisat")

range_choice = st.selectbox(
    "Kisarajaus",
    [
        "Kaikki datassa olevat kilpailut",
        "Mukautettu kilpailu-ID-väli"
    ]
)

if range_choice == "Kaikki datassa olevat kilpailut":
    df_filtered = df.copy()
    range_text = None
else:
    range_text = st.text_input(
        "Kirjoita kilpailu-ID-välit",
        value="2401-2449,2501-2550,2601-2622"
    )
    wanted_ids = parse_range_text(range_text)
    df_filtered = df[df["competition"].isin(wanted_ids)].copy()

if df_filtered.empty:
    st.error("Tällä kisarajauksella ei löytynyt dataa.")
    st.stop()
    )

wanted_ids = parse_range_text(range_text)
df_filtered = df[df["competition"].isin(wanted_ids)].copy()

if df_filtered.empty:
    st.error("Tällä kisarajauksella ei löytynyt dataa.")
    st.stop()

players_table = compute_player_table(df_filtered)

st.caption(
    f"Käytössä kilpailut: {min(wanted_ids)}–{max(wanted_ids)} | "
    f"kisoja mukana: {df_filtered['competition'].nunique()} | "
    f"rivejä: {len(df_filtered)} | "
    f"pelaajia: {df_filtered['player'].nunique()}"
)

# --- Top 5 heti näkyviin ---
st.markdown("## Top 5 (eniten top5-sijoituksia)")
top5_board = players_table.sort_values(
    ["top5_finishes", "top5_rate"], ascending=False
).head(5)

st.dataframe(
    top5_board[["player", "top5_finishes", "top5_rate", "best_rank", "tournaments"]],
    use_container_width=True
)

# --- Selite ---
with st.expander("Miten luvut on laskettu?"):
    st.markdown("""
- **best_rank** = paras sijoitus (pienin rank)
- **avg_rank** = sijoitusten keskiarvo
- **top5_finishes** = montako kertaa rank ≤ 5
- **top5_rate** = top5_finishes / starts
- **performance_score** = 1 − (rank−1)/(field_size−1)
- **trend_slope** = lineaarinen trendi performance_scorelle
- **current_form** = viimeisten 5 kilpailun performance_score-keskiarvo
- **score** = painotettu yhdistelmä avg_perf, top5_rate, consistency, trend_slope
""")

# --- Tabit ---
tab1, tab2, tab3 = st.tabs(["Pelaajahaku", "Top-listat", "Trendit"])

with tab1:
    st.subheader("Pelaajahaku")

    q = st.text_input("Suodata nimeä", "")
    if q:
        qn = norm_name(q)
        options = players_table[
            players_table["player_norm"].str.contains(qn, na=False)
        ]["player"].tolist()
        if not options:
            options = players_table["player"].tolist()
            st.info("Ei osumia — näytetään koko lista.")
    else:
        options = players_table["player"].tolist()

    chosen = st.selectbox("Valitse pelaaja", options=options, index=0)
    pn = norm_name(chosen)
    row = players_table[players_table["player_norm"] == pn].iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Best rank", int(row["best_rank"]))
    c2.metric("Avg rank", f"{row['avg_rank']:.2f}")
    c3.metric("Top5", f"{int(row['top5_finishes'])} ({row['top5_rate']*100:.1f}%)")
    c4.metric("Trendi", f"{row['trend_slope']:+.4f}")

    ts = player_timeseries(df_filtered, pn)

    st.markdown("### Trendikäyrä (performance_score)")
    st.line_chart(ts.set_index("competition")["performance_score"])

    st.markdown("### Viimeisimmät kilpailut")
    st.dataframe(ts.tail(30), use_container_width=True)

with tab2:
    st.subheader("Top-listat")

    st.markdown("### Eniten top5-sijoituksia")
    st.dataframe(
        players_table.sort_values("top5_finishes", ascending=False)[
            ["player", "top5_finishes", "top5_rate", "tournaments", "best_rank"]
        ].head(50),
        use_container_width=True
    )

    st.markdown("### Nousujohteisin")
    st.dataframe(
        players_table.sort_values("trend_slope", ascending=False)[
            ["player", "trend_slope", "current_form", "tournaments", "top5_rate"]
        ].head(50),
        use_container_width=True
    )

    st.markdown("### Paras keskimääräinen suoritus")
    st.dataframe(
        players_table.sort_values("avg_perf", ascending=False)[
            ["player", "avg_perf", "best_rank", "top5_rate", "tournaments"]
        ].head(50),
        use_container_width=True
    )

with tab3:
    st.subheader("Trendit")

    options = players_table["player"].tolist()
    selected = st.multiselect("Valitse pelaajat", options=options, default=options[:2])

    if selected:
        dfp = add_performance(df_filtered)
        dfp["player_norm"] = dfp["player"].apply(norm_name)

        chart_df = []
        for p in selected:
            pn = norm_name(p)
            sub = dfp[dfp["player_norm"] == pn].sort_values("competition")[
                ["competition", "performance_score"]
            ].copy()
            sub["player"] = p
            chart_df.append(sub)

        chart_df = pd.concat(chart_df, ignore_index=True)
        pivot = chart_df.pivot(index="competition", columns="player", values="performance_score").sort_index()

        st.line_chart(pivot)
