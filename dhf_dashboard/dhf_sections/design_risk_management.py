# File: dhf_dashboard/dhf_sections/design_risk_management.py
# --- Enhanced Version ---
"""
Renders the Risk Management File (RMF) Summary section of the DHF dashboard.

This module provides the UI for documenting the risk analysis process according
to ISO 14971, including hazard identification, risk estimation, and control.
"""

# --- Standard Library Imports ---
import logging
from typing import Any, Dict, List

# --- Third-party Imports ---
import pandas as pd
import streamlit as st
from pandas.api.types import is_numeric_dtype

# --- Local Application Imports ---
from ..utils.session_state_manager import SessionStateManager

# --- Setup Logging ---
logger = logging.getLogger(__name__)


def get_risk_level(severity: Any, probability: Any) -> str:
    """
    Calculates a qualitative risk level based on a 5x5 Severity/Probability matrix.

    Args:
        severity (Any): The severity rating (expected 1-5).
        probability (Any): The probability rating (expected 1-5).

    Returns:
        str: The calculated risk level ('Low', 'Medium', 'High') or 'N/A' if inputs are invalid.
    """
    # This risk map is a common industry practice.
    risk_map = {
        # Probability -> 1(VL),  2(L),     3(P),     4(F),     5(VF)
        1: ["Low",   "Low",    "Low",    "Medium", "Medium"],  # Severity 1 (Negligible)
        2: ["Low",   "Low",    "Medium", "Medium", "High"],    # Severity 2 (Minor)
        3: ["Low",   "Medium", "Medium", "High",   "High"],    # Severity 3 (Serious)
        4: ["Medium","Medium", "High",   "High",   "High"],    # Severity 4 (Critical)
        5: ["Medium","High",   "High",   "High",   "High"],    # Severity 5 (Catastrophic)
    }
    if pd.isna(severity) or pd.isna(probability) or not is_numeric_dtype(severity) or not is_numeric_dtype(probability):
        return "N/A"
    try:
        sev, prob = int(severity), int(probability)
        if 1 <= sev <= 5 and 1 <= prob <= 5:
            # -1 because list indices are 0-4 while ratings are 1-5.
            return risk_map[sev - 1][prob - 1]
    except (ValueError, TypeError):
        return "N/A"
    return "N/A"


