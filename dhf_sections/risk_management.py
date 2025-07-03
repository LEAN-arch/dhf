# File: dhf_dashboard/dhf_sections/design_risk_management.py

import streamlit as st
import pandas as pd
from utils.session_state_manager import SessionStateManager
from datetime import date

def render(ssm: SessionStateManager):
    """
    Renders the Risk Management File (RMF) Summary section.
    Based on ISO 14971 principles and integrated with project management.
    """
    st.header("2. Risk Management File (RMF) Summary")
    
    # --- Project Task Integration ---
    tasks = ssm.get_data("project_management", "tasks")
    task_id_to_find = "RISK"
    task_index = next((i for i, task in enumerate(tasks) if task['id'] == task_id_to_find), None)

    if task_index is not None:
        task = tasks[task_index]
        with st.expander("Show/Edit Phase Timeline and Status", expanded=False):
            original_task = task.copy()
            
            task['start_date'] = st.date_input("Phase Start Date", value=task.get('start_date', date.today()), key=f"risk_start_{task_id_to_find}")
            task['end_date'] = st.date_input("Phase End Date", value=task.get('end_date', date.today()), key=f"risk_end_{task_id_to_find}")
            
            status_options = ["Not Started", "In Progress", "Completed", "At Risk"]
            current_status_index = status_options.index(task.get('status', "Not Started"))
            task['status'] = st.selectbox("Phase Status", options=status_options, index=current_status_index, key=f"risk_status_{task_id_to_find}")
            
            task['completion_pct'] = st.slider("Completion %", min_value=0, max_value=100, value=task.get('completion_pct', 0), key=f"risk_pct_{task_id_to_find}")
            
            if task != original_task:
                tasks[task_index] = task
                ssm.update_data(tasks, "project_management", "tasks")
                st.rerun()
    # --- End Integration ---

    st.markdown("""
    *As per ISO 14971:2019 Application of risk management to medical devices.*

    This section summarizes the risk analysis for the smart-pill combination product. It documents identified
    hazards, the foreseeable sequence of events, potential harms, and the estimation of risk *before*
    and *after* risk controls are applied.
    """)

    rmf_data = ssm.get_data("risk_management_file")

    st.subheader("2.1 Hazard Analysis and Risk Evaluation")
    st.info("Document all identified hazards related to the device, the drug, and their interaction. Link risk controls from the Design Inputs section to demonstrate mitigation.")

    hazards_df = pd.DataFrame(rmf_data.get("hazards", []))
    
    # --- Live Traceability Link ---
    # Fetch requirements that have been flagged as risk controls from the Design Inputs section
    # This creates a dynamic dropdown for linking a hazard to its specific mitigation.
    inputs_data = ssm.get_data("design_inputs", "requirements")
    risk_control_requirement_ids = [""] + [
        req.get('id', '') for req in inputs_data if req.get('source_type') == 'Risk Control'
    ]
    
    edited_df = st.data_editor(
        hazards_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "hazard_id": st.column_config.TextColumn("Hazard ID", help="Unique ID (e.g., H-001)", required=True),
            "hazard_description": st.column_config.TextColumn("Hazard Description", help="e.g., Premature battery failure, Incorrect drug dose released, Casing material degradation", required=True),
            "potential_harm": st.column_config.TextColumn("Potential Harm(s)", help="e.g., Ineffective therapy, Toxic exposure, Choking hazard", required=True),
            "initial_severity": st.column_config.NumberColumn("Initial Severity (S)", help="Severity on a 1-5 scale", min_value=1, max_value=5, required=True),
            "initial_probability": st.column_config.NumberColumn("Initial Probability (P)", help="Probability on a 1-5 scale", min_value=1, max_value=5, required=True),
            "initial_risk": st.column_config.TextColumn("Initial Risk Level", help="Calculated or classified (e.g., High, Medium, Low)"),
            "risk_control_req_id": st.column_config.SelectboxColumn("Risk Control (Req. ID)", help="Link to the Design Input requirement that mitigates this risk.", options=risk_control_requirement_ids, required=True),
            "residual_severity": st.column_config.NumberColumn("Residual Severity (S)", help="Severity after risk control", min_value=1, max_value=5),
            "residual_probability": st.column_config.NumberColumn("Residual Probability (P)", help="Probability after risk control", min_value=1, max_value=5),
            "residual_risk": st.column_config.TextColumn("Residual Risk Level", help="Risk level after controls are implemented."),
            "risk_acceptability": st.column_config.SelectboxColumn("Acceptability", options=["", "Acceptable", "Not Acceptable"]),
        },
        key="risk_management_editor"
    )

    rmf_data["hazards"] = edited_df.to_dict('records')

    # --- Formal Risk-Benefit Analysis Conclusion ---
    st.subheader("2.2 Overall Residual Risk Acceptability")
    st.info("""
    This is the final conclusion of the risk management process, as required by ISO 14971.
    It should be a formal statement declaring whether the overall residual risk, considering all identified hazards and mitigations,
    is acceptable in relation to the documented medical benefits of the device. This statement is a key part of the Risk Management Report.
    """)
    rmf_data["overall_risk_benefit_analysis"] = st.text_area(
        "Risk-Benefit Analysis Statement:",
        value=rmf_data.get("overall_risk_benefit_analysis", "Analysis pending completion of all verification and validation activities."),
        height=150,
        help="Example: 'The overall residual risk of the Smart-Pill System is judged to be acceptable, as the benefits of accurate and timely drug delivery for the specified patient population outweigh the identified residual risks.'"
    )
    
    # Persist all changes to the session state
    ssm.update_data(rmf_data, "risk_management_file")

    if st.button("Save Risk Management Section", key="save_risk_management"):
        st.success("Risk Management File data saved successfully!")

    if st.button("Save Risk Management Section"):
        st.success("Risk Management File data saved successfully!")
