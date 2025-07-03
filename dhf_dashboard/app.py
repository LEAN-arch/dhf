# File: app.py (This file should be in your project root, NOT inside dhf_dashboard)

import pandas as pd
import streamlit as st

# --- MODULAR IMPORTS FROM THE PROJECT PACKAGE ---
# SME Rationale: With app.py outside the package, we now use absolute imports
# from the 'dhf_dashboard' package. This is the standard, correct way.
from dhf_dashboard.utils.session_state_manager import SessionStateManager
from dhf_dashboard.utils.critical_path_utils import find_critical_path
from dhf_dashboard.utils.plot_utils import (
    create_progress_donut, create_risk_profile_chart,
    create_gantt_chart, create_action_item_chart
)
from dhf_dashboard.analytics.traceability_matrix import render_traceability_matrix
from dhf_dashboard.analytics.action_item_tracker import render_action_item_tracker

# Import all DHF section rendering functions
from dhf_dashboard.dhf_sections import (
    design_plan, design_risk_management, human_factors, design_inputs,
    design_outputs, design_reviews, design_verification, design_validation,
    design_transfer, design_changes
)

# --- PAGE CONFIGURATION ---
st.set_page_config(layout="wide", page_title="DHF Command Center", page_icon="🚀")

# --- INITIALIZE SESSION STATE ---
# The SessionStateManager class itself does not need any changes.
ssm = SessionStateManager()

# --- DATA PREPARATION PIPELINE (CRASH-PROOF) ---
try:
    tasks_df = pd.DataFrame(ssm.get_data("project_management", "tasks"))
    if not tasks_df.empty:
        tasks_df['start_date'] = pd.to_datetime(tasks_df['start_date'], errors='coerce')
        tasks_df['end_date'] = pd.to_datetime(tasks_df['end_date'], errors='coerce')
        tasks_df.dropna(subset=['start_date', 'end_date'], inplace=True)

        critical_path_ids = find_critical_path(tasks_df.copy())
        status_colors = {"Completed": "#2ca02c", "In Progress": "#1f77b4", "Not Started": "#7f7f7f", "At Risk": "#d62728"}
        tasks_df['color'] = tasks_df['status'].map(status_colors).fillna('#7f7f7f')
        tasks_df['is_critical'] = tasks_df['id'].isin(critical_path_ids)
        tasks_df['line_color'] = tasks_df.apply(lambda r: 'red' if r['is_critical'] else '#FFFFFF', axis=1)
        tasks_df['line_width'] = tasks_df.apply(lambda r: 4 if r['is_critical'] else 0, axis=1)
        tasks_df['display_text'] = tasks_df.apply(lambda r: f"<b>{r['name']}</b> ({r.get('completion_pct', 0)}%)", axis=1)
    else:
        st.error("FATAL ERROR: Project tasks could not be loaded.", icon="🚨")
        st.stop()
except Exception as e:
    st.error(f"FATAL ERROR during data preparation: {e}", icon="🚨")
    st.stop()

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("🚀 DHF Command Center")
    project_name = ssm.get_data("design_plan", "project_name")
    st.markdown(f"**Project:**\n*{project_name}*")
    st.divider()

    st.header("Views")
    main_selection = st.radio(
        "Select a View:",
        ["📊 Dashboard", "🗂️ DHF Explorer", "🔬 Advanced Analytics"],
        key="main_view_selection",
        label_visibility="collapsed"
    )
    st.divider()

    if main_selection == "🗂️ DHF Explorer":
        st.header("DHF Sections")
        PAGES = {
            "1. Design Plan": design_plan.render_design_plan,
            "2. Risk Management": design_risk_management.render_design_risk_management,
            "3. Human Factors": human_factors.render_human_factors,
            "4. Design Inputs": design_inputs.render_design_inputs,
            "5. Design Outputs": design_outputs.render_design_outputs,
            "6. Design Reviews": design_reviews.render_design_reviews,
            "7. Design Verification": design_verification.render_design_verification,
            "8. Design Validation": design_validation.render_design_validation,
            "9. Design Transfer": design_transfer.render_design_transfer,
            "10. Design Changes": design_changes.render_design_changes,
        }
        dhf_selection = st.radio(
            "Go to Section:",
            PAGES.keys(),
            key="sidebar_dhf_selection",
            label_visibility="collapsed"
        )

