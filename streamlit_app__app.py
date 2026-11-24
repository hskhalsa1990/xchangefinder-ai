"""
XchangeFinder — Interactive Streamlit Dashboard
SocGen Finhack 2017 · Team 17 (FinNoobs)
"""

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="XchangeFinder Dashboard",
    page_icon="💱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Paths ────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "db" / "XchangeFinder.db"


# ── Data loading (cached) ────────────────────────────────────
@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)
    stores = pd.read_sql("SELECT * FROM stores", conn)
    users = pd.read_sql("SELECT * FROM users", conn)
    user_rates = pd.read_sql("SELECT * FROM userRateSubmissions", conn)
    store_rates = pd.read_sql("SELECT * FROM storeRateSubmissions", conn)
    safety = pd.read_sql("SELECT * FROM safetyRatings", conn)
    conn.close()
    return stores, users, user_rates, store_rates, safety


@st.cache_data
def build_summary(stores, user_rates, store_rates, safety):
    summary = stores[["storeUUID", "displayName", "latitude", "longitude", "time"]].copy()
    summary = summary.rename(columns={"displayName": "Store", "time": "Opening Hours"})

    avg_s = safety.groupby("storeUUID")["rating"].agg(["mean", "count"]).reset_index()
    avg_s.columns = ["storeUUID", "Avg Safety", "Num Ratings"]
    summary = summary.merge(avg_s, on="storeUUID", how="left")

    ur = user_rates.groupby("storeUUID").size().reset_index(name="User Rate Subs")
    summary = summary.merge(ur, on="storeUUID", how="left")

    sr = store_rates.groupby("storeUUID").size().reset_index(name="Official Rate Subs")
    summary = summary.merge(sr, on="storeUUID", how="left")

    summary = summary.fillna(0)
    summary["Avg Safety"] = summary["Avg Safety"].round(2)
    return summary.sort_values("Avg Safety", ascending=False).reset_index(drop=True)


@st.cache_data
def build_rate_comparison(user_rates, store_rates):
    user_pair = (
        user_rates.groupby(["fromCurrency", "toCurrency"])
        .agg(
            User_Avg=("rate", "mean"),
            User_Min=("rate", "min"),
            User_Max=("rate", "max"),
            User_Count=("rate", "count"),
        )
        .reset_index()
    )
    store_pair = (
        store_rates.groupby(["fromCurrency", "toCurrency"])
        .agg(
            Store_Avg=("rate", "mean"),
            Store_Min=("rate", "min"),
            Store_Max=("rate", "max"),
            Store_Count=("rate", "count"),
        )
        .reset_index()
    )
    rc = pd.merge(user_pair, store_pair, on=["fromCurrency", "toCurrency"], how="outer").fillna(0)
    rc["Pair"] = rc["fromCurrency"] + " → " + rc["toCurrency"]
    rc["Diff (User−Store)"] = (rc["User_Avg"] - rc["Store_Avg"]).round(4)
    cols = [
        "Pair",
        "User_Avg",
        "Store_Avg",
        "Diff (User−Store)",
        "User_Count",
        "Store_Count",
        "User_Min",
        "User_Max",
        "Store_Min",
        "Store_Max",
    ]
    return rc[cols].round(4).sort_values("User_Count", ascending=False)


# ── Load ─────────────────────────────────────────────────────
stores, users, user_rates, store_rates, safety = load_data()
summary = build_summary(stores, user_rates, store_rates, safety)
rate_cmp = build_rate_comparison(user_rates, store_rates)

# ── Sidebar ──────────────────────────────────────────────────
st.sidebar.title("💱 XchangeFinder")
st.sidebar.markdown("**SocGen Finhack 2017 · Team 17**")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    [
        "🏠 Overview",
        "🏪 Stores",
        "💱 Rates",
        "⭐ Safety",
        "🗺️ Map & 3D",
        "📊 Comparisons",
        "ℹ️ About",
    ],
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    f"""
**Quick Stats**
| Metric | Value |
|--------|-------|
| Stores | {len(stores)} |
| Users | {len(users)} |
| User rates | {len(user_rates)} |
| Store rates | {len(store_rates)} |
| Safety votes | {len(safety)} |
"""
)

