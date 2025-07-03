# File: dhf_dashboard/analytics/action_item_tracker.py

import streamlit as st
import pandas as pd
from datetime import datetime

def render_action_item_tracker(ssm):
    """Aggregates, analyzes, and displays all action items from across the DHF."""
    st.header("🗃️ Centralized Action Item Tracker")
    st.info("This table consolidates all action items from Design Reviews and Design Changes for project-wide oversight.")

    # --- SME Enhancement: Aggregate from all potential sources ---
    all_actions = []

    # 1. Extract action items from Design Reviews
    reviews = ssm.get_data("design_reviews", "reviews")
    for i, review in enumerate(reviews):
        for action in review.get("action_items", []):
            action_copy = action.copy()
            action_copy['source'] = f"Review #{i+1} ({review.get('date')})"
            all_actions.append(action_copy)

    # 2. Extract action items from Design Changes (future-proofing)
    changes = ssm.get_data("design_changes", "changes")
    for i, change in enumerate(changes):
        for action in change.get("action_items", []):
            action_copy = action.copy()
            action_copy['source'] = f"Change Request {change.get('id', i+1)}"
            all_actions.append(action_copy)

    if not all_actions:
        st.warning("No action items have been recorded in any DHF section yet.")
        return

    actions_df = pd.DataFrame(all_actions)

    # --- Data Scientist SME: Enrich the data for better insights ---
    # Ensure all necessary columns exist to prevent errors
    for col in ['id', 'description', 'owner', 'due_date', 'status', 'source']:
        if col not in actions_df.columns:
            actions_df[col] = None

    # Convert due_date to datetime for comparison, handling potential errors
    actions_df['due_date'] = pd.to_datetime(actions_df['due_date'], errors='coerce')

    # Automatically identify overdue items
    now = pd.to_datetime(datetime.now().date())
    is_overdue = (actions_df['due_date'] < now) & (actions_df['status'] != 'Completed')
    actions_df.loc[is_overdue, 'status'] = 'Overdue'

    # 2. Create insightful KPIs
    total_items = len(actions_df)
    completed_items = len(actions_df[actions_df['status'] == 'Completed'])
    open_items = total_items - completed_items
    overdue_count = len(actions_df[actions_df['status'] == 'Overdue'])


    st.subheader("Action Item Health KPIs")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Open Items", open_items)
    col2.metric("‼️ Overdue Items", overdue_count)
    col3.metric("✅ Completed Items", completed_items)

    # 3. Create interactive filters with smart defaults
    st.divider()
    st.subheader("Filter and Export Action Items")
    filter_col1, filter_col2 = st.columns(2)

    # --- UX SME: Set smart defaults for filters ---
    status_options = sorted(actions_df['status'].unique())
    default_status = [s for s in status_options if s != 'Completed']

    status_filter = filter_col1.multiselect(
        "Filter by Status:",
        options=status_options,
        default=default_status
    )
    owner_filter = filter_col2.multiselect(
        "Filter by Owner:",
        options=sorted(actions_df['owner'].unique()),
    )

    # Apply filters
    filtered_df = actions_df.copy()
    if status_filter:
        filtered_df = filtered_df[filtered_df['status'].isin(status_filter)]
    if owner_filter:
        filtered_df = filtered_df[filtered_df['owner'].isin(owner_filter)]

    # --- UX SME: Add conditional styling to highlight overdue items ---
    def style_overdue(row):
        return ['background-color: #ffcccc' if row.status == 'Overdue' else '' for _ in row]

    st.dataframe(
        filtered_df[['id', 'description', 'owner', 'due_date', 'status', 'source']].style.apply(style_overdue, axis=1),
        use_container_width=True,
        column_config={
            "id": "Action ID",
            "description": st.column_config.TextColumn("Description", width="large"),
            "owner": "Owner",
            "due_date": st.column_config.DateColumn("Due Date", format="YYYY-MM-DD"),
            "status": "Status",
            "source": st.column_config.TextColumn("Source", width="medium"),
        }
    )

    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Export View to CSV",
        csv,
        "action_items_export.csv",
        "text/csv",
        key="export_action_items"
    )
