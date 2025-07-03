# File: dhf_dashboard/dhf_sections/design_verification.py

import streamlit as st
import pandas as pd
from ..utils.session_state_manager import SessionStateManager

def render_design_verification(ssm: SessionStateManager):
    """
    Renders the Design Verification section, integrating risk control verification.
    """
    st.header("7. Design Verification")
    st.markdown("""
    *As per 21 CFR 820.30(f) and ISO 14971.*

    Verification confirms that design outputs meet design inputs. **Crucially, it also proves that implemented risk controls are effective.**
    It answers the question: **"Did we build the product right?"**
    """)
    st.info("Changes made here are saved automatically. Link each test to the output it checks and, if applicable, the risk control it proves.", icon="ℹ️")

    verification_data = ssm.get_data("design_verification", "tests")
    outputs_data = ssm.get_data("design_outputs", "documents")
    inputs_data = ssm.get_data("design_inputs", "requirements")

    # --- SME Enhancement: Prepare lists for dual traceability ---
    # 1. List of all Design Outputs to link to
    output_ids = [""] + [doc.get('id', '') for doc in outputs_data]

    # 2. List of only the requirements that are Risk Controls
    risk_control_ids = [""] + [
        req.get('id') for req in inputs_data if req.get('is_risk_control')
    ]

    st.subheader("Verification Test Protocols & Results")
    st.markdown("Document each verification test, its outcome, and its traceability.")

    tests_df = pd.DataFrame(verification_data)

    edited_df = st.data_editor(
        tests_df,
        num_rows="dynamic",
        use_container_width=True,
        key="design_verification_editor",
        column_config={
            "id": st.column_config.TextColumn("Test ID", help="Unique ID for the test protocol (e.g., VER-001).", required=True),
            "test_name": st.column_config.TextColumn("Test Name/Protocol", width="large", required=True),
            "output_verified": st.column_config.SelectboxColumn(
                "Design Output Verified",
                options=output_ids,
                help="Select the Design Output (e.g., drawing, spec) that this test examines.",
                required=True
            ),
            "risk_control_verified_id": st.column_config.SelectboxColumn(
                "Verifies Risk Control (Req. ID)",
                options=risk_control_ids,
                help="If this test proves a risk control is effective, link to the Risk Control Requirement ID here."
            ),
            "result": st.column_config.SelectboxColumn("Result", options=["Not Started", "In Progress", "Pass", "Fail"], required=True),
            "report_file": st.column_config.TextColumn("Link to Test Report", help="Filename or link to the test report/evidence."),
        },
    )

    # Persist the updated data back to the session state
    ssm.update_data(edited_df.to_dict('records'), "design_verification", "tests")
