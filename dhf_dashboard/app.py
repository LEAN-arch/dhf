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
try:
    # --- TASKS DATA PIPELINE ---
    tasks_df = pd.DataFrame(ssm.get_data("project_management", "tasks"))
    if not tasks_df.empty:
        tasks_df['start_date'] = pd.to_datetime(tasks_df['start_date'], errors='coerce')
        tasks_df['end_date'] = pd.to_datetime(tasks_df['end_date'], errors='coerce')
        tasks_df.dropna(subset=['start_date', 'end_date'], inplace=True)
        
        # --- FIX IS HERE: Prepare separate columns for line color and width ---
        critical_path_ids = find_critical_path(tasks_df)
        status_colors = {"Completed": "#2ca02c", "In Progress": "#ff7f0e", "Not Started": "#7f7f7f", "At Risk": "#d62728"}
        tasks_df['color'] = tasks_df['status'].map(status_colors).fillna('#7f7f7f')
        
        # Create a boolean column for is_critical
        tasks_df['is_critical'] = tasks_df['id'].isin(critical_path_ids)
        
        # Use the boolean column to set color and width
        tasks_df['line_color'] = tasks_df.apply(lambda row: 'red' if row['is_critical'] else row['color'], axis=1)
        tasks_df['line_width'] = tasks_df.apply(lambda row: 4 if row['is_critical'] else 2, axis=1)
        
        tasks_df['display_text'] = tasks_df.apply(lambda row: f"<b>{row['name']}</b> ({row['completion_pct']}%)", axis=1)
        # --- END OF FIX ---
    
    # --- OTHER DATA ---
    hazards_df = pd.DataFrame(ssm.get_data("risk_management_file", "hazards"))
    all_actions = []
    reviews_data = ssm.get_data("design_reviews", "reviews")
    if reviews_data:
        for review in reviews_data:
            all_actions.extend(review.get("action_items", []))
    actions_df = pd.DataFrame(all_actions)
    inputs_df = pd.DataFrame(ssm.get_data("design_inputs", "requirements"))
    outputs_df = pd.DataFrame(ssm.get_data("design_outputs", "documents"))

except Exception as e:
    st.error(f"FATAL ERROR during data loading: {e}", icon="🚨")
    st.stop()
# --- END OF DATA PIPELINE ---

# --- Main App ---
st.title("🚀 DHF Command Center")
st.caption(f"Live monitoring for **{ssm.get_data('design_plan', 'project_name')}**")

with st.sidebar:
    st.header("DHF Section Navigation")
    page_options = ["1. Design Plan", "2. Risk Management File", "3. Human Factors", "4. Design Inputs", "5. Design Outputs", "6. Design Reviews & Gates", "7. Design Verification", "8. Design Validation", "9. Design Transfer", "10. Design Changes", "11. Project Task Editor"]
    selection = st.radio("Go to Section:", page_options, key="sidebar_selection")
    st.info("Navigate and edit DHF sections. Content is shown in the 'DHF Section Details' tab.")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Project Dashboard", "📈 Advanced Analytics", "📜 DHF Structure (V-Model)", "🗂️ DHF Section Details"])

with tab1:
    st.header("Project Health & KPIs")
    
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(create_progress_donut(tasks_df['completion_pct'].mean() if not tasks_df.empty else 0), use_container_width=True)
    with col2:
        st.plotly_chart(create_risk_profile_chart(hazards_df), use_container_width=True)

    st.divider()

    col3, col4 = st.columns(2)
    with col3:
        st.plotly_chart(create_action_item_chart(actions_df), use_container_width=True)
    with col4:
        st.subheader("Compliance Scorecard")
        # ... (compliance scorecard logic remains the same) ...

    st.divider()
    st.header("Project Timeline and Critical Path")
    if not tasks_df.empty:
        gantt_fig = create_gantt_chart(tasks_df)
        st.plotly_chart(gantt_fig, use_container_width=True)
        st.info("The **Critical Path** (tasks with a red border) represents the longest sequence of dependent tasks. Any delay in these tasks will delay the entire project.")
    else:
        st.warning("No project tasks found.")

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
    st.markdown("The 'V-Model' is a standard graphical representation for the medical device design control process...")

with tab4:
    st.header(f"DHF Section Details: {selection}")
    st.info("Navigate using the sidebar. Changes are saved on rerun.")
    PAGES = {"1. Design Plan": design_plan, "2. Risk Management File": design_risk_management, "3. Human Factors": human_factors, "4. Design Inputs": design_inputs, "5. Design Outputs": design_outputs, "6. Design Reviews & Gates": design_reviews, "7. Design Verification": design_verification, "8. Design Validation": design_validation, "9. Design Transfer": design_transfer, "10. Design Changes": design_changes}
    if selection == "11. Project Task Editor":
        st.subheader("Project Timeline and Task Editor")
        st.warning("Directly edit project timelines, statuses, and dependencies.")
        edited_df = st.data_editor(tasks_df, key="main_task_editor", num_rows="dynamic", use_container_width=True, column_config={"start_date": st.column_config.DateColumn("Start Date", format="YYYY-MM-DD"), "end_date": st.column_config.DateColumn("End Date", format="YYYY-MM-DD")})
        if not edited_df.equals(tasks_df):
            ssm.update_data(edited_df.to_dict('records'), "project_management", "tasks")
            st.success("Project tasks updated! Rerunning...")
            st.rerun()
    else:
        page_module = PAGES[selection]
        page_module.render(ssm)
