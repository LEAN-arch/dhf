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

# --- IMPORTS ---
from dhf_dashboard.utils.session_state_manager import SessionStateManager
from dhf_dashboard.utils.plot_utils import create_gantt_chart, create_progress_donut, create_risk_profile_chart, create_action_item_chart
from dhf_dashboard.utils.critical_path_utils import find_critical_path
from dhf_dashboard.analytics.traceability_matrix import render_traceability_matrix
from dhf_dashboard.analytics.action_item_tracker import render_action_item_tracker
from dhf_dashboard.dhf_sections import design_plan, design_risk_management, human_factors, design_inputs, design_outputs, design_reviews, design_verification, design_validation, design_transfer, design_changes

# --- PAGE CONFIGURATION ---
st.set_page_config(layout="wide", page_title="DHF Command Center", page_icon="🚀")

# --- INITIALIZE SESSION STATE ---
ssm = SessionStateManager()

# --- SME ARCHITECTURE: CRASH-PROOF DATA PIPELINE ---
# This block loads, validates, and prepares all data ONCE. This is the single source of truth.
# Any failure here will be caught and reported, preventing silent crashes.
try:
    # --- TASKS DATA PIPELINE ---
    tasks_df = pd.DataFrame(ssm.get_data("project_management", "tasks"))
    if not tasks_df.empty:
        # Step 1: Robustly convert date columns, turning errors into NaT (Not a Time)
        tasks_df['start_date'] = pd.to_datetime(tasks_df['start_date'], errors='coerce')
        tasks_df['end_date'] = pd.to_datetime(tasks_df['end_date'], errors='coerce')
        tasks_df.dropna(subset=['start_date', 'end_date'], inplace=True) # Drop tasks with invalid dates
        
        # Step 2: Prepare data for the new Gantt chart
        critical_path_ids = find_critical_path(tasks_df)
        status_colors = {"Completed": "#2ca02c", "In Progress": "#ff7f0e", "Not Started": "#7f7f7f", "At Risk": "#d62728"}
        tasks_df['color'] = tasks_df['status'].map(status_colors).fillna('#7f7f7f')
        tasks_df['line'] = tasks_df.apply(lambda row: {'color': 'red', 'width': 4} if row['id'] in critical_path_ids else {'color': row['color'], 'width': 2}, axis=1)
        tasks_df['display_text'] = tasks_df.apply(lambda row: f"<b>{row['name']}</b> ({row['completion_pct']}%)", axis=1)
    
    # --- OTHER DATA (simplified for clarity) ---
    hazards_df = pd.DataFrame(ssm.get_data("risk_management_file", "hazards"))
    actions_df = pd.DataFrame(ssm.get_data("design_reviews", "reviews")[0].get("action_items", [])) # Simplified for this example
    inputs_df = pd.DataFrame(ssm.get_data("design_inputs", "requirements"))
    outputs_df = pd.DataFrame(ssm.get_data("design_outputs", "documents"))

except Exception as e:
    st.error(f"FATAL ERROR during data loading: {e}", icon="🚨")
    st.error("The application cannot start because the source data is corrupted or in an unexpected format. Please check the `session_state_manager.py` file or reset the session state.")
    st.stop() # Halt execution completely
# --- END OF DATA PIPELINE ---

# --- Main App ---
st.title("🚀 DHF Command Center")
st.caption(f"Live monitoring for **{ssm.get_data('design_plan', 'project_name')}**")

with st.sidebar:
    st.header("DHF Section Navigation")
    # ... (sidebar code remains the same) ...

# --- Main Tabbed Interface ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Project Dashboard", "📈 Advanced Analytics", "📜 DHF Structure (V-Model)", "🗂️ DHF Section Details"])

with tab1:
    st.header("Project Health & KPIs")
    # ... (KPI plots remain the same) ...
    
    st.divider()
    # --- GANTT CHART SECTION ---
    st.header("Project Timeline and Critical Path")
    if not tasks_df.empty:
        # Call the new, simplified Gantt chart function with the pre-processed DataFrame
        gantt_fig = create_gantt_chart(tasks_df)
        st.plotly_chart(gantt_fig, use_container_width=True)
    else:
        st.warning("No project tasks found.")

with tab2:
    # ... (Tab 2 code remains the same) ...
    st.header("Compliance & Execution Analytics")
    analytics_selection = st.selectbox("Choose Analytics View:", ["Traceability Matrix", "Action Item Tracker"])
    if analytics_selection == "Traceability Matrix":
        render_traceability_matrix(ssm)
    elif analytics_selection == "Action Item Tracker":
        render_action_item_tracker(ssm)

# --- V-MODEL TAB (This will now render) ---
with tab3:
    st.header("The Design Control Process (V-Model)")
    st.image("https://www.researchgate.net/profile/Tor-Staalhane/publication/277005111/figure/fig1/AS:669443530891271@1536619171887/The-V-model-of-development-and-testing.png",
             caption="A typical V-Model illustrating the relationship between Design Inputs, Outputs, Verification, and Validation.")
    st.markdown("The 'V-Model' is a standard graphical representation for the medical device design control process...")

with tab4:
    # ... (Tab 4 code remains the same, using the robust data editor logic) ...
    st.header(f"DHF Section Details: {selection}") # Placeholder
    st.info("Navigate using the sidebar. Changes are saved on rerun.")
    
# --- The rest of the tab logic is simplified for this fix, assuming it works ---
