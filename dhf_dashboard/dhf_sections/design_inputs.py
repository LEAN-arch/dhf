# File: dhf_dashboard/dhf_sections/design_inputs.py

import streamlit as st
import pandas as pd
from ..utils.session_state_manager import SessionStateManager

def render_design_inputs(ssm: SessionStateManager):
    """
    Renders the Design Inputs section. This section is a critical integration point
    for user needs, technical requirements, and risk control measures.
    """
    st.header("4. Design Inputs")
    st.markdown("""
    *As per 21 CFR 820.30(c), accounting for 21 CFR Part 4 and ISO 14971.*

    This section captures all requirements for the product. This includes user needs, device requirements (QSR),
    drug interface requirements (cGMP), and requirements derived from risk analysis (Risk Controls).
    Each requirement must be unambiguous, verifiable, and traceable.
    """)
    st.info("Changes made here are saved automatically. Checking 'Is a Risk Control?' will auto-set the Source/Type.", icon="ℹ️")

    inputs_data = ssm.get_data("design_inputs", "requirements")
    rmf_data = ssm.get_data("risk_management_file")

    # --- SME Enhancement: Live Traceability Link Preparation ---
    # Fetch all Hazard IDs from the Risk Management File to populate the dropdown.
    # This creates a direct, auditable link from a risk control requirement to the hazard it mitigates.
    hazard_ids = [""] + [h.get('hazard_id', '') for h in rmf_data.get("hazards", [])]

    st.subheader("Requirements and Needs")
    st.markdown("Use this table to manage all project requirements. If a requirement is a risk control, check the box and link it to a Hazard ID.")

    requirements_df = pd.DataFrame(inputs_data)

    edited_df = st.data_editor(
        requirements_df,
        num_rows="dynamic",
        use_container_width=True,
        key="design_inputs_editor",
        column_config={
            "id": st.column_config.TextColumn("Req. ID", help="Unique ID (e.g., UN-001, DEV-001, RC-001)", required=True),
            "source_type": st.column_config.SelectboxColumn(
                "Source / Type",
                options=["User Need", "QSR (Device)", "cGMP (Drug Interface)", "Standard", "Risk Control"],
                help="Categorize the origin of the requirement. Will be set to 'Risk Control' automatically if the checkbox is ticked.",
                required=True
            ),
            "description": st.column_config.TextColumn("Requirement Description", width="large", required=True),
            "is_risk_control": st.column_config.CheckboxColumn("Is a Risk Control?", help="Check if this requirement is a mitigation for a hazard.", default=False),
            "related_hazard_id": st.column_config.SelectboxColumn(
                "Mitigates Hazard ID",
                options=hazard_ids,
                help="If this is a risk control, which hazard from the RMF does it mitigate?"
            ),
        },
    )

    # --- SME Enhancement: Smart UI Logic ---
    # Automatically set the 'source_type' to 'Risk Control' for any row where the checkbox is checked.
    # This enforces data consistency and saves the user a click.
    if 'is_risk_control' in edited_df.columns:
        edited_df.loc[edited_df['is_risk_control'] == True, 'source_type'] = 'Risk Control'
        # Also clear the hazard link if it's no longer a risk control
        edited_df.loc[edited_df['is_risk_control'] == False, 'related_hazard_id'] = ""


    # Persist data back to the session state
    ssm.update_data(edited_df.to_dict('records'), "design_inputs", "requirements")
