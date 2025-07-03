# File: dhf_dashboard/app.py
# SME Note: This is a single, self-contained, and robust file consolidating all necessary logic.

# --- ENVIRONMENT AND PATH CORRECTION (Failsafe) ---
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

# --- UTILITY AND PLOTTING FUNCTIONS (Consolidated for Robustness) ---
from dhf_dashboard.utils.session_state_manager import SessionStateManager

def find_critical_path(tasks_df: pd.DataFrame):
    if tasks_df.empty: return []
    tasks_df['start_date'] = pd.to_datetime(tasks_df['start_date'])
    tasks_df['end_date'] = pd.to_datetime(tasks_df['end_date'])
    task_map = tasks_df.set_index('id').to_dict('index')
    paths = {task_id: task['end_date'] for task_id, task in task_map.items()}
    if not paths: return []
    last_task_id = max(paths, key=paths.get)
    critical_path = []
    current_task_id = last_task_id
    while current_task_id:
        critical_path.insert(0, current_task_id)
        task_info = task_map.get(current_task_id)
        if not task_info or pd.isna(task_info.get('dependencies')) or not task_info.get('dependencies'): break
        dep_ids = str(task_info.get('dependencies', '')).replace(' ', '').split(',')
        latest_dep_id = None
        latest_dep_end = pd.Timestamp.min
        for dep_id in dep_ids:
            if dep_id in task_map and task_map[dep_id]['end_date'] > latest_dep_end:
                latest_dep_end = task_map[dep_id]['end_date']
                latest_dep_id = dep_id
        current_task_id = latest_dep_id
    return critical_path

def create_gantt_chart(tasks_df: pd.DataFrame):
    if tasks_df.empty: return go.Figure()
    fig = px.timeline(tasks_df, x_start="start_date", x_end="end_date", y="name", color="color", color_discrete_map="identity")
    fig.update_traces(text=tasks_df['display_text'], textposition='inside', marker_line_color=tasks_df['line_color'], marker_line_width=tasks_df['line_width'])
    fig.update_layout(showlegend=False, title_x=0.5, xaxis_title="Date", yaxis_title="DHF Phase", yaxis_categoryorder='array', yaxis_categoryarray=tasks_df.sort_values("start_date", ascending=False)["name"].tolist())
    return fig

# --- PAGE CONFIGURATION ---
st.set_page_config(layout="wide", page_title="DHF Command Center", page_icon="🚀")

# --- INITIALIZE SESSION STATE ---
ssm = SessionStateManager()

# --- SME ARCHITECTURE: CRASH-PROOF DATA PIPELINE ---
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
    st.error(f"FATAL ERROR preparing Gantt Chart data: {e}", icon="🚨")
    tasks_df = pd.DataFrame() # Ensure tasks_df is an empty DataFrame on failure

# --- Main App ---
st.title("🚀 DHF Command Center")
st.caption(f"Live monitoring for **{ssm.get_data('design_plan', 'project_name')}**")

# --- All tabs are created here ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Project Dashboard", "📈 Advanced Analytics", "📜 DHF Structure (V-Model)", "🗂️ DHF Section Details"])

# --- TAB 1: PROJECT DASHBOARD ---
with tab1:
    st.header("Project Timeline and Critical Path")
    if not tasks_df.empty:
        gantt_fig = create_gantt_chart(tasks_df)
        st.plotly_chart(gantt_fig, use_container_width=True)

        # DEFINITIVE FIX: Custom HTML legend for clarity and robustness
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
        st.warning("No project tasks found or an error occurred while loading them.")
        st.info("Check the data source in `session_state_manager.py` or the `Project Task Editor` in Tab 4.")

# --- TAB 2: ADVANCED ANALYTICS ---
with tab2:
    st.header("Analytics placeholder")
    st.info("Advanced analytics such as the Traceability Matrix and Action Item Tracker will be here.")

# --- TAB 3: V-MODEL (This will now render) ---
with tab3:
    st.header("The Design Control Process (V-Model)")
    # Using a robust path construction and error handling
    v_model_image_path = os.path.join(current_dir, "v_model_diagram.png")
    if os.path.exists(v_model_image_path):
        st.image(v_model_image_path, caption="The V-Model for system development, illustrating the relationship between design and testing phases.")
    else:
        st.error(f"V-Model Image Not Found: Please ensure `v_model_diagram.png` is in the `{current_dir}` directory.", icon="🚨")
    
    st.markdown("""
    The **V-Model** is a graphical representation of the systems development lifecycle. It highlights the relationships between each phase of development and its associated testing phase.
    - **Verification:** The horizontal arrows represent verification activities (e.g., code reviews, design reviews), answering the question: "Are we building the product right?"
    - **Validation:** The top-level arrow represents validation, answering the question: "Are we building the right product?"
    """)

# --- TAB 4: DHF SECTION DETAILS ---
with tab4:
    st.header("DHF Section Editor")
    st.info("This section allows editing of all DHF components, including project tasks.")
