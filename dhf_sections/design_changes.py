# File: dhf_dashboard/dhf_sections/design_changes.py

import streamlit as st
import pandas as pd
from utils.session_state_manager import SessionStateManager

def render_design_changes(ssm: SessionStateManager):
    """
    Renders the Design Changes section.
    """
    st.header("9. Design Changes")
    st.markdown("""
    *As per 21 CFR 820.30(i).*
    
    Formal documentation of all design changes made after the design controls have been established.
    For a combination product, the impact analysis **must** evaluate effects on both the device and drug components,
    as well as a re-assessment of the overall risk profile.
    """)
    
    changes_data = ssm.get_section_data("design_changes")

    st.info("Log all formal design change requests. The impact analysis is critical.")

    changes_df = pd.DataFrame(changes_data.get("changes", []))

    edited_df = st.data_editor(
        changes_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "id": st.column_config.TextColumn("Change Request ID", required=True),
            "description": st.column_config.TextColumn("Change Description", required=True),
            "reason": st.column_config.TextColumn("Reason for Change"),
            "impact_analysis": st.column_config.TextColumn("Impact on Constituent Parts (Device & Drug) and Risk File", help="Describe impact on device performance, drug stability/efficacy, and whether new risks are introduced."),
            "approval_status": st.column_config.SelectboxColumn("Approval Status", options=["Pending", "Approved", "Rejected"], required=True),
        },
        key="design_changes_editor"
    )

    changes_data["changes"] = edited_df.to_dict('records')
    ssm.update_section_data("design_changes", changes_data)

    if st.button("Save Design Changes Section"):
        st.success("Design Changes data saved successfully!")
