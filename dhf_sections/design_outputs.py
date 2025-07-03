# File: dhf_dashboard/dhf_sections/design_outputs.py

import streamlit as st
import pandas as pd
from utils.session_state_manager import SessionStateManager
from datetime import date

def render(ssm: SessionStateManager):
    """
    Renders the Design Outputs section.
    This section documents all the tangible outputs of the design process and ensures
    they are traceable back to a specific design input.
    """
    st.header("5. Design Outputs")
    
    # --- Project Task Integration ---
    tasks = ssm.get_data("project_management", "tasks")
    task_id_to_find = "OUTPUTS"
    task_index = next((i for i, task in enumerate(tasks) if task['id'] == task_id_to_find), None)

    if task_index is not None:
        task = tasks[task_index]
        with st.expander("Show/Edit Phase Timeline and Status", expanded=False):
            original_task = task.copy()
            
            task['start_date'] = st.date_input("Phase Start Date", value=task.get('start_date', date.today()), key=f"outputs_start_{task_id_to_find}")
            task['end_date'] = st.date_input("Phase End Date", value=task.get('end_date', date.today()), key=f"outputs_end_{task_id_to_find}")
            
            status_options = ["Not Started", "In Progress", "Completed", "At Risk"]
            current_status_index = status_options.index(task.get('status', "Not Started"))
            task['status'] = st.selectbox("Phase Status", options=status_options, index=current_status_index, key=f"outputs_status_{task_id_to_find}")
            
            task['completion_pct'] = st.slider("Completion %", min_value=0, max_value=100, value=task.get('completion_pct', 0), key=f"outputs_pct_{task_id_to_find}")
            
            if task != original_task:
                tasks[task_index] = task
                ssm.update_data(tasks, "project_management", "tasks")
                st.rerun()
    # --- End Integration ---
    
    st.markdown("""
    *As per 21 CFR 820.30(d).*

    Design outputs are the tangible results of the design process. For this smart-pill, they include not only
    device drawings and software source code, but also specifications for drug-device interaction, such as:
    - Material specifications (biocompatibility, inertness to the drug)
    - Drug release profile specifications
    - Finalized software architecture and code
    - Manufacturing procedures that address both device assembly and drug handling.
    
    **Crucially, each output must be traceable to a design input.**
    """)

    outputs_data = ssm.get_data("design_outputs", "documents")
    inputs_data = ssm.get_data("design_inputs", "requirements")

    # --- Live Traceability Link Preparation ---
    # Create a list of all existing Design Input IDs to populate the dropdown.
    # The initial blank string is a best practice for dropdowns.
    if not inputs_data:
        st.warning("⚠️ No Design Inputs found. Please add requirements in the 'Design Inputs' section before creating outputs.")
        req_ids = [""]
    else:
        req_ids = [""] + [req.get('id', '') for req in inputs_data]

    st.info("Use the table to list all design outputs (e.g., drawings, specifications, source code) and link them to a design input requirement.")

    outputs_df = pd.DataFrame(outputs_data)
    
    edited_df = st.data_editor(
        outputs_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "id": st.column_config.TextColumn("Output ID", help="Unique identifier for the output (e.g., DWG-101, SPEC-002)", required=True),
            "title": st.column_config.TextColumn("Output Title/Description", width="large", required=True),
            "file": st.column_config.TextColumn("File Name / Link", help="e.g., 'CAD-Assembly-Final.zip' or a link to a document repository"),
            "linked_input_id": st.column_config.SelectboxColumn(
                "Trace to Input ID", 
                help="Select the Design Input Requirement this output satisfies.",
                options=req_ids, 
                required=True # This enforces traceability
            ),
        },
        key="design_outputs_editor"
    )
    
    # Persist the updated data back to the session state
    ssm.update_data(edited_df.to_dict('records'), "design_outputs", "documents")

    if st.button("Save Design Outputs Section", key="save_design_outputs"):
        st.success("Design Outputs data saved successfully!")