def render_design_risk_management(ssm: SessionStateManager) -> None:
    """
    Renders the UI for the Risk Management File (RMF) Summary.

    Args:
        ssm (SessionStateManager): The session state manager to access DHF data.
    """
    st.header("2. Risk Management File (RMF) Summary")
    st.markdown("""
    *As per ISO 14971:2019 Application of risk management to medical devices.*

    This section summarizes the risk analysis for the smart-pill. It documents identified
    hazards, foreseeable events, potential harms, and the estimation of risk *before*
    and *after* risk controls are applied.
    """)
    st.info("Changes made here are saved automatically. Risk Levels are calculated in real-time based on Severity and Probability.", icon="ℹ️")

    try:
        # --- 1. Load Data and Prepare Dependencies ---
        rmf_data: Dict[str, Any] = ssm.get_data("risk_management_file")
        hazards_data: List[Dict[str, Any]] = rmf_data.get("hazards", [])
        hazards_df = pd.DataFrame(hazards_data)
        logger.info(f"Loaded {len(hazards_df)} hazard records.")

        # Prepare list of risk control requirements for the traceability dropdown
        inputs_data: List[Dict[str, Any]] = ssm.get_data("design_inputs", "requirements")
        risk_control_reqs = [req for req in inputs_data if req.get('is_risk_control')]
        risk_control_ids: List[str] = [""] + [req.get('id', '') for req in risk_control_reqs if req.get('id')]
        logger.debug(f"Populated risk control dropdown with: {risk_control_ids}")

        # --- 2. Hazard Analysis Section ---
        st.subheader("2.1 Hazard Analysis and Risk Evaluation")
        st.markdown("Document all identified hazards. Link risk controls from the Design Inputs section to demonstrate mitigation.")

        # --- Calculate risk levels before displaying in the editor ---
        if not hazards_df.empty:
            hazards_df['initial_risk_level'] = hazards_df.apply(lambda row: get_risk_level(row.get('initial_S'), row.get('initial_O')), axis=1)
            hazards_df['final_risk_level'] = hazards_df.apply(lambda row: get_risk_level(row.get('final_S'), row.get('final_O')), axis=1)

        edited_df = st.data_editor(
            hazards_df,
            num_rows="dynamic",
            use_container_width=True,
            key="risk_management_editor",
            column_config={
                "hazard_id": st.column_config.TextColumn("Hazard ID", help="Unique ID (e.g., H-001)", required=True),
                "description": st.column_config.TextColumn("Hazard Description", width="large", help="e.g., Premature battery failure.", required=True),
                "initial_S": st.column_config.NumberColumn("Initial S", help="Severity (1-5)", min_value=1, max_value=5, required=True),
                "initial_O": st.column_config.NumberColumn("Initial O", help="Occurrence (1-5)", min_value=1, max_value=5, required=True),
                "initial_D": st.column_config.NumberColumn("Initial D", help="Detection (1-5)", min_value=1, max_value=5, required=True),
                "initial_risk_level": st.column_config.TextColumn("Initial Risk", help="Calculated automatically.", disabled=True),
                "risk_control_req_id": st.column_config.SelectboxColumn("Risk Control (Req. ID)", help="Link to the Design Input that mitigates this risk.", options=risk_control_ids),
                "final_S": st.column_config.NumberColumn("Final S", help="Severity after control.", min_value=1, max_value=5),
                "final_O": st.column_config.NumberColumn("Final O", help="Occurrence after control.", min_value=1, max_value=5),
                "final_D": st.column_config.NumberColumn("Final D", help="Detection after control.", min_value=1, max_value=5),
                "final_risk_level": st.column_config.TextColumn("Final Risk", help="Calculated automatically.", disabled=True),
            },
            hide_index=True
        )

        # --- Re-calculate after editing to reflect changes immediately ---
        if not edited_df.empty:
            edited_df['initial_risk_level'] = edited_df.apply(lambda row: get_risk_level(row.get('initial_S'), row.get('initial_O')), axis=1)
            edited_df['final_risk_level'] = edited_df.apply(lambda row: get_risk_level(row.get('final_S'), row.get('final_O')), axis=1)

        # --- 3. Risk-Benefit Analysis Section ---
        st.subheader("2.2 Overall Residual Risk Acceptability")
        st.markdown("This is the final conclusion of the risk management process, required by ISO 14971. It should be a formal statement declaring whether the overall residual risk is acceptable in relation to the documented medical benefits of the device.")
        
        overall_analysis = st.text_area(
            "**Risk-Benefit Analysis Statement:**",
            value=rmf_data.get("overall_risk_benefit_analysis", ""),
            key="rmf_overall_analysis",
            height=150,
            help="Example: 'The overall residual risk of the Smart-Pill System is judged to be acceptable...'"
        )

        # --- 4. Persist Data ---
        updated_hazards = edited_df.to_dict('records')
        
        if updated_hazards != hazards_data or overall_analysis != rmf_data.get("overall_risk_benefit_analysis"):
            rmf_data["hazards"] = updated_hazards
            rmf_data["overall_risk_benefit_analysis"] = overall_analysis
            ssm.update_data(rmf_data, "risk_management_file")
            logger.info("Risk management data updated in session state.")
            st.toast("Risk management file saved!", icon="✅")

    except Exception as e:
        st.error("An error occurred while displaying the Risk Management section. The data may be malformed.")
        logger.error(f"Failed to render design risk management: {e}", exc_info=True)
