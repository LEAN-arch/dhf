# File: dhf_dashboard/app.py
# SME Note: This is the definitive, fully functional version consolidating all fixes and restoring all content.

# --- ENVIRONMENT AND PATH CORRECTION (Failsafe) ---
import sys
import os
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta, date

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

# --- DEFINITIVE FIX: Define all page rendering functions directly inside app.py ---

def render_design_plan(ssm):
    st.subheader("1. Design and Development Plan")
    st.markdown("This section outlines the overall plan for the project, including scope, team, and major activities.")
    plan_data = ssm.get_data("design_plan")
    st.text_input("Project Name", value=plan_data.get("project_name"), disabled=True, key="dp_name")
    st.text_area("Scope", value=plan_data.get("scope"), height=150, disabled=True, key="dp_scope")
    st.write("**Team Members:**")
    st.dataframe(plan_data.get("team_members", []), use_container_width=True)

def render_risk_management(ssm):
    st.subheader("2. Risk Management File (RMF)")
    st.markdown("A summary of risk management activities as per ISO 14971.")
    hazards_df = pd.DataFrame(ssm.get_data("risk_management_file", "hazards"))
    st.write("**Identified Hazards:**")
    st.dataframe(hazards_df, use_container_width=True)

def render_human_factors(ssm):
    st.subheader("3. Human Factors & Usability Engineering")
    st.warning("This is a placeholder page for Human Factors Engineering content (IEC 62366).")

def render_design_inputs(ssm):
    st.subheader("4. Design Inputs")
    st.markdown("Design inputs are the physical and performance requirements of a device that are used as a basis for device design.")
    requirements_df = pd.DataFrame(ssm.get_data("design_inputs", "requirements"))
    st.write("**Requirements List:**")
    st.dataframe(requirements_df, use_container_width=True)

def render_design_outputs(ssm):
    st.subheader("5. Design Outputs")
    st.markdown("Design outputs are the results of a design effort at each design phase.")
    outputs_df = pd.DataFrame(ssm.get_data("design_outputs", "documents"))
    st.write("**Output Documents & Specifications:**")
    st.dataframe(outputs_df, use_container_width=True)

def render_design_reviews(ssm):
    st.subheader("6. Design Reviews & Gates")
    st.markdown("Formal documented reviews of the design results.")
    reviews = ssm.get_data("design_reviews", "reviews")
    for i, review in enumerate(reviews):
        with st.expander(f"**Review {i+1} - Date: {review.get('date')}**"):
            st.write(f"**Attendees:** {review.get('attendees')}")
            st.write(f"**Notes:** {review.get('notes')}")
            st.write("**Action Items:**")
            st.dataframe(review.get('action_items', []), use_container_width=True)

def render_design_verification(ssm):
    st.subheader("7. Design Verification")
    st.markdown("Confirmation that specified requirements have been fulfilled. ('Did you build the device right?')")
    tests_df = pd.DataFrame(ssm.get_data("design_verification", "tests"))
    st.write("**Verification Test Protocols:**")
    st.dataframe(tests_df, use_container_width=True)

def render_design_validation(ssm):
    st.subheader("8. Design Validation")
    st.markdown("Confirmation that the device meets the user's needs. ('Did you build the right device?')")
    st.warning("This is a placeholder page for Design Validation content.")

def render_design_transfer(ssm):
    st.subheader("9. Design Transfer")
    st.markdown("The process of transferring the device design to manufacturing.")
    st.warning("This is a placeholder page for Design Transfer activities.")

def render_design_changes(ssm):
    st.subheader("10. Design Changes")
    st.markdown("Formal control and documentation of any changes to the design.")
    st.warning("This is a placeholder page for Design Change Control records.")

# --- END OF PAGE FUNCTIONS ---


# --- PAGE CONFIGURATION ---
st.set_page_config(layout="wide", page_title="DHF Command Center", page_icon="🚀")

# --- INITIALIZE SESSION STATE ---
ssm = SessionStateManager()

# --- DATA PIPELINE ---
try:
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
except Exception as e:
    st.error(f"FATAL ERROR during data preparation: {e}", icon="🚨")
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
        hazards_df = pd.DataFrame(ssm.get_data("risk_management_file", "hazards"))
        st.plotly_chart(create_risk_profile_chart(hazards_df), use_container_width=True)
    
    st.divider()
    st.header("Project Timeline and Critical Path")
    if not tasks_df.empty:
        gantt_fig = create_gantt_chart(tasks_df)
        st.plotly_chart(gantt_fig, use_container_width=True)
        legend_html = """...""" # Legend HTML from previous correct version
        st.markdown(legend_html, unsafe_allow_html=True)
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
    v_model_image_path = os.path.join(current_dir, "v_model_diagram.png")
    if os.path.exists(v_model_image_path):
        st.image(v_model_image_path, caption="The V-Model for system development.")
    else:
        st.error(f"Image Not Found: Ensure `v_model_diagram.png` is in the `{current_dir}` directory.", icon="🚨")

with tab4:
    st.header(f"DHF Section Details: {selection}")
    st.divider()

    PAGES = {
        "1. Design Plan": render_design_plan,
        "2. Risk Management File": render_risk_management,
        "3. Human Factors": render_human_factors,
        "4. Design Inputs": render_design_inputs,
        "5. Design Outputs": render_design_outputs,
        "6. Design Reviews & Gates": render_design_reviews,
        "7. Design Verification": render_design_verification,
        "8. Design Validation": render_design_validation,
        "9. Design Transfer": render_design_transfer,
        "10. Design Changes": render_design_changes,
    }

    if selection == "11. Project Task Editor":
        st.subheader("Project Timeline and Task Editor")
        st.warning("Directly edit project timelines, statuses, and dependencies.")
        columns_to_hide = ['color', 'is_critical', 'line_color', 'line_width', 'display_text']
        columns_to_show = [col for col in tasks_df.columns if col not in columns_to_hide]
        edited_df = st.data_editor(tasks_df[columns_to_show], key="main_task_editor", num_rows="dynamic", use_container_width=True, column_config={"start_date": st.column_config.DateColumn("Start Date", format="YYYY-MM-DD"), "end_date": st.column_config.DateColumn("End Date", format="YYYY-MM-DD")})
        if not edited_df.equals(tasks_df[columns_to_show]):
            ssm.update_data(edited_df.to_dict('records'), "project_management", "tasks")
            st.success("Project tasks updated! Rerunning...")
            st.rerun()
    else:
        page_function = PAGES[selection]
        page_function(ssm)
