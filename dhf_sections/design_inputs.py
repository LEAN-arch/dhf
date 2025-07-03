# File: dhf_dashboard/dhf_sections/design_inputs.py

import streamlit as st
import pandas as pd
from utils.session_state_manager import SessionStateManager

def render_design_inputs(ssm: SessionStateManager):
    """
    Renders the Design Inputs section, adapted for a combination product and ISO 14971.
    """
    st.header("3. Design Inputs")
    st.markdown("""
    *As per 21 CFR 820.30(c), accounting for 21 CFR Part 4 and ISO 14971.*

    This section captures all requirements for the smart-pill. This includes user needs, device requirements (QSR),
    drug interface requirements (cGMP), and requirements derived from risk analysis (Risk Controls).
    """)

    inputs_data = ssm.get_section_data("design_inputs")
    rmf_data = ssm.get_section_data("risk_management_file")
    
    # Get a list of hazard IDs for the dropdown
    hazard_ids = [""] + [h.get('hazard_id', '') for h in rmf_data.get("hazards", [])]

    st.info("Use the table to manage requirements. If a requirement is a risk control, link it to a Hazard ID.")

    requirements_df = pd.DataFrame(inputs_data.get("requirements", []))

    edited_df = st.data_editor(
        requirements_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "id": st.column_config.TextColumn("Req. ID", help="Unique ID (e.g., URS-001, DEV-001, DRG-001)", required=True),
            "source_type": st.column_config.SelectboxColumn(
                "Source / Type",
                options=["User Need", "QSR (Device)", "cGMP (Drug Interface)", "Standard", "Risk Control"],
                required=True
            ),
            "description": st.column_config.TextColumn("Requirement Description", required=True),
            "is_risk_control": st.column_config.CheckboxColumn("Is this a Risk Control?", default=False),
            "related_hazard_id": st.column_config.SelectboxColumn(
                "Mitigates Hazard ID",
                options=hazard_ids,
                help="If this is a risk control, which hazard does it mitigate?"
            ),
        },
        key="design_inputs_editor"
    )
    
    # Logic to automatically mark 'source_type' if 'is_risk_control' is checked
    edited_df.loc[edited_df['is_risk_control'] == True, 'source_type'] = 'Risk Control'
    
    inputs_data["requirements"] = edited_df.to_dict('records')
    ssm.update_section_data("design_inputs", inputs_data)

    if st.button("Save Design Inputs Section"):
        st.success("Design Inputs data saved successfully!")
