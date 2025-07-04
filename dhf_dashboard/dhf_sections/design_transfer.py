# File: dhf_dashboard/dhf_sections/design_transfer.py
# --- Enhanced Version ---
"""
Renders the Design Transfer section of the DHF dashboard.

This module provides the UI for documenting the activities required to transfer
the final, validated design to manufacturing, as specified by 21 CFR 820.30(h).
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


def render_design_transfer(ssm: SessionStateManager) -> None:
    """
    Renders the UI for the Design Transfer section.

    This function displays an editable table for tracking all activities
    required to ensure the design is correctly translated into production
    specifications, forming the basis of the Device Master Record (DMR).

    Args:
        ssm (SessionStateManager): The session state manager to access DHF data.
    """
    st.header("9. Design Transfer")
    st.markdown("""
    *As per 21 CFR 820.30(h).*

    This section documents the transfer of the final, validated design to manufacturing. This process is complex
    for a combination product and must ensure that procedures for handling both the **device components (QSR)** and
    the **drug substance (cGMP)** are robust and result in a consistently manufactured final product.
    The output of this phase is a complete Device Master Record (DMR).
    """)
    st.info("Changes made here are saved automatically. Track all activities required to make the design manufacturable.", icon="ℹ️")

    try:
        # --- 1. Load Data ---
        transfer_data: List[Dict[str, Any]] = ssm.get_data("design_transfer", "activities")
        activities_df = pd.DataFrame(transfer_data)
        logger.info(f"Loaded {len(activities_df)} design transfer activities.")

        # --- 2. Display Data Editor ---
        st.subheader("Transfer Activities and Checklist")
        st.markdown("Track activities for transferring the complete combination product design to production. These activities and their outputs (procedures, specs) will form the basis of the Device Master Record (DMR).")

        edited_df = st.data_editor(
            activities_df,
            num_rows="dynamic",
            use_container_width=True,
            key="design_transfer_editor",
            column_config={
                "activity": st.column_config.TextColumn(
                    "Transfer Activity / Document",
                    help="e.g., 'Finalize Device Master Record (DMR)', 'Validate automated assembly line', 'Qualify drug substance supplier', 'Process Validation (IQ/OQ/PQ)'.",
                    required=True,
                    width="large"
                ),
                "responsible_party": st.column_config.TextColumn(
                    "Responsible Dept/Party",
                    help="e.g., 'Manufacturing Eng.', 'Quality Assurance', 'Supply Chain'."
                ),
                "status": st.column_config.SelectboxColumn(
                    "Status",
                    options=["Not Started", "In Progress", "Completed", "On Hold"],
                    required=True
                ),
                "completion_date": st.column_config.DateColumn(
                    "Date Completed",
                    format="YYYY-MM-DD"
                ),
                "evidence_link": st.column_config.TextColumn(
                    "Link to Evidence",
                    help="Filename or hyperlink to the procedure, report, or record providing evidence of completion."
                ),
            },
            hide_index=True
        )

        # --- 3. Persist Updated Data ---
        updated_records = edited_df.to_dict('records')

        if updated_records != transfer_data:
            ssm.update_data(updated_records, "design_transfer", "activities")
            logger.info("Design transfer data updated in session state.")
            st.toast("Design transfer activities saved!", icon="✅")

    except Exception as e:
        st.error("An error occurred while displaying the Design Transfer section. The data may be malformed.")
        logger.error(f"Failed to render design transfer: {e}", exc_info=True)
