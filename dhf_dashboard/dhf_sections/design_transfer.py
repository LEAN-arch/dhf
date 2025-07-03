# File: dhf_dashboard/dhf_sections/design_transfer.py

import streamlit as st
import pandas as pd
from ..utils.session_state_manager import SessionStateManager

def render_design_transfer(ssm: SessionStateManager):
    """
    Renders the Design Transfer section of the DHF.
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

    transfer_data = ssm.get_data("design_transfer", "activities")

    st.subheader("Transfer Activities and Checklist")
    st.markdown("Track activities for transferring the complete combination product design to production. This information will form the basis of the Device Master Record (DMR).")

    activities_df = pd.DataFrame(transfer_data)

    edited_df = st.data_editor(
        activities_df,
        num_rows="dynamic",
        use_container_width=True,
        key="design_transfer_editor",
        column_config={
            "activity": st.column_config.TextColumn(
                "Transfer Activity / Document",
                help="e.g., 'Finalize Device Master Record (DMR)', 'Validate automated assembly line', 'Qualify drug substance supplier'.",
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
                help="Filename or link to the procedure, report, or record."
            ),
        },
    )

    # Persist the updated data back to the session state
    ssm.update_data(edited_df.to_dict('records'), "design_transfer", "activities")
