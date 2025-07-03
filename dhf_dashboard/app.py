# File: dhf_dashboard/app.py

# NO MORE sys.path.append HERE.
# We will handle the path by how we EXECUTE the script.

import streamlit as st
import pandas as pd
import os

# --- EXPLICIT, ABSOLUTE IMPORTS ---
# These are correct. They assume the directory containing 'dhf_dashboard'
# is the top-level of our project path.

# Import utilities
from dhf_dashboard.utils.session_state_manager import SessionStateManager
from dhf_dashboard.utils.plot_utils import create_gantt_chart
from dhf_dashboard.utils.critical_path_utils import find_critical_path

# Import analytics modules
from dhf_dashboard.analytics.traceability_matrix import render_traceability_matrix
from dhf_dashboard.analytics.action_item_tracker import render_action_item_tracker

# Import all section rendering modules
from dhf_dashboard.dhf_sections import design_plan
from dhf_dashboard.dhf_sections import design_risk_management
from dhf_dashboard.dhf_sections import human_factors
from dhf_dashboard.dhf_sections import design_inputs
from dhf_dashboard.dhf_sections import design_outputs
from dhf_dashboard.dhf_sections import design_reviews
from dhf_dashboard.dhf_sections import design_verification
from dhf_dashboard.dhf_sections import design_validation
from dhf_dashboard.dhf_sections import design_transfer
from dhf_dashboard.dhf_sections import design_changes

# --- Page Configuration ---
st.set_page_config(
    layout="wide",
    page_title="DHF Command Center",
    page_icon="🚀",
    initial_sidebar_state="expanded"
)

# --- Initialize Session State ---
ssm = SessionStateManager()

# --- Main App Title ---
st.title("🚀 DHF Command Center: Smart-Pill Combination Product")
project_name = ssm.get_data("design_plan", "project_name")
st.caption(f"Live monitoring, analytics, and compliance for **{project_name}**")

# --- Define Sidebar Navigation at the Global Level ---
with st.sidebar:
    st.header("DHF Section Navigation")
    page_options = [
        "1. Design Plan", "2. Risk Management File", "3. Human Factors", "4. Design Inputs", "5. Design Outputs",
        "6. Design Reviews & Gates", "7. Design Verification", "8. Design Validation",
        "9. Design Transfer", "10. Design Changes", "11. Project Task Editor"
    ]
    selection = st.radio("Go to Section:", page_options)
    st.info("This sidebar allows you to navigate and edit the detailed content for each DHF section, which is displayed in the 'DHF Section Details' tab.")
    st.warning("Ensure all data is saved before navigating away.")

# --- Main Tabbed Interface ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Project Dashboard", 
    "📈 Advanced Analytics", 
    "📜 DHF Structure (V-Model)", 
    "🗂️ DHF Section Details"
])

# ======================================================================================
# --- TAB 1: PROJECT DASHBOARD ---
# ======================================================================================
with tab1:
    st.header("Project Health & Key Performance Indicators (KPIs)")
    
    col1, col2, col3, col4 = st.columns(4)
    
    tasks_df = pd.DataFrame(ssm.get_data("project_management", "tasks"))
    completion_pct = tasks_df['completion_pct'].mean() if not tasks_df.empty else 0
    col1.metric("Overall Progress", f"{completion_pct:.1f}%")
    
    hazards_df = pd.DataFrame(ssm.get_data("risk_management_file", "hazards"))
    high_risks = 0
    if not hazards_df.empty and 'initial_risk' in hazards_df.columns:
        high_risks = len(hazards_df[hazards_df['initial_risk'] == 'High'])
    col2.metric("High-Risk Hazards Identified", f"{high_risks}")

    actions = []
    reviews_data = ssm.get_data("design_reviews", "reviews")
    if reviews_data:
        for review in reviews_data:
            actions.extend(review.get("action_items", []))
    open_actions = len([a for a in actions if a.get('status') != 'Completed'])
    col3.metric("Open Action Items", f"{open_actions}")
    
    inputs_df = pd.DataFrame(ssm.get_data("design_inputs", "requirements"))
    outputs_df = pd.DataFrame(ssm.get_data("design_outputs", "documents"))
    traced_inputs = 0
    
    if not inputs_df.empty and 'id' in inputs_df.columns and not outputs_df.empty and 'linked_input_id' in outputs_df.columns:
        linked_ids = outputs_df['linked_input_id'].dropna()
        traced_inputs = inputs_df['id'].isin(linked_ids).sum()
        
    coverage = (traced_inputs / len(inputs_df)) * 100 if not inputs_df.empty else 0
    col4.metric("Input→Output Trace Coverage", f"{coverage:.1f}%", help="Percentage of design inputs that have at least one design output linked to them.")

    st.divider()
    st.header("Project Timeline and Critical Path")
    
    if not tasks_df.empty:
        # --- FIX IS HERE ---
        # Robustly convert date columns to datetime objects before using them.
        # This prevents crashes if the data in session_state is not in the correct format.
        tasks_df['start_date'] = pd.to_datetime(tasks_df['start_date'])
        tasks_df['end_date'] = pd.to_datetime(tasks_df['end_date'])
        # --- END OF FIX ---

        critical_path = find_critical_path(tasks_df)
        gantt_fig = create_gantt_chart(tasks_df, critical_path)
        st.plotly_chart(gantt_fig, use_container_width=True)
        st.info("The **Critical Path** (tasks with a red border) represents the longest sequence of dependent tasks. Any delay in these tasks will delay the entire project.")
    else:
        st.warning("No project tasks found. Check the Project Task Editor.")

