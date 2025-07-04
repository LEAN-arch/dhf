# --- Definitive, Corrected, and Unabridged Optimized Version ---
"""
Module for rendering the Design Reviews section of the DHF Explorer.

This component provides an interface to view and manage records from
formal design reviews, including their attendees, notes, and action items.
This version is hardened against data type mismatches for the data editor.
"""

# --- Standard Library Imports ---
import logging

# --- Third-party Imports ---
import pandas as pd
import streamlit as st

# --- Local Application Imports ---
from dhf_dashboard.utils.session_state_manager import SessionStateManager

# --- Setup Logging ---
logger = logging.getLogger(__name__)

def render_design_reviews(ssm: SessionStateManager):
    """
    Renders an editable view of all design review records.
    
    This function displays each design review in a separate container,
    allowing for focused viewing and editing of its details and associated
    action items via a robustly configured data editor.
    """
    st.header("6. Design Reviews")
    st.markdown("Document and track formal reviews of the design at appropriate stages of the project lifecycle. Each review generates action items that must be tracked to closure.")
    st.info("💡 **Best Practice:** Hold design reviews at the end of each major phase (e.g., after Design Inputs are finalized) to ensure readiness for the next phase. These are often called 'Gate Reviews'.", icon="💡")
    st.divider()

    try:
        reviews = ssm.get_data("design_reviews", "reviews")
        if not reviews:
            st.warning("No design review records found.")
            return

        # Sort reviews by date, most recent first
        reviews.sort(key=lambda r: pd.to_datetime(r.get('date')), reverse=True)

        for i, review in enumerate(reviews):
            with st.container(border=True):
                st.subheader(f"Design Review: {pd.to_datetime(review.get('date')).strftime('%Y-%m-%d')}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Attendees:** {review.get('attendees', 'N/A')}")
                with col2:
                    is_gate_review = "Yes" if review.get('is_gate_review', False) else "No"
                    st.markdown(f"**Is Gate Review:** {is_gate_review}")
                
                st.markdown("**Notes:**")
                st.caption(review.get('notes', 'No notes recorded.'))

                st.markdown("**Action Items:**")
                
                editor_key = f"action_item_editor_{i}"
                
                action_items_list = review.get("action_items", [])
                if not action_items_list:
                    st.caption("No action items for this review.")
                    continue

                action_items_df = pd.DataFrame(action_items_list)
                
                # FIX: Convert 'due_date' string to datetime objects BEFORE passing to the editor.
                # This is the critical fix for the StreamlitAPIException.
                if 'due_date' in action_items_df.columns:
                    action_items_df['due_date'] = pd.to_datetime(action_items_df['due_date'], errors='coerce')

                # Capture original state for comparison after editing
                original_df = action_items_df.copy()
                
                edited_df = st.data_editor(
                    action_items_df,
                    key=editor_key,
                    num_rows="dynamic",
                    use_container_width=True,
                    column_config={
                        "id": st.column_config.TextColumn("ID", disabled=True, help="Unique ID for the action item."),
                        "description": st.column_config.TextColumn("Description", width="large", required=True),
                        "owner": st.column_config.SelectboxColumn(
                            "Owner",
                            options=["B. Chen", "C. Day", "D. Evans", "Jose Bautista", "Dr. Alice Weber"],
                            required=True
                        ),
                        "due_date": st.column_config.DateColumn(
                            "Due Date",
                            format="YYYY-MM-DD",
                            required=True
                        ),
                        "status": st.column_config.SelectboxColumn(
                            "Status",
                            options=["Open", "In Progress", "Completed", "Overdue"],
                            required=True
                        )
                    },
                    hide_index=True,
                )

                # Check if the data has been changed by the user
                if not original_df.equals(edited_df):
                    # Convert datetime objects back to strings for JSON compatibility before saving
                    df_to_save = edited_df.copy()
                    df_to_save['due_date'] = pd.to_datetime(df_to_save['due_date']).dt.strftime('%Y-%m-%d')
                    
                    # Update the specific review's action items in the session state
                    reviews[i]["action_items"] = df_to_save.to_dict('records')
                    ssm.update_data(reviews, "design_reviews", "reviews")
                    st.toast(f"Action items for review on {review.get('date')} updated!", icon="✅")
                    st.rerun()

    except Exception as e:
        st.error("An error occurred while displaying the Design Reviews section. The data may be malformed.")
        logger.error(f"Failed to render design reviews: {e}", exc_info=True)
