# File: dhf_dashboard/app.py

import streamlit as st
import pandas as pd

# Import utilities, analytics modules, and section renderers
from utils.session_state_manager import SessionStateManager
from utils.plot_utils import create_gantt_chart, create_status_pie_chart
from utils.critical_path_utils import find_critical_path
from analytics.traceability_matrix import render_traceability_matrix # NEW
from analytics.action_item_tracker import render_action_item_tracker # NEW

from dhf_sections import (
    design_plan, design_risk_management, human_factors, design_inputs, design_outputs,
    design_reviews, design_verification, design_validation, design_transfer, design_changes
)

st.set_page_config(layout="wide", page_title="DHF Command Center", page_icon="🚀")
ssm = SessionStateManager()

st.title("🚀 DHF Command Center: Smart-Pill Combination Product")
project_name = ssm.get_data("design_plan", "project_name")
st.caption(f"Live monitoring, analytics, and compliance for **{project_name}**")

# --- Tabbed Interface with a new Analytics Tab ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Project Dashboard", 
    "📈 Advanced Analytics", # NEW
    "📜 DHF Structure (V-Model)", 
    "🗂️ DHF Section Details"
])

# ============================ TAB 1: PROJECT DASHBOARD ============================
with tab1:
    st.header("Project Health & KPIs")
    
    # --- Enhanced KPIs ---
    col1, col2, col3, col4 = st.columns(4)
    
    # Progress KPI
    tasks_df = pd.DataFrame(ssm.get_data("project_management", "tasks"))
    completion_pct = tasks_df['completion_pct'].mean()
    col1.metric("Overall Progress", f"{completion_pct:.1f}%")
    
    # Risk KPI
    hazards_df = pd.DataFrame(ssm.get_data("risk_management_file", "hazards"))
    high_risks = 0
    if not hazards_df.empty and 'initial_risk' in hazards_df.columns:
        high_risks = len(hazards_df[hazards_df['initial_risk'] == 'High'])
    col2.metric("High-Risk Hazards Identified", f"{high_risks}")

    # Action Item KPI
    actions = []
    for review in ssm.get_data("design_reviews", "reviews"):
        actions.extend(review.get("action_items", []))
    open_actions = len([a for a in actions if a.get('status') != 'Completed'])
    col3.metric("Open Action Items", f"{open_actions}")
    
    # Traceability KPI
    inputs_df = pd.DataFrame(ssm.get_data("design_inputs", "requirements"))
    outputs_df = pd.DataFrame(ssm.get_data("design_outputs", "documents"))
    traced_inputs = 0
    if not inputs_df.empty and not outputs_df.empty:
        traced_inputs = inputs_df['id'].isin(outputs_df['linked_input_id']).sum()
    coverage = (traced_inputs / len(inputs_df)) * 100 if not inputs_df.empty else 0
    col4.metric("Input→Output Trace Coverage", f"{coverage:.1f}%")

    st.divider()
    # ... (Gantt Chart and Pie chart logic remains the same) ...
    st.header("Project Timeline and Critical Path")
    critical_path = find_critical_path(tasks_df)
    gantt_fig = create_gantt_chart(tasks_df, critical_path)
    st.plotly_chart(gantt_fig, use_container_width=True)


# ============================ TAB 2: ADVANCED ANALYTICS ============================
with tab2:
    st.header("Compliance & Execution Analytics")
    analytics_selection = st.selectbox("Choose Analytics View:", ["Traceability Matrix", "Action Item Tracker"])
    
    if analytics_selection == "Traceability Matrix":
        render_traceability_matrix(ssm)
    elif analytics_selection == "Action Item Tracker":
        render_action_item_tracker(ssm)

# ============================ TAB 3: DHF STRUCTURE ===============================
with tab3:
    # ... (V-Model content is the same) ...
    st.header("The Design Control Process (V-Model)")
    st.image("https://www.researchgate.net/profile/Tor-Staalhane/publication/277005111/figure/fig1/AS:669443530891271@1536619171887/The-V-model-of-development-and-testing.png")
    st.markdown("For software-driven devices like this smart-pill, the V-Model is augmented by processes from **IEC 62304** (Software Lifecycle Processes), ensuring rigor in software requirements, architecture, coding, and testing.")


# ============================ TAB 4: DHF SECTION DETAILS =========================
with tab4:
    st.header("Data Entry for DHF & RMF Sections")
    with st.sidebar:
        st.header("DHF Section Navigation")
        selection = st.radio(
            "Go to Section:",
            [
                "1. Design Plan", "2. Risk Management File", "3. Human Factors", "4. Design Inputs", "5. Design Outputs",
                "6. Design Reviews & Gates", "7. Design Verification", "8. Design Validation",
                "9. Design Transfer", "10. Design Changes", "11. Project Task Editor"
            ]
        )
    
    PAGES = {
        "1. Design Plan": design_plan.render, "2. Risk Management File": design_risk_management.render,
        "3. Human Factors": human_factors.render, "4. Design Inputs": design_inputs.render,
        "5. Design Outputs": design_outputs.render, "6. Design Reviews & Gates": design_reviews.render,
        "7. Design Verification": design_verification.render, "8. Design Validation": design_validation.render,
        "9. Design Transfer": design_transfer.render, "10. Design Changes": design_changes.render,
    }
    
    # ... (Page routing logic remains largely the same, just with new pages added) ...
    if "Project Task Editor" in selection:
        # ... task editor logic
        pass
    else:
        page_function = PAGES[selection]
        page_function(ssm)
