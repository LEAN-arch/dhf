# File: dhf_dashboard/dhf_sections/design_changes.py
# --- Enhanced Version ---
"""
Renders the Design Changes section of the DHF dashboard.

This module provides the user interface for documenting and managing formal
design change control records, as required by 21 CFR 820.30(i).
"""

# --- Standard Library Imports ---
import logging
from typing import Any, Dict, List

# --- Third-party Imports ---
import pandas as pd
import streamlit as st

# --- Local Application Imports ---
from ..utils.session_state_manager import SessionStateManager

# --- Setup Logging ---
logger = logging.getLogger(__name__)


def render_design_changes(ssm: SessionStateManager) -> None:
    """
    Renders the UI for the Design Changes section.

    This function displays an editable table for managing Design Change
    Requests (DCRs), including their description, reason, impact analysis,
    and approval status. All changes are saved back to the session state.

    Args:
        ssm (SessionStateManager): The session state manager to access DHF data.
    """
    st.header("10. Design Changes")
    st.markdown("""
    *As per 21 CFR 820.30(i).*

    This section documents the formal control of all design changes made after the design has been finalized and approved.
    For a combination product, the **Impact Analysis** is critical and must evaluate effects on both the device and drug
    components, as well as a re-assessment of the overall risk profile.
    """)
    st.info("Changes made here are saved automatically. Log all formal design change requests and their impact.", icon="ℹ️")

    try:
        # --- 1. Load Data ---
        changes_data: List[Dict[str, Any]] = ssm.get_data("design_changes", "changes")
        changes_df = pd.DataFrame(changes_data)
        logger.info(f"Loaded {len(changes_df)} design change records.")

        # --- 2. Display Data Editor ---
        st.subheader("Design Change Control Records")
        st.markdown("Log all formal design change requests. The impact analysis is a critical part of the review and approval process.")

        edited_df = st.data_editor(
            changes_df,
            num_rows="dynamic",
            use_container_width=True,
            key="design_changes_editor",
            column_config={
                "id": st.column_config.TextColumn(
                    "Change Request ID",
                    help="Unique ID for the change, e.g., DCR-001.",
                    required=True
                ),
                "description": st.column_config.TextColumn(
                    "Change Description",
                    width="large",
                    help="A clear and concise summary of the change being made.",
                    required=True
                ),
                "reason": st.column_config.TextColumn(
                    "Reason for Change",
                    width="large",
                    help="Justification for the change, e.g., 'Corrective action from CAPA-01', 'Improved performance', 'Supplier change'."
                ),
                "impact_analysis": st.column_config.TextColumn(
                    "Impact Analysis",
                    width="large",
                    help="Describe impact on device performance, drug stability/efficacy, user interface, manufacturing processes, and whether new risks are introduced or existing ones affected."
                ),
                "approval_status": st.column_config.SelectboxColumn(
                    "Approval Status",
                    options=["Pending", "Approved", "Rejected", "Implementation Pending"],
                    help="The current status of the change request.",
                    required=True
                ),
                "approval_date": st.column_config.DateColumn(
                    "Approval Date",
                    format="YYYY-MM-DD",
                    help="The date the change was formally approved or rejected."
                ),
            },
            hide_index=True
        )

        # --- 3. Persist Updated Data ---
        # Convert the potentially edited DataFrame back to the list-of-dicts
        # format required by the session state.
        updated_records = edited_df.to_dict('records')

        # Only update the session state if there's a change to avoid unnecessary reruns
        if updated_records != changes_data:
            ssm.update_data(updated_records, "design_changes", "changes")
            logger.info("Design changes data updated in session state.")
            st.toast("Design changes saved!", icon="✅")

    except Exception as e:
        st.error("An error occurred while displaying the Design Changes section. The data may be malformed.")
        logger.error(f"Failed to render design changes: {e}", exc_info=True)
