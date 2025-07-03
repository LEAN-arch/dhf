# File: dhf_dashboard/utils/plot_utils.py

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def create_progress_donut(completion_pct: float):
    # This function is fine and remains unchanged.
    fig = go.Figure(go.Indicator(mode="gauge+number", value=completion_pct, title={'text': "<b>Overall Project Progress</b>"}, number={'suffix': "%"}, gauge={'axis': {'range': [None, 100]},'bar': {'color': "#2ca02c"}}))
    fig.update_layout(height=250, margin=dict(l=10, r=10, t=50, b=10))
    return fig

def create_risk_profile_chart(hazards_df: pd.DataFrame):
    # This function is fine and remains unchanged.
    if hazards_df.empty: return go.Figure(layout_title_text="<b>Risk Profile</b>")
    risk_levels = ['Low', 'Medium', 'High']
    initial_counts = hazards_df['initial_risk'].value_counts().reindex(risk_levels, fill_value=0)
    final_counts = hazards_df['final_risk'].value_counts().reindex(risk_levels, fill_value=0)
    fig = go.Figure(data=[go.Bar(name='Initial', x=risk_levels, y=initial_counts.values), go.Bar(name='Residual', x=risk_levels, y=final_counts.values)])
    fig.update_layout(barmode='group', title_text="<b>Risk Profile (Initial vs. Residual)</b>", title_x=0.5)
    return fig

def create_action_item_chart(actions_df: pd.DataFrame):
    # This function is fine and remains unchanged.
    if actions_df.empty: return go.Figure(layout_title_text="<b>Action Items</b>")
    open_items_df = actions_df[actions_df['status'] != 'Completed']
    if open_items_df.empty: return go.Figure(layout_title_text="<b>No Open Action Items</b>")
    workload = pd.crosstab(index=open_items_df['owner'], columns=open_items_df['status'])
    fig = px.bar(workload, title="<b>Open Action Items by Owner & Status</b>")
    fig.update_layout(barmode='stack', title_x=0.5)
    return fig

# SME NOTE: The old Gantt chart function has been deleted and replaced with this simpler, more robust version.
# It no longer performs complex overlays. Instead, it expects a pre-processed DataFrame with color and border information.
def create_gantt_chart(tasks_df: pd.DataFrame):
    """
    Creates an interactive Gantt chart from a pre-processed DataFrame.
    The DataFrame must contain 'start_date', 'end_date', 'name', 'color', 'line', and 'display_text' columns.
    """
    if tasks_df.empty:
        return go.Figure()

    fig = px.timeline(
        tasks_df,
        x_start="start_date",
        x_end="end_date",
        y="name",
        color="color", # Use the pre-calculated color column
        title="<b>Project Timeline and Critical Path</b>",
        # Use the explicit colors from the DataFrame
        color_discrete_map="identity" 
    )

    # Update the traces with pre-calculated border and text info
    fig.update_traces(
        text=tasks_df['display_text'],
        textposition='inside',
        marker_line=tasks_df['line'].to_list() # Use the pre-calculated line column
    )
    
    # Standard layout updates
    fig.update_layout(
        showlegend=False, # Legend is redundant now
        title_x=0.5,
        xaxis_title="Date",
        yaxis_title="DHF Phase",
        font=dict(family="Arial, sans-serif", size=12),
        # Sort tasks top-to-bottom by start date
        yaxis_categoryorder='array',
        yaxis_categoryarray=tasks_df.sort_values("start_date", ascending=False)["name"].tolist()
    )
    return fig
