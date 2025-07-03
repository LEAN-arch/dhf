# File: dhf_dashboard/app.py
# SME Note: This is the definitive, all-inclusive version. It includes the robust
# path correction block, the refined UI, and a fully expanded "Design Controls Guide"
# with details on key ISO standards, CFR parts, and Quality Engineering responsibilities.

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
# TAB 4: DESIGN CONTROLS GUIDE (FULLY EXPANDED)
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
