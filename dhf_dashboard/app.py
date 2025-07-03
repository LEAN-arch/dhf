# File: dhf_dashboard/app.py

# --- ENVIRONMENT AND PATH CORRECTION ---
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
# --- END OF CORRECTION ---

import streamlit as st
import pandas as pd

# --- EXPLICIT, ABSOLUTE IMPORTS ---
from dhf_dashboard.utils.session_state_manager import SessionStateManager
from dhf_dashboard.utils.plot_utils import (
    create_gantt_chart, 
    create_progress_donut, 
    create_risk_profile_chart, 
    create_action_item_chart
)
from dhf_dashboard.utils.critical_path_utils import find_critical_path
from dhf_dashboard.analytics.traceability_matrix import render_traceability_matrix
from dhf_dashboard.analytics.action_item_tracker import render_action_item_tracker
from dhf_dashboard.dhf_sections import design_plan, design_risk_management, human_factors, design_inputs, design_outputs, design_reviews, design_verification, design_validation, design_transfer, design_changes

# --- Page Configuration ---
st.set_page_config(layout="wide", page_title="DHF Command Center", page_icon="🚀", initial_sidebar_state="expanded")

# --- Initialize Session State ---
ssm = SessionStateManager()

# --- SME ARCHITECTURE: CENTRALIZED DATA LOADING & SANITIZATION ---
# All data is loaded and prepared once, creating a "single source of truth" for this app run.
try:
    # --- Tasks Data ---
    tasks_df = pd.DataFrame(ssm.get_data("project_management", "tasks"))
    if not tasks_df.empty:
        tasks_df['start_date'] = pd.to_datetime(tasks_df['start_date']).dt.date
        tasks_df['end_date'] = pd.to_datetime(tasks_df['end_date']).dt.date
        tasks_df['completion_pct'] = pd.to_numeric(tasks_df['completion_pct'])

    # --- Hazards Data ---
    hazards_df = pd.DataFrame(ssm.get_data("risk_management_file", "hazards"))
    
    # --- Action Items Data ---
    all_actions = []
    reviews_data = ssm.get_data("design_reviews", "reviews")
    if reviews_data:
        for review in reviews_data:
            for item in review.get("action_items", []):
                item['source'] = f"Review: {review.get('id', 'N/A')}"
                all_actions.append(item)
    actions_df = pd.DataFrame(all_actions)

    # --- Traceability Data ---
    inputs_df = pd.DataFrame(ssm.get_data("design_inputs", "requirements"))
    outputs_df = pd.DataFrame(ssm.get_data("design_outputs", "documents"))

except Exception as e:
    st.error(f"An error occurred while loading and processing data: {e}")
    st.warning("Cannot render dashboard. Please check data integrity or reset session.")
    st.stop()
# --- END OF CENTRALIZED DATA LOADING ---


# --- Main App ---
st.title("🚀 DHF Command Center: Smart-Pill Combination Product")
project_name = ssm.get_data("design_plan", "project_name")
st.caption(f"Live monitoring, analytics, and compliance for **{project_name}**")

# --- Sidebar Navigation ---
with st.sidebar:
    st.header("DHF Section Navigation")
    page_options = ["1. Design Plan", "2. Risk Management File", "3. Human Factors", "4. Design Inputs", "5. Design Outputs", "6. Design Reviews & Gates", "7. Design Verification", "8. Design Validation", "9. Design Transfer", "10. Design Changes", "11. Project Task Editor"]
    selection = st.radio("Go to Section:", page_options)
    st.info("Navigate and edit DHF sections. Content is shown in the 'DHF Section Details' tab.")

# --- Main Tabbed Interface ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Project Dashboard", "📈 Advanced Analytics", "📜 DHF Structure (V-Model)", "🗂️ DHF Section Details"])

