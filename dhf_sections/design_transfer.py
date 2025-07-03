# File: dhf_dashboard/dhf_sections/design_transfer.py

import streamlit as st
import pandas as pd
from utils.session_state_manager import SessionStateManager

def render_design_transfer(ssm: SessionStateManager):
    """
    Renders the Design Transfer section.
    """
    st.header("8. Design Transfer")
    st.markdown("""
    *As per 21 CFR 820.30(h).*
    
    This section documents the transfer of the smart-pill design to manufacturing. This process is complex
    and must ensure that procedures for handling both the device components (QSR) and the drug substance (cGMP)
    are robust and result in a consistently manufactured final product.
    """)
    
    transfer_data = ssm.get_section_data("design_transfer")

    st.info("Track activities for transferring the complete combination product design to production.")

    activities_df = pd.DataFrame(transfer_data.get("activities", []))

    edited_df = st.data_editor(
        activities_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "activity": st.column_config.TextColumn("Transfer Activity / Document", help="e.g., 'Qualify drug supplier', 'Validate automated assembly line', 'Finalize device master record (DMR)'", required=True),
            "responsible_party": st.column_config.TextColumn("Responsible Party"),
            "status": st.column_config.SelectboxColumn("Status", options=["Not Started", "In Progress", "Completed", "N/A"], required=True),
            "completion_date": st.column_config.DateColumn("Date Completed"),
        },
        key="design_transfer_editor"
    )

    transfer_data["activities"] = edited_df.to_dict('records')
    ssm.update_section_data("design_transfer", transfer_data)

    if st.button("Save Design Transfer Section"):
        st.success("Design Transfer data saved successfully!")
