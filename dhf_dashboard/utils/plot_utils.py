# File: dhf_dashboard/utils/plot_utils.py

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def create_progress_donut(completion_pct: float):
    """Creates a donut-style gauge chart for overall project progress."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=completion_pct,
        title={'text': "<b>Overall Project Progress</b>", 'font': {'size': 20}},
        number={'suffix': "%", 'font': {'size': 24}},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "#2ca02c"},
            'steps': [
                {'range': [0, 50], 'color': 'lightgray'},
                {'range': [50, 80], 'color': 'gray'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    fig.update_layout(height=250, margin=dict(l=10, r=10, t=50, b=10))
    return fig

def create_risk_profile_chart(hazards_df: pd.DataFrame):
    """Creates a grouped bar chart showing the distribution of initial vs. residual risks."""
    if hazards_df.empty:
        return go.Figure(layout_title_text="<b>Risk Profile (Initial vs. Residual)</b>")

    risk_levels = ['Low', 'Medium', 'High']
    initial_counts = hazards_df['initial_risk'].value_counts().reindex(risk_levels, fill_value=0)
    final_counts = hazards_df['final_risk'].value_counts().reindex(risk_levels, fill_value=0)

    fig = go.Figure(data=[
        go.Bar(name='Initial Risk', x=risk_levels, y=initial_counts.values, marker_color='#ff7f0e'),
        go.Bar(name='Residual Risk', x=risk_levels, y=final_counts.values, marker_color='#1f77b4')
    ])
    fig.update_layout(
        barmode='group',
        title_text="<b>Risk Profile (Initial vs. Residual)</b>",
        title_x=0.5,
        xaxis_title="Risk Level",
        yaxis_title="Number of Hazards",
        legend_title="Risk Stage"
    )
    return fig

def create_action_item_chart(actions_df: pd.DataFrame):
    """Creates a stacked bar chart of open action items by owner and status."""
    if actions_df.empty:
        return go.Figure(layout_title_text="<b>Action Item Workload</b>")

    # Filter for only open items
    open_items_df = actions_df[actions_df['status'] != 'Completed'].copy()
    if open_items_df.empty:
         return go.Figure(layout_title_text="<b>Action Item Workload (No Open Items)</b>")

    # Create a cross-tabulation of owners vs. status
    workload = pd.crosstab(
        index=open_items_df['owner'],
        columns=open_items_df['status']
    )

    fig = px.bar(
        workload,
        title="<b>Open Action Items by Owner & Status</b>",
        labels={"value": "Count of Action Items", "owner": "Assigned To"},
        color_discrete_map={
            "In Progress": "#1f77b4",
            "Overdue": "#d62728",
            "Not Started": "#7f7f7f"
        }
    )
    fig.update_layout(barmode='stack', title_x=0.5)
    return fig


def create_gantt_chart(tasks_df: pd.DataFrame, critical_path_ids: list):
    """Creates an interactive Gantt chart with a robust method for highlighting the critical path."""
    if tasks_df.empty:
        return go.Figure()

    tasks_df['is_critical'] = tasks_df['id'].isin(critical_path_ids)
    tasks_df['display_text'] = tasks_df.apply(
        lambda row: f"<b>{row['name']}</b><br>Status: {row['status']}<br>Completion: {row['completion_pct']}%", 
        axis=1
    )
    fig = px.timeline(
        tasks_df,
        x_start="start_date",
        x_end="end_date",
        y="name",
        color="status",
        text="display_text",
        title="<b>Project Timeline and Critical Path</b>",
        color_discrete_map={
            "Completed": "#2ca02c",
            "In Progress": "#ff7f0e",
            "Not Started": "#7f7f7f",
            "At Risk": "#d62728"
        },
        category_orders={"name": tasks_df.sort_values("start_date", ascending=False)["name"].tolist()} 
    )
    critical_df = tasks_df[tasks_df['is_critical']].copy()
    if not critical_df.empty:
        critical_df['delta'] = pd.to_datetime(critical_df['end_date']) - pd.to_datetime(critical_df['start_date'])
        fig.add_trace(go.Bar(
            x=critical_df['delta'],
            y=critical_df['name'],
            base=critical_df['start_date'],
            orientation='h',
            marker=dict(
                color='rgba(0, 0, 0, 0)',
                line=dict(color='red', width=4)
            ),
            showlegend=False,
            hoverinfo='none'
        ))
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="DHF Phase",
        legend_title="Status",
        font=dict(family="Arial, sans-serif", size=12),
        title_x=0.5,
    )
    fig.update_traces(textposition='inside')
    return fig
