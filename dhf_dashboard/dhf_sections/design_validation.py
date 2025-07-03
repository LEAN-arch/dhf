# File: dhf_dashboard/dhf_sections/design_validation.py

import streamlit as st
import pandas as pd
from utils.session_state_manager import SessionStateManager

def render_design_validation(ssm: SessionStateManager):
    """
    Renders the Design Validation section, focusing on user needs and risk.
    """
    st.header("7. Design Validation")
    st.markdown("""
    *As per 21 CFR 820.30(g) and ISO 14971.*
    
    Validation ensures the final combination product meets user needs and intended uses under actual or
    simulated conditions. It also serves as a final check on the effectiveness of risk controls.
    It answers the question: **"Did we build the right product?"**
    """)
    
    validation_data = ssm.get_section_data("design_validation")
    inputs_data = ssm.get_section_data("design_inputs")

    user_need_ids = [""] + [req.get('id') for req in inputs_data.get("requirements", []) if req.get('source_type') == 'User Need']

    st.info("Document each validation study (e.g., usability study, clinical trial), linking it to a user need.")

    studies_df = pd.DataFrame(validation_data.get("studies", []))

    edited_df = st.data_editor(
        studies_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "id": st.column_config.TextColumn("Study ID", required=True),
            "study_name": st.column_config.TextColumn("Study/Protocol Name", required=True),
            "user_need_validated": st.column_config.SelectboxColumn("User Need Validated", options=user_need_ids, required=True),
            "risk_control_effectiveness": st.column_config.CheckboxColumn("Confirms Risk Control Effectiveness?", help="Did this study confirm risk controls are effective in the hands of the user?"),
            "result": st.column_config.SelectboxColumn("Result", options=["Pass", "Fail", "In Progress"], required=True),
            "report_file": st.column_config.TextColumn("Link to Validation Report"),
        },
        key="design_validation_editor"
    )

    validation_data["studies"] = edited_df.to_dict('records')
    ssm.update_section_data("design_validation", validation_data)
    
    if st.button("Save Design Validation Section"):
        st.success("Design Validation data saved successfully!")
