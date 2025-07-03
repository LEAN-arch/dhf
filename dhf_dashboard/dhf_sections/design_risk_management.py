# File: dhf_dashboard/dhf_sections/design_risk_management.py

import streamlit as st
import pandas as pd
from ..utils.session_state_manager import SessionStateManager

def render_design_risk_management(ssm: SessionStateManager):
    """
    Renders the Risk Management File (RMF) Summary section, based on ISO 14971.
    """
    st.header("2. Risk Management File (RMF) Summary")
    st.markdown("""
    *As per ISO 14971:2019 Application of risk management to medical devices.*

    This section summarizes the risk analysis for the smart-pill. It documents identified
    hazards, foreseeable events, potential harms, and the estimation of risk *before*
    and *after* risk controls are applied.
    """)
    st.info("Changes made here are saved automatically. Risk Levels are calculated based on Severity and Probability.", icon="ℹ️")

    rmf_data = ssm.get_data("risk_management_file")
    hazards_df = pd.DataFrame(rmf_data.get("hazards", []))

    st.subheader("2.1 Hazard Analysis and Risk Evaluation")
    st.markdown("Document all identified hazards. Link risk controls from the Design Inputs section to demonstrate mitigation.")

    # --- SME Enhancement: Live traceability link for risk controls ---
    inputs_data = ssm.get_data("design_inputs", "requirements")
    risk_control_requirement_ids = [""] + [
        req.get('id', '') for req in inputs_data if req.get('is_risk_control')
    ]

    # --- SME Enhancement: Automatic Risk Calculation ---
    risk_map = {
        # S/P   1        2        3        4        5
        1: ["Low",   "Low",    "Low",    "Medium", "Medium"],
        2: ["Low",   "Low",    "Medium", "Medium", "High"],
        3: ["Low",   "Medium", "Medium", "High",   "High"],
        4: ["Medium","Medium", "High",   "High",   "High"],
        5: ["Medium","High",   "High",   "High",   "High"],
    }
    def get_risk_level(severity, probability):
        if pd.isna(severity) or pd.isna(probability): return "N/A"
        sev, prob = int(severity), int(probability)
        if 1 <= sev <= 5 and 1 <= prob <= 5:
            return risk_map[sev][prob-1]
        return "N/A"

    # Apply calculations before editing to show current state
    for index, row in hazards_df.iterrows():
        hazards_df.loc[index, 'initial_risk_level'] = get_risk_level(row.get('initial_severity'), row.get('initial_probability'))
        hazards_df.loc[index, 'residual_risk_level'] = get_risk_level(row.get('residual_severity'), row.get('residual_probability'))

    edited_df = st.data_editor(
        hazards_df,
        num_rows="dynamic",
        use_container_width=True,
        key="risk_management_editor",
        column_config={
            "hazard_id": st.column_config.TextColumn("Hazard ID", help="Unique ID (e.g., H-001)", required=True),
            "hazard_description": st.column_config.TextColumn("Hazard Description", width="large", help="e.g., Premature battery failure, Incorrect drug dose released.", required=True),
            "potential_harm": st.column_config.TextColumn("Potential Harm(s)", width="large", help="e.g., Ineffective therapy, Toxic exposure.", required=True),
            "initial_severity": st.column_config.NumberColumn("Initial S", help="Severity (1-5)", min_value=1, max_value=5, required=True),
            "initial_probability": st.column_config.NumberColumn("Initial P", help="Probability (1-5)", min_value=1, max_value=5, required=True),
            "initial_risk_level": st.column_config.TextColumn("Initial Risk", help="Calculated automatically.", disabled=True),
            "risk_control_req_id": st.column_config.SelectboxColumn("Risk Control (Req. ID)", help="Link to the Design Input that mitigates this risk.", options=risk_control_requirement_ids, required=True),
            "residual_severity": st.column_config.NumberColumn("Residual S", help="Severity after control.", min_value=1, max_value=5),
            "residual_probability": st.column_config.NumberColumn("Residual P", help="Probability after control.", min_value=1, max_value=5),
            "residual_risk_level": st.column_config.TextColumn("Residual Risk", help="Calculated automatically.", disabled=True),
            "risk_acceptability": st.column_config.SelectboxColumn("Acceptability", options=["", "Acceptable", "Not Acceptable"]),
        },
    )

    # Re-calculate after editing to reflect changes
    for index, row in edited_df.iterrows():
        edited_df.loc[index, 'initial_risk_level'] = get_risk_level(row.get('initial_severity'), row.get('initial_probability'))
        edited_df.loc[index, 'residual_risk_level'] = get_risk_level(row.get('residual_severity'), row.get('residual_probability'))

    # Update session state
    rmf_data["hazards"] = edited_df.to_dict('records')
    ssm.update_data(rmf_data, "risk_management_file")


    # --- Formal Risk-Benefit Analysis Conclusion ---
    st.subheader("2.2 Overall Residual Risk Acceptability")
    st.markdown("""
    This is the final conclusion of the risk management process, required by ISO 14971.
    It should be a formal statement declaring whether the overall residual risk is acceptable in relation to the documented medical benefits of the device.
    """)
    rmf_data["overall_risk_benefit_analysis"] = st.text_area(
        "**Risk-Benefit Analysis Statement:**",
        value=rmf_data.get("overall_risk_benefit_analysis", ""),
        key="rmf_overall_analysis",
        height=150,
        help="Example: 'The overall residual risk of the Smart-Pill System is judged to be acceptable...'"
    )
    ssm.update_data(rmf_data, "risk_management_file")
