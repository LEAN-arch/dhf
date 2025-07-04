# File: dhf_dashboard/dhf_sections/design_plan.py
# --- Enhanced Version ---
"""
Renders the Design and Development Plan section of the DHF dashboard.

This module provides the UI for creating and editing the foundational planning
document for the project, as required by 21 CFR 820.30(b).
"""

# --- Standard Library Imports ---
import logging
from typing import Any, Dict

# --- Third-party Imports ---
import pandas as pd
import streamlit as st

# --- Local Application Imports ---
from ..utils.session_state_manager import SessionStateManager

# --- Setup Logging ---
logger = logging.getLogger(__name__)


def render_design_plan(ssm: SessionStateManager) -> None:
    """
    Renders the UI for the Design and Development Plan section.

    This function displays a form with various input widgets to capture all
    aspects of the design plan, including scope, team responsibilities, and
    key regulatory considerations. All changes are saved back to the session state.

    Args:
        ssm (SessionStateManager): The session state manager to access DHF data.
    """
    st.header("1. Design and Development Plan")
    st.markdown("""
    *As per 21 CFR 820.30(b) and principles of 21 CFR Part 4.*

    This plan outlines the design activities for the **smart-pill combination product**. It must
    address both the device component (under the Quality System Regulation) and its interface
    with the drug component (under cGMPs). It also defines the project scope, team, and key regulatory considerations.
    """)
    st.info("Changes made on this page are saved automatically upon interaction.", icon="ℹ️")

    try:
        # --- 1. Load Data ---
        # Load the entire design_plan dictionary into a local variable.
        # Edits will be made to this dict, and it will be saved once at the end.
        plan_data: Dict[str, Any] = ssm.get_data("design_plan")
        logger.info("Loaded design plan data.")

        # --- 2. Render UI Sections ---
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
            value=plan_data.get("risk_management_plan_ref", "RMP-001"),
            key="dp_rmp_ref",
            help="Reference to the main Risk Management Plan document governing activities under ISO 14971."
        )

        # --- Software Classification ---
        st.subheader("1.3 Software Level of Concern (Per FDA Guidance)")
        loc_options = ["Major", "Moderate", "Minor"]
        try:
            # Gracefully handle invalid stored values
            current_loc_index = loc_options.index(plan_data.get("software_level_of_concern", "Moderate"))
        except ValueError:
            logger.warning("Invalid 'software_level_of_concern' found in data. Defaulting to 'Moderate'.")
            current_loc_index = 1  # Default to Moderate

        plan_data["software_level_of_concern"] = st.selectbox(
            "**Select Software Level of Concern (LOC):**",
            options=loc_options,
            index=current_loc_index,
            key="dp_sw_loc",
            help="Determines the required rigor of software documentation (per IEC 62304). Major: Serious injury or death possible. Moderate: Non-serious injury possible. Minor: No injury possible."
        )

        # --- Team and Responsibilities ---
        st.subheader("1.4 Team and Responsibilities")
        st.markdown("Define roles, assign team members, and outline their key responsibilities.")

        team_df = pd.DataFrame(plan_data.get("team_members", []))
        edited_team_df = st.data_editor(
            team_df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "role": st.column_config.TextColumn(
                    "Role",
                    help="e.g., Device Engineer, Pharma Scientist, RA Specialist, SW Engineer",
                    required=True
                ),
                "name": st.column_config.TextColumn("Assigned Member", required=True),
                "responsibility": st.column_config.TextColumn("Key Responsibilities", width="large"),
            },
            key="design_plan_team_editor",
            hide_index=True
        )
        plan_data["team_members"] = edited_team_df.to_dict('records')

        # --- 3. Persist All Changes ---
        # A single update call at the end ensures atomicity for this section's edits.
        ssm.update_data(plan_data, "design_plan")
        logger.debug("Design plan data updated in session state.")

    except Exception as e:
        st.error("An error occurred while displaying the Design Plan section. The data may be malformed.")
        logger.error(f"Failed to render design plan: {e}", exc_info=True)


# ==============================================================================
# --- UNIT TEST SCAFFOLDING (for `pytest`) ---
# ==============================================================================
"""
import pytest
from unittest.mock import MagicMock

# To run tests, place this in a 'tests' directory and run pytest.
# The UI rendering is not tested, but the data handling logic is.

def load_and_process_plan(ssm: SessionStateManager) -> Dict[str, Any]:
    '''Refactored logic for testing: just loads the data.'''
    return ssm.get_data("design_plan")

def prepare_team_df(plan_data: Dict[str, Any]) -> pd.DataFrame:
    '''Refactored logic for testing: prepares the team DataFrame.'''
    return pd.DataFrame(plan_data.get("team_members", []))


@pytest.fixture
def mock_ssm_with_plan():
    '''Mocks SessionStateManager with sample design plan data.'''
    ssm = MagicMock()
    mock_data = {
        "project_name": "Test Project",
        "scope": "Test Scope",
        "team_members": [
            {"role": "Lead", "name": "Alice", "responsibility": "Oversight"},
            {"role": "Engineer", "name": "Bob", "responsibility": "Build"},
        ]
    }
    ssm.get_data.return_value = mock_data
    return ssm

def test_load_plan_data(mock_ssm_with_plan):
    '''Tests that the data is correctly loaded into a dictionary.'''
    plan_data = load_and_process_plan(mock_ssm_with_plan)
    assert isinstance(plan_data, dict)
    assert plan_data.get("project_name") == "Test Project"
    assert "team_members" in plan_data

def test_prepare_team_dataframe(mock_ssm_with_plan):
    '''Tests that the team members list is correctly converted to a DataFrame.'''
    plan_data = load_and_process_plan(mock_ssm_with_plan)
    team_df = prepare_team_df(plan_data)
    assert isinstance(team_df, pd.DataFrame)
    assert len(team_df) == 2
    assert "Alice" in team_df['name'].values

def test_edit_plan_data(mock_ssm_with_plan):
    '''Simulates editing the loaded data dictionary.'''
    plan_data = load_and_process_plan(mock_ssm_with_plan)

    # Simulate editing a text field
    plan_data["project_name"] = "Updated Project Name"
    assert plan_data["project_name"] == "Updated Project Name"

    # Simulate editing the team DataFrame and converting it back
    team_df = prepare_team_df(plan_data)
    team_df.loc[1, 'name'] = 'Robert' # Edit a value
    plan_data["team_members"] = team_df.to_dict('records')

    assert plan_data["team_members"][1]["name"] == "Robert"
"""
