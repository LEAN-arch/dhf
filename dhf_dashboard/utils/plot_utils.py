# File: dhf_dashboard/utils/plot_utils.py

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def create_gantt_chart(tasks_df: pd.DataFrame, critical_path_ids: list):
    """
    Creates an interactive Gantt chart with a robust method for highlighting the critical path.
    """
    if tasks_df.empty:
        return go.Figure()

    # --- Step 1: Create the base Gantt chart with colors based on status ---
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
            "Completed": "#2ca02c",  # Muted green
            "In Progress": "#ff7f0e",  # Orange
            "Not Started": "#7f7f7f",  # Grey
            "At Risk": "#d62728"  # Red
        },
        # Sorts tasks top-to-bottom by start date
        category_orders={"name": tasks_df.sort_values("start_date", ascending=False)["name"].tolist()} 
    )

    # --- Step 2 (The Fix): Overlay a trace for the critical path borders ---
    # This is a robust method that does not rely on matching indices.
    
    # Filter the dataframe to only the tasks on the critical path
    critical_df = tasks_df[tasks_df['is_critical']].copy()

    if not critical_df.empty:
        # Calculate the duration for the bar trace
        critical_df['delta'] = pd.to_datetime(critical_df['end_date']) - pd.to_datetime(critical_df['start_date'])
        
        # Add a new, invisible bar trace that only has a red border
        fig.add_trace(go.Bar(
            x=critical_df['delta'],
            y=critical_df['name'],
            base=critical_df['start_date'],
            orientation='h',
            marker=dict(
                color='rgba(0, 0, 0, 0)',  # Transparent fill
                line=dict(color='red', width=4) # Thick red border
            ),
            # Do not show this extra trace in the legend
            showlegend=False,
            # Ensure hover info is disabled for this trace
            hoverinfo='none'
        ))

    # --- Step 3: Final figure styling ---
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
    # This function did not have an error and remains the same.
    if tasks_df.empty:
        return go.Figure(layout_title_text="<b>Task Status Distribution</b>")

    status_counts = tasks_df['status'].value_counts().reset_index()
    status_counts.columns = ['status', 'count']
    
    fig = px.pie(
        status_counts,
        values='count',
        names='status',
        title="<b>Task Status Distribution</b>",
        color='status',
        color_discrete_map={
            "Completed": "#2ca02c",
            "In Progress": "#ff7f0e",
            "Not Started": "#7f7f7f",
            "At Risk": "#d62728"
        }
    )
    return fig
