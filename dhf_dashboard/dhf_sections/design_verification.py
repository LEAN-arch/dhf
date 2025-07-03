# File: dhf_dashboard/dhf_sections/design_verification.py

import streamlit as st
import pandas as pd
from utils.session_state_manager import SessionStateManager

def render_design_verification(ssm: SessionStateManager):
    """
    Renders the Design Verification section, integrating risk control verification.
    """
    st.header("6. Design Verification")
    st.markdown("""
    *As per 21 CFR 820.30(f) and ISO 14971.*
    
    Verification confirms that design outputs meet design inputs. **Crucially, it also proves that implemented risk controls are effective.**
    For the smart-pill, this includes tests for electrical safety, material leachables, and drug release accuracy.
    It answers the question: **"Did we build the product right?"**
    """)
    
    verification_data = ssm.get_section_data("design_verification")
    outputs_data = ssm.get_section_data("design_outputs")
    inputs_data = ssm.get_section_data("design_inputs")

    output_ids = [""] + [doc.get('id', '') for doc in outputs_data.get("documents", [])]
    risk_control_ids = [""] + [req.get('id') for req in inputs_data.get("requirements", []) if req.get('is_risk_control')]

    st.info("Document each verification test. Link it to the design output it checks AND the risk control it proves.")
    
    tests_df = pd.DataFrame(verification_data.get("tests", []))
    
    edited_df = st.data_editor(
        tests_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "id": st.column_config.TextColumn("Test ID", required=True),
            "test_name": st.column_config.TextColumn("Test Name/Protocol", required=True),
            "output_verified": st.column_config.SelectboxColumn("Design Output Verified", options=output_ids, required=True),
            "risk_control_verified_id": st.column_config.SelectboxColumn("Verifies Risk Control (Req. ID)", options=risk_control_ids, help="Select the Risk Control Requirement this test proves."),
            "result": st.column_config.SelectboxColumn("Result", options=["Pass", "Fail", "In Progress"], required=True),
            "report_file": st.column_config.TextColumn("Link to Test Report"),
        },
        key="design_verification_editor"
    )
    
    verification_data["tests"] = edited_df.to_dict('records')
    ssm.update_section_data("design_verification", verification_data)

    if st.button("Save Design Verification Section"):
        st.success("Design Verification data saved successfully!")
