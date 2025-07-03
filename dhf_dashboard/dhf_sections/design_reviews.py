# File: dhf_dashboard/dhf_sections/design_reviews.py

import streamlit as st
import pandas as pd
from utils.session_state_manager import SessionStateManager
from datetime import date

def render(ssm: SessionStateManager):
    """
    Renders the Design Reviews & Gates section.
    Allows for documenting formal design reviews, designating them as gates,
    and managing structured action items for each review.
    """
    st.header("6. Design Reviews & Gates")
    st.markdown("""
    *As per 21 CFR 820.30(e).*
    
    This section documents formal, planned reviews of the design at appropriate stages. For a combination product,
    attendees must include individuals with expertise in both the device and drug constituent parts.
    
    - A review marked as a **Gate Review** represents a critical Go/No-Go decision point in the project.
    - **Action Items** are tracked with owners and due dates to ensure accountability and closure.
    """)

    # Get the list of review dictionaries from the session state
    reviews = ssm.get_data("design_reviews", "reviews")

    # --- Button to add a new review ---
    # This button appends a new, blank review structure to our list.
    if st.button("➕ Add New Design Review"):
        new_review = {
            "date": date.today(),
            "attendees": "",
            "notes": "",
            "is_gate_review": False,
            "action_items": []  # Initialize with an empty list for the data editor
        }
        reviews.append(new_review)
        # Save the updated list back to the session state and rerun the script
        # This makes the new review appear instantly for the user to edit.
        ssm.update_data(reviews, "design_reviews", "reviews")
        st.rerun()

    if not reviews:
        st.info("No design reviews have been added yet. Click the button above to add the first one.")
        return

    # --- Iterate through each review and display it in an expander ---
    # This keeps the UI clean, showing one review's details at a time.
    for i, review in enumerate(reviews):
        # The last review added is expanded by default for easy editing.
        is_expanded = (i == len(reviews) - 1)
        
        with st.expander(f"Review #{i + 1} on {review.get('date', 'N/A')}", expanded=is_expanded):
            
            col1, col2 = st.columns([3, 1])

            with col1:
                # Basic review details
                review['date'] = st.date_input(
                    "Review Date", 
                    value=review.get('date', date.today()), 
                    key=f"date_{i}"
                )
            with col2:
                review['is_gate_review'] = st.checkbox(
                    "Mark as Gate Review", 
                    value=review.get('is_gate_review', False), 
                    key=f"gate_review_{i}",
                    help="Check this if the review is a formal phase-gate with a Go/No-Go decision."
                )

            review['attendees'] = st.text_area(
                "Attendees (Name - Role)",
                value=review.get('attendees', ''),
                key=f"attendees_{i}",
                height=100,
                help="List all attendees and their function, e.g., 'John Doe - Lead Engineer, Jane Smith - Quality Assurance'."
            )
            review['notes'] = st.text_area(
                "Minutes / Notes Summary",
                value=review.get('notes', ''),
                key=f"notes_{i}",
                height=150,
                help="Summarize the discussion, decisions made, and the overall outcome of the review. Include a summary of the risk status review."
            )

            # --- Structured Action Item Editor ---
            # This is the most critical part for tracking and compliance.
            st.subheader("Action Items for this Review")
            action_items_df = pd.DataFrame(review.get("action_items", []))

            edited_actions_df = st.data_editor(
                action_items_df,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "id": st.column_config.TextColumn("Action ID", help="Unique ID, e.g., AI-001", required=True),
                    "description": st.column_config.TextColumn("Description", width="large", required=True),
                    "owner": st.column_config.TextColumn("Owner", help="Name of the responsible person", required=True),
                    "due_date": st.column_config.DateColumn("Due Date", required=True),
                    "status": st.column_config.SelectboxColumn("Status", options=["Open", "In Progress", "Completed"], required=True)
                },
                key=f"actions_editor_{i}"
            )
            # Update the review dictionary with the potentially modified action items
            review["action_items"] = edited_actions_df.to_dict('records')

    st.divider()

    # --- Main save button to commit all changes made across all expanders ---
    if st.button("Commit All Review Changes", type="primary"):
        ssm.update_data(reviews, "design_reviews", "reviews")
        st.success("All design review changes have been saved successfully!")
    if st.button("Save Design Reviews Section"):
        st.success("Design Reviews data saved successfully!")
