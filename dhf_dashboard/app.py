# File: dhf_dashboard/app.py
# SME Note: This is the definitive, all-inclusive, and untruncated version. It includes the robust
# path correction block, the professional-grade QE dashboard, and the fully expanded "Design
# Controls Guide" with all detailed text restored.

import sys
import os
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

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
# SME Rationale: To keep the main UI code clean, complex dashboard sections are
# encapsulated in their own functions.

def render_design_control_tracker(ssm):
    st.subheader("1. Design Control Tracker")
    st.markdown("Monitor the flow of Design Controls from inputs to outputs, including cross-functional sign-offs and DHF document status.")
    tasks = ssm.get_data("project_management", "tasks")
    docs = pd.DataFrame(ssm.get_data("design_outputs", "documents"))

    for task in tasks:
        with st.expander(f"**{task['name']}** (Status: {task['status']} - {task['completion_pct']}%)"):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown("**Associated DHF Documents:**")
                phase_docs = docs[docs['phase'] == task['name']]
                if not phase_docs.empty:
                    st.dataframe(phase_docs[['id', 'title', 'status']], use_container_width=True)
                else:
                    st.caption("No documents for this phase yet.")
            with col2:
                st.markdown("**Cross-Functional Sign-offs:**")
                sign_offs = task.get('sign_offs', {})
                for team, status in sign_offs.items():
                    color = "green" if status == "✅" else "orange" if status == "In Progress" else "grey"
                    st.markdown(f"- **{team}:** <span style='color:{color};'>{status}</span>", unsafe_allow_html=True)
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

    # Risk Heatmap
    st.markdown("**Residual Risk Heatmap (Severity vs. Occurrence)**")
    heatmap_data = df.pivot_table(index='final_S', columns='final_O', aggfunc='size', fill_value=0)
    heatmap_data = heatmap_data.reindex(index=range(5, 0, -1), columns=range(1, 6), fill_value=0) # Ensure full 5x5 grid
    fig = go.Figure(data=go.Heatmap(
                   z=heatmap_data.values,
                   x=heatmap_data.columns,
                   y=heatmap_data.index,
                   hoverongaps=False,
                   colorscale='Reds'))
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
        "risk_control": "Linked Risk Control"
    })
    st.info("💡 Usability testing protocols (IEC 62366) should be included here and linked to Human Factors analysis.", icon="💡")

def render_audit_readiness_scorecard(ssm):
    st.subheader("4. Audit & Inspection Readiness Scorecard")
    st.markdown("A high-level assessment of DHF completeness and Quality System health to gauge readiness for internal or external audits.")

    # Calculations
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
    # --- Top Level KPIs ---
    st.header("Project Health At-a-Glance")
    col1, col2, col3 = st.columns(3)
    with col1:
        tasks_df = pd.DataFrame(ssm.get_data("project_management", "tasks"))
        completion_pct = tasks_df['completion_pct'].mean() if not tasks_df.empty else 0
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
        reviews = ssm.get_data("design_reviews", "reviews") # In a real app, this would pull from more sources
        actions = [item for r in reviews for item in r.get("action_items", [])]
        actions_df = pd.DataFrame(actions)
        st.plotly_chart(create_action_item_chart(actions_df), use_container_width=True)
    st.divider()

    # --- Calling the new, detailed dashboard components ---
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
        tasks_df = pd.DataFrame(ssm.get_data("project_management", "tasks"))
        edited_df = st.data_editor(
            tasks_df, key="main_task_editor", num_rows="dynamic", use_container_width=True,
            column_config={"start_date": st.column_config.DateColumn("Start Date", format="YYYY-MM-DD"), "end_date": st.column_config.DateColumn("End Date", format="YYYY-MM-DD")}
        )
        if not pd.DataFrame(ssm.get_data("project_management", "tasks")).equals(edited_df):
            ssm.update_data(edited_df.to_dict('records'), "project_management", "tasks")
            st.toast("Project tasks updated! Rerunning...")
            st.rerun()

