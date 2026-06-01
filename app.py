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
def load_data(path="results.parquet", version="v3") -> pd.DataFrame:
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


