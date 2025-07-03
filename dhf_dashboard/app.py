# File: dhf_dashboard/app.py
# SME Note: This is the definitive, all-inclusive version. It includes a robust
# path correction block, a refined UI using tabs, and a new, comprehensive
# "Design Controls Guide" tab to provide essential regulatory context.

import sys
import os
import pandas as pd
import streamlit as st

# --- ROBUST PATH CORRECTION BLOCK ---
# This is the definitive fix for the ModuleNotFoundError.
# It finds the project's root directory (the one containing 'dhf_dashboard')
# and adds it to Python's search path.
try:
    current_file_path = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file_path)
    project_root = os.path.dirname(current_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
except Exception as e:
    st.error(f"Error adjusting system path: {e}")
# --- END OF PATH CORRECTION BLOCK ---


# --- MODULAR IMPORTS FROM THE PROJECT PACKAGE ---
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
ssm = SessionStateManager()

# --- DATA PREPARATION PIPELINE ---
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


# --- UI LAYOUT ---
st.title("🚀 DHF Command Center")
project_name = ssm.get_data("design_plan", "project_name")
st.caption(f"Live monitoring for the **{project_name}** project.")

# UX SME Rationale: A tabbed interface provides a clean, high-level separation of concerns.
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 **Dashboard**",
    "🗂️ **DHF Explorer**",
    "🔬 **Advanced Analytics**",
    "🏛️ **Design Controls Guide**"
])


# ==============================================================================
# TAB 1: PROJECT DASHBOARD
# ==============================================================================
with tab1:
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


# ==============================================================================
# TAB 2: DHF EXPLORER
# ==============================================================================
with tab2:
    st.header("Design History File Explorer")
    st.markdown("Select a DHF section from the sidebar to view or edit its contents.")

    # --- Sidebar for DHF Section Navigation ---
    with st.sidebar:
        st.header("DHF Section Navigation")
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
            "Select a section to edit:",
            PAGES.keys(),
            key="sidebar_dhf_selection",
        )

    # --- Render the selected DHF section editor ---
    st.divider()
    page_function = PAGES[dhf_selection]
    page_function(ssm)


# ==============================================================================
# TAB 3: ADVANCED ANALYTICS
# ==============================================================================
with tab3:
    st.header("Advanced Compliance & Project Analytics")
    analytics_tabs = st.tabs(["Traceability Matrix", "Action Item Tracker", "Project Task Editor"])

    with analytics_tabs[0]:
        render_traceability_matrix(ssm)
    with analytics_tabs[1]:
        render_action_item_tracker(ssm)
    with analytics_tabs[2]:
        st.subheader("Project Timeline and Task Editor")
        st.warning("Directly edit project timelines, statuses, and dependencies. Changes are saved automatically.", icon="⚠️")
        columns_to_hide = ['color', 'is_critical', 'line_color', 'line_width', 'display_text']
        editable_cols = [col for col in tasks_df.columns if col not in columns_to_hide]
        edited_df = st.data_editor(
            tasks_df[editable_cols], key="main_task_editor", num_rows="dynamic", use_container_width=True,
            column_config={"start_date": st.column_config.DateColumn("Start Date", format="YYYY-MM-DD"), "end_date": st.column_config.DateColumn("End Date", format="YYYY-MM-DD")}
        )
        original_subset = tasks_df[editable_cols].reset_index(drop=True)
        if not edited_df.reset_index(drop=True).equals(original_subset):
            ssm.update_data(edited_df.to_dict('records'), "project_management", "tasks")
            st.toast("Project tasks updated! Rerunning...")
            st.rerun()