# ══════════════════════════════════════════════════════════════
# PAGE: Overview
# ══════════════════════════════════════════════════════════════
if page == "🏠 Overview":
    st.title("💱 XchangeFinder Dashboard")
    st.markdown("Crowdsourced currency-exchange rates & shop safety — Hong Kong")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Stores", len(stores))
    c2.metric("Users", len(users))
    c3.metric("User Rate Submissions", len(user_rates))
    c4.metric("Official Rate Submissions", len(store_rates))
    c5.metric("Safety Ratings", len(safety))

    st.markdown("---")
    col_a, col_b = st.columns(2)

    with col_a:
        fig = px.bar(
            summary,
            x="Store",
            y="Avg Safety",
            color="Avg Safety",
            color_continuous_scale="Viridis",
            text="Avg Safety",
            title="Average Safety Rating by Store",
            hover_data=["Num Ratings", "User Rate Subs", "Official Rate Subs"],
        )
        fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig.update_layout(yaxis_range=[0, 5.5], height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        sub_long = summary.melt(
            id_vars=["Store"],
            value_vars=["User Rate Subs", "Official Rate Subs"],
            var_name="Source",
            value_name="Submissions",
        )
        sub_long["Source"] = sub_long["Source"].replace(
            {"User Rate Subs": "User", "Official Rate Subs": "Store"}
        )
        fig2 = px.bar(
            sub_long,
            x="Store",
            y="Submissions",
            color="Source",
            barmode="group",
            title="Rate Submissions: User vs Store",
            color_discrete_map={"User": "#3498db", "Store": "#e74c3c"},
            text="Submissions",
        )
        fig2.update_traces(textposition="outside")
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Store Summary Table")
    st.dataframe(summary, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════
# PAGE: Stores
# ══════════════════════════════════════════════════════════════
elif page == "🏪 Stores":
    st.title("🏪 Exchange Stores")

    store_names = summary["Store"].tolist()
    selected = st.multiselect("Filter stores", store_names, default=store_names)

    filtered = summary[summary["Store"].isin(selected)]

    st.dataframe(
        filtered.style.background_gradient(subset=["Avg Safety"], cmap="RdYlGn"),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")
    st.subheader("Store Details")
    for _, row in filtered.iterrows():
        with st.expander(f"📍 {row['Store']}  ·  Safety {row['Avg Safety']:.2f} ★"):
            c1, c2, c3 = st.columns(3)
            c1.write(f"**Lat / Lon:** {row['latitude']:.5f}, {row['longitude']:.5f}")
            c2.write(f"**Hours:** {row['Opening Hours']}")
            c3.write(f"**Ratings:** {int(row['Num Ratings'])}")
            c1.write(f"**User rate subs:** {int(row['User Rate Subs'])}")
            c2.write(f"**Official rate subs:** {int(row['Official Rate Subs'])}")

# ══════════════════════════════════════════════════════════════
# PAGE: Rates
# ══════════════════════════════════════════════════════════════
elif page == "💱 Rates":
    st.title("💱 Exchange Rates")

    tab1, tab2, tab3 = st.tabs(["Comparison Table", "Heatmap", "Boxplots"])

    with tab1:
        st.subheader("User vs Store Rate Comparison")
        st.dataframe(rate_cmp, use_container_width=True, hide_index=True)

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                name="User Avg",
                x=rate_cmp["Pair"],
                y=rate_cmp["User_Avg"],
                marker_color="#3498db",
            )
        )
        fig.add_trace(
            go.Bar(
                name="Store Avg",
                x=rate_cmp["Pair"],
                y=rate_cmp["Store_Avg"],
                marker_color="#e74c3c",
            )
        )
        fig.update_layout(
            barmode="group",
            title="Average Rate by Currency Pair",
            yaxis_title="Rate",
            height=450,
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        if len(user_rates) > 0:
            heat = user_rates.pivot_table(
                index="fromCurrency", columns="toCurrency", values="rate", aggfunc="mean"
            )
            fig = px.imshow(
                heat,
                text_auto=".3f",
                color_continuous_scale="YlOrRd",
                title="User-Submitted Rate Heatmap",
                labels=dict(x="To", y="From", color="Avg Rate"),
                aspect="auto",
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No user rate data.")

    with tab3:
        user_c = user_rates.copy()
        user_c["Source"] = "User"
        store_c = store_rates.copy()
        store_c["Source"] = "Store"
        combined = pd.concat(
            [
                user_c[["fromCurrency", "toCurrency", "rate", "Source"]],
                store_c[["fromCurrency", "toCurrency", "rate", "Source"]],
            ],
            ignore_index=True,
        )
        combined["Pair"] = combined["fromCurrency"] + "→" + combined["toCurrency"]

        fig = px.box(
            combined,
            x="Pair",
            y="rate",
            color="Source",
            title="Rate Distribution by Pair — User vs Store",
            color_discrete_map={"User": "#3498db", "Store": "#e74c3c"},
            points="all",
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

    # Live rates section
    st.markdown("---")
    st.subheader("🌐 Live Official Rates (forex-python)")
    try:
        from forex_python.converter import CurrencyRates

        c = CurrencyRates()
        pairs = [("USD", "CNY"), ("USD", "HKD"), ("EUR", "USD"), ("HKD", "CNY"), ("SGD", "USD"), ("EUR", "CNY")]
        rows = []
        for frm, to in pairs:
            try:
                r = c.get_rate(frm, to)
                rows.append({"Pair": f"{frm} → {to}", "Live Rate": round(r, 4)})
            except Exception:
                rows.append({"Pair": f"{frm} → {to}", "Live Rate": None})
        live_df = pd.DataFrame(rows)
        st.dataframe(live_df, use_container_width=True, hide_index=True)

        live_ok = live_df.dropna()
        if len(live_ok):
            fig = px.bar(
                live_ok,
                x="Pair",
                y="Live Rate",
                color="Live Rate",
                color_continuous_scale="Teal",
                text="Live Rate",
                title="Live Official Exchange Rates",
            )
            fig.update_traces(texttemplate="%{text:.4f}", textposition="outside")
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Could not fetch live rates: {e}")

# ══════════════════════════════════════════════════════════════
# PAGE: Safety
# ══════════════════════════════════════════════════════════════
elif page == "⭐ Safety":
    st.title("⭐ Safety Ratings")

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            summary,
            x="Store",
            y="Avg Safety",
            color="Avg Safety",
            color_continuous_scale="RdYlGn",
            range_color=[1, 5],
            text="Avg Safety",
            title="Average Safety by Store",
            hover_data=["Num Ratings"],
        )
        fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig.update_layout(yaxis_range=[0, 5.5], height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.histogram(
            safety,
            x="rating",
            nbins=5,
            title="Safety Rating Distribution",
            labels={"rating": "Rating (1–5)"},
            color_discrete_sequence=["#9b59b6"],
            marginal="box",
        )
        fig.update_layout(bargap=0.15, height=400)
        fig.update_xaxes(dtick=1)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Leaderboard")
    safety_detail = safety.merge(stores[["storeUUID", "displayName"]], on="storeUUID", how="left")
    leaderboard = (
        safety_detail.groupby("displayName")
        .agg(
            Average_Rating=("rating", "mean"),
            Total_Votes=("rating", "count"),
            Min=("rating", "min"),
            Max=("rating", "max"),
        )
        .round(2)
        .sort_values("Average_Rating", ascending=False)
    )
    st.dataframe(leaderboard, use_container_width=True)

    st.subheader("Correlation: Safety vs Activity")
    corr = summary[["Avg Safety", "Num Ratings", "User Rate Subs", "Official Rate Subs"]].corr().round(3)
    fig = px.imshow(
        corr,
        text_auto=True,
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        title="Correlation Matrix",
        aspect="auto",
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# PAGE: Map & 3D
# ══════════════════════════════════════════════════════════════
elif page == "🗺️ Map & 3D":
    st.title("🗺️ Map & 3D Views")

    map_df = stores.merge(
        summary[["storeUUID", "Avg Safety", "Num Ratings", "User Rate Subs", "Official Rate Subs"]],
        on="storeUUID",
        how="left",
    )

    tab1, tab2, tab3 = st.tabs(["2D Map", "3D Location + Safety", "3D Rate Comparison"])

    with tab1:
        fig = px.scatter(
            map_df,
            x="longitude",
            y="latitude",
            size="Avg Safety",
            color="Avg Safety",
            hover_name="displayName",
            hover_data={
                "longitude": ":.5f",
                "latitude": ":.5f",
                "Avg Safety": ":.2f",
                "Num Ratings": True,
                "User Rate Subs": True,
                "time": True,
            },
            color_continuous_scale="RdYlGn",
            range_color=[1, 5],
            size_max=45,
            title="Hong Kong Exchange Stores (Size & Color = Safety)",
        )
        fig.update_layout(height=550)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.caption("Drag to rotate · Scroll to zoom")
        fig = px.scatter_3d(
            map_df,
            x="longitude",
            y="latitude",
            z="Avg Safety",
            color="Avg Safety",
            size="Avg Safety",
            hover_name="displayName",
            hover_data={"Avg Safety": ":.2f", "Num Ratings": True},
            color_continuous_scale="RdYlGn",
            range_color=[1, 5],
            size_max=30,
            title="3D: Latitude × Longitude × Safety",
        )
        fig.update_layout(
            height=650,
            scene=dict(zaxis=dict(range=[0, 5.5]), camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))),
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.caption("Drag to rotate · Scroll to zoom")
        if len(rate_cmp) > 0:
            pairs = rate_cmp["Pair"].tolist()
            x = list(range(len(pairs)))
            user_r = rate_cmp["User_Avg"].tolist()
            store_r = rate_cmp["Store_Avg"].tolist()

            fig = go.Figure()
            fig.add_trace(
                go.Scatter3d(
                    x=x,
                    y=[0] * len(x),
                    z=user_r,
                    mode="lines+markers",
                    name="User Avg",
                    line=dict(color="#3498db", width=5),
                    marker=dict(size=8, color="#3498db"),
                    text=pairs,
                    hovertemplate="Pair: %{text}<br>User: %{z:.4f}<extra></extra>",
                )
            )
            fig.add_trace(
                go.Scatter3d(
                    x=x,
                    y=[1] * len(x),
                    z=store_r,
                    mode="lines+markers",
                    name="Store Avg",
                    line=dict(color="#e74c3c", width=5),
                    marker=dict(size=8, color="#e74c3c"),
                    text=pairs,
                    hovertemplate="Pair: %{text}<br>Store: %{z:.4f}<extra></extra>",
                )
            )
            for i in range(len(x)):
                fig.add_trace(
                    go.Scatter3d(
                        x=[x[i], x[i]],
                        y=[0, 1],
                        z=[user_r[i], store_r[i]],
                        mode="lines",
                        line=dict(color="gray", width=2, dash="dash"),
                        showlegend=False,
                        hoverinfo="skip",
                    )
                )
            fig.update_layout(
                title="3D Rate Comparison: User vs Store",
                height=650,
                scene=dict(
                    xaxis=dict(tickvals=x, ticktext=pairs, title="Pair"),
                    yaxis=dict(tickvals=[0, 1], ticktext=["User", "Store"], title="Source"),
                    zaxis=dict(title="Rate"),
                    camera=dict(eye=dict(x=1.5, y=1.8, z=1.0)),
                ),
            )
            st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════
# PAGE: Comparisons
# ══════════════════════════════════════════════════════════════
elif page == "📊 Comparisons":
    st.title("📊 Side-by-side Comparisons")

    st.subheader("Store Comparison Table")
    st.dataframe(summary, use_container_width=True, hide_index=True)

    st.subheader("Rate Comparison Table")
    st.dataframe(rate_cmp, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("Most Active Rate Submitters")
    top_users = (
        user_rates.groupby("username")
        .size()
        .reset_index(name="Submissions")
        .sort_values("Submissions", ascending=False)
    )
    col1, col2 = st.columns([1, 2])
    with col1:
        st.dataframe(top_users, use_container_width=True, hide_index=True)
    with col2:
        fig = px.bar(
            top_users,
            x="username",
            y="Submissions",
            color="Submissions",
            color_continuous_scale="Plasma",
            text="Submissions",
            title="Top Users by Submissions",
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

    # Download buttons
    st.markdown("---")
    st.subheader("Download Data")
    c1, c2, c3 = st.columns(3)
    c1.download_button(
        "📥 Store Summary CSV",
        summary.to_csv(index=False),
        "store_summary.csv",
        "text/csv",
    )
    c2.download_button(
        "📥 Rate Comparison CSV",
        rate_cmp.to_csv(index=False),
        "rate_comparison.csv",
        "text/csv",
    )
    c3.download_button(
        "📥 Safety Ratings CSV",
        safety.to_csv(index=False),
        "safety_ratings.csv",
        "text/csv",
    )

# ══════════════════════════════════════════════════════════════
# PAGE: About
# ══════════════════════════════════════════════════════════════
elif page == "ℹ️ About":
    st.title("ℹ️ About XchangeFinder")
    st.markdown(
        """
### Project
**XchangeFinder (FinNoobs)** — SocGen Finhack 2017, Team 17

A Flask web app that helps users find currency-exchange shops (mainly Hong Kong),
compare crowdsourced vs official rates, and rate shop safety.

### Features in this dashboard
- **Overview** — KPIs + key charts  
- **Stores** — filterable store table & details  
- **Rates** — comparison tables, heatmap, boxplots, live forex rates  
- **Safety** — ratings, distribution, correlation  
- **Map & 3D** — interactive 2D/3D geographic & rate views  
- **Comparisons** — side-by-side tables + CSV download  

### Tech
| Layer | Stack |
|-------|-------|
| Original app | Flask, SQLite, forex-python, Bootstrap |
| Dashboard | Streamlit + Plotly |
| Analysis notebook | Jupyter + Plotly |

### Database tables
`stores` · `users` · `userRateSubmissions` · `storeRateSubmissions` · `safetyRatings`

### Run the original Flask app
```bash
pip install -r requirements.txt
python run.py
# → http://localhost:5000
```

### Run this dashboard
```bash
streamlit run streamlit_app/app.py
```
"""
    )
    st.info("Educational / hackathon project from 2017. Use for learning purposes.")
