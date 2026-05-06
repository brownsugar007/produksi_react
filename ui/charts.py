"""
Charts — Cumulative production charts with Plotly.
Side-by-side layout, per-point colored labels, clean design.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import OP_HOURS, COLORS
from calculations.formatting import fmt


# ── Modern Color Palette (Professional & Sophisticated) ──────────────────
CHART_COLORS = {
    "ob": {
        "line": "#6366f1",      # Indigo 500
        "fill": "rgba(99, 102, 241, 0.12)",
        "marker": "#4f46e5",    # Indigo 600
        "gradient_start": "rgba(99, 102, 241, 0.2)",
        "gradient_end": "rgba(99, 102, 241, 0.0)"
    },
    "ch": {
        "line": "#10b981",      # Emerald 500
        "fill": "rgba(16, 185, 129, 0.12)",
        "marker": "#059669",    # Emerald 600
        "gradient_start": "rgba(16, 185, 129, 0.2)",
        "gradient_end": "rgba(16, 185, 129, 0.0)"
    },
    "plan": "#64748b",          # Neutral gray
    "target": "#94a3b8",        # Light gray
    "success": "#10b981",       # Emerald
    "danger": "#ef4444",        # Red
    "warning": "#f59e0b",       # Amber
}


def build_cumm_chart(
    actual_df,
    value_col: str,
    plan_cumm_col: str,
    plan_daily_val: float,
    title: str,
    y_label: str,
    cumm_pit: pd.DataFrame,
    convert_kg: bool = False,
    palette: str = "ob",
    rain_df: pd.DataFrame = None,
    min_last_idx: int = -1,
) -> go.Figure:
    """Build cumulative chart with per-point labels."""

    colors = CHART_COLORS[palette]

    # --- Actual: group by Hour LU ---
    hourly = actual_df.groupby("Hour LU")[value_col].sum(min_count=1).reset_index()
    hourly.columns = ["Hour", "Actual"]
    if convert_kg:
        hourly["Actual"] = hourly["Actual"] / 1000

    hourly_full = pd.DataFrame({"Hour": OP_HOURS})
    hourly_full = hourly_full.merge(hourly, on="Hour", how="left")

    # --- Plan cumulative curve ---
    plan_full = pd.DataFrame({"Hour": OP_HOURS})
    if len(cumm_pit) > 0:
        plan_data = cumm_pit[["Hour LU", plan_cumm_col]].rename(columns={"Hour LU": "Hour"})
        plan_full = plan_full.merge(plan_data, on="Hour", how="left")
        plan_full[plan_cumm_col] = plan_full[plan_cumm_col].ffill().fillna(0)
    else:
        plan_full[plan_cumm_col] = 0

    # Last hour explicitly reported (Actual is not NaN)
    has_data = hourly_full[hourly_full["Actual"].notna()]
    last_actual_idx = has_data.index.max() if len(has_data) > 0 else -1
    # If a reference horizon is provided (e.g. from OB), extend our line to match
    if min_last_idx > last_actual_idx:
        last_actual_idx = min_last_idx

    # Safely fillna(0) for cumsum calculation
    hourly_full["Actual"] = hourly_full["Actual"].fillna(0)
    hourly_full["Cumm_Actual"] = hourly_full["Actual"].cumsum()

    # Dynamic Y-axis range calculation (Must happen before figure updates)
    all_y = []
    if last_actual_idx >= 0:
        all_y.append(hourly_full.iloc[:last_actual_idx + 1]["Cumm_Actual"].max())
    if plan_daily_val > 0:
        all_y.append(plan_daily_val)
    y_max = max(all_y) * 1.10 if all_y else 100

    fig = go.Figure()

    # 1) Plan daily target (dashed line)
    if plan_daily_val > 0:
        fig.add_trace(
            go.Scatter(
                x=[-0.5, len(OP_HOURS) - 0.5],
                y=[plan_daily_val, plan_daily_val],
                mode="lines",
                name="Plan (Target)",
                line=dict(color=colors["line"], width=1, dash="dash"),
                showlegend=True,
                hoverinfo="skip"
            )
        )
        # Annotation for the plan value
        fig.add_annotation(
            x=0, y=plan_daily_val,
            xref="paper", yref="y",
            text=f"<b>Plan: {fmt(plan_daily_val)}</b>",
            showarrow=False,
            font=dict(size=14, color=colors["line"], family="Rubik"),
            bgcolor="rgba(255, 255, 255, 0.7)",
            xanchor="left", yanchor="bottom"
        )

    # 2) Actual line
    if last_actual_idx >= 0:
        show = hourly_full.iloc[: last_actual_idx + 1].copy()
        total_actual = show["Cumm_Actual"].iloc[-1]
        hours_count = len(show[show["Actual"] > 0])
        avg_per_hour = total_actual / hours_count if hours_count > 0 else 0

        # Create custom hover text for each data point
        hover_texts = []
        for v, h in zip(show["Cumm_Actual"], show["Hour"]):
            if v >= 1000:
                hover_texts.append(f"{v/1000:.1f}k at {h}")
            else:
                hover_texts.append(f"{v:,.0f} at {h}")

        # Main line with colored markers
        marker_colors = [colors["marker"]] * len(show)
        text_colors = [
            CHART_COLORS["success"] if v >= plan_daily_val else CHART_COLORS["danger"]
            for v in show["Cumm_Actual"]
        ]
        x_coords = [OP_HOURS.index(h) for h in show["Hour"]]

        fig.add_trace(
            go.Scatter(
                x=x_coords,
                y=show["Cumm_Actual"],
                customdata=hover_texts,
                mode="lines+markers",
                name="Actual (dalam K)",
                line=dict(color=colors["line"], width=2.5, shape="spline", smoothing=1.3),
                marker=dict(size=7, color=marker_colors, line=dict(color="#fff", width=1.5)),
                hovertemplate="Actual<br><b>%{customdata}</b><extra></extra>",
            )
        )

        # Labels for points
        for i, row in show.iterrows():
            idx = show.index.get_loc(i)
            val = row["Cumm_Actual"]
            fig.add_annotation(
                x=x_coords[idx],
                y=val,
                text=f"<b>{val/1000:.1f}</b>",
                showarrow=False,
                yshift=14, # Sedikit dinaikkan agar tidak menabrak titik jika font lebih besar
                font=dict(size=14, color=text_colors[idx], family="Rubik"),
                opacity=0.9
            )

        # Last point highlight
        last = show.iloc[-1]
        is_above = last["Cumm_Actual"] >= plan_daily_val
        dot_color = CHART_COLORS["success"] if is_above else CHART_COLORS["danger"]

        fig.add_trace(
            go.Scatter(
                x=[x_coords[-1]],
                y=[last["Cumm_Actual"]],
                mode="markers",
                marker=dict(size=10, color=dot_color, line=dict(color="#fff", width=1.5)),
                showlegend=False,
                hoverinfo="skip",
            )
        )
        
        # Summary Header Figures
        gap = total_actual - plan_daily_val
        gap_color = CHART_COLORS["success"] if gap >= 0 else CHART_COLORS["danger"]
        
        summary_stats = [
            {"label": "ACTUAL", "value": f"{total_actual/1000:.1f}K", "sub": "MT Hari Ini" if palette=="ch" else "BCM Hari Ini", "color": colors["marker"]},
            {"label": "PLAN",   "value": f"{plan_daily_val/1000:.1f}K", "sub": "MT Target" if palette=="ch" else "BCM Target", "color": "#1f2937"},
            {"label": "GAP",    "value": f"{gap/1000:+.1f}K", "sub": f"{(gap/plan_daily_val*100):.1f}% {'lead' if gap>=0 else 'miss'}" if plan_daily_val>0 else "", "color": gap_color},
            {"label": "AVG RATE", "value": f"{avg_per_hour/1000:.1f}K", "sub": "MT / hr" if palette=="ch" else "BCM / hr", "color": "#1f2937"},
        ]

        # Title — own row at top
        fig.add_annotation(
            xref="paper", yref="paper", x=0, y=1.20,
            text=f"<span style='font-size:16px;color:#1a1f36;font-weight:bold;'>{title}</span>",
            showarrow=False, align="left", xanchor="left", yanchor="bottom"
        )

        # Stats row — right side, below title
        n_stats = len(summary_stats)
        for i, stat in enumerate(summary_stats):
            x_pos = 0.56 + (i / max(n_stats - 1, 1)) * 0.42
            
            # Value + Label combined
            fig.add_annotation(
                xref="paper", yref="paper", x=x_pos, y=1.12,
                text=(
                    f"<span style='font-size:9px;color:#64748b;font-weight:600;'>{stat['label']}</span>"
                    f"<br>"
                    f"<span style='font-size:15px;color:{stat['color']};font-weight:bold;'>{stat['value']}</span>"
                ),
                showarrow=False, align="center", xanchor="center", yanchor="bottom"
            )
            # Sub-label
            fig.add_annotation(
                xref="paper", yref="paper", x=x_pos, y=1.04,
                text=f"<span style='font-size:8px;color:#94a3b8;'>{stat['sub']}</span>",
                showarrow=False, align="center", xanchor="center", yanchor="bottom"
            )

    # --- Rain Bars Section ---
    if rain_df is not None and not rain_df.empty:
        rain_val_col = "Minute" if "Minute" in rain_df.columns else ("Duration" if "Duration" in rain_df.columns else None)
        if rain_val_col:
            rdf = rain_df.copy()
            rdf[rain_val_col] = pd.to_numeric(rdf[rain_val_col], errors="coerce").fillna(0)
            
            if rain_val_col == "Duration":
                rdf["RainVal"] = rdf[rain_val_col]
                unit = "hrs"
            else:
                rdf["RainVal"] = rdf[rain_val_col] / 60 
                unit = "hrs"
            
            rain_hourly = rdf.groupby("Hour LU")["RainVal"].sum().reset_index()
            rain_hourly.columns = ["Hour", "RainVal"]
            rain_full = pd.DataFrame({"Hour": OP_HOURS})
            rain_full = rain_full.merge(rain_hourly, on="Hour", how="left").fillna(0)
            rx_coords = list(range(len(OP_HOURS)))
            
            fig.add_trace(
                go.Bar(
                    x=rx_coords, y=rain_full["RainVal"], name="Rainfall",
                    marker=dict(color="rgba(14, 165, 233, 0.4)", line=dict(color="rgba(14, 165, 233, 0.7)", width=1)),
                    yaxis="y2",
                    hovertemplate=f"Rain: <b>%{{y:.1f}} {unit}</b> at %{{x}}<extra></extra>",
                    text=[f"<b>{v:.1f}h</b>" if v > 0 else "" for v in rain_full["RainVal"]],
                    textposition="outside",
                    textfont=dict(size=8, color="rgba(14, 165, 233, 1)", family="Rubik"),
                )
            )

    fig.update_layout(
        height=420,  # Restored height to give breathing room for rainfall bars below
        autosize=True,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            tickmode="array", tickvals=list(range(len(OP_HOURS))), ticktext=OP_HOURS,
            range=[-0.5, len(OP_HOURS) - 0.5], showgrid=False,
            linecolor="#e5e7eb", linewidth=1,
            tickfont=dict(size=12, color="#475569", family="Rubik"),
        ),
        yaxis=dict(
            showgrid=True, gridcolor="#f3f4f6", gridwidth=1,
            zeroline=False, showline=False,
            tickfont=dict(size=12, color="#9ca3af", family="Rubik"),
            # RAISED LINE: start at negative to leave room for bars (reduced gap)
            range=[-y_max * 0.25, y_max * 1.30],
            title=dict(text=y_label, font=dict(size=12, color="#64748b")),
        ),
        yaxis2=dict(
            title=dict(text="Rain (hrs)", font=dict(color="rgba(14, 165, 233, 1)", size=9)),
            tickfont=dict(color="rgba(14, 165, 233, 1)", size=7),
            anchor="x", overlaying="y", side="right",
            # SCALE BARS: Tighter range brings them closer to the line
            range=[0, 8], showgrid=False,
        ),
        legend=dict(
            orientation="h", y=-0.12,
            font=dict(size=10, color="#6b7280", family="Rubik"),
            bgcolor="rgba(0,0,0,0)",
            traceorder="normal",
        ),
        margin=dict(t=110, b=40, r=35, l=50),
        font=dict(family="Rubik"),
    )

    # 4) X-Axis Label (Time WITA)
    fig.add_annotation(
        xref="paper", yref="paper",
        x=-0.01, y=-0.06,
        text="Time (WITA)",
        showarrow=False,
        font=dict(size=9, color="#475569", family="Rubik"),
        xanchor="right",
        yanchor="middle"
    )

    # 5) Unit legend note — angka pada titik dot
    unit_note = "● Angka titik = K (ribuan MT)" if palette == "ch" else "● Angka titik = K (ribuan BCM)"
    fig.add_annotation(
        xref="paper", yref="paper",
        x=1.0, y=-0.14,  # Diturunkan sedikit dari -0.12 ke -0.14 agar sejajar horizontal dengan legend
        text=f"<i>{unit_note}</i>",
        showarrow=False,
        font=dict(size=8, color="#94a3b8", family="Rubik"),
        xanchor="right",
        yanchor="middle"
    )

    return fig


def _get_last_hour_idx(df, value_col: str) -> int:
    """Get the index (in OP_HOURS) of the last hour that has reported data."""
    if df.empty or value_col not in df.columns or "Hour LU" not in df.columns:
        return -1
    hourly = df.groupby("Hour LU")[value_col].sum(min_count=1).reset_index()
    hourly.columns = ["Hour", "Val"]
    reported = hourly[hourly["Val"].notna()]
    if reported.empty:
        return -1
    # Map to OP_HOURS index
    indices = [OP_HOURS.index(h) for h in reported["Hour"] if h in OP_HOURS]
    return max(indices) if indices else -1


def render_production_charts(
    ob_f, ch_f, cumm_pit, plan_ob_val: float, plan_ch_val: float, rain_f: pd.DataFrame = None
):
    """Render OB and CH cumulative charts side-by-side."""
    st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)

    # Compute OB's last reported hour index to sync CH's time horizon
    ob_last_idx = _get_last_hour_idx(ob_f, "Volume")

    col_ob, col_ch = st.columns(2, gap="small")

    with col_ob:
        fig_ob = build_cumm_chart(
            ob_f, "Volume", "Cumm OB", plan_ob_val,
            "Cumulative OB Production", "BCM",
            cumm_pit, palette="ob",
            rain_df=rain_f
        )
        st.plotly_chart(
            fig_ob, 
            key="chart_ob_cumm", 
            use_container_width=True, 
            config={"responsive": True, "displayModeBar": False}
        )

    with col_ch:
        fig_ch = build_cumm_chart(
            ch_f, "Volume", "Cumm CH", plan_ch_val,
            "Cumulative Coal Hauling", "MT",
            cumm_pit, convert_kg=False, palette="ch",
            rain_df=rain_f,
            min_last_idx=ob_last_idx,
        )
        st.plotly_chart(
            fig_ch, 
            key="chart_ch_cumm", 
            use_container_width=True, 
            config={"responsive": True, "displayModeBar": False}
        )
