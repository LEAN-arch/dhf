# File: dhf_dashboard/utils/plot_utils.py

import plotly.express as px
import pandas as pd

def create_gantt_chart(tasks_df: pd.DataFrame, critical_path_ids: list):
    """Creates an interactive Gantt chart with Plotly."""
    
    # Add a column to identify critical path tasks for coloring
    tasks_df['is_critical'] = tasks_df['id'].isin(critical_path_ids)
    tasks_df['display_text'] = tasks_df.apply(lambda row: f"<b>{row['name']}</b><br>Status: {row['status']}<br>Completion: {row['completion_pct']}%", axis=1)

    fig = px.timeline(
        tasks_df,
        x_start="start_date",
        x_end="end_date",
        y="name",
        color="status",
        text="display_text",
        title="<b>Project Timeline and Critical Path</b>",
        color_discrete_map={
            "Completed": "green",
            "In Progress": "orange",
            "Not Started": "grey",
            "At Risk": "red"
        },
        category_orders={"name": tasks_df.sort_values("start_date", ascending=False)["name"].tolist()} # Sorts tasks top-to-bottom
    )
    
    # Customize the appearance of critical path bars
    for i, task in enumerate(tasks_df.to_dict('records')):
        if task['is_critical']:
            fig.data[i].marker.line = dict(color='red', width=4)

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="DHF Phase",
        legend_title="Status",
        font=dict(family="Arial, sans-serif", size=12),
        title_x=0.5,
    )
    fig.update_traces(textposition='inside')
    return fig

def create_status_pie_chart(tasks_df: pd.DataFrame):
    """Creates a pie chart showing the distribution of task statuses."""
    if tasks_df.empty:
        return px.pie(title="<b>Task Status Distribution</b>")

    status_counts = tasks_df['status'].value_counts().reset_index()
    status_counts.columns = ['status', 'count']
    
    fig = px.pie(
        status_counts,
        values='count',
        names='status',
        title="<b>Task Status Distribution</b>",
        color='status',
        color_discrete_map={
            "Completed": "green",
            "In Progress": "orange",
            "Not Started": "grey",
            "At Risk": "red"
        }
    )
    return fig
