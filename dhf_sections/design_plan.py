# File: dhf_dashboard/dhf_sections/design_plan.py

import streamlit as st
import pandas as pd
from utils.session_state_manager import SessionStateManager
from datetime import date

def render(ssm: SessionStateManager):
    """
    Renders the Design and Development Plan section of the DHF Dashboard.
    This section is adapted for a combination product and integrated with project management timelines.
    """
    st.header("1. Design and Development Plan")

    # --- Project Task Integration ---
    # This block links the detailed plan to its high-level project task on the main dashboard.
    tasks = ssm.get_data("project_management", "tasks")
    task_id_to_find = "PLAN"
    
    # Find the specific task for this DHF section
    task_index = next((i for i, task in enumerate(tasks) if task['id'] == task_id_to_find), None)

    if task_index is not None:
        task = tasks[task_index]
        with st.expander("Show/Edit Phase Timeline and Status", expanded=False):
            # Allow users to update the timeline and status directly from this page
            original_task = task.copy()

            task['start_date'] = st.date_input(
                "Phase Start Date", 
                value=task.get('start_date', date.today()), 
                key=f"plan_start_{task_id_to_find}"
            )
            task['end_date'] = st.date_input(
                "Phase End Date", 
                value=task.get('end_date', date.today()), 
                key=f"plan_end_{task_id_to_find}"
            )
            
            status_options = ["Not Started", "In Progress", "Completed", "At Risk"]
            current_status_index = status_options.index(task.get('status', "Not Started"))
            task['status'] = st.selectbox(
                "Phase Status", 
                options=status_options, 
                index=current_status_index, 
                key=f"plan_status_{task_id_to_find}"
            )
            task['completion_pct'] = st.slider(
                "Completion %", 
                min_value=0, 
                max_value=100, 
                value=task.get('completion_pct', 0), 
                key=f"plan_pct_{task_id_to_find}"
            )
            
            # If changes were made, update the session state
            if task != original_task:
                tasks[task_index] = task
                ssm.update_data(tasks, "project_management", "tasks")
                st.rerun() # Rerun to reflect changes immediately
    # --- End Integration ---

    st.markdown("""
    *As per 21 CFR 820.30(b) and principles of 21 CFR Part 4.*

    This plan outlines the design activities for the **smart-pill combination product**. It must
    address both the device component (under the Quality System Regulation) and its interface
    with the drug component (under cGMPs). It also defines the project scope, team, and key regulatory considerations.
    """)

    plan_data = ssm.get_data("design_plan")

    # --- Project Information ---
    st.subheader("1.1 Project Overview")
    plan_data["project_name"] = st.text_input(
        "Project Name",
        value=plan_data.get("project_name", "Smart-Pill Drug Delivery System"),
        help="The official name of the combination product project."
    )
    plan_data["scope"] = st.text_area(
        "Project Scope & Intended Use",
        value=plan_data.get("scope", ""),
        height=150,
        help="Describe the device, the drug it delivers, the target patient population, the clinical indication, and the use environment."
    )

    # --- Regulatory and Risk Framework ---
    st.subheader("1.2 Regulatory and Risk Management Framework")
    plan_data["applicable_cgmp"] = st.text_input(
        "Applicable Drug cGMPs",
        value=plan_data.get("applicable_cgmp", "21 CFR Parts 210, 211"),
        help="Reference the Current Good Manufacturing Practices applicable to the drug constituent part."
    )
    plan_data["risk_management_plan_ref"] = st.text_input(
        "Risk Management Plan Document ID",
        value=plan_data.get("risk_management_plan_ref", ""),
        help="Reference to the main Risk Management Plan document governing activities under ISO 14971."
    )
    
    # --- Software Classification ---
    st.subheader("1.3 Software Level of Concern (Per FDA Guidance)")
    current_loc_index = ["Major", "Moderate", "Minor"].index(plan_data.get("software_level_of_concern", "Moderate"))
    plan_data["software_level_of_concern"] = st.selectbox(
        "Select Software Level of Concern (LOC):",
        options=["Major", "Moderate", "Minor"],
        index=current_loc_index,
        help="Determines the required rigor of software documentation per IEC 62304. Major: Serious injury or death possible. Moderate: Non-serious injury possible. Minor: No injury possible."
    )

    # --- Team and Responsibilities ---
    st.subheader("1.4 Team and Responsibilities")
    st.info("Use the table below to define roles, assign team members, and outline their key responsibilities.")
    
    team_df = pd.DataFrame(plan_data.get("team_members", []))
    edited_df = st.data_editor(
        team_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "role": st.column_config.TextColumn("Role", help="e.g., Device Engineer, Pharma Scientist, RA Specialist, SW Engineer", required=True),
            "name": st.column_config.TextColumn("Assigned Member", required=True),
            "responsibility": st.column_config.TextColumn("Key Responsibilities"),
        },
        key="design_plan_team_editor"
    )
    plan_data["team_members"] = edited_df.to_dict('records')

    # Persist all changes made in this section
    ssm.update_data(plan_data, "design_plan")
    
    if st.button("Save Design Plan Section", key="save_design_plan"):
        st.success("Design Plan data saved successfully!")
