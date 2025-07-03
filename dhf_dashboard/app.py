# File: dhf_dashboard/app.py

import streamlit as st
import pandas as pd
import sys
import os

# --- CRITICAL PATH CORRECTION ---
# This is the robust solution to the ModuleNotFoundError.
# It programmatically adds the parent directory (e.g., '/mount/src/dhf/') to the
# system path. This allows Python to find the 'dhf_dashboard' package and its modules
# regardless of where the streamlit command is executed.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# --- EXPLICIT, ABSOLUTE IMPORTS ---
# Now that the path is set correctly, we use absolute imports starting from our
# main package directory 'dhf_dashboard'. This is unambiguous and best practice.

# Import utilities
from dhf_dashboard.utils.session_state_manager import SessionStateManager
from dhf_dashboard.utils.plot_utils import create_gantt_chart
from dhf_dashboard.utils.critical_path_utils import find_critical_path

# Import analytics modules
from dhf_dashboard.analytics.traceability_matrix import render_traceability_matrix
from dhf_dashboard.analytics.action_item_tracker import render_action_item_tracker

# Import all section rendering functions
from dhf_dashboard.dhf_sections import (
    design_plan, design_risk_management, human_factors, design_inputs, design_outputs,
    design_reviews, design_verification, design_validation, design_transfer, design_changes
)

# --- Page Configuration (must be the first Streamlit command) ---
st.set_page_config(
    layout="wide",
    page_title="DHF Command Center",
    page_icon="🚀",
    initial_sidebar_state="expanded"
)

# --- Initialize Session State ---
# This creates our session state manager, which is the single source of truth for all DHF data.
ssm = SessionStateManager()

# --- Main App Title ---
st.title("🚀 DHF Command Center: Smart-Pill Combination Product")
project_name = ssm.get_data("design_plan", "project_name")
st.caption(f"Live monitoring, analytics, and compliance for **{project_name}**")

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
    
    # KPI 1: Overall Progress
    tasks_df = pd.DataFrame(ssm.get_data("project_management", "tasks"))
    completion_pct = tasks_df['completion_pct'].mean() if not tasks_df.empty else 0
    col1.metric("Overall Progress", f"{completion_pct:.1f}%")
    
    # KPI 2: Risk Profile
    hazards_df = pd.DataFrame(ssm.get_data("risk_management_file", "hazards"))
    high_risks = 0
    if not hazards_df.empty and 'initial_risk' in hazards_df.columns:
        high_risks = len(hazards_df[hazards_df['initial_risk'] == 'High'])
    col2.metric("High-Risk Hazards Identified", f"{high_risks}")

    # KPI 3: Open Actions
    actions = []
    for review in ssm.get_data("design_reviews", "reviews"):
        actions.extend(review.get("action_items", []))
    open_actions = len([a for a in actions if a.get('status') != 'Completed'])
    col3.metric("Open Action Items", f"{open_actions}")
    
    # KPI 4: Traceability Coverage
    inputs_df = pd.DataFrame(ssm.get_data("design_inputs", "requirements"))
    outputs_df = pd.DataFrame(ssm.get_data("design_outputs", "documents"))
    traced_inputs = 0
    if not inputs_df.empty and not outputs_df.empty and 'linked_input_id' in outputs_df.columns:
        traced_inputs = inputs_df['id'].isin(outputs_df['linked_input_id']).sum()
    coverage = (traced_inputs / len(inputs_df)) * 100 if not inputs_df.empty else 0
    col4.metric("Input→Output Trace Coverage", f"{coverage:.1f}%", help="Percentage of design inputs that have at least one design output linked to them.")

    st.divider()
    st.header("Project Timeline and Critical Path")
    
    # Calculate and display Gantt chart with critical path
    if not tasks_df.empty:
        critical_path = find_critical_path(tasks_df)
        gantt_fig = create_gantt_chart(tasks_df, critical_path)
        st.plotly_chart(gantt_fig, use_container_width=True)
        st.info("The **Critical Path** (tasks with a red border) represents the longest sequence of dependent tasks. Any delay in these tasks will delay the entire project.")
    else:
        st.warning("No project tasks found. Check the Project Task Editor.")

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
# --- TAB 3: DHF STRUCTURE (V-MODEL) ---
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
# --- TAB 4: DHF SECTION DETAILS & SIDEBAR NAVIGATION ---
# ======================================================================================
with tab4:
    st.header("Data Entry for DHF & RMF Sections")
    st.info("Select a DHF section from the sidebar to view or edit its contents. Changes made here will be reflected across the entire dashboard.")
    
    with st.sidebar:
        st.header("DHF Section Navigation")
        # List of all available pages for the user to select
        page_options = [
            "1. Design Plan", "2. Risk Management File", "3. Human Factors", "4. Design Inputs", "5. Design Outputs",
            "6. Design Reviews & Gates", "7. Design Verification", "8. Design Validation",
            "9. Design Transfer", "10. Design Changes", "11. Project Task Editor"
        ]
        selection = st.radio("Go to Section:", page_options)

        # Helpful info box for users
        st.info("""
        **How to Use:**
        1. Navigate through sections using the radio buttons.
        2. Enter data in the tables and forms.
        3. View high-level progress and analytics on the main dashboard tabs.
        """)
        st.warning("""
        **Dependencies:**
        Ensure you have installed all required packages by running:
        `pip install -r requirements.txt`
        """)

    # --- Page Routing Logic ---
    # A dictionary to map the user's selection to the correct rendering function
    PAGES = {
        "1. Design Plan": design_plan.render,
        "2. Risk Management File": design_risk_management.render,
        "3. Human Factors": human_factors.render,
        "4. Design Inputs": design_inputs.render,
        "5. Design Outputs": design_outputs.render,
        "6. Design Reviews & Gates": design_reviews.render,
        "7. Design Verification": design_verification.render,
        "8. Design Validation": design_validation.render,
        "9. Design Transfer": design_transfer.render,
        "10. Design Changes": design_changes.render,
    }
    
    # Special handling for the Project Task Editor, which is a simple data editor
    if selection == "11. Project Task Editor":
        st.subheader("11. Project Timeline and Task Editor")
        st.warning("Directly edit project timelines, statuses, and dependencies. Changes here will impact the Gantt chart and critical path analysis.")
        tasks_list = ssm.get_data("project_management", "tasks")
        
        # Use st.data_editor to provide a spreadsheet-like interface for editing tasks
        edited_tasks = st.data_editor(tasks_list, num_rows="dynamic", use_container_width=True)
        
        # If the user made changes, save them back to the session state
        if edited_tasks != tasks_list:
            ssm.update_data(edited_tasks, "project_management", "tasks")
            st.success("Project tasks updated!")
            st.rerun() # Rerun the app to immediately reflect changes on the dashboard
    else:
        # For all other selections, call the corresponding function from the PAGES dictionary
        page_function = PAGES[selection]
        page_function(ssm)
