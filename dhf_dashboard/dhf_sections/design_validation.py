# File: dhf_dashboard/dhf_sections/design_validation.py

import streamlit as st
import pandas as pd
from ..utils.session_state_manager import SessionStateManager

def render_design_validation(ssm: SessionStateManager):
    """
    Renders the Design Validation section, focusing on confirming user needs.
    """
    st.header("8. Design Validation")
    st.markdown("""
    *As per 21 CFR 820.30(g) and ISO 14971.*

    Validation ensures the final product meets **user needs** and intended uses under actual or
    simulated conditions. It also serves as a final check on the effectiveness of risk controls.
    It answers the question: **"Did we build the right product?"**
    """)
    st.info("Changes made here are saved automatically. Each validation study must be linked to a specific User Need.", icon="ℹ️")

    validation_data = ssm.get_data("design_validation", "studies")
    inputs_data = ssm.get_data("design_inputs", "requirements")

    # --- SME Enhancement: Only allow linking to User Needs ---
    user_needs = [
        req for req in inputs_data if req.get('source_type') == 'User Need'
    ]
    if not user_needs:
        st.warning("⚠️ No 'User Need' requirements found. Please add them in the '4. Design Inputs' section before documenting validation.", icon="❗")
        user_need_options = []
    else:
        user_need_options = [f"{un.get('id')}: {un.get('description')}" for un in user_needs]

    user_need_map = {f"{un.get('id')}: {un.get('description')}": un.get('id') for un in user_needs}


    st.subheader("Validation Studies & Results")
    st.markdown("Document each validation study (e.g., usability study, clinical trial) and link it to the User Need it confirms.")

    studies_df = pd.DataFrame(validation_data)
    # Convert saved IDs to the descriptive format for display
    reverse_user_need_map = {v: k for k, v in user_need_map.items()}
    if 'user_need_validated' in studies_df.columns:
        studies_df['user_need_validated_descriptive'] = studies_df['user_need_validated'].map(reverse_user_need_map)


    edited_df = st.data_editor(
        studies_df,
        num_rows="dynamic",
        use_container_width=True,
        key="design_validation_editor",
        column_config={
            "id": st.column_config.TextColumn("Study ID", help="Unique ID for the study protocol (e.g., VAL-001).", required=True),
            "study_name": st.column_config.TextColumn("Study/Protocol Name", width="large", required=True),
            "user_need_validated_descriptive": st.column_config.SelectboxColumn(
                "User Need Validated",
                options=user_need_options,
                help="Select the User Need that this study confirms.",
                required=True
            ),
            "risk_control_effectiveness": st.column_config.CheckboxColumn(
                "Confirms Risk Control?",
                help="Did this study also confirm that risk controls are effective in the hands of the user?",
                default=False
            ),
            "result": st.column_config.SelectboxColumn("Result", options=["Not Started", "In Progress", "Pass", "Fail"], required=True),
            "report_file": st.column_config.TextColumn("Link to Validation Report", help="Filename or link to the final study report."),
            "user_need_validated": None, # Hide the raw ID column
        },
    )

    # Convert descriptive selection back to raw ID for storage
    if 'user_need_validated_descriptive' in edited_df.columns:
        edited_df['user_need_validated'] = edited_df['user_need_validated_descriptive'].map(user_need_map)

    # Persist the updated data back to the session state
    ssm.update_data(edited_df.to_dict('records'), "design_validation", "studies")