with tab1:
    st.header("Project Health & Key Performance Indicators (KPIs)")
    
    col1, col2 = st.columns(2)
    with col1:
        completion_pct = tasks_df['completion_pct'].mean() if not tasks_df.empty else 0
        st.plotly_chart(create_progress_donut(completion_pct), use_container_width=True)
    with col2:
        st.plotly_chart(create_risk_profile_chart(hazards_df), use_container_width=True)

    st.divider()

    col3, col4 = st.columns(2)
    with col3:
        st.plotly_chart(create_action_item_chart(actions_df), use_container_width=True)
    with col4:
        st.subheader("Compliance Scorecard")
        traced_inputs = 0
        if not inputs_df.empty and 'id' in inputs_df.columns and not outputs_df.empty and 'linked_input_id' in outputs_df.columns:
            linked_ids = outputs_df['linked_input_id'].dropna()
            traced_inputs = inputs_df['id'].isin(linked_ids).sum()
        coverage = (traced_inputs / len(inputs_df)) * 100 if not inputs_df.empty else 0
        st.metric( "Input→Output Trace Coverage", f"{coverage:.1f}%", f"{traced_inputs} of {len(inputs_df)} inputs traced", delta_color="off")
        
        unaccepted_risks = 0
        if not hazards_df.empty and 'residual_risk_accepted' in hazards_df.columns:
            unaccepted_risks = len(hazards_df[hazards_df['residual_risk_accepted'] == False])
        st.metric( "Unaccepted Residual Risks", f"{unaccepted_risks}", help="Number of risks where mitigations are complete but the final risk has not been formally accepted.", delta_color="inverse")

    st.divider()
    st.header("Project Timeline and Critical Path")
    
    if not tasks_df.empty:
        # We now use the globally defined and sanitized tasks_df
        critical_path = find_critical_path(tasks_df.copy()) # Pass a copy to prevent mutation
        gantt_fig = create_gantt_chart(tasks_df, critical_path)
        st.plotly_chart(gantt_fig, use_container_width=True)
    else:
        st.warning("No project tasks found. Add tasks in the Project Task Editor.")

with tab2:
    st.header("Compliance & Execution Analytics")
    analytics_selection = st.selectbox("Choose Analytics View:", ["Traceability Matrix", "Action Item Tracker"])
    if analytics_selection == "Traceability Matrix":
        render_traceability_matrix(ssm)
    elif analytics_selection == "Action Item Tracker":
        render_action_item_tracker(ssm)

with tab3:
    st.header("The Design Control Process (V-Model)")
    st.image("https://www.researchgate.net/profile/Tor-Staalhane/publication/277005111/figure/fig1/AS:669443530891271@1536619171887/The-V-model-of-development-and-testing.png",
             caption="A typical V-Model illustrating the relationship between Design Inputs, Outputs, Verification, and Validation.")
    st.markdown("""
    The "V-Model" is a standard graphical representation for the medical device design control process. It illustrates how the design and development phases (the left side of the V) are directly linked to corresponding testing and validation phases (the right side of the V).
    For software-driven devices like this smart-pill, the V-Model is augmented by processes from **IEC 62304** (Software Lifecycle Processes) and **IEC 62366** (Usability Engineering), ensuring rigor in both software development and user interface design.
    """)

with tab4:
    st.header(f"DHF Section Details: {selection}")
    st.info("Use the sidebar to navigate. Changes made here will be reflected across the dashboard on the next rerun.")
    st.divider()

    PAGES = {"1. Design Plan": design_plan, "2. Risk Management File": design_risk_management, "3. Human Factors": human_factors, "4. Design Inputs": design_inputs, "5. Design Outputs": design_outputs, "6. Design Reviews & Gates": design_reviews, "7. Design Verification": design_verification, "8. Design Validation": design_validation, "9. Design Transfer": design_transfer, "10. Design Changes": design_changes}
    
    if selection == "11. Project Task Editor":
        st.subheader("Project Timeline and Task Editor")
        st.warning("Directly edit project timelines, statuses, and dependencies. Dates should be YYYY-MM-DD.")
        
        # --- SME FIX: Use the authoritative tasks_df as the input for the editor ---
        edited_df = st.data_editor(
            tasks_df, 
            key="main_task_editor", 
            num_rows="dynamic", 
            use_container_width=True,
            # Ensure dates are editable in a user-friendly format
            column_config={
                "start_date": st.column_config.DateColumn("Start Date", format="YYYY-MM-DD"),
                "end_date": st.column_config.DateColumn("End Date", format="YYYY-MM-DD")
            }
        )

        # Use the robust .equals() method for DataFrame comparison
        if not edited_df.equals(tasks_df):
            # Convert the edited DataFrame back to the primitive format for storage
            updated_tasks_list = edited_df.to_dict('records')
            ssm.update_data(updated_tasks_list, "project_management", "tasks")
            st.success("Project tasks updated! Rerunning to reflect changes across the dashboard...")
            st.rerun()
    else:
        page_module = PAGES[selection]
        page_module.render(ssm)