# ... (rest of the file is unchanged) ...

# ======================================================================================
# --- TAB 2: ADVANCED ANALYTICS ---
# ======================================================================================
with tab2:
    st.header("Compliance & Execution Analytics")
    analytics_selection = st.selectbox("Choose Analytics View:", ["Traceability Matrix", "Action Item Tracker"])
    
    if analytics_selection == "Traceability Matrix":
        render_traceability_matrix(ssm)
    elif analytics_selection == "Action Item Tracker":
        render_action_item_tracker(ssm)

# ======================================================================================
# --- TAB 3: DHF STRUCTURE (V-Model) ---
# ======================================================================================
with tab3:
    st.header("The Design Control Process (V-Model)")
    st.image("https://www.researchgate.net/profile/Tor-Staalhane/publication/277005111/figure/fig1/AS:669443530891271@1536619171887/The-V-model-of-development-and-testing.png",
             caption="A typical V-Model illustrating the relationship between Design Inputs, Outputs, Verification, and Validation.")
    st.markdown("""
    The "V-Model" is a standard graphical representation for the medical device design control process. It illustrates how the design and development phases (the left side of the V) are directly linked to corresponding testing and validation phases (the right side of the V).

    For software-driven devices like this smart-pill, the V-Model is augmented by processes from **IEC 62304** (Software Lifecycle Processes) and **IEC 62366** (Usability Engineering), ensuring rigor in both software development and user interface design.
    """)

# ======================================================================================
# --- TAB 4: DHF SECTION DETAILS ---
# ======================================================================================
with tab4:
    st.header(f"DHF Section Details: {selection}")
    st.info("Use the sidebar to navigate between DHF sections. Changes made here will be reflected across the entire dashboard.")
    st.divider()

    PAGES = {
        "1. Design Plan": design_plan,
        "2. Risk Management File": design_risk_management,
        "3. Human Factors": human_factors,
        "4. Design Inputs": design_inputs,
        "5. Design Outputs": design_outputs,
        "6. Design Reviews & Gates": design_reviews,
        "7. Design Verification": design_verification,
        "8. Design Validation": design_validation,
        "9. Design Transfer": design_transfer,
        "10. Design Changes": design_changes,
    }
    
    if selection == "11. Project Task Editor":
        st.subheader("Project Timeline and Task Editor")
        st.warning("Directly edit project timelines, statuses, and dependencies.")
        tasks_list = ssm.get_data("project_management", "tasks")
        edited_tasks = st.data_editor(tasks_list, key="main_task_editor", num_rows="dynamic", use_container_width=True)
        if edited_tasks != tasks_list:
            ssm.update_data(edited_tasks, "project_management", "tasks")
            st.success("Project tasks updated!")
            st.rerun()
    else:
        page_module = PAGES[selection]
        page_module.render(ssm)
