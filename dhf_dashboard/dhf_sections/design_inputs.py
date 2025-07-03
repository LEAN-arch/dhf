# File: dhf_dashboard/dhf_sections/design_inputs.py

import streamlit as st
import pandas as pd
from utils.session_state_manager import SessionStateManager
from datetime import date

def render(ssm: SessionStateManager):
    """
    Renders the Design Inputs section.
    This section is a critical integration point for user needs, technical requirements,
    and risk control measures derived from the risk analysis.
    """
    st.header("4. Design Inputs")

    # --- Project Task Integration ---
    tasks = ssm.get_data("project_management", "tasks")
    task_id_to_find = "INPUTS"
    task_index = next((i for i, task in enumerate(tasks) if task['id'] == task_id_to_find), None)

    if task_index is not None:
        task = tasks[task_index]
        with st.expander("Show/Edit Phase Timeline and Status", expanded=False):
            original_task = task.copy()
            
            task['start_date'] = st.date_input("Phase Start Date", value=task.get('start_date', date.today()), key=f"inputs_start_{task_id_to_find}")
            task['end_date'] = st.date_input("Phase End Date", value=task.get('end_date', date.today()), key=f"inputs_end_{task_id_to_find}")
            
            status_options = ["Not Started", "In Progress", "Completed", "At Risk"]
            current_status_index = status_options.index(task.get('status', "Not Started"))
            task['status'] = st.selectbox("Phase Status", options=status_options, index=current_status_index, key=f"inputs_status_{task_id_to_find}")
            
            task['completion_pct'] = st.slider("Completion %", min_value=0, max_value=100, value=task.get('completion_pct', 0), key=f"inputs_pct_{task_id_to_find}")
            
            if task != original_task:
                tasks[task_index] = task
                ssm.update_data(tasks, "project_management", "tasks")
                st.rerun()
    # --- End Integration ---
    
    st.markdown("""
    *As per 21 CFR 820.30(c), accounting for 21 CFR Part 4 and ISO 14971.*

    This section captures all requirements for the smart-pill. This includes user needs, device requirements (QSR),
    drug interface requirements (cGMP), and requirements derived from risk analysis (Risk Controls).
    Each requirement should be unambiguous, verifiable, and traceable.
    """)

    inputs_data = ssm.get_data("design_inputs", "requirements")
    rmf_data = ssm.get_data("risk_management_file")
    
    # --- Live Traceability Link Preparation ---
    # Fetch all Hazard IDs from the Risk Management File to populate the dropdown.
    # This creates a direct, auditable link from a risk control requirement to the hazard it mitigates.
    hazard_ids = [""] + [h.get('hazard_id', '') for h in rmf_data.get("hazards", [])]

    st.info("Use the table to manage requirements. If a requirement is a risk control, check the box and link it to a Hazard ID.")

    requirements_df = pd.DataFrame(inputs_data)

    edited_df = st.data_editor(
        requirements_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "id": st.column_config.TextColumn("Req. ID", help="Unique ID (e.g., URS-001, DEV-001, DRG-001)", required=True),
            "source_type": st.column_config.SelectboxColumn(
                "Source / Type",
                options=["User Need", "QSR (Device)", "cGMP (Drug Interface)", "Standard", "Risk Control"],
                help="Categorize the origin of the requirement.",
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
        key="design_inputs_editor"
    )
    
    # --- Smart UI Logic ---
    # Automatically set the 'source_type' to 'Risk Control' for any row where the checkbox is checked.
    # This enforces data consistency and saves the user a click.
    if 'is_risk_control' in edited_df.columns:
        edited_df.loc[edited_df['is_risk_control'] == True, 'source_type'] = 'Risk Control'
    
    # Persist data back to the session state
    ssm.update_data(edited_df.to_dict('records'), "design_inputs", "requirements")

    if st.button("Save Design Inputs Section", key="save_design_inputs"):
        st.success("Design Inputs data saved successfully!")
