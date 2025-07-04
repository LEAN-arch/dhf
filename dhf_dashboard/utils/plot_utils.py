# File: dhf_dashboard/utils/plot_utils.py
# --- Enhanced Version ---
"""
Plotting utilities for creating standardized Plotly visualizations.

This module contains functions that generate various Plotly figures
(donuts, bar charts, etc.) used throughout the DHF dashboard application.
These functions encapsulate the plotting logic, ensuring a consistent
visual style and robust error handling.
"""

# --- Standard Library Imports ---
import logging
from typing import List

# --- Third-party Imports ---
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pandas.api.types import is_numeric_dtype

# --- Setup Logging ---
logger = logging.getLogger(__name__)


def create_progress_donut(completion_pct: float) -> go.Figure:
    """
    Creates a donut-style gauge indicator for overall project progress.

    Args:
        completion_pct (float): The overall project completion percentage (0-100).

    Returns:
        go.Figure: A Plotly Figure object representing the gauge. Returns a
                   placeholder figure on error.
    """
    try:
        if not isinstance(completion_pct, (int, float)) or not (0 <= completion_pct <= 100):
            logger.warning(f"Invalid completion_pct value: {completion_pct}. Defaulting to 0.")
            completion_pct = 0.0

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=completion_pct,
            title={'text': "<b>Overall Project Progress</b>", 'font': {'size': 20}},
            number={'suffix': "%", 'font': {'size': 24}},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "#2ca02c"}
            }
        ))
        fig.update_layout(
            height=250,
            margin=dict(l=20, r=20, t=50, b=10),
            title_x=0.5
        )
        return fig
    except Exception as e:
        logger.error(f"Error creating progress donut: {e}", exc_info=True)
        return _create_placeholder_figure("Error: Progress Chart")


def create_risk_profile_chart(hazards_df: pd.DataFrame) -> go.Figure:
    """
    Creates a bar chart comparing initial vs. residual risk levels.

    This function calculates risk levels based on a predefined Severity/Probability
    matrix and displays the counts of hazards at each level (Low, Medium, High)
    for both the initial and residual risk states.

    Args:
        hazards_df (pd.DataFrame): DataFrame of hazards, requiring columns like
                                   'initial_S', 'initial_O', 'final_S', 'final_O'.

    Returns:
        go.Figure: A Plotly Figure object. Returns a placeholder if the
                   DataFrame is empty or data is malformed.
    """
    title = "<b>Risk Profile (Initial vs. Residual)</b>"
    try:
        if hazards_df.empty:
            logger.info("hazards_df is empty. Returning placeholder for risk profile chart.")
            return _create_placeholder_figure("No Risk Data Available", title)

        required_cols = {'initial_S', 'initial_O', 'final_S', 'final_O'}
        if not required_cols.issubset(hazards_df.columns):
            missing = required_cols - set(hazards_df.columns)
            logger.warning(f"Risk data missing columns: {missing}. Cannot create risk profile chart.")
            return _create_placeholder_figure("Incomplete Risk Data", title)

        # Configuration for S x O matrix (Severity x Occurrence)
        risk_map = {
            # Occurrence ->  1       2        3        4        5
            1: ["Low",   "Low",    "Low",    "Medium", "Medium"],  # Severity 1
            2: ["Low",   "Low",    "Medium", "Medium", "High"],    # Severity 2
            3: ["Low",   "Medium", "Medium", "High",   "High"],    # Severity 3
            4: ["Medium","Medium", "High",   "High",   "High"],    # Severity 4
            5: ["Medium","High",   "High",   "High",   "High"],    # Severity 5
        }

        def get_risk_level(severity, occurrence) -> str:
            if pd.isna(severity) or pd.isna(occurrence) or not is_numeric_dtype(type(severity)) or not is_numeric_dtype(type(occurrence)):
                return "N/A"
            sev, occ = int(severity), int(occurrence)
            if 1 <= sev <= 5 and 1 <= occ <= 5:
                return risk_map[sev - 1][occ - 1]
            return "N/A"

        df = hazards_df.copy()
        df['initial_level'] = df.apply(lambda row: get_risk_level(row['initial_S'], row['initial_O']), axis=1)
        df['final_level'] = df.apply(lambda row: get_risk_level(row['final_S'], row['final_O']), axis=1)

        risk_levels_order = ['Low', 'Medium', 'High']
        initial_counts = df['initial_level'].value_counts().reindex(risk_levels_order, fill_value=0)
        final_counts = df['final_level'].value_counts().reindex(risk_levels_order, fill_value=0)

        fig = go.Figure(data=[
            go.Bar(name='Initial', x=risk_levels_order, y=initial_counts.values, marker_color='#ff7f0e', text=initial_counts.values),
            go.Bar(name='Residual', x=risk_levels_order, y=final_counts.values, marker_color='#1f77b4', text=final_counts.values)
        ])
        fig.update_layout(
            barmode='group',
            title_text=title,
            title_x=0.5,
            legend_title_text='Risk State',
            xaxis_title="Calculated Risk Level",
            yaxis_title="Number of Hazards",
            height=250,
            margin=dict(l=20, r=20, t=50, b=10)
        )
        fig.update_traces(textposition='outside')
        return fig

    except Exception as e:
        logger.error(f"Error creating risk profile chart: {e}", exc_info=True)
        return _create_placeholder_figure("Error: Risk Chart", title)


