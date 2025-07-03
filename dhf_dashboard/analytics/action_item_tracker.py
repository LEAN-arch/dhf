# File: dhf_dashboard/analytics/action_item_tracker.py

import streamlit as st
import pandas as pd
from datetime import date

def render_action_item_tracker(ssm):
    """Aggregates and displays all action items from across the project."""
    st.header("Centralized Action Item Tracker")
    st.info("This table consolidates all action items from Design Reviews and Design Changes.")

    # 1. Extract action items from Design Reviews
    all_actions = []
    reviews = ssm.get_data("design_reviews", "reviews")
    for i, review in enumerate(reviews):
        for action in review.get("action_items", []):
            action['source'] = f"Review {i+1} ({review.get('date')})"
            all_actions.append(action)

    # (In a full implementation, you would also extract actions from Design Changes)

    if not all_actions:
        st.warning("No action items have been recorded in any Design Review yet.")
        return

    actions_df = pd.DataFrame(all_actions)
    
    # Ensure all columns exist
    for col in ['id', 'description', 'owner', 'due_date', 'status', 'source']:
        if col not in actions_df.columns:
            actions_df[col] = None
    
    # Convert due_date to datetime for comparison
    actions_df['due_date'] = pd.to_datetime(actions_df['due_date'], errors='coerce')
    
    # 2. Create KPIs
    open_items = actions_df[actions_df['status'] != 'Completed']
    overdue_items = open_items[open_items['due_date'] < pd.to_datetime(date.today())]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Open Action Items", len(open_items))
    col2.metric("‼️ Overdue Items", len(overdue_items))
    col3.metric("Completed Items", len(actions_df) - len(open_items))

    # 3. Create interactive filters
    st.write("---")
    filter_col1, filter_col2 = st.columns(2)
    
    status_filter = filter_col1.multiselect(
        "Filter by Status:",
        options=actions_df['status'].unique(),
        default=[s for s in actions_df['status'].unique() if s != 'Completed']
    )
    owner_filter = filter_col2.multiselect(
        "Filter by Owner:",
        options=actions_df['owner'].unique(),
    )
    
    # Apply filters
    filtered_df = actions_df
    if status_filter:
        filtered_df = filtered_df[filtered_df['status'].isin(status_filter)]
    if owner_filter:
        filtered_df = filtered_df[filtered_df['owner'].isin(owner_filter)]
    
    st.dataframe(filtered_df[['id', 'description', 'owner', 'due_date', 'status', 'source']], use_container_width=True)
    
    csv = filtered_df.to_csv().encode('utf-8')
    st.download_button("Export View to CSV", csv, "action_items.csv", "text/csv")
