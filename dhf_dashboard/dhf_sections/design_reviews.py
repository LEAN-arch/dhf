# File: dhf_dashboard/dhf_sections/design_reviews.py

import streamlit as st
import pandas as pd
from ..utils.session_state_manager import SessionStateManager
from datetime import date

def render_design_reviews(ssm: SessionStateManager):
    """
    Renders the Design Reviews & Gates section, allowing for structured
    documentation and management of action items for each review.
    """
    st.header("6. Design Reviews & Gates")
    st.markdown("""
    *As per 21 CFR 820.30(e).*

    This section documents formal, planned reviews of the design at appropriate stages. For a combination product,
    attendees must include individuals with expertise in both the device and drug constituent parts.
    - A **Gate Review** represents a critical Go/No-Go decision point.
    - **Action Items** are tracked with owners and due dates to ensure closure.
    """)

    # Get the list of review dictionaries from the session state
    reviews = ssm.get_data("design_reviews", "reviews")

    # --- UX SME: Clear call-to-action to add a new review ---
    if st.button("➕ Add New Design Review"):
        new_review = {
            "date": date.today(),
            "attendees": "",
            "notes": "",
            "is_gate_review": False,
            "action_items": [] # Initialize with an empty list for the data editor
        }
        reviews.insert(0, new_review) # Insert at the beginning to show newest first
        ssm.update_data(reviews, "design_reviews", "reviews")
        st.rerun()

    if not reviews:
        st.info("No design reviews have been added yet. Click the button above to add the first one.")
        return

    # --- Iterate through each review and display it in an expander ---
    for i, review in enumerate(reviews):
        # The first review in the list (newest) is expanded by default.
        is_expanded = (i == 0)

        with st.expander(f"**Review on {review.get('date', 'N/A')}** {' (GATE REVIEW)' if review.get('is_gate_review') else ''}", expanded=is_expanded):

            col1, col2 = st.columns([3, 1])
            with col1:
                review['date'] = st.date_input(
                    "**Review Date**",
                    value=pd.to_datetime(review.get('date', date.today())).date(),
                    key=f"date_{i}"
                )
            with col2:
                review['is_gate_review'] = st.checkbox(
                    "**Mark as Gate Review**",
                    value=review.get('is_gate_review', False),
                    key=f"gate_review_{i}",
                    help="Check this if the review is a formal phase-gate with a Go/No-Go decision."
                )

            review['attendees'] = st.text_area(
                "**Attendees (Name - Role)**",
                value=review.get('attendees', ''),
                key=f"attendees_{i}",
                height=100,
                help="List all attendees and their function, e.g., 'John Doe - Lead Engineer, Jane Smith - Quality Assurance'."
            )
            review['notes'] = st.text_area(
                "**Minutes / Notes / Outcome**",
                value=review.get('notes', ''),
                key=f"notes_{i}",
                height=150,
                help="Summarize discussion, decisions made, and the overall outcome (e.g., 'Approved to proceed to next phase')."
            )

            # --- Design Control SME: Structured Action Item Editor ---
            st.subheader("Action Items for this Review")
            action_items_df = pd.DataFrame(review.get("action_items", []))

            edited_actions_df = st.data_editor(
                action_items_df,
                num_rows="dynamic",
                use_container_width=True,
                key=f"actions_editor_{i}",
                column_config={
                    "id": st.column_config.TextColumn("Action ID", help="Unique ID, e.g., AI-DR1-01", required=True),
                    "description": st.column_config.TextColumn("Description", width="large", required=True),
                    "owner": st.column_config.TextColumn("Owner", help="Name of the responsible person", required=True),
                    "due_date": st.column_config.DateColumn("Due Date", format="YYYY-MM-DD", required=True),
                    "status": st.column_config.SelectboxColumn("Status", options=["Open", "In Progress", "Completed"], required=True)
                },
            )
            # Update the review dictionary with the potentially modified action items
            review["action_items"] = edited_actions_df.to_dict('records')

    # Persist all changes back to the session state
    ssm.update_data(reviews, "design_reviews", "reviews")
