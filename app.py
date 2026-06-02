import streamlit as st
import pandas as pd
import numpy as np
import unicodedata

st.set_page_config(page_title="Pelaajahaku", layout="wide")

def norm_name(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return s.lower().strip()

@st.cache_data
def load_data(path="results.parquet", version="rescue_v1") -> pd.DataFrame:
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

    df["player"] = df["player"].astype(str).str.strip()
    df = df[df["player"].notna()].copy()
    df = df[df["player"] != ""].copy()
    df = df[df["player"].str.lower() != "nan"].copy()

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

    return agg.merge(base, on="player_norm", how="left").sort_values(
        ["top5_finishes", "best_rank"], ascending=[False, True]
    )

df = load_data()

if df.empty:
    st.error("Dataa ei löytynyt.")
    st.stop()

players = compute_player_table(df)

st.title("Pelaajahaku & tilastot")

st.caption(
    f"Kisoja: {df['competition'].nunique()} | "
    f"Pelaajia: {df['player'].nunique()} | "
    f"Rivejä: {len(df)}"
)

st.markdown("## Top 5 (eniten top5-sijoituksia)")
top5_home = players.sort_values(["top5_finishes", "top5_rate"], ascending=False).head(5)
st.dataframe(
    top5_home[["player", "top5_finishes", "top5_rate", "best_rank", "avg_rank", "consistency"]],
    use_container_width=True
)

st.markdown("## Pelaajahaku")
q = st.text_input("Suodata nimeä", "")

if q:
    qn = norm_name(q)
    options = players[players["player_norm"].str.contains(qn, na=False)]["player"].tolist()
    if not options:
        options = players["player"].tolist()
        st.info("Ei osumia — näytetään koko lista.")
else:
    options = players["player"].tolist()

chosen = st.selectbox("Valitse pelaaja", options=options, index=0)

row = players[players["player"] == chosen].iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Paras sijoitus", int(row["best_rank"]))
c2.metric("Sijoituskeskiarvo", f"{row['avg_rank']:.2f}")
c3.metric("Top 5", f"{int(row['top5_finishes'])} ({row['top5_rate']*100:.1f}%)")
c4.metric("Tasaisuus", f"{row['consistency']:.3f}")

st.markdown("## Pelaajan rivit")
player_rows = df[df["player"] == chosen].sort_values("competition")
st.dataframe(
    player_rows[["competition", "rank", "player"]],
    use_container_width=True
)

st.markdown("---")
st.markdown("© 2026 Sahlberg.G – All rights reserved.")
