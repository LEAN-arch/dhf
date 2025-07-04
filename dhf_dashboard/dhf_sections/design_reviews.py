# File: dhf_dashboard/dhf_sections/design_reviews.py
# --- Enhanced Version ---
"""
Renders the Design Reviews section of the DHF dashboard.

This module provides a structured UI for documenting formal design reviews,
including their minutes, attendees, and associated action items, as required
by 21 CFR 820.30(e).
"""

# --- Standard Library Imports ---
import copy
import logging
from datetime import date
from typing import Any, Dict, List

# --- Third-party Imports ---
import pandas as pd
import streamlit as st

# --- Local Application Imports ---
from ..utils.session_state_manager import SessionStateManager

# --- Setup Logging ---
logger = logging.getLogger(__name__)


def render_design_reviews(ssm: SessionStateManager) -> None:
    """
    Renders the UI for the Design Reviews & Gates section.

    This function displays an interface to add, view, and edit design reviews.
    Each review is presented in an expander, containing fields for metadata and
    a nested data editor for managing action items.

    Args:
        ssm (SessionStateManager): The session state manager to access DHF data.
    """
    st.header("6. Design Reviews & Gates")
    st.markdown("""
    *As per 21 CFR 820.30(e).*

    This section documents formal, planned reviews of the design at appropriate stages. For a combination product,
    attendees must include individuals with expertise in both the device and drug constituent parts.
    - A **Gate Review** represents a critical Go/No-Go decision point.
    - **Action Items** are tracked with owners and due dates to ensure closure.
    """)

    try:
        # --- 1. Load Data and Handle New Review Creation ---
        reviews_data: List[Dict[str, Any]] = ssm.get_data("design_reviews", "reviews")
        # Work on a deep copy to compare against for changes later
        reviews_copy = copy.deepcopy(reviews_data)

        if st.button("➕ Add New Design Review"):
            new_review = {
                "date": str(date.today()),  # Store as string for JSON compatibility
                "attendees": "",
                "notes": "",
                "is_gate_review": False,
                "action_items": []  # Initialize with an empty list
            }
            reviews_copy.insert(0, new_review)  # Insert at the top
            ssm.update_data(reviews_copy, "design_reviews", "reviews")
            logger.info("Added a new design review record.")
            st.rerun()

        if not reviews_copy:
            st.info("No design reviews have been added yet. Click the button above to add the first one.")
            return

        # --- 2. Iterate and Render Each Review ---
        # The key to making this work is using a unique `key` for every single widget.
        for i, review in enumerate(reviews_copy):
            # Gracefully handle malformed data
            if not isinstance(review, dict):
                st.warning(f"Skipping malformed review entry at index {i}.")
                logger.warning(f"Malformed review entry found: {review}")
                continue

            # The first review in the list (newest) is expanded by default.
            is_expanded = (i == 0)
            expander_title = f"**Review on {review.get('date', 'N/A')}** {' (GATE REVIEW)' if review.get('is_gate_review') else ''}"

            with st.expander(expander_title, expanded=is_expanded):
                col1, col2 = st.columns([3, 1])
                with col1:
                    # Robustly convert stored string date to datetime object for widget
                    stored_date = pd.to_datetime(review.get('date', date.today())).date()
                    review['date'] = str(st.date_input(
                        "**Review Date**",
                        value=stored_date,
                        key=f"date_{i}"
                    ))
                with col2:
                    review['is_gate_review'] = st.checkbox(
                        "**Mark as Gate Review**",
                        value=review.get('is_gate_review', False),
                        key=f"gate_review_{i}",
                        help="Check if this review is a formal phase-gate with a Go/No-Go decision."
                    )

                review['attendees'] = st.text_area(
                    "**Attendees (Name - Role)**",
                    value=review.get('attendees', ''),
                    key=f"attendees_{i}",
                    height=100,
                    help="List all attendees and their function, e.g., 'John Doe - Lead Engineer'."
                )
                review['notes'] = st.text_area(
                    "**Minutes / Notes / Outcome**",
                    value=review.get('notes', ''),
                    key=f"notes_{i}",
                    height=150,
                    help="Summarize discussion, decisions made, and the overall outcome (e.g., 'Approved to proceed')."
                )

                # --- Nested Action Item Editor ---
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
                    hide_index=True
                )
                review["action_items"] = edited_actions_df.to_dict('records')

        # --- 3. Persist All Changes ---
        # Only update the session state if the data has actually changed.
        if reviews_copy != reviews_data:
            ssm.update_data(reviews_copy, "design_reviews", "reviews")
            logger.info("Design reviews data updated in session state.")
            st.toast("Design review changes saved!", icon="✅")

    except Exception as e:
        st.error("An error occurred while displaying the Design Reviews section. The data may be malformed.")
        logger.error(f"Failed to render design reviews: {e}", exc_info=True)