# --- MAIN PANEL RENDERING ---

if main_selection == "📊 Dashboard":
    st.header("Project Health & KPIs")
    col1, col2, col3 = st.columns(3)
    with col1:
        completion_pct = tasks_df['completion_pct'].mean() if not tasks_df.empty else 0
        st.plotly_chart(create_progress_donut(completion_pct), use_container_width=True)
    with col2:
        hazards_df = pd.DataFrame(ssm.get_data("risk_management_file", "hazards"))
        st.plotly_chart(create_risk_profile_chart(hazards_df), use_container_width=True)
    with col3:
        reviews = ssm.get_data("design_reviews", "reviews")
        actions = [item for r in reviews for item in r.get("action_items", [])]
        actions_df = pd.DataFrame(actions)
        st.plotly_chart(create_action_item_chart(actions_df), use_container_width=True)

    st.divider()
    st.header("Project Timeline")
    gantt_fig = create_gantt_chart(tasks_df)
    st.plotly_chart(gantt_fig, use_container_width=True)
    legend_html = """
    <div style="padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin-top: 15px; font-size: 0.9em;">
    <b>Legend:</b>
    <ul style="list-style-type: none; padding-left: 0; margin-top: 5px; column-count: 2;">
        <li style="margin-bottom: 5px;"><span style="display:inline-block; width:15px; height:15px; background-color:#2ca02c; margin-right: 8px; vertical-align: middle;"></span> Completed</li>
        <li style="margin-bottom: 5px;"><span style="display:inline-block; width:15px; height:15px; background-color:#1f77b4; margin-right: 8px; vertical-align: middle;"></span> In Progress</li>
        <li style="margin-bottom: 5px;"><span style="display:inline-block; width:15px; height:15px; background-color:#d62728; margin-right: 8px; vertical-align: middle;"></span> At Risk</li>
        <li style="margin-bottom: 5px;"><span style="display:inline-block; width:15px; height:15px; background-color:#7f7f7f; margin-right: 8px; vertical-align: middle;"></span> Not Started</li>
        <li style="margin-bottom: 5px;"><span style="display:inline-block; width:11px; height:11px; border: 2px solid red; margin-right: 8px; vertical-align: middle;"></span> Task on Critical Path</li>
    </ul></div>
    """
    st.markdown(legend_html, unsafe_allow_html=True)

elif main_selection == "🗂️ DHF Explorer":
    page_function = PAGES[dhf_selection]
    page_function(ssm)

elif main_selection == "🔬 Advanced Analytics":
    st.title("🔬 Advanced Analytics")
    analytics_tabs = st.tabs(["Traceability Matrix", "Action Item Tracker", "Project Task Editor"])

    with analytics_tabs[0]:
        render_traceability_matrix(ssm)
    with analytics_tabs[1]:
        render_action_item_tracker(ssm)
    with analytics_tabs[2]:
        st.header("Project Timeline and Task Editor")
        st.warning("Directly edit project timelines, statuses, and dependencies. Changes are saved automatically and will reflect on the main dashboard.", icon="⚠️")
        columns_to_hide = ['color', 'is_critical', 'line_color', 'line_width', 'display_text']
        editable_cols = [col for col in tasks_df.columns if col not in columns_to_hide]
        edited_df = st.data_editor(
            tasks_df[editable_cols],
            key="main_task_editor",
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "start_date": st.column_config.DateColumn("Start Date", format="YYYY-MM-DD"),
                "end_date": st.column_config.DateColumn("End Date", format="YYYY-MM-DD")
            }
        )
        original_subset = tasks_df[editable_cols].reset_index(drop=True)
        if not edited_df.reset_index(drop=True).equals(original_subset):
            ssm.update_data(edited_df.to_dict('records'), "project_management", "tasks")
            st.toast("Project tasks updated! Rerunning...")
            st.rerun()
