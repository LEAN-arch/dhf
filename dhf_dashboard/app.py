# File: dhf_dashboard/app.py
# SME Note: This is the definitive, corrected version. It fixes the AttributeError
# by ensuring the Design Control Tracker reads from the original list of task
# dictionaries in the session state, not the pandas DataFrame.

import sys
import os
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

# --- ROBUST PATH CORRECTION BLOCK ---
try:
    current_file_path = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file_path)
    project_root = os.path.dirname(current_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
except Exception as e:
    st.error(f"Error adjusting system path: {e}")
# --- END OF PATH CORRECTION BLOCK ---


# --- MODULAR IMPORTS ---
from dhf_dashboard.utils.session_state_manager import SessionStateManager
from dhf_dashboard.utils.critical_path_utils import find_critical_path
from dhf_dashboard.utils.plot_utils import create_progress_donut, create_action_item_chart
from dhf_dashboard.analytics.traceability_matrix import render_traceability_matrix
from dhf_dashboard.analytics.action_item_tracker import render_action_item_tracker
from dhf_dashboard.dhf_sections import (
    design_plan, design_risk_management, human_factors, design_inputs,
    design_outputs, design_reviews, design_verification, design_validation,
    design_transfer, design_changes
)

# --- DASHBOARD COMPONENT FUNCTIONS ---

def render_design_control_tracker(ssm):
    st.subheader("1. Design Control Tracker")
    st.markdown("Monitor the flow of Design Controls from inputs to outputs, including cross-functional sign-offs and DHF document status.")
    
    # --- FIX IS HERE: Fetch the raw list of dictionaries, not the processed DataFrame ---
    tasks_raw = ssm.get_data("project_management", "tasks")
    docs = pd.DataFrame(ssm.get_data("design_outputs", "documents"))

    for task in tasks_raw:
        with st.expander(f"**{task.get('name', 'N/A')}** (Status: {task.get('status', 'N/A')} - {task.get('completion_pct', 0)}%)"):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown("**Associated DHF Documents:**")
                phase_docs = docs[docs['phase'] == task.get('name')]
                if not phase_docs.empty:
                    st.dataframe(phase_docs[['id', 'title', 'status']], use_container_width=True)
                else:
                    st.caption("No documents for this phase yet.")
            with col2:
                st.markdown("**Cross-Functional Sign-offs:**")
                # This now correctly receives a dictionary object
                sign_offs = task.get('sign_offs', {})
                if isinstance(sign_offs, dict): # Add a safety check
                    for team, status in sign_offs.items():
                        color = "green" if status == "✅" else "orange" if status == "In Progress" else "grey"
                        st.markdown(f"- **{team}:** <span style='color:{color};'>{status}</span>", unsafe_allow_html=True)
                else:
                    st.caption("Sign-off data is not in the correct format.")
    st.caption("This tracker provides a live view of the DHF's completeness and the project's adherence to the design plan.")


def render_risk_management_dashboard(ssm):
    st.subheader("2. Risk Management Dashboard (ISO 14971, ICH Q9)")
    st.markdown("Analyze the project's risk profile, including the top risks by RPN, historical trends, and mitigation status.")
    hazards_data = ssm.get_data("risk_management_file", "hazards")
    historical_rpn = pd.DataFrame(ssm.get_data("risk_management_file", "historical_rpn"))

    if not hazards_data:
        st.warning("No risk data available.")
        return

    df = pd.DataFrame(hazards_data)
    df['initial_rpn'] = df['initial_S'] * df['initial_O'] * df['initial_D']
    df['final_rpn'] = df['final_S'] * df['final_O'] * df['final_D']

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Top 5 Risks by Initial RPN**")
        top_risks = df.sort_values('initial_rpn', ascending=False).head(5)
        st.dataframe(top_risks[['hazard_id', 'description', 'initial_rpn', 'final_rpn']], use_container_width=True)

    with col2:
        st.markdown("**RPN Trend Over Time**")
        if not historical_rpn.empty:
            fig = px.line(historical_rpn, x='date', y='total_rpn', title="Total Project RPN Reduction", markers=True)
            fig.update_layout(height=300, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Residual Risk Heatmap (Severity vs. Occurrence)**")
    heatmap_data = df.pivot_table(index='final_S', columns='final_O', aggfunc='size', fill_value=0)
    heatmap_data = heatmap_data.reindex(index=range(5, 0, -1), columns=range(1, 6), fill_value=0)
    fig = go.Figure(data=go.Heatmap(
                   z=heatmap_data.values, x=heatmap_data.columns, y=heatmap_data.index,
                   hoverongaps=False, colorscale='Reds'))
    fig.update_layout(title="Count of Residual Risks", yaxis_title="Severity", xaxis_title="Occurrence")
    st.plotly_chart(fig, use_container_width=True)

def render_vv_readiness_panel(ssm):
    st.subheader("3. Verification & Validation Readiness Panel")
    st.markdown("Track the status of V&V protocols, their traceability to risk controls, and flags for key compliance activities like usability engineering.")
    protocols = pd.DataFrame(ssm.get_data("design_verification", "tests"))
    if protocols.empty:
        st.warning("No V&V protocols have been defined.")
        return

    total_protocols = len(protocols)
    completed_protocols = len(protocols[protocols['status'] == 'Completed'])
    completion_pct = (completed_protocols / total_protocols) * 100 if total_protocols > 0 else 0

    st.markdown("**Overall Protocol Completion**")
    st.progress(int(completion_pct), text=f"{completion_pct:.1f}% Complete ({completed_protocols}/{total_protocols})")

    st.markdown("**Protocol Status & Traceability**")
    st.dataframe(protocols, use_container_width=True, column_config={
        "name": "Protocol Name",
        "tmv_status": st.column_config.SelectboxColumn("TMV Status", options=["N/A", "Required", "Completed"]),
        "risk_control_verified_id": "Linked Risk Control ID" # Corrected key
    })
    st.info("💡 Usability testing protocols (IEC 62366) should be included here and linked to Human Factors analysis.", icon="💡")

def render_audit_readiness_scorecard(ssm):
    st.subheader("4. Audit & Inspection Readiness Scorecard")
    st.markdown("A high-level assessment of DHF completeness and Quality System health to gauge readiness for internal or external audits.")
    
    docs = pd.DataFrame(ssm.get_data("design_outputs", "documents"))
    approved_docs = docs[docs['status'] == 'Approved']
    doc_readiness = (len(approved_docs) / len(docs)) * 100 if not docs.empty else 0

    capas = pd.DataFrame(ssm.get_data("quality_system", "capa_records"))
    open_capas = len(capas[capas['status'] == 'Open'])

    suppliers = pd.DataFrame(ssm.get_data("quality_system", "supplier_audits"))
    supplier_pass_rate = (len(suppliers[suppliers['status'] == 'Pass']) / len(suppliers)) * 100 if not suppliers.empty else 100

    def get_light(score):
        if score >= 90: return "🟢"
        if score >= 70: return "🟡"
        return "🔴"

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(f"DHF Document Readiness {get_light(doc_readiness)}", f"{doc_readiness:.1f}% Approved")
    with col2:
        st.metric(f"Open CAPAs {get_light(100 - open_capas*20)}", f"{open_capas} Item(s)")
    with col3:
        st.metric(f"Supplier Audit Pass Rate {get_light(supplier_pass_rate)}", f"{supplier_pass_rate:.1f}%")

    st.success("Bonus: Next mock internal audit scheduled for 2024-09-15.")

def render_continuous_improvement_dashboard(ssm):
    st.subheader("5. Continuous Improvement Dashboard")
    st.markdown("Track metrics related to process efficiency and quality improvements, including mocked data from statistical tools.")
    improvements = pd.DataFrame(ssm.get_data("quality_system", "continuous_improvement"))

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Process Improvements Logged**")
        if not improvements.empty:
            fig = px.bar(improvements, x='date', y='impact', color='area', title="Impact of Improvements Over Time (%)")
            fig.update_layout(height=300, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown("**Mocked Minitab Output**")
        st.info("Simulated analysis shows that after implementing `SOP-MFG-101`, the process capability for dose accuracy has increased.")
        st.metric("Process Sigma Level", "4.8 σ", delta="0.5 σ")
        st.caption("This indicates a more reliable and consistent manufacturing process.")

# --- PAGE CONFIGURATION AND MAIN LAYOUT ---
st.set_page_config(layout="wide", page_title="DHF Command Center", page_icon="🚀")
ssm = SessionStateManager()

# --- Initial Data Prep for components that need the DataFrame ---
tasks_df_processed = pd.DataFrame(ssm.get_data("project_management", "tasks"))
if not tasks_df_processed.empty:
    tasks_df_processed['start_date'] = pd.to_datetime(tasks_df_processed['start_date'], errors='coerce')
    tasks_df_processed['end_date'] = pd.to_datetime(tasks_df_processed['end_date'], errors='coerce')
    tasks_df_processed.dropna(subset=['start_date', 'end_date'], inplace=True)
    critical_path_ids = find_critical_path(tasks_df_processed.copy())
    status_colors = {"Completed": "#2ca02c", "In Progress": "#1f77b4", "Not Started": "#7f7f7f", "At Risk": "#d62728"}
    tasks_df_processed['color'] = tasks_df_processed['status'].map(status_colors).fillna('#7f7f7f')
    tasks_df_processed['is_critical'] = tasks_df_processed['id'].isin(critical_path_ids)
    tasks_df_processed['line_color'] = tasks_df_processed.apply(lambda r: 'red' if r['is_critical'] else '#FFFFFF', axis=1)
    tasks_df_processed['line_width'] = tasks_df_processed.apply(lambda r: 4 if r['is_critical'] else 0, axis=1)
    tasks_df_processed['display_text'] = tasks_df_processed.apply(lambda r: f"<b>{r['name']}</b> ({r.get('completion_pct', 0)}%)", axis=1)

st.title("🚀 DHF Command Center")
project_name = ssm.get_data("design_plan", "project_name")
st.caption(f"Live monitoring for the **{project_name}** project.")

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 **Dashboard**", "🗂️ **DHF Explorer**", "🔬 **Advanced Analytics**", "🏛️ **Design Controls Guide**"
])

# ==============================================================================
# TAB 1: PROFESSIONAL DASHBOARD
# ==============================================================================
with tab1:
    st.header("Project Health At-a-Glance")
    col1, col2, col3 = st.columns(3)
    with col1:
        completion_pct = tasks_df_processed['completion_pct'].mean() if not tasks_df_processed.empty else 0
        st.plotly_chart(create_progress_donut(completion_pct), use_container_width=True)
    with col2:
        st.markdown("#### Overall Risk Profile")
        st.caption("Based on Initial vs. Final RPN")
        hazards_df = pd.DataFrame(ssm.get_data("risk_management_file", "hazards"))
        hazards_df['initial_rpn'] = hazards_df['initial_S'] * hazards_df['initial_O'] * hazards_df['initial_D']
        hazards_df['final_rpn'] = hazards_df['final_S'] * hazards_df['final_O'] * hazards_df['final_D']
        st.metric("Initial Total RPN", f"{hazards_df['initial_rpn'].sum():,}",)
        st.metric("Current Residual RPN", f"{hazards_df['final_rpn'].sum():,}", delta=f"{(hazards_df['final_rpn'].sum() - hazards_df['initial_rpn'].sum()):,}")
    with col3:
        reviews = ssm.get_data("design_reviews", "reviews")
        actions = [item for r in reviews for item in r.get("action_items", [])]
        actions_df = pd.DataFrame(actions)
        st.plotly_chart(create_action_item_chart(actions_df), use_container_width=True)
    st.divider()

    render_design_control_tracker(ssm)
    st.divider()
    render_risk_management_dashboard(ssm)
    st.divider()
    render_vv_readiness_panel(ssm)
    st.divider()
    render_audit_readiness_scorecard(ssm)
    st.divider()
    render_continuous_improvement_dashboard(ssm)

# ==============================================================================
# TAB 2: DHF EXPLORER
# ==============================================================================
with tab2:
    st.header("Design History File Explorer")
    st.markdown("Select a DHF section from the sidebar to view or edit its contents.")
    with st.sidebar:
        st.header("DHF Section Navigation")
        PAGES = {
            "1. Design Plan": design_plan.render_design_plan, "2. Risk Management": design_risk_management.render_design_risk_management,
            "3. Human Factors": human_factors.render_human_factors, "4. Design Inputs": design_inputs.render_design_inputs,
            "5. Design Outputs": design_outputs.render_design_outputs, "6. Design Reviews": design_reviews.render_design_reviews,
            "7. Design Verification": design_verification.render_design_verification, "8. Design Validation": design_validation.render_design_validation,
            "9. Design Transfer": design_transfer.render_design_transfer, "10. Design Changes": design_changes.render_design_changes,
        }
        dhf_selection = st.radio("Select a section to edit:", PAGES.keys(), key="sidebar_dhf_selection")
    st.divider()
    page_function = PAGES[dhf_selection]
    page_function(ssm)

# ==============================================================================
# TAB 3: ADVANCED ANALYTICS
# ==============================================================================
with tab3:
    st.header("Advanced Compliance & Project Analytics")
    analytics_tabs = st.tabs(["Traceability Matrix", "Action Item Tracker", "Project Task Editor"])
    with analytics_tabs[0]: render_traceability_matrix(ssm)
    with analytics_tabs[1]: render_action_item_tracker(ssm)
    with analytics_tabs[2]:
        st.subheader("Project Timeline and Task Editor")
        st.warning("Directly edit project timelines, statuses, and dependencies. Changes are saved automatically.", icon="⚠️")
        tasks_df_to_edit = pd.DataFrame(ssm.get_data("project_management", "tasks"))
        edited_df = st.data_editor(
            tasks_df_to_edit, key="main_task_editor", num_rows="dynamic", use_container_width=True,
            column_config={"start_date": st.column_config.DateColumn("Start Date", format="YYYY-MM-DD"), "end_date": st.column_config.DateColumn("End Date", format="YYYY-MM-DD")}
        )
        if not tasks_df_to_edit.equals(edited_df):
            ssm.update_data(edited_df.to_dict('records'), "project_management", "tasks")
            st.toast("Project tasks updated! Rerunning...")
            st.rerun()

# ==============================================================================
# TAB 4: DESIGN CONTROLS GUIDE
# ==============================================================================
with tab4:
    st.header("A Guide to Design Controls & the Regulatory Landscape")
    st.markdown("This section provides a high-level overview of the Design Controls methodology and the key regulations and standards governing medical device development.")

    st.subheader("Navigating the Regulatory Maze for Combination Products")
    st.info("A 'Combination Product' like the Smart-Pill contains both device and drug components, so it must comply with regulations for both.")
    with st.expander("▶️ **21 CFR Part 4: The 'Rulebook for Rulebooks'**"):
        st.markdown("""
        Part 4 governs combination products...
        """)
    with st.expander("▶️ **21 CFR Part 820: The Quality System Regulation (QSR) for Devices**"):
        st.markdown("""
        This is the FDA's rulebook... The DHF is that proof.
        """)
    with st.expander("▶️ **21 CFR Parts 210/211: Current Good Manufacturing Practices (cGMP) for Drugs**"):
        st.markdown("""
        This is the FDA's rulebook for pharmaceutical products... Key Design Considerations:
            - **Material Compatibility:** ...
            - **Stability:** ...
            - **Release Profile:** ...
        """)
    with st.expander("▶️ **ISO 13485:2016: Quality Management Systems (International Standard)**"):
        st.markdown("""
        ISO 13485 is the internationally recognized standard for a medical device QMS...
        """)
    with st.expander("▶️ **ISO 14971:2019: Risk Management for Medical Devices (International Standard)**"):
        st.markdown("""
        This is the global "how-to" guide for risk management... The **"2. Risk Management"** section... is a direct implementation...
        """)
    st.divider()

    st.subheader("The Role of a Design Assurance Quality Engineer")
    st.markdown("A Design Assurance QE is the steward of the DHF...")
    with st.expander("✅ **Owning the Design History File (DHF)**"):
        st.markdown("""
        The QE is responsible for the **creation, remediation, and maintenance** of the DHF... The Traceability Matrix is the QE's primary tool for identifying gaps.
        """)
    with st.expander("✅ **Driving Verification & Validation (V&V) Strategy**"):
        st.markdown("""
        The QE... architect[s] the entire V&V strategy... **V&V Master Plan**... **Protocol & Report Review**.
        """)
    with st.expander("✅ **Ensuring Robust Test Methods (Test Method Validation - TMV)**"):
        st.markdown("""
        A core QE principle: **You cannot trust test results if you cannot trust the test method itself.** TMV involves formal studies to assess: **Accuracy**, **Precision (Repeatability & Reproducibility)**...
        """)
    with st.expander("✅ **Applying Statistical Rationale**"):
        st.markdown("""
        ...Statistical methods are required... **Sample Size Justification** (Reliability and Confidence)... **Acceptance Criteria**... **Data Analysis** (Cpk, t-tests, ANOVA).
        """)
    with st.expander("✅ **Guiding Design Transfer and Supplier Quality**"):
         st.markdown("""
         The QE acts as the bridge between R&D and Manufacturing... **Device Master Record (DMR)**... **Process Validation (IQ/OQ/PQ)**... **Supplier Controls**.
         """)

    st.divider()

    st.subheader("Visualizing the Process: The V-Model")
    v_model_image_path = os.path.join(os.path.dirname(__file__), "v_model_diagram.png")
    if os.path.exists(v_model_image_path): st.image(v_model_image_path, caption="The V-Model illustrates the relationship between design decomposition and integration/testing.", use_container_width=True)
    else: st.error(f"Image Not Found: Ensure `v_model_diagram.png` is in the same directory as this script.", icon="🚨")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Left Side: Decomposition & Design")
        st.markdown("""
        - **User Needs & Intended Use:** What problem does the user need to solve?
        - **Design Inputs (Requirements):** How must the device perform to meet those needs?
        - **System & Architectural Design:** How will the components be structured to meet the requirements?
        - **Detailed Design (Outputs):** The final drawings, code, and specifications used to build the device.
        """)
    with col2:
        st.subheader("Right Side: Integration & Testing")
        st.markdown("""
        - **Unit/Component Verification:** Does each individual part meet its detailed design specification?
        - **Integration & System Verification:** Do the assembled parts work together as defined in the architectural design?
        - **Design Validation:** Does the final, complete device meet the high-level User Needs?
        """)
    st.success("""
    #### The Core Principle: Verification vs. Validation
    - **Verification:** *'Are we building the product right?'*
    - **Validation:** *'Are we building the right product?'*
    """)
