# File: dhf_dashboard/dhf_sections/design_plan.py

import streamlit as st
import pandas as pd
from ..utils.session_state_manager import SessionStateManager

def render_design_plan(ssm: SessionStateManager):
    """
    Renders the Design and Development Plan section of the DHF Dashboard.
    This section is adapted for a combination product and integrated with project management timelines.
    """
    st.header("1. Design and Development Plan")
    st.markdown("""
    *As per 21 CFR 820.30(b) and principles of 21 CFR Part 4.*

    This plan outlines the design activities for the **smart-pill combination product**. It must
    address both the device component (under the Quality System Regulation) and its interface
    with the drug component (under cGMPs). It also defines the project scope, team, and key regulatory considerations.
    """)
    st.info("Changes made here are saved automatically.", icon="ℹ️")

    plan_data = ssm.get_data("design_plan")

    # --- Project Information ---
    st.subheader("1.1 Project Overview")
    plan_data["project_name"] = st.text_input(
        "**Project Name**",
        value=plan_data.get("project_name", "New Project"),
        key="dp_project_name",
        help="The official name of the combination product project."
    )
    plan_data["scope"] = st.text_area(
        "**Project Scope & Intended Use**",
        value=plan_data.get("scope", ""),
        key="dp_scope",
        height=150,
        help="Describe the device, the drug it delivers, the target patient population, the clinical indication, and the use environment."
    )

    # --- Regulatory and Risk Framework ---
    st.subheader("1.2 Regulatory and Risk Management Framework")
    plan_data["applicable_cgmp"] = st.text_input(
        "**Applicable Drug cGMPs**",
        value=plan_data.get("applicable_cgmp", "21 CFR Parts 210, 211"),
        key="dp_cgmp",
        help="Reference the Current Good Manufacturing Practices applicable to the drug constituent part."
    )
    plan_data["risk_management_plan_ref"] = st.text_input(
        "**Risk Management Plan Document ID**",
        value=plan_data.get("risk_management_plan_ref", ""),
        key="dp_rmp_ref",
        help="Reference to the main Risk Management Plan document governing activities under ISO 14971."
    )

    # --- Software Classification ---
    st.subheader("1.3 Software Level of Concern (Per FDA Guidance)")
    loc_options = ["Major", "Moderate", "Minor"]
    try:
        current_loc_index = loc_options.index(plan_data.get("software_level_of_concern", "Moderate"))
    except ValueError:
        current_loc_index = 1 # Default to Moderate if value is invalid

    plan_data["software_level_of_concern"] = st.selectbox(
        "**Select Software Level of Concern (LOC):**",
        options=loc_options,
        index=current_loc_index,
        key="dp_sw_loc",
        help="Determines the required rigor of software documentation per IEC 62304. Major: Serious injury or death possible. Moderate: Non-serious injury possible. Minor: No injury possible."
    )

    # --- Team and Responsibilities ---
    st.subheader("1.4 Team and Responsibilities")
    st.markdown("Define roles, assign team members, and outline their key responsibilities.")

    team_df = pd.DataFrame(plan_data.get("team_members", []))
    edited_df = st.data_editor(
        team_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "role": st.column_config.TextColumn("Role", help="e.g., Device Engineer, Pharma Scientist, RA Specialist, SW Engineer", required=True),
            "name": st.column_config.TextColumn("Assigned Member", required=True),
            "responsibility": st.column_config.TextColumn("Key Responsibilities", width="large"),
        },
        key="design_plan_team_editor"
    )
    plan_data["team_members"] = edited_df.to_dict('records')

    # Persist all changes made in this section back to the session state
    ssm.update_data(plan_data, "design_plan")
