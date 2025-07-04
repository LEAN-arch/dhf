# File: dhf_dashboard/dhf_sections/design_verification.py
# --- Enhanced Version ---
"""
Renders the Design Verification section of the DHF dashboard.

This module provides the UI for documenting design verification activities,
which confirm that design outputs meet their corresponding design inputs,
as required by 21 CFR 820.30(f). It also provides traceability for the
verification of implemented risk controls.
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


def render_design_verification(ssm: SessionStateManager) -> None:
    """
    Renders the UI for the Design Verification section.

    This function displays an editable table for managing verification tests.
    It provides a "dual traceability" feature, allowing each test to be linked
    to the design output it examines and, separately, to any risk control
    requirement it also verifies.

    Args:
        ssm (SessionStateManager): The session state manager to access DHF data.
    """
    st.header("7. Design Verification")
    st.markdown("""
    *As per 21 CFR 820.30(f) and ISO 14971.*

    Verification confirms that design outputs meet design inputs. **Crucially, it also proves that implemented risk controls are effective.**
    It answers the question: **"Did we build the product right?"**
    """)
    st.info("Changes made here are saved automatically. Link each test to the output it checks and, if applicable, the risk control it proves.", icon="ℹ️")

    try:
        # --- 1. Load Data and Prepare Dependencies ---
        verification_data: List[Dict[str, Any]] = ssm.get_data("design_verification", "tests")
        outputs_data: List[Dict[str, Any]] = ssm.get_data("design_outputs", "documents")
        inputs_data: List[Dict[str, Any]] = ssm.get_data("design_inputs", "requirements")
        logger.info(f"Loaded {len(verification_data)} verification tests, {len(outputs_data)} outputs, and {len(inputs_data)} inputs.")

        # --- SME Enhancement: Prepare lists for dual traceability ---
        # 1. List of all Design Outputs to link to.
        output_ids: List[str] = [""] + [doc.get('id', '') for doc in outputs_data if doc.get('id')]
        logger.debug(f"Populated design output dropdown with: {output_ids}")

        # 2. List of *only* the requirements that are Risk Controls.
        risk_control_reqs = [req for req in inputs_data if req.get('is_risk_control')]
        risk_control_ids: List[str] = [""] + [req.get('id', '') for req in risk_control_reqs if req.get('id')]
        logger.debug(f"Populated risk control dropdown with: {risk_control_ids}")

        # --- 2. Display Data Editor ---
        st.subheader("Verification Test Protocols & Results")
        st.markdown("Document each verification test, its outcome, and its traceability. A single test can verify both a standard output and a specific risk control.")

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
                    help="Select the Design Output (e.g., drawing, spec) that this test examines. This is a mandatory link.",
                    required=True
                ),
                "risk_control_verified_id": st.column_config.SelectboxColumn(
                    "Verifies Risk Control (Req. ID)",
                    options=risk_control_ids,
                    help="If this test also proves a risk control is effective, link to the Risk Control Requirement ID here. Leave blank otherwise."
                ),
                "result": st.column_config.SelectboxColumn("Result", options=["Not Started", "In Progress", "Pass", "Fail"], required=True),
                "report_file": st.column_config.TextColumn("Link to Test Report", help="Filename or link to the test report/evidence."),
            },
            hide_index=True
        )

        # --- 3. Persist Updated Data ---
        updated_records = edited_df.to_dict('records')

        if updated_records != verification_data:
            ssm.update_data(updated_records, "design_verification", "tests")
            logger.info("Design verification data updated in session state.")
            st.toast("Design verification tests saved!", icon="✅")

    except Exception as e:
        st.error("An error occurred while displaying the Design Verification section. The data may be malformed.")
        logger.error(f"Failed to render design verification: {e}", exc_info=True)
