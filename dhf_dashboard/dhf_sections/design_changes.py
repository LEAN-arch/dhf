# File: dhf_dashboard/dhf_sections/design_changes.py
# --- Enhanced Version ---
"""
Renders the Design Changes section of the DHF dashboard.

This module provides the user interface for documenting and managing formal
design change control records, as required by 21 CFR 820.30(i).
"""

# --- Standard Library Imports ---
import logging
from typing import Any, Dict, List

# --- Third-party Imports ---
import pandas as pd
import streamlit as st

# --- Local Application Imports ---
from ..utils.session_state_manager import SessionStateManager

# --- Setup Logging ---
logger = logging.getLogger(__name__)


def render_design_changes(ssm: SessionStateManager) -> None:
    """
    Renders the UI for the Design Changes section.

    This function displays an editable table for managing Design Change
    Requests (DCRs), including their description, reason, impact analysis,
    and approval status. All changes are saved back to the session state.

    Args:
        ssm (SessionStateManager): The session state manager to access DHF data.
    """
    st.header("10. Design Changes")
    st.markdown("""
    *As per 21 CFR 820.30(i).*

    This section documents the formal control of all design changes made after the design has been finalized and approved.
    For a combination product, the **Impact Analysis** is critical and must evaluate effects on both the device and drug
    components, as well as a re-assessment of the overall risk profile.
    """)
    st.info("Changes made here are saved automatically. Log all formal design change requests and their impact.", icon="ℹ️")

    try:
        # --- 1. Load Data ---
        changes_data: List[Dict[str, Any]] = ssm.get_data("design_changes", "changes")
        changes_df = pd.DataFrame(changes_data)
        logger.info(f"Loaded {len(changes_df)} design change records.")

        # --- 2. Display Data Editor ---
        st.subheader("Design Change Control Records")
        st.markdown("Log all formal design change requests. The impact analysis is a critical part of the review and approval process.")

        edited_df = st.data_editor(
            changes_df,
            num_rows="dynamic",
            use_container_width=True,
            key="design_changes_editor",
            column_config={
                "id": st.column_config.TextColumn(
                    "Change Request ID",
                    help="Unique ID for the change, e.g., DCR-001.",
                    required=True
                ),
                "description": st.column_config.TextColumn(
                    "Change Description",
                    width="large",
                    help="A clear and concise summary of the change being made.",
                    required=True
                ),
                "reason": st.column_config.TextColumn(
                    "Reason for Change",
                    width="large",
                    help="Justification for the change, e.g., 'Corrective action from CAPA-01', 'Improved performance', 'Supplier change'."
                ),
                "impact_analysis": st.column_config.TextColumn(
                    "Impact Analysis",
                    width="large",
                    help="Describe impact on device performance, drug stability/efficacy, user interface, manufacturing processes, and whether new risks are introduced or existing ones affected."
                ),
                "approval_status": st.column_config.SelectboxColumn(
                    "Approval Status",
                    options=["Pending", "Approved", "Rejected", "Implementation Pending"],
                    help="The current status of the change request.",
                    required=True
                ),
                "approval_date": st.column_config.DateColumn(
                    "Approval Date",
                    format="YYYY-MM-DD",
                    help="The date the change was formally approved or rejected."
                ),
                # SME Note: A future enhancement could be a nested data editor
                # for action items required to implement the change, similar
                # to the design reviews section.
            },
            hide_index=True
        )

        # --- 3. Persist Updated Data ---
        # Convert the potentially edited DataFrame back to the list-of-dicts
        # format required by the session state.
        updated_records = edited_df.to_dict('records')

        # Only update the session state if there's a change to avoid unnecessary reruns
        if updated_records != changes_data:
            ssm.update_data(updated_records, "design_changes", "changes")
            logger.info("Design changes data updated in session state.")
            st.toast("Design changes saved!", icon="✅")

    except Exception as e:
        st.error("An error occurred while displaying the Design Changes section. The data may be malformed.")
        logger.error(f"Failed to render design changes: {e}", exc_info=True)


# ==============================================================================
# --- UNIT TEST SCAFFOLDING (for `pytest`) ---
# ==============================================================================
"""
import pytest
from unittest.mock import MagicMock

# To run tests, place this in a 'tests' directory and run pytest.
# The render function is refactored into a testable "pure" function.

def process_design_changes(ssm: SessionStateManager) -> pd.DataFrame:
    '''Refactored logic for testing: loads data and converts to DataFrame.'''
    changes_data = ssm.get_data("design_changes", "changes")
    return pd.DataFrame(changes_data)

def save_design_changes(df: pd.DataFrame) -> List[Dict[str, Any]]:
    '''Refactored logic for testing: converts DataFrame back to records.'''
    # Ensure date columns are handled correctly if they exist
    if 'approval_date' in df.columns:
        # Convert NaT to None and datetime to string for JSON-like storage
        df['approval_date'] = pd.to_datetime(df['approval_date']).dt.strftime('%Y-%m-%d').replace({pd.NaT: None})
    return df.to_dict('records')

@pytest.fixture
def mock_ssm_with_changes():
    '''Mocks SessionStateManager with sample design change data.'''
    ssm = MagicMock()
    mock_data = [
        {"id": "DCR-001", "description": "Initial change", "approval_status": "Approved"},
        {"id": "DCR-002", "description": "Second change", "approval_status": "Pending"},
    ]
    ssm.get_data.return_value = mock_data
    return ssm

def test_load_design_changes(mock_ssm_with_changes):
    '''Tests that the data is correctly loaded into a DataFrame.'''
    df = process_design_changes(mock_ssm_with_changes)
    assert not df.empty
    assert len(df) == 2
    assert "DCR-001" in df['id'].values
    assert df.columns.tolist() == ["id", "description", "approval_status"]

def test_load_empty_design_changes():
    '''Tests handling of an empty list of changes.'''
    ssm = MagicMock()
    ssm.get_data.return_value = []
    df = process_design_changes(ssm)
    assert df.empty

def test_save_design_changes():
    '''Tests the conversion from an edited DataFrame back to a list of dicts.'''
    edited_df = pd.DataFrame([
        {"id": "DCR-001", "description": "Updated change", "approval_status": "Approved"},
        {"id": "DCR-003", "description": "New change", "approval_status": "Pending"},
    ])

    saved_data = save_design_changes(edited_df)
    assert isinstance(saved_data, list)
    assert len(saved_data) == 2
    assert saved_data[0]['description'] == "Updated change"
    assert saved_data[1]['id'] == "DCR-003"
"""
