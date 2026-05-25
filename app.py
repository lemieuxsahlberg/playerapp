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
def load_data(path="results.parquet") -> pd.DataFrame:
    df = pd.read_parquet(path).copy()
    df["rank"] = pd.to_numeric(df["rank"], errors="coerce")

    if "competition" in df.columns:
        df["competition"] = pd.to_numeric(df["competition"], errors="coerce")
    elif "source" in df.columns:
        df["competition"] = pd.to_numeric(df["source"].astype(str).str.extract(r"/(\d+)/")[0], errors="coerce")
    else:
        df["competition"] = np.nan

    df["player_norm"] = df["player"].apply(norm_name)
    return df

def add_performance(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    field_sizes = df.groupby("competition")["rank"].max().reset_index(name="field_size")
    df = df.merge(field_sizes, on="competition", how="left")
    df["performance_score"] = 1 - ((df["rank"] - 1) / (df["field_size"] - 1))
    df["performance_score"] = df["performance_score"].fillna(1.0)
    return df

def compute_player_table(df: pd.DataFrame) -> pd.DataFrame:
    dfp = add_performance(df)

    top5 = (dfp[dfp["rank"] <= 5]
            .groupby("player_norm").size().reset_index(name="top5_finishes"))

    total = dfp.groupby("player_norm").size().reset_index(name="starts")
    base = total.merge(top5, on="player_norm", how="left").fillna({"top5_finishes": 0})
    base["top5_rate"] = base["top5_finishes"] / base["starts"]

    agg = (dfp.groupby("player_norm")
           .agg(
               player=("player", "first"),
               tournaments=("competition", "count"),
               avg_rank=("rank", "mean"),
               best_rank=("rank", "min"),
               avg_perf=("performance_score", "mean"),
               std_perf=("performance_score", "std"),
           ).reset_index())
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
        0.45*out["avg_perf"] +
        0.20*out["top5_rate"] +
        0.20*out["consistency"] +
        0.15*out["trend_slope"]
    )
    return out.sort_values("score", ascending=False)

def player_timeseries(df: pd.DataFrame, player_norm: str) -> pd.DataFrame:
    dfp = add_performance(df)
    sub = dfp[dfp["player_norm"] == player_norm].sort_values("competition")
    return sub[["competition", "rank", "performance_score"]]

# ---------- App ----------
df = load_data()
players_table = compute_player_table(df)

# Sidebar: Top 5 always visible
st.sidebar.markdown("## Top 5 (eniten top5-sijoituksia)")
top5_board = players_table.sort_values(["top5_finishes", "top5_rate"], ascending=False).head(5)
st.sidebar.dataframe(
    top5_board[["player", "top5_finishes", "top5_rate"]],
    use_container_width=True
)

with st.expander("Miten luvut on laskettu? (avaa tästä)", expanded=False):
    st.markdown(
        """
### Käytetyt käsitteet

**1) Sijoitus (rank)**  
- Pienempi rank = parempi. Rank tulee suoraan datasta.

**2) Field size (kilpailun koko)**  
- Lasketaan per kilpailu:  
  **field_size = max(rank)** kyseisessä kilpailussa  
  (eli suurin sijoitusarvo = osallistujien määrä arviolta).

**3) Performance score (0–1)**  
- Muutetaan sijoitus vertailukelpoiseksi eri kokoisissa kilpailuissa:  
  **performance_score = 1 − (rank − 1) / (field_size − 1)**  
  - 1. sija → score = 1  
  - viimeinen → score = 0  
  - Jos field_size = 1 (vain yksi), score asetetaan 1.

**4) Avg rank / Best rank**  
- **avg_rank** = pelaajan rankien keskiarvo (kaikki kisat mukana)  
- **best_rank** = pelaajan pienin rank (paras sijoitus)

**5) Top 5 -tilastot**  
- **top5_finishes** = montako kertaa rank ≤ 5  
- **top5_rate** = top5_finishes / starts  
- **starts** = montako tulosriviä pelaajalla on (kisoja datassa)

**6) Consistency (tasaisuus)**  
- Lasketaan suorituspisteiden hajonnasta:  
  **std_perf = std(performance_score)**  
  **consistency = 1 − std_perf**  
  (suurempi = tasaisempi; jos std puuttuu, consistency = 0)

**7) Trend slope (nousujohteisuus / trendi)**  
- Järjestetään pelaajan kisat kilpailu-ID:n mukaan (proxy ajalle).  
- Tehdään yksinkertainen lineaarinen trendi `performance_score`:lle:  
  **trend_slope = slope( performance_score ~ kisaindeksi )**  
  - positiivinen → keskimäärin nouseva  
  - negatiivinen → laskeva

**8) Current form (nykykunto)**  
- **current_form = keskiarvo(performance_score viimeiset 5 kisaa)**  
  (jos kisoja < 5, käytetään niitä mitä on)

**9) Kokonais-score (järjestysluku top-listoihin)**  
- Painotettu yhdistelmä:
  - 45% avg_perf  
  - 20% top5_rate  
  - 20% consistency  
  - 15% trend_slope  

Kaava:
**score = 0.45·avg_perf + 0.20·top5_rate + 0.20·consistency + 0.15·trend_slope**

> Huom: voit muuttaa painoja, jos haluat korostaa esim. nousua tai top5-osumia.
        """
    )

st.title("Pelaajahaku & tilastot")

tab1, tab2, tab3 = st.tabs(["Pelaajahaku", "Top-listat", "Trendit"])

with tab1:
    st.subheader("Pelaajahaku")

    # Kevyt haku: suodattaa listaa
    q = st.text_input("Suodata (esim. greta / sahlberg)", "")
    if q:
        qn = norm_name(q)
        options = players_table[players_table["player_norm"].str.contains(qn, na=False)]["player"].tolist()
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

    ts = player_timeseries(df, pn)
    st.markdown("### Trendikäyrä (performance_score, parempi = ylempänä)")
    st.line_chart(ts.set_index("competition")["performance_score"])
    st.markdown("### Viimeisimmät kisat")
    st.dataframe(ts.tail(30), use_container_width=True)

with tab2:
    st.subheader("Top-listat")

    st.markdown("### Eniten top5-sijoituksia")
    st.dataframe(
        players_table.sort_values("top5_finishes", ascending=False)
        [["player","top5_finishes","top5_rate","tournaments","best_rank"]].head(50),
        use_container_width=True
    )

    st.markdown("### Nousujohteisin (trend_slope)")
    st.dataframe(
        players_table.sort_values("trend_slope", ascending=False)
        [["player","trend_slope","current_form","tournaments","top5_rate"]].head(50),
        use_container_width=True
    )

    st.markdown("### Paras keskimääräinen suoritus (avg_perf)")
    st.dataframe(
        players_table.sort_values("avg_perf", ascending=False)
        [["player","avg_perf","best_rank","top5_rate","tournaments"]].head(50),
        use_container_width=True
    )

with tab3:
    st.subheader("Trendit (valitse useita)")
    options = players_table["player"].tolist()
    selected = st.multiselect("Valitse pelaajat", options=options, default=options[:2])

    if selected:
        dfp = add_performance(df)
        dfp["player_norm"] = dfp["player"].apply(norm_name)

        chart_df = []
        for p in selected:
            pn = norm_name(p)

