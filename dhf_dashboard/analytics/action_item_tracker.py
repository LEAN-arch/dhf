# File: dhf_dashboard/analytics/action_item_tracker.py
# --- Enhanced Version ---
"""
Renders the centralized Action Item Tracker.

This module provides the logic for aggregating all action items from across the
DHF (e.g., from Design Reviews, Design Changes) into a single, interactive,
and analyzable view.
"""

# --- Standard Library Imports ---
import logging
from datetime import datetime
from typing import Any, Dict, List

# --- Third-party Imports ---
import pandas as pd
import streamlit as st

# --- Local Application Imports ---
from ..utils.session_state_manager import SessionStateManager

# --- Setup Logging ---
logger = logging.getLogger(__name__)


def render_action_item_tracker(ssm: SessionStateManager) -> None:
    """
    Aggregates, analyzes, and displays all action items from across the DHF.

    This function fetches action items from various sections (Design Reviews,
    Design Changes), enriches the data (e.g., identifies overdue items),
    displays KPIs, and provides an interactive, filterable table for users.

    Args:
        ssm (SessionStateManager): The session state manager to access DHF data.
    """
    st.header("🗃️ Centralized Action Item Tracker")
    st.info("This table consolidates all action items from Design Reviews and Design Changes for project-wide oversight.")

    try:
        # --- 1. Aggregate action items from all potential sources ---
        all_actions: List[Dict[str, Any]] = []

        # Source 1: Design Reviews
        reviews = ssm.get_data("design_reviews", "reviews")
        for i, review in enumerate(reviews):
            if not isinstance(review, dict): continue
            for action in review.get("action_items", []):
                if not isinstance(action, dict): continue
                action_copy = action.copy()
                # Provide a descriptive source for traceability
                action_copy['source'] = f"Review on {review.get('date', f'#{i+1}')}"
                all_actions.append(action_copy)

        # Source 2: Design Changes (future-proofing)
        changes = ssm.get_data("design_changes", "changes")
        for change in changes:
            if not isinstance(change, dict): continue
            for action in change.get("action_items", []):
                if not isinstance(action, dict): continue
                action_copy = action.copy()
                action_copy['source'] = f"DCR-{change.get('id', 'N/A')}"
                all_actions.append(action_copy)

        logger.info(f"Aggregated a total of {len(all_actions)} action items from all sources.")

        if not all_actions:
            st.success("🎉 No action items have been recorded in any DHF section yet.")
            return

        actions_df = pd.DataFrame(all_actions)

        # --- 2. Enrich the data for better insights ---
        # Ensure all necessary columns exist to prevent errors, filling with None
        required_cols = ['id', 'description', 'owner', 'due_date', 'status', 'source']
        for col in required_cols:
            if col not in actions_df.columns:
                actions_df[col] = None

        # Convert due_date to datetime for comparison, coercing errors to NaT
        actions_df['due_date'] = pd.to_datetime(actions_df['due_date'], errors='coerce')

        # Automatically identify overdue items: due date is in the past and status is not 'Completed'
        now = pd.to_datetime(datetime.now().date())
        is_overdue = (actions_df['due_date'].notna()) & (actions_df['due_date'] < now) & (actions_df['status'] != 'Completed')
        actions_df.loc[is_overdue, 'status'] = 'Overdue'

        # --- 3. Create insightful KPIs ---
        total_items = len(actions_df)
        completed_items = len(actions_df[actions_df['status'] == 'Completed'])
        open_items = total_items - completed_items
        overdue_count = len(actions_df[actions_df['status'] == 'Overdue'])

        st.subheader("Action Item Health KPIs")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Open Items", open_items, help="Sum of items with status 'Open', 'In Progress', or 'Overdue'.")
        col2.metric("‼️ Overdue Items", overdue_count, help="Items past their due date that are not yet 'Completed'.")
        col3.metric("✅ Completed Items", completed_items)

        # --- 4. Create interactive filters with smart defaults ---
        st.divider()
        st.subheader("Filter and Export Action Items")
        filter_col1, filter_col2 = st.columns(2)

        # Smart defaults: Show all statuses that are not 'Completed' by default
        status_options = sorted(actions_df['status'].unique())
        default_status = [s for s in status_options if s != 'Completed']

        with filter_col1:
            status_filter = st.multiselect(
                "Filter by Status:",
                options=status_options,
                default=default_status
            )
        with filter_col2:
            # Provide a sorted, unique list of owners for the filter
            owner_options = sorted(actions_df['owner'].dropna().unique())
            owner_filter = st.multiselect(
                "Filter by Owner:",
                options=owner_options,
            )

        # Apply filters to a new DataFrame
        filtered_df = actions_df.copy()
        if status_filter:
            filtered_df = filtered_df[filtered_df['status'].isin(status_filter)]
        if owner_filter:
            filtered_df = filtered_df[filtered_df['owner'].isin(owner_filter)]

        # --- 5. Display the filtered and styled DataFrame ---
        def style_overdue_row(row: pd.Series) -> List[str]:
            """Applies a background color to the entire row if the status is 'Overdue'."""
            return ['background-color: #ffcccc' if row.status == 'Overdue' else '' for _ in row]

        st.dataframe(
            filtered_df[['id', 'description', 'owner', 'due_date', 'status', 'source']].style.apply(style_overdue_row, axis=1),
            use_container_width=True,
            column_config={
                "id": st.column_config.TextColumn("Action ID"),
                "description": st.column_config.TextColumn("Description", width="large"),
                "owner": st.column_config.TextColumn("Owner"),
                "due_date": st.column_config.DateColumn("Due Date", format="YYYY-MM-DD"),
                "status": st.column_config.TextColumn("Status"),
                "source": st.column_config.TextColumn("Source", width="medium"),
            },
            hide_index=True
        )

        # --- 6. Add an Export Button for the filtered view ---
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Filtered View to CSV",
            data=csv,
            file_name="action_items_export.csv",
            mime="text/csv",
            key="export_action_items"
        )

    except Exception as e:
        st.error("An error occurred while generating the action item tracker. The data may be incomplete or malformed.")
        logger.error(f"Failed to render action item tracker: {e}", exc_info=True)
