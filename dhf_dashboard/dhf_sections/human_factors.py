# File: dhf_dashboard/dhf_sections/human_factors.py

import streamlit as st
import pandas as pd
from utils.session_state_manager import SessionStateManager

def render(ssm: SessionStateManager):
    st.header("3. Human Factors & Usability Engineering (IEC 62366)")
    
    # --- Project Task Integration ---
    tasks = ssm.get_data("project_management", "tasks")
    task = next((t for t in tasks if t['id'] == 'HF'), None)
    if task:
        with st.expander("Show/Edit Phase Timeline and Status", expanded=False):
            # ... (task editor logic for 'HF' task) ...
            pass
    
    st.markdown("""
    This section documents the usability engineering process to ensure the smart-pill can be used safely and effectively.
    We identify tasks users perform, analyze potential use errors, and link them to clinical hazards.
    """)
    
    hf_data = ssm.get_data("human_factors", "use_scenarios")
    rmf_data = ssm.get_data("risk_management_file")
    
    # Get hazard IDs to link to
    hazard_ids = [""] + [h.get('hazard_id', '') for h in rmf_data.get("hazards", [])]
    
    st.subheader("Use-Related Risk Analysis (URRA)")
    
    edited_df = st.data_editor(
        pd.DataFrame(hf_data),
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "use_scenario": st.column_config.TextColumn("Use Scenario", help="e.g., Patient receives prescription, Patient takes daily pill", required=True),
            "user_task": st.column_config.TextColumn("Critical User Task", help="e.g., Swallows pill with water, Checks app for confirmation", required=True),
            "potential_use_error": st.column_config.TextColumn("Potential Use Error", help="e.g., Takes pill without water, Forgets to take pill, Takes double dose"),
            "potential_harm": st.column_config.TextColumn("Resulting Potential Harm", help="e.g., Pill lodges in esophagus, Ineffective therapy, Overdose"),
            "related_hazard_id": st.column_config.SelectboxColumn("Links to Hazard ID", options=hazard_ids, help="Link this use error to a formal system hazard."),
        },
        key="hf_editor"
    )
    
    ssm.update_data(edited_df.to_dict('records'), "human_factors", "use_scenarios")
    
    if st.button("Save Human Factors Section"):
        st.success("Human Factors data saved successfully!")
