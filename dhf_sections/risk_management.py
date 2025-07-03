# File: dhf_dashboard/dhf_sections/risk_management.py

import streamlit as st
import pandas as pd
from utils.session_state_manager import SessionStateManager

def render_risk_management(ssm: SessionStateManager):
    """
    Renders the Risk Management File (RMF) Summary section.
    Based on ISO 14971 principles.
    """
    st.header("2. Risk Management File (RMF) Summary")
    st.markdown("""
    *As per ISO 14971:2019 Application of risk management to medical devices.*

    This section summarizes the risk analysis for the smart-pill combination product. It documents identified
    hazards, the foreseeable sequence of events, potential harms, and the estimation of risk *before*
    and *after* risk controls are applied.
    """)

    rmf_data = ssm.get_section_data("risk_management_file")

    st.subheader("2.1 Hazard Analysis and Risk Evaluation")
    st.info("Document all identified hazards related to the device, the drug, and their interaction.")

    hazards_df = pd.DataFrame(rmf_data.get("hazards", []))
    
    # Generate lists for linking
    inputs_data = ssm.get_section_data("design_inputs")
    requirement_ids = [""] + [req.get('id', '') for req in inputs_data.get("requirements", []) if req.get('is_risk_control')]
    
    edited_df = st.data_editor(
        hazards_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "hazard_id": st.column_config.TextColumn("Hazard ID", help="Unique ID (e.g., H-001)", required=True),
            "hazard_description": st.column_config.TextColumn("Hazard Description", help="e.g., Premature battery failure, Incorrect drug dose released, Casing material degradation", required=True),
            "potential_harm": st.column_config.TextColumn("Potential Harm(s)", help="e.g., Ineffective therapy, Toxic exposure, Choking hazard", required=True),
            "initial_severity": st.column_config.NumberColumn("Initial Severity (S)", min_value=1, max_value=5, required=True),
            "initial_probability": st.column_config.NumberColumn("Initial Probability (P)", min_value=1, max_value=5, required=True),
            "initial_risk": st.column_config.TextColumn("Initial Risk Level", help="Calculated or classified (e.g., High, Medium, Low)"),
            "risk_control_req_id": st.column_config.SelectboxColumn("Risk Control (Req. ID)", help="Link to the Design Input requirement that mitigates this risk.", options=requirement_ids),
            "residual_severity": st.column_config.NumberColumn("Residual Severity (S)", min_value=1, max_value=5),
            "residual_probability": st.column_config.NumberColumn("Residual Probability (P)", min_value=1, max_value=5),
            "residual_risk": st.column_config.TextColumn("Residual Risk Level", help="Risk level after controls are implemented."),
            "risk_acceptability": st.column_config.SelectboxColumn("Acceptability", options=["", "Acceptable", "Not Acceptable"]),
        },
        key="risk_management_editor"
    )

    rmf_data["hazards"] = edited_df.to_dict('records')
    ssm.update_section_data("risk_management_file", rmf_data)

    if st.button("Save Risk Management Section"):
        st.success("Risk Management File data saved successfully!")
