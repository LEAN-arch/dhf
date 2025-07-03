# File: dhf_dashboard/app.py
# SME Note: This is the definitive, fully functional version consolidating all fixes.

# --- ENVIRONMENT AND PATH CORRECTION ---
import sys
import os
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta

# This block ensures the app can be run from anywhere
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# --- IMPORTS FROM THE PROJECT PACKAGE ---
from dhf_dashboard.utils.session_state_manager import SessionStateManager
from dhf_dashboard.utils.plot_utils import create_gantt_chart, create_progress_donut, create_risk_profile_chart, create_action_item_chart
from dhf_dashboard.utils.critical_path_utils import find_critical_path
from dhf_dashboard.analytics.traceability_matrix import render_traceability_matrix
from dhf_dashboard.analytics.action_item_tracker import render_action_item_tracker

# Import all section rendering modules
from dhf_dashboard.dhf_sections import design_plan, design_risk_management, human_factors, design_inputs, design_outputs, design_reviews, design_verification, design_validation, design_transfer, design_changes

# --- PAGE CONFIGURATION ---
st.set_page_config(layout="wide", page_title="DHF Command Center", page_icon="🚀")

# --- INITIALIZE SESSION STATE ---
ssm = SessionStateManager()

# --- SME ARCHITECTURE: CRASH-PROOF DATA PIPELINE ---
try:
    # --- TASKS DATA ---
    tasks_df = pd.DataFrame(ssm.get_data("project_management", "tasks"))
    if not tasks_df.empty:
        tasks_df['start_date'] = pd.to_datetime(tasks_df['start_date'], errors='coerce')
        tasks_df['end_date'] = pd.to_datetime(tasks_df['end_date'], errors='coerce')
        tasks_df.dropna(subset=['start_date', 'end_date'], inplace=True)
        
        critical_path_ids = find_critical_path(tasks_df.copy())
        status_colors = {"Completed": "#2ca02c", "In Progress": "#ff7f0e", "Not Started": "#7f7f7f", "At Risk": "#d62728"}
        tasks_df['color'] = tasks_df['status'].map(status_colors).fillna('#7f7f7f')
        tasks_df['is_critical'] = tasks_df['id'].isin(critical_path_ids)
        tasks_df['line_color'] = tasks_df.apply(lambda row: 'red' if row['is_critical'] else row['color'], axis=1)
        tasks_df['line_width'] = tasks_df.apply(lambda row: 4 if row['is_critical'] else 1, axis=1)
        tasks_df['display_text'] = tasks_df.apply(lambda row: f"<b>{row['name']}</b> ({row.get('completion_pct', 0)}%)", axis=1)
    
    # --- OTHER DATA ---
    all_actions = []
    reviews_data = ssm.get_data("design_reviews", "reviews")
    if reviews_data:
        for review in reviews_data:
            all_actions.extend(review.get("action_items", []))
    actions_df = pd.DataFrame(all_actions)

except Exception as e:
    st.error(f"A FATAL ERROR occurred during data preparation: {e}", icon="🚨")
    st.info("The dashboard cannot be displayed. Please check the mock data source.")
    st.stop()
# --- END OF DATA PIPELINE ---

# --- MAIN APP UI ---
st.title("🚀 DHF Command Center")
st.caption(f"Live monitoring for **{ssm.get_data('design_plan', 'project_name')}**")

with st.sidebar:
    st.header("DHF Section Navigation")
    page_options = ["1. Design Plan", "2. Risk Management File", "3. Human Factors", "4. Design Inputs", "5. Design Outputs", "6. Design Reviews & Gates", "7. Design Verification", "8. Design Validation", "9. Design Transfer", "10. Design Changes", "11. Project Task Editor"]
    selection = st.radio("Go to Section:", page_options, key="sidebar_selection")
    st.info("Select a section to view or edit its contents in the 'DHF Section Details' tab.")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Project Dashboard", "📈 Advanced Analytics", "📜 DHF Structure (V-Model)", "🗂️ DHF Section Details"])