# ==============================================================================
# --- UNIT TEST SCAFFOLDING (for `pytest`) ---
# ==============================================================================
"""
import pytest
from unittest.mock import MagicMock

# To run tests, place this in a 'tests' directory and run pytest.
# This tests the data manipulation logic, not the Streamlit rendering.

@pytest.fixture
def sample_reviews_data():
    return [
        {
            "date": "2023-10-26",
            "attendees": "Alice, Bob",
            "notes": "First review.",
            "is_gate_review": True,
            "action_items": [
                {"id": "AI-01", "description": "Fix bug", "owner": "Alice", "due_date": "2023-11-01", "status": "Open"}
            ]
        }
    ]

def test_add_new_review(sample_reviews_data):
    '''Tests adding a new review to the list of reviews.'''
    reviews_list = copy.deepcopy(sample_reviews_data)
    
    new_review = {
        "date": str(date.today()),
        "attendees": "",
        "notes": "",
        "is_gate_review": False,
        "action_items": []
    }
    reviews_list.insert(0, new_review)

    assert len(reviews_list) == 2
    assert reviews_list[0]["date"] == str(date.today())
    assert reviews_list[1]["attendees"] == "Alice, Bob"

def test_edit_review_field(sample_reviews_data):
    '''Tests modifying a field in an existing review.'''
    reviews_list = copy.deepcopy(sample_reviews_data)
    reviews_list[0]['notes'] = "Updated notes for the first review."
    
    assert reviews_list[0]['notes'] == "Updated notes for the first review."

def test_edit_nested_action_items(sample_reviews_data):
    '''Tests modifying the nested DataFrame of action items.'''
    reviews_list = copy.deepcopy(sample_reviews_data)
    
    # Simulate loading action items into a DataFrame
    action_items_df = pd.DataFrame(reviews_list[0]["action_items"])
    
    # Simulate editing the DataFrame
    action_items_df.loc[0, 'status'] = 'Completed'
    
    # Simulate saving it back to the review dictionary
    reviews_list[0]["action_items"] = action_items_df.to_dict('records')
    
    assert reviews_list[0]["action_items"][0]["status"] == "Completed"

def test_add_new_action_item(sample_reviews_data):
    '''Tests adding a new row to the nested action items DataFrame.'''
    reviews_list = copy.deepcopy(sample_reviews_data)
    action_items_df = pd.DataFrame(reviews_list[0]["action_items"])
    
    # Simulate adding a new row in the data_editor
    new_action_item = pd.DataFrame([{
        "id": "AI-02", "description": "New task", "owner": "Bob", "due_date": "2023-11-15", "status": "Open"
    }])
    edited_df = pd.concat([action_items_df, new_action_item], ignore_index=True)
    
    reviews_list[0]["action_items"] = edited_df.to_dict('records')
    
    assert len(reviews_list[0]["action_items"]) == 2
    assert reviews_list[0]["action_items"][1]["id"] == "AI-02"
"""
