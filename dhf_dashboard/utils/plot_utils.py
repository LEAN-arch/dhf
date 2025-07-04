# --- Definitive, Corrected, and Unabridged Optimized Version ---
"""
Plotting utilities for creating standardized Plotly visualizations.

This module contains functions that generate various Plotly figures
(donuts, bar charts, etc.) used throughout the DHF dashboard application.
These functions encapsulate the plotting logic, ensuring a consistent
visual style and robust error handling by centralizing configuration
and business logic.
"""

# --- Standard Library Imports ---
import logging
from typing import Dict, List, Optional, Tuple

# --- Third-party Imports ---
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pandas.api.types import is_numeric_dtype

# --- Setup Logging ---
logger = logging.getLogger(__name__)


# ==============================================================================
# --- MODULE-LEVEL CONFIGURATION CONSTANTS ---
# ==============================================================================
# Centralized configuration for consistent plot styling and logic.

# Standard layout for dashboard components to ensure visual consistency.
_PLOT_LAYOUT_CONFIG: Dict[str, any] = {
    "height": 250,
    "margin": dict(l=20, r=20, t=50, b=20),
    "title_x": 0.5,
    "font": {"family": "sans-serif"}
}

# Configuration for Action Item statuses and colors.
_ACTION_ITEM_STATUS_ORDER: List[str] = ["Overdue", "In Progress", "Open"]
_ACTION_ITEM_COLOR_MAP: Dict[str, str] = {
    "Open": "#ff7f0e",        # Orange
    "In Progress": "#1f77b4", # Blue
    "Overdue": "#d62728",     # Red
    "Completed": "#2ca02c"    # Green
}

# Canonical Risk Matrix Configuration (aligned with ISO 14971 principles).
# This is the single source of truth for risk calculations across the app.
_RISK_CONFIG: Dict[str, any] = {
    'levels': {
        # (Severity, Occurrence): Risk Level
        (1, 1): 'Low', (1, 2): 'Low', (1, 3): 'Medium', (1, 4): 'Medium', (1, 5): 'High',
        (2, 1): 'Low', (2, 2): 'Low', (2, 3): 'Medium', (2, 4): 'High', (2, 5): 'High',
        (3, 1): 'Medium', (3, 2): 'Medium', (3, 3): 'High', (3, 4): 'High', (3, 5): 'Unacceptable',
        (4, 1): 'Medium', (4, 2): 'High', (4, 3): 'High', (4, 4): 'Unacceptable', (4, 5): 'Unacceptable',
        (5, 1): 'High', (5, 2): 'High', (5, 3): 'Unacceptable', (5, 4): 'Unacceptable', (5, 5): 'Unacceptable'
    },
    'colors': {
        'Unacceptable': 'rgba(139, 0, 0, 0.9)',
        'High': 'rgba(214, 39, 40, 0.9)',
        'Medium': 'rgba(255, 127, 14, 0.9)',
        'Low': 'rgba(44, 160, 44, 0.9)'
    },
    'order': ['Low', 'Medium', 'High', 'Unacceptable']
}


def _create_placeholder_figure(text: str, title: str, icon: str = "ℹ️") -> go.Figure:
    """
    Creates a standardized, empty figure with an icon and text annotation.
    Used as a fallback when data is missing or an error occurs.
    """
    fig = go.Figure()
    fig.update_layout(
        title_text=f"<b>{title}</b>",
        xaxis={'visible': False},
        yaxis={'visible': False},
        annotations=[{
            'text': f"{icon}<br>{text}",
            'xref': 'paper', 'yref': 'paper',
            'showarrow': False, 'font': {'size': 16, 'color': '#7f7f7f'}
        }],
        **_PLOT_LAYOUT_CONFIG
    )
    return fig