with tab1:
    st.header("Project Health & KPIs")
    col1, col2 = st.columns(2)
    with col1:
        completion_pct = tasks_df['completion_pct'].mean() if not tasks_df.empty and 'completion_pct' in tasks_df.columns else 0
        st.plotly_chart(create_progress_donut(completion_pct), use_container_width=True)
    with col2:
        st.plotly_chart(create_risk_profile_chart(pd.DataFrame(ssm.get_data("risk_management_file", "hazards"))), use_container_width=True)

    st.divider()
    st.header("Project Timeline and Critical Path")
    if not tasks_df.empty:
        gantt_fig = create_gantt_chart(tasks_df)
        st.plotly_chart(gantt_fig, use_container_width=True)
        # Custom HTML legend
        legend_html = """
        <div style="padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin-top: 15px;">
        <b>Legend:</b>
        <ul style="list-style-type: none; padding-left: 0;">
            <li style="margin-bottom: 5px;"><span style="display:inline-block; width:15px; height:15px; background-color:#2ca02c; margin-right: 5px; vertical-align: middle;"></span> Completed</li>
            <li style="margin-bottom: 5px;"><span style="display:inline-block; width:15px; height:15px; background-color:#ff7f0e; margin-right: 5px; vertical-align: middle;"></span> In Progress</li>
            <li style="margin-bottom: 5px;"><span style="display:inline-block; width:15px; height:15px; background-color:#d62728; margin-right: 5px; vertical-align: middle;"></span> At Risk</li>
            <li style="margin-bottom: 5px;"><span style="display:inline-block; width:15px; height:15px; background-color:#7f7f7f; margin-right: 5px; vertical-align: middle;"></span> Not Started</li>
            <li style="margin-bottom: 5px;"><span style="display:inline-block; width:13px; height:13px; border: 2px solid red; margin-right: 5px; vertical-align: middle;"></span> Task on Critical Path</li>
        </ul>
        </div>
        """
        st.markdown(legend_html, unsafe_allow_html=True)
    else:
        st.warning("No project tasks found.")

with tab2:
    st.header("Compliance & Execution Analytics")
    render_traceability_matrix(ssm)

with tab3:
    st.header("The Design Control Process (V-Model)")
    v_model_image_path = os.path.join(current_dir, "v_model_diagram.png")
    if os.path.exists(v_model_image_path):
        st.image(v_model_image_path, caption="The V-Model for system development.")
    else:
        st.error(f"Image Not Found: Ensure `v_model_diagram.png` is in the `{current_dir}` directory.", icon="🚨")
    st.markdown("The **V-Model** illustrates the lifecycle of a development project...")

# --- DEFINITIVE FIX: Restored Page Navigation Logic ---
with tab4:
    st.header(f"DHF Section Details: {selection}")
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
        
        # Hide internal helper columns from the user editor
        columns_to_hide = ['color', 'is_critical', 'line_color', 'line_width', 'display_text']
        columns_to_show = [col for col in tasks_df.columns if col not in columns_to_hide]
        
        # Present the clean dataframe to the user
        edited_df = st.data_editor(
            tasks_df[columns_to_show], 
            key="main_task_editor", 
            num_rows="dynamic", 
            use_container_width=True,
            column_config={
                "start_date": st.column_config.DateColumn("Start Date", format="YYYY-MM-DD"),
                "end_date": st.column_config.DateColumn("End Date", format="YYYY-MM-DD")
            }
        )
        
        # Compare the edited data back to the original subset of columns
        if not edited_df.equals(tasks_df[columns_to_show]):
            ssm.update_data(edited_df.to_dict('records'), "project_management", "tasks")
            st.success("Project tasks updated! Rerunning...")
            st.rerun()
    else:
        # Call the render function from the selected module
        page_module = PAGES[selection]
        page_module.render(ssm)
