# File: dhf_dashboard/dhf_sections/design_plan.py

import streamlit as st
import pandas as pd
from utils.session_state_manager import SessionStateManager

def render_design_plan(ssm: SessionStateManager):
    """
    Renders the Design and Development Plan section.
    Adapted for a combination product.
    """
    st.header("1. Design and Development Plan")
    st.markdown("""
    *As per 21 CFR 820.30(b) and principles of 21 CFR Part 4.*

    This plan outlines the design activities for the **smart-pill combination product**. It must
    address both the device component (under the Quality System Regulation) and its interface
    with the drug component (under cGMPs).
    """)

    plan_data = ssm.get_section_data("design_plan")

    st.subheader("1.1 Project Overview")
    plan_data["project_name"] = st.text_input(
        "Project Name",
        value=plan_data.get("project_name", ""),
        help="The official name of the combination product project."
    )
    plan_data["scope"] = st.text_area(
        "Project Scope & Intended Use",
        value=plan_data.get("scope", ""),
        height=150,
        help="Describe the device, the drug it delivers, the target patient population, and the clinical indication."
    )

    st.subheader("1.2 Regulatory and Risk Management Framework")
    plan_data["applicable_cgmp"] = st.text_input(
        "Applicable Drug cGMPs",
        value=plan_data.get("applicable_cgmp", "21 CFR Parts 210, 211"),
        help="Reference the Current Good Manufacturing Practices applicable to the drug constituent part."
    )
    plan_data["risk_management_plan_ref"] = st.text_input(
        "Risk Management Plan Document ID",
        value=plan_data.get("risk_management_plan_ref", ""),
        help="Reference to the main Risk Management Plan document governing activities under ISO 14971."
    )

    st.subheader("1.3 Team and Responsibilities")
    team_df = pd.DataFrame(plan_data.get("team_members", []))
    edited_df = st.data_editor(
        team_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "role": st.column_config.TextColumn("Role", help="e.g., Device Engineer, Pharma Scientist, RA Specialist", required=True),
            "name": st.column_config.TextColumn("Assigned Member", required=True),
            "responsibility": st.column_config.TextColumn("Key Responsibilities"),
        }
    )
    plan_data["team_members"] = edited_df.to_dict('records')

    ssm.update_section_data("design_plan", plan_data)

    if st.button("Save Design Plan Section"):
        st.success("Design Plan data saved successfully!")
