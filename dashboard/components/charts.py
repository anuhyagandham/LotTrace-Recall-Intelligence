"""
Plotly Chart Helpers for LotTrace AI Streamlit Dashboard.
Consistent enterprise theme with Navy, Teal, and Slate accents.
"""

from typing import Dict, List, Any
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

CORPORATE_COLORS = ["#1E3E62", "#008DDA", "#41B06E", "#E72929", "#F59E0B", "#8B5CF6"]


def plot_recall_gauge(value: float, title: str = "Recall Completion Rate"):
    """Creates a modern radial gauge chart."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 18, 'color': '#1E3E62'}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#94A3B8"},
            'bar': {'color': "#008DDA"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#E2E8F0",
            'steps': [
                {'range': [0, 50], 'color': '#FEE2E2'},
                {'range': [50, 85], 'color': '#FEF3C7'},
                {'range': [85, 100], 'color': '#DCFCE7'},
            ],
            'threshold': {
                'line': {'color': "#166534", 'width': 4},
                'thickness': 0.75,
                'value': 90.0,
            }
        }
    ))
    fig.update_layout(height=260, margin=dict(l=20, r=20, t=40, b=20))
    return fig


def plot_bar_chart(df: pd.DataFrame, x_col: str, y_col: str, title: str, color_col: str = None):
    """Creates a clean styled corporate bar chart."""
    fig = px.bar(
        df,
        x=x_col,
        y=y_col,
        color=color_col,
        title=title,
        color_discrete_sequence=CORPORATE_COLORS,
    )
    fig.update_layout(
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        title_font=dict(size=16, color="#0B192C"),
        xaxis=dict(showgrid=False, linecolor="#CBD5E1"),
        yaxis=dict(gridcolor="#F1F5F9", linecolor="#CBD5E1"),
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig


def plot_genealogy_sankey(graph_data: Dict[str, Any]):
    """Creates a multi-echelon Sankey flow diagram from genealogy graph data."""
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])

    if not nodes or not edges:
        fig = go.Figure()
        fig.add_annotation(text="No genealogy flow data available", showarrow=False)
        return fig

    node_ids = [n["id"] for n in nodes]
    node_labels = [n["label"] for n in nodes]
    node_colors = [
        "#E72929" if n.get("is_contaminated") else
        ("#008DDA" if n.get("is_affected") else "#1E3E62")
        for n in nodes
    ]

    sources = []
    targets = []
    values = []

    for edge in edges:
        if edge["source"] in node_ids and edge["target"] in node_ids:
            sources.append(node_ids.index(edge["source"]))
            targets.append(node_ids.index(edge["target"]))
            values.append(edge.get("quantity") or 10.0)

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="#0B192C", width=0.5),
            label=node_labels,
            color=node_colors,
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color="rgba(30, 62, 98, 0.2)",
        )
    )])
    fig.update_layout(
        title_text="Traceability Genealogy Flow (Upstream & Downstream)",
        font_size=12,
        height=450,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig
