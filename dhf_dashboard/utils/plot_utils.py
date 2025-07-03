# File: dhf_dashboard/utils/plot_utils.py

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def create_progress_donut(completion_pct: float):
    """Creates a donut chart for overall project progress."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=completion_pct,
        title={'text': "<b>Overall Project Progress</b>", 'font': {'size': 20}},
        number={'suffix': "%", 'font': {'size': 24}},
        gauge={'axis': {'range': [None, 100]}, 'bar': {'color': "#2ca02c"}}
    ))
    fig.update_layout(height=250, margin=dict(l=10, r=10, t=50, b=10))
    return fig

def create_risk_profile_chart(hazards_df: pd.DataFrame):
    """Creates a bar chart comparing initial vs. residual risk levels."""
    if hazards_df.empty:
        return go.Figure(layout_title_text="<b>Risk Profile</b>")

    # --- SME Enhancement: Calculate risk levels dynamically from S x P matrix ---
    risk_map = {
        # Probability ->
        # Severity
        # |
        # v     1      2         3         4         5
        1: ["Low",   "Low",    "Low",    "Medium", "Medium"],
        2: ["Low",   "Low",    "Medium", "Medium", "High"],
        3: ["Low",   "Medium", "Medium", "High",   "High"],
        4: ["Medium","Medium", "High",   "High",   "High"],
        5: ["Medium","High",   "High",   "High",   "High"],
    }
    def get_risk_level(severity, probability):
        if pd.isna(severity) or pd.isna(probability): return "N/A"
        sev = int(severity)
        prob = int(probability)
        if 1 <= sev <= 5 and 1 <= prob <= 5:
            return risk_map[sev][prob-1]
        return "N/A"

    if 'initial_severity' in hazards_df.columns and 'initial_probability' in hazards_df.columns:
         hazards_df['initial_risk_level'] = hazards_df.apply(lambda row: get_risk_level(row['initial_severity'], row['initial_probability']), axis=1)
    if 'residual_severity' in hazards_df.columns and 'residual_probability' in hazards_df.columns:
        hazards_df['residual_risk_level'] = hazards_df.apply(lambda row: get_risk_level(row['residual_severity'], row['residual_probability']), axis=1)

    risk_levels = ['Low', 'Medium', 'High']
    initial_counts = hazards_df['initial_risk_level'].value_counts().reindex(risk_levels, fill_value=0)
    final_counts = hazards_df['residual_risk_level'].value_counts().reindex(risk_levels, fill_value=0)

    fig = go.Figure(data=[
        go.Bar(name='Initial', x=risk_levels, y=initial_counts.values, marker_color='#ff7f0e'),
        go.Bar(name='Residual', x=risk_levels, y=final_counts.values, marker_color='#1f77b4')
    ])
    fig.update_layout(
        barmode='group',
        title_text="<b>Risk Profile (Initial vs. Residual)</b>",
        title_x=0.5,
        legend_title_text='Risk State',
        xaxis_title="Calculated Risk Level",
        yaxis_title="Number of Hazards"
    )
    return fig

def create_action_item_chart(actions_df: pd.DataFrame):
    """Creates a stacked bar chart of open action items by owner and status."""
    if actions_df.empty:
        return go.Figure(layout_title_text="<b>No Action Items</b>")

    open_items_df = actions_df[actions_df['status'] != 'Completed'].copy()
    if open_items_df.empty:
        # Create a placeholder figure if there are no open items
        fig = go.Figure()
        fig.update_layout(
            title_text="<b>No Open Action Items</b>",
            title_x=0.5,
            xaxis={'visible': False},
            yaxis={'visible': False},
            annotations=[{
                'text': 'All action items are completed. 🎉',
                'xref': 'paper', 'yref': 'paper',
                'showarrow': False, 'font': {'size': 16}
            }]
        )
        return fig

    # --- SME Enhancement: Use crosstab for a more insightful workload view ---
    workload = pd.crosstab(
        index=open_items_df['owner'],
        columns=open_items_df['status']
    )
    # Ensure all possible open statuses are present for consistent coloring
    for status in ["Open", "In Progress", "Overdue"]:
        if status not in workload.columns:
            workload[status] = 0

    fig = px.bar(
        workload,
        title="<b>Open Action Items by Owner & Status</b>",
        labels={'value': 'Number of Items', 'owner': 'Assigned Owner'},
        color_discrete_map={"Open": "#ff7f0e", "In Progress": "#1f77b4", "Overdue": "#d62728"}
    )
    fig.update_layout(barmode='stack', title_x=0.5, legend_title_text='Status')
    return fig

def create_gantt_chart(tasks_df: pd.DataFrame):
    """Creates an interactive Gantt chart from a pre-processed DataFrame."""
    if tasks_df.empty:
        return go.Figure()

    fig = px.timeline(
        tasks_df,
        x_start="start_date",
        x_end="end_date",
        y="name",
        color="color",
        color_discrete_map="identity" # Use the color specified in the dataframe directly
    )

    fig.update_traces(
        text=tasks_df['display_text'],
        textposition='inside',
        insidetextanchor='middle',
        marker_line_color=tasks_df['line_color'],
        marker_line_width=tasks_df['line_width']
    )

    fig.update_layout(
        title_text="<b>Project Timeline and Critical Path</b>",
        title_x=0.5,
        showlegend=False,
        xaxis_title="Date",
        yaxis_title="DHF Phase",
        yaxis_categoryorder='array',
        yaxis_categoryarray=tasks_df.sort_values("start_date", ascending=False)["name"].tolist()
    )
    return fig