def create_progress_donut(completion_pct: float) -> go.Figure:
    """
    Creates a donut-style gauge indicator for overall project progress with
    dynamic coloring for at-a-glance status assessment.

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

        # Dynamic coloring for better visual feedback
        if completion_pct < 33.3:
            bar_color = _ACTION_ITEM_COLOR_MAP["Overdue"] # At Risk
        elif completion_pct < 66.6:
            bar_color = _ACTION_ITEM_COLOR_MAP["Open"] # In Progress
        else:
            bar_color = _ACTION_ITEM_COLOR_MAP["Completed"] # On Track

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=completion_pct,
            title={'text': "<b>Overall Project Progress</b>", 'font': {'size': 20}},
            number={'suffix': "%", 'font': {'size': 24}},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': bar_color},
                'steps': [
                    {'range': [0, 33.3], 'color': '#fbebeb'},
                    {'range': [33.3, 66.6], 'color': '#fef3e7'},
                    {'range': [66.6, 100], 'color': '#eaf5ea'},
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': completion_pct
                }
            }
        ))
        fig.update_layout(**_PLOT_LAYOUT_CONFIG)
        return fig
    except Exception as e:
        logger.error(f"Error creating progress donut: {e}", exc_info=True)
        return _create_placeholder_figure("Progress Chart Error", "Overall Project Progress", icon="⚠️")


def create_risk_profile_chart(hazards_df: pd.DataFrame) -> go.Figure:
    """
    Creates a bar chart comparing initial vs. residual risk levels based on
    the application's canonical risk matrix.

    Args:
        hazards_df (pd.DataFrame): DataFrame of hazards, requiring columns
                                   'initial_S', 'initial_O', 'final_S', 'final_O'.

    Returns:
        go.Figure: A Plotly Figure object. Returns a placeholder if the
                   DataFrame is empty or data is malformed.
    """
    title = "<b>Risk Profile (Initial vs. Residual)</b>"
    try:
        if hazards_df.empty:
            logger.info("hazards_df is empty. Returning placeholder for risk profile chart.")
            return _create_placeholder_figure("No Risk Data Available", title, icon="📊")

        required_cols = {'initial_S', 'initial_O', 'final_S', 'final_O'}
        if not required_cols.issubset(hazards_df.columns):
            missing = required_cols - set(hazards_df.columns)
            logger.warning(f"Risk data missing columns: {missing}. Cannot create risk profile chart.")
            return _create_placeholder_figure(f"Data Missing: {', '.join(missing)}", title, icon="⚠️")

        def get_risk_level(severity: int, occurrence: int) -> str:
            """Looks up risk level from the canonical _RISK_CONFIG."""
            # Ensure inputs are valid integers before tuple lookup
            if pd.isna(severity) or pd.isna(occurrence) or not is_numeric_dtype(severity) or not is_numeric_dtype(occurrence):
                return "N/A"
            return _RISK_CONFIG['levels'].get((int(severity), int(occurrence)), "N/A")

        df = hazards_df.copy()
        df['initial_level'] = df.apply(lambda row: get_risk_level(row['initial_S'], row['initial_O']), axis=1)
        df['final_level'] = df.apply(lambda row: get_risk_level(row['final_S'], row['final_O']), axis=1)

        risk_levels_order = _RISK_CONFIG['order']
        initial_counts = df['initial_level'].value_counts().reindex(risk_levels_order, fill_value=0)
        final_counts = df['final_level'].value_counts().reindex(risk_levels_order, fill_value=0)
        
        # Use semantic colors for better interpretation
        bar_colors = [_RISK_CONFIG['colors'][level] for level in risk_levels_order]

        fig = go.Figure(data=[
            go.Bar(name='Initial Risk', x=risk_levels_order, y=initial_counts.values, text=initial_counts.values,
                   marker=dict(color=bar_colors, line=dict(color='rgba(0,0,0,0.5)', width=1)),
                   opacity=0.6),
            go.Bar(name='Residual Risk', x=risk_levels_order, y=final_counts.values, text=final_counts.values,
                   marker=dict(color=bar_colors, line=dict(color='rgba(0,0,0,1)', width=1.5)))
        ])
        fig.update_layout(
            barmode='group',
            title_text=title,
            legend_title_text='Risk State',
            xaxis_title="Calculated Risk Level",
            yaxis_title="Number of Hazards",
            **_PLOT_LAYOUT_CONFIG
        )
        fig.update_traces(textposition='outside')
        return fig

    except Exception as e:
        logger.error(f"Error creating risk profile chart: {e}", exc_info=True)
        return _create_placeholder_figure("Risk Chart Error", title, icon="⚠️")


def create_action_item_chart(actions_df: pd.DataFrame) -> go.Figure:
    """
    Creates a stacked bar chart of open action items by owner and status,
    ordered logically for quick assessment.

    Args:
        actions_df (pd.DataFrame): DataFrame of action items, requiring
                                   'status' and 'owner' columns.

    Returns:
        go.Figure: A Plotly Figure object. Returns a placeholder if there are
                   no open action items.
    """
    title = "<b>Open Action Items by Owner</b>"
    try:
        if actions_df.empty or 'status' not in actions_df.columns or 'owner' not in actions_df.columns:
            return _create_placeholder_figure("No Action Items Found", title, icon="📊")

        open_items_df = actions_df[actions_df['status'] != 'Completed'].copy()

        if open_items_df.empty:
            return _create_placeholder_figure("All action items are completed.", title, icon="🎉")

        # Crosstab provides a robust pivot of owners vs. status counts
        workload = pd.crosstab(
            index=open_items_df['owner'],
            columns=open_items_df['status']
        )
        
        # Ensure all possible open statuses are present and ordered for consistent coloring and stacking
        for status in _ACTION_ITEM_STATUS_ORDER:
            if status not in workload.columns:
                workload[status] = 0
        workload = workload[_ACTION_ITEM_STATUS_ORDER]

        fig = px.bar(
            workload,
            title=title,
            labels={'value': 'Number of Items', 'owner': 'Assigned Owner', 'status': 'Item Status'},
            color_discrete_map=_ACTION_ITEM_COLOR_MAP
        )
        fig.update_layout(
            barmode='stack',
            legend_title_text='Status',
            xaxis={'categoryorder':'total descending'}, # Show owners with most items first
            **_PLOT_LAYOUT_CONFIG
        )
        return fig

    except Exception as e:
        logger.error(f"Error creating action item chart: {e}", exc_info=True)
        return _create_placeholder_figure("Action Item Chart Error", title, icon="⚠️")
