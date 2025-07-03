# File: dhf_dashboard/dhf_sections/design_changes.py

import streamlit as st
import pandas as pd
from ..utils.session_state_manager import SessionStateManager

def render_design_changes(ssm: SessionStateManager):
    """
    Renders the Design Changes section for formal change control.
    """
    st.header("10. Design Changes")
    st.markdown("""
    *As per 21 CFR 820.30(i).*

    This section documents the formal control of all design changes made after the design has been finalized and approved.
    For a combination product, the **Impact Analysis** is critical and must evaluate effects on both the device and drug
    components, as well as a re-assessment of the overall risk profile.
    """)
    st.info("Changes made here are saved automatically. Log all formal design change requests and their impact.", icon="ℹ️")

    changes_data = ssm.get_data("design_changes", "changes")

    st.subheader("Design Change Control Records")
    st.markdown("Log all formal design change requests. The impact analysis is a critical part of the review and approval process.")

    changes_df = pd.DataFrame(changes_data)

    edited_df = st.data_editor(
        changes_df,
        num_rows="dynamic",
        use_container_width=True,
        key="design_changes_editor",
        column_config={
            "id": st.column_config.TextColumn("Change Request ID", help="Unique ID for the change, e.g., DCR-001.", required=True),
            "description": st.column_config.TextColumn("Change Description", width="large", required=True),
            "reason": st.column_config.TextColumn("Reason for Change", width="large"),
            "impact_analysis": st.column_config.TextColumn(
                "Impact Analysis",
                width="large",
                help="Describe impact on device performance, drug stability/efficacy, user interface, and whether new risks are introduced or existing ones affected."
            ),
            "approval_status": st.column_config.SelectboxColumn(
                "Approval Status",
                options=["Pending", "Approved", "Rejected", "Implementation Pending"],
                required=True
            ),
            "approval_date": st.column_config.DateColumn(
                "Approval Date",
                format="YYYY-MM-DD"
            ),
            # SME Note: A future enhancement could be a nested data editor for action items,
            # similar to the design reviews section, to track the implementation of the change.
        },
    )

    # Persist the updated data back to the session state
    ssm.update_data(edited_df.to_dict('records'), "design_changes", "changes")