def create_action_item_chart(actions_df: pd.DataFrame) -> go.Figure:
    """
    Creates a stacked bar chart of open action items by owner and status.

    Args:
        actions_df (pd.DataFrame): DataFrame of action items, requiring columns
                                   'status' and 'owner'.

    Returns:
        go.Figure: A Plotly Figure object. Returns a placeholder if there are
                   no open action items.
    """
    title = "<b>Open Action Items by Owner & Status</b>"
    try:
        if actions_df.empty or 'status' not in actions_df.columns:
            return _create_placeholder_figure("No Action Items Found", title)

        open_items_df = actions_df[actions_df['status'] != 'Completed'].copy()

        if open_items_df.empty:
            return _create_placeholder_figure("All action items are completed. 🎉", title)

        # Use crosstab for a more robust and insightful workload view
        # This creates a pivot table of owners vs. status counts
        workload = pd.crosstab(
            index=open_items_df['owner'],
            columns=open_items_df['status']
        )
        
        # Ensure all possible open statuses are present for consistent coloring
        all_statuses: List[str] = ["Open", "In Progress", "Overdue"]
        for status in all_statuses:
            if status not in workload.columns:
                workload[status] = 0

        # Ensure consistent order of statuses in the chart
        workload = workload[all_statuses]

        fig = px.bar(
            workload,
            title=title,
            labels={'value': 'Number of Items', 'owner': 'Assigned Owner'},
            color_discrete_map={"Open": "#ff7f0e", "In Progress": "#1f77b4", "Overdue": "#d62728"}
        )
        fig.update_layout(
            barmode='stack',
            title_x=0.5,
            legend_title_text='Status',
            height=250,
            margin=dict(l=20, r=20, t=50, b=10)
        )
        return fig

    except Exception as e:
        logger.error(f"Error creating action item chart: {e}", exc_info=True)
        return _create_placeholder_figure("Error: Action Item Chart", title)


def _create_placeholder_figure(text: str, title: str = "Chart") -> go.Figure:
    """
    Creates a standardized, empty figure with a text annotation.
    Used as a fallback when data is missing or an error occurs.
    """
    fig = go.Figure()
    fig.update_layout(
        title_text=f"<b>{title}</b>",
        title_x=0.5,
        height=250,
        margin=dict(l=20, r=20, t=50, b=10),
        xaxis={'visible': False},
        yaxis={'visible': False},
        annotations=[{
            'text': text,
            'xref': 'paper', 'yref': 'paper',
            'showarrow': False, 'font': {'size': 16}
        }]
    )
    return fig


# ==============================================================================
# --- UNIT TEST SCAFFOLDING (for `pytest`) ---
# ==============================================================================
"""
import pytest
import pandas as pd
import plotly.graph_objects as go

# To run tests, place this in a 'tests' directory and run pytest.
# from dhf_dashboard.utils.plot_utils import (
#     create_progress_donut,
#     create_risk_profile_chart,
#     create_action_item_chart
# )

def test_create_progress_donut_valid_input():
    fig = create_progress_donut(75.5)
    assert isinstance(fig, go.Figure)
    assert fig.data[0].value == 75.5
    assert fig.layout.title.text == "<b>Overall Project Progress</b>"

def test_create_progress_donut_invalid_input():
    # Test with a value outside the 0-100 range
    fig = create_progress_donut(150)
    assert isinstance(fig, go.Figure)
    assert fig.data[0].value == 0.0 # Should default to 0

@pytest.fixture
def sample_risk_data():
    return pd.DataFrame([
        {'initial_S': 5, 'initial_O': 4, 'final_S': 2, 'final_O': 1},
        {'initial_S': 3, 'initial_O': 3, 'final_S': 1, 'final_O': 1},
        {'initial_S': 5, 'initial_O': 5, 'final_S': 3, 'final_O': 2},
    ])

def test_create_risk_profile_chart_with_data(sample_risk_data):
    fig = create_risk_profile_chart(sample_risk_data)
    assert isinstance(fig, go.Figure)
    # Check that there are two bars (Initial and Residual)
    assert len(fig.data) == 2
    # Check if the title is set correctly
    assert "Risk Profile" in fig.layout.title.text

def test_create_risk_profile_chart_empty_df():
    fig = create_risk_profile_chart(pd.DataFrame())
    assert isinstance(fig, go.Figure)
    assert "No Risk Data Available" in fig.layout.annotations[0].text

@pytest.fixture
def sample_action_items():
    return pd.DataFrame([
        {'owner': 'Alice', 'status': 'Open'},
        {'owner': 'Bob', 'status': 'In Progress'},
        {'owner': 'Alice', 'status': 'Overdue'},
        {'owner': 'Charlie', 'status': 'Completed'}, # This one should be filtered out
        {'owner': 'Alice', 'status': 'Open'},
    ])

def test_create_action_item_chart_with_data(sample_action_items):
    fig = create_action_item_chart(sample_action_items)
    assert isinstance(fig, go.Figure)
    assert "Open Action Items" in fig.layout.title.text
    # We expect 3 traces for Open, In Progress, Overdue
    assert len(fig.data) == 3

def test_create_action_item_chart_all_completed(sample_action_items):
    completed_df = sample_action_items.copy()
    completed_df['status'] = 'Completed'
    fig = create_action_item_chart(completed_df)
    assert isinstance(fig, go.Figure)
    assert "All action items are completed" in fig.layout.annotations[0].text

def test_create_action_item_chart_empty_df():
    fig = create_action_item_chart(pd.DataFrame())
    assert isinstance(fig, go.Figure)
    assert "No Action Items Found" in fig.layout.annotations[0].text
"""