# ==============================================================================
# TAB 4: DESIGN CONTROLS GUIDE (FULLY EXPANDED AND UNTRUNCATED)
# ==============================================================================
with tab4:
    st.header("A Guide to Design Controls & the Regulatory Landscape")
    st.markdown("This section provides a high-level overview of the Design Controls methodology and the key regulations and standards governing medical device development.")

    st.subheader("Navigating the Regulatory Maze for Combination Products")
    st.info("A 'Combination Product' like the Smart-Pill contains both device and drug components, so it must comply with regulations for both.")

    with st.expander("▶️ **21 CFR Part 4: The 'Rulebook for Rulebooks'**"):
        st.markdown("""
        Part 4 governs combination products. It doesn't add new requirements, but instead tells you **which existing regulations to apply**. For the Smart-Pill, this means:
        - The **device aspects** (casing, electronics, software) must follow the **Quality System Regulation (QSR) for devices**.
        - The **drug aspects** (formulation, stability, purity) must follow the **Current Good Manufacturing Practices (cGMP) for drugs**.
        - Design Controls (part of the QSR) must consider the entire system, including how the device and drug interact.
        """)
    with st.expander("▶️ **21 CFR Part 820: The Quality System Regulation (QSR) for Devices**"):
        st.markdown("""
        This is the FDA's rulebook for medical device manufacturing and design. The Design Controls section (`820.30`) is the foundation of this entire application. It mandates a systematic approach to design to ensure the final product is safe and effective.
        - **Applies to:** The physical pill, its electronics, the embedded software, and the companion mobile app.
        - **Key Principle:** You must document everything to prove you designed the device in a state of control. The DHF is that proof.
        """)
    with st.expander("▶️ **21 CFR Parts 210/211: Current Good Manufacturing Practices (cGMP) for Drugs**"):
        st.markdown("""
        This is the FDA's rulebook for pharmaceutical products. While this app focuses on the DHF (a device concept), the design of the Smart-Pill must not violate cGMP principles.
        - **Applies to:** The drug substance itself and its interaction with a device.
        - **Key Design Considerations:**
            - **Material Compatibility:** The pill casing cannot contaminate or react with the drug.
            - **Stability:** The device cannot cause the drug to degrade over its shelf life.
            - **Release Profile:** The device's mechanism must release the drug in a way that is safe and therapeutically effective.
        """)
    with st.expander("▶️ **ISO 13485:2016: Quality Management Systems (International Standard)**"):
        st.markdown("""
        ISO 13485 is the internationally recognized standard for a medical device Quality Management System (QMS). It is very similar to the FDA's QSR but is required for market access in many other regions, including Europe (as part of MDR), Canada, and Australia.
        - **Relationship to QSR:** Following the QSR gets you very close to ISO 13485 compliance. The key difference is that ISO 13485 places a stronger emphasis on **risk management** throughout the entire QMS.
        - **Why it matters:** A DHF built to QSR standards is easily adaptable for ISO 13485 audits, enabling global market strategies.
        """)
    with st.expander("▶️ **ISO 14971:2019: Risk Management for Medical Devices (International Standard)**"):
        st.markdown("""
        This is the global "how-to" guide for risk management. Both the FDA and international regulators consider it the state-of-the-art process for ensuring device safety.
        - **Process:** It defines a lifecycle approach: identify hazards, estimate and evaluate risks, implement controls, and monitor the effectiveness of those controls.
        - **Role in this App:** The **"2. Risk Management"** section of the DHF Explorer is a direct implementation of the documentation required by ISO 14971.
        """)
    
    st.divider()

    # --- CONTENT TAILORED TO THE SENIOR QUALITY ENGINEER ROLE ---
    st.subheader("The Role of a Design Assurance Quality Engineer")
    st.markdown("A Design Assurance QE is the steward of the DHF, ensuring compliance, quality, and safety are designed into the product from day one. This tool is designed to be their primary workspace. Key responsibilities within this framework include:")

    with st.expander("✅ **Owning the Design History File (DHF)**"):
        st.markdown("""
        The QE is responsible for the **creation, remediation, and maintenance** of the DHF. It's not just a repository; it's a living document that tells the story of the product's development.
        - This application serves as the DHF's active workspace.
        - **Key QE Goal:** Ensure the DHF is complete, coherent, and audit-ready at all times. The Traceability Matrix is the QE's primary tool for identifying gaps.
        """)
    with st.expander("✅ **Driving Verification & Validation (V&V) Strategy**"):
        st.markdown("""
        The QE doesn't just witness tests; they help architect the entire V&V strategy.
        - **V&V Master Plan:** This is a high-level document, referenced in the Design Plan, that outlines the scope, methods, and acceptance criteria for all V&V activities.
        - **Protocol & Report Review:** The QE reviews and approves all test protocols (to ensure they are adequate) and reports (to ensure they are accurate and complete). The "Design Verification" and "Design Validation" sections track these deliverables.
        """)
    with st.expander("✅ **Ensuring Robust Test Methods (Test Method Validation - TMV)**"):
        st.markdown("""
        A core QE principle: **You cannot trust test results if you cannot trust the test method itself.** TMV is the process of providing objective evidence that a test method is accurate, precise, and reliable for its intended purpose.
        - **When is it needed?** For any custom or non-standard test method used in V&V.
        - **What does it involve?** Formal studies to assess:
            - **Accuracy:** How close is the measurement to the true value?
            - **Precision (Repeatability & Reproducibility):** How consistent are the results over time, with different operators, and on different equipment?
            - **Linearity, Range, and Specificity:** Other parameters depending on the test type.
        - **Documentation:** TMV results in a formal report that should be linked or referenced within the DHF.
        """)
    with st.expander("✅ **Applying Statistical Rationale**"):
        st.markdown("""
        "Because we said so" is not a valid rationale for an auditor. Statistical methods are required to provide objective evidence that the design is reliable and safe.
        - **Sample Size Justification:** The QE must justify *why* a certain number of units were tested. This is often based on establishing a specific **Reliability and Confidence** level (e.g., "we are 95% confident that the device is 99% reliable").
        - **Acceptance Criteria:** The pass/fail criteria for a test must be defined *before* the test is run and should be clinically relevant.
        - **Data Analysis:** Using tools like capability analysis (Cpk), t-tests, or ANOVA to analyze test data and draw valid conclusions.
        """)
    with st.expander("✅ **Guiding Design Transfer and Supplier Quality**"):
         st.markdown("""
         The QE acts as the bridge between R&D and Manufacturing, ensuring the design can be produced consistently and at scale without losing quality.
         - **Device Master Record (DMR):** The QE helps compile the DMR, which is the 'recipe' for building the device, derived from the Design Outputs.
         - **Process Validation (IQ/OQ/PQ):** The QE oversees the validation of the manufacturing line itself.
         - **Supplier Controls:** The QE is responsible for qualifying suppliers of critical components (like the battery or pill casing material), ensuring their quality systems are adequate. This is documented as part of Design Outputs and Transfer activities.
         """)

    st.divider()

    st.subheader("Visualizing the Process: The V-Model")
    st.markdown("The V-Model is a powerful way to visualize the Design Controls process, emphasizing the critical link between design (left side) and testing (right side).")

    v_model_image_path = os.path.join(os.path.dirname(__file__), "v_model_diagram.png")
    if os.path.exists(v_model_image_path):
        st.image(v_model_image_path, caption="The V-Model illustrates the relationship between design decomposition and integration/testing.", use_container_width=True)
    else:
        st.error(f"Image Not Found: Ensure `v_model_diagram.png` is in the same directory as this script.", icon="🚨")

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