# ==============================================================================
# TAB 4: DESIGN CONTROLS GUIDE (NEW CONTENT)
# ==============================================================================
with tab4:
    st.header("A Guide to Design Controls & the V-Model")
    st.markdown("This section provides a high-level overview of the Design Controls methodology, a cornerstone of medical device development required by the FDA.")

    st.subheader("The Design Controls Process (21 CFR 820.30)")
    st.markdown("""
    Design Controls are a systematic process to ensure that a medical device is safe and effective for its intended use. It's not just about paperwork; it's a framework for quality-driven product development. The entire process is designed to create a **Design History File (DHF)**, which is the collection of documents that proves you followed the process. This application is a tool to build and manage that DHF.
    """)

    with st.expander("Expand to see how DHF sections map to FDA regulations"):
        st.markdown("""
        | DHF Section in this App      | Regulation (21 CFR 820.30) | Purpose                                                                 |
        |------------------------------|----------------------------|-------------------------------------------------------------------------|
        | **1. Design Plan**           | `(b) Design/Dev. Planning` | Outlines project scope, activities, team, and responsibilities.         |
        | **2. Risk Management**       | `(g) Design Validation`    | Identifies, evaluates, and controls risks (as per ISO 14971).           |
        | **3. Human Factors**         | `(c) Design Input`         | Ensures user needs and safe use are considered in the design.           |
        | **4. Design Inputs**         | `(c) Design Input`         | Defines all requirements (user, technical, regulatory).                 |
        | **5. Design Outputs**        | `(d) Design Output`        | The tangible results of design (drawings, specs) that meet inputs.      |
        | **6. Design Reviews**        | `(e) Design Review`        | Formal checkpoints to review the design's progress and adequacy.        |
        | **7. Design Verification**   | `(f) Design Verification`  | Confirms that design outputs meet the design inputs. *Built it right?*  |
        | **8. Design Validation**     | `(g) Design Validation`    | Confirms the device meets user needs. *Built the right thing?*          |
        | **9. Design Transfer**       | `(h) Design Transfer`      | Transfers the design to manufacturing for production.                   |
        | **10. Design Changes**       | `(i) Design Changes`       | Formally controls any changes made after the design is approved.        |
        """)

    st.subheader("Visualizing the Process: The V-Model")
    st.markdown("The V-Model is a powerful way to visualize the Design Controls process, emphasizing the critical link between design (left side) and testing (right side).")

    v_model_image_path = os.path.join(current_dir, "v_model_diagram.png")
    if os.path.exists(v_model_image_path):
        st.image(v_model_image_path, caption="The V-Model illustrates the relationship between design decomposition and integration/testing.", use_container_width=True)
    else:
        st.error(f"Image Not Found: Ensure `v_model_diagram.png` is in the `{current_dir}` directory.", icon="🚨")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Left Side: Decomposition & Design")
        st.markdown("""
        Moving down the left side of the 'V' involves breaking down the high-level concept into detailed, buildable specifications.
        - **User Needs & Intended Use:** What problem does the user need to solve?
        - **Design Inputs (Requirements):** How must the device perform to meet those needs? This includes technical, functional, and safety requirements.
        - **System & Architectural Design:** How will the components be structured to meet the requirements?
        - **Detailed Design (Outputs):** At the lowest level, these are the final drawings, code, and specifications that are used to build the device.
        """)
    with col2:
        st.subheader("Right Side: Integration & Testing")
        st.markdown("""
        Moving up the right side of the 'V' involves building the device from its components and testing at each level to ensure it matches the corresponding design phase on the left.
        - **Unit/Component Verification:** Does each individual part meet its detailed design specification?
        - **Integration & System Verification:** Do the assembled parts work together as defined in the architectural design?
        - **Design Validation:** Does the final, complete device meet the high-level User Needs? This is the ultimate test.
        """)

    st.success("""
    #### The Core Principle: Verification vs. Validation
    - **Verification (Horizontal Arrows):** Answers the question, **"Are we building the product right?"** It is the process of confirming that a design output meets its specified input requirements (e.g., does the code correctly implement the detailed design?).
    - **Validation (Top-Level Arrow):** Answers the question, **"Are we building the right product?"** It is the process of confirming that the final, finished product meets the user's actual needs and its intended use.
    """)
