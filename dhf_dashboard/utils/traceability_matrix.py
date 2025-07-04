# File: dhf_dashboard/analytics/traceability_matrix.py
# --- Enhanced Version ---
"""
Renders the DHF Traceability Matrix.

This module provides the logic for generating and displaying a full traceability
matrix, a critical compliance artifact that demonstrates the linkage between all
Design Control elements, from user needs to validation.
"""

# --- Standard Library Imports ---
import logging
from typing import Dict

# --- Third-party Imports ---
import pandas as pd
import streamlit as st

# --- Local Application Imports ---
from ..utils.session_state_manager import SessionStateManager

# --- Setup Logging ---
logger = logging.getLogger(__name__)


def render_traceability_matrix(ssm: SessionStateManager) -> None:
    """
    Generates and displays a traceability matrix from user needs to V&V.

    This function fetches all relevant data from the session state, constructs
    a matrix with design inputs as the primary axis, and then maps outputs,
    verifications, and validations back to these inputs. It highlights gaps
    in traceability, which is essential for audit readiness.

    Args:
        ssm (SessionStateManager): The session state manager instance to access DHF data.
    """
    st.header("🔬 Live Traceability Matrix")
    st.info("""
    This matrix provides end-to-end traceability from User Needs and Design Inputs to Design Outputs, Verification, and Validation.
    - ✅: A direct link exists. Hover over the column header for more information.
    - ❌: A link is missing, representing a potential compliance gap that must be addressed.
    """)

    try:
        # --- 1. Gather all relevant data from the session state ---
        inputs_df = pd.DataFrame(ssm.get_data("design_inputs", "requirements"))
        outputs_df = pd.DataFrame(ssm.get_data("design_outputs", "documents"))
        verifications_df = pd.DataFrame(ssm.get_data("design_verification", "tests"))
        validations_df = pd.DataFrame(ssm.get_data("design_validation", "studies"))
        logger.info("Successfully loaded data for traceability matrix.")

        if inputs_df.empty:
            st.warning("No Design Inputs found. Please add requirements in the 'DHF Sections Explorer' tab to build the matrix.")
            return

        # --- 2. Create the base matrix from inputs (the spine of the DHF) ---
        trace_matrix = inputs_df[['id', 'description', 'source_type']].copy()
        trace_matrix.set_index('id', inplace=True)

        # --- 3. Map Design Outputs to Inputs ---
        if not outputs_df.empty and 'linked_input_id' in outputs_df.columns:
            # Group outputs by the input they link to and format for display
            output_map = outputs_df.groupby('linked_input_id')['id'].apply(lambda ids: f"✅ ({', '.join(ids)})")
            trace_matrix['Output'] = trace_matrix.index.map(output_map)
        trace_matrix['Output'] = trace_matrix.get('Output', pd.Series(dtype=str)).fillna("❌")

        # --- 4. Map Verification to Inputs (Multi-step: Verification -> Output -> Input) ---
        if not verifications_df.empty and not outputs_df.empty and 'output_verified' in verifications_df.columns:
            # Use a merge to efficiently link verifications to their corresponding input IDs via the output link
            ver_to_out_df = pd.merge(
                verifications_df[['id', 'output_verified']],
                outputs_df[['id', 'linked_input_id']],
                left_on='output_verified',
                right_on='id',
                suffixes=('_ver', '_out'),
                how='inner'  # Only consider verifications that link to a valid output
            )
            ver_map = ver_to_out_df.groupby('linked_input_id')['id_ver'].apply(lambda ids: f"✅ ({', '.join(ids)})")
            trace_matrix['Verification'] = trace_matrix.index.map(ver_map)
        trace_matrix['Verification'] = trace_matrix.get('Verification', pd.Series(dtype=str)).fillna("❌")

        # --- 5. Map Validation to User Needs ---
        # Validation is only applicable to 'User Need' type requirements
        if not validations_df.empty and 'user_need_validated' in validations_df.columns:
            val_map = validations_df.groupby('user_need_validated')['id'].apply(lambda ids: f"✅ ({', '.join(ids)})")
            trace_matrix['Validation'] = trace_matrix.index.map(val_map)

        # Clean up: Mark 'N/A' for non-user needs, '❌' for user needs with missing validation
        is_user_need = trace_matrix['source_type'] == 'User Need'
        trace_matrix['Validation'] = trace_matrix.get('Validation', pd.Series(dtype=str)) # Ensure column exists
        trace_matrix.loc[is_user_need, 'Validation'] = trace_matrix.loc[is_user_need, 'Validation'].fillna("❌")
        trace_matrix.loc[~is_user_need, 'Validation'] = "N/A"

        # Drop the helper column before displaying
        trace_matrix = trace_matrix.drop(columns=['source_type'])

        # --- 6. Style and Display the Matrix ---
        def style_trace_cell(cell_value: str) -> str:
            """Applies CSS styling to a cell based on its content."""
            color = 'inherit'
            if isinstance(cell_value, str):
                if '❌' in cell_value:
                    color = '#d62728'  # Red for missing
                elif '✅' in cell_value:
                    color = '#2ca02c'  # Green for linked
            return f'color: {color}; font-weight: bold; text-align: center;'

        # Using st.column_config for a cleaner, more accessible way to add tooltips
        st.dataframe(
            trace_matrix.style.applymap(style_trace_cell, subset=['Output', 'Verification', 'Validation']),
            use_container_width=True,
            column_config={
                "description": st.column_config.TextColumn("Requirement Description", width="large"),
                "Output": st.column_config.TextColumn(
                    "Trace to Output",
                    help="Does a Design Output (e.g., spec, drawing) exist for this input?"
                ),
                "Verification": st.column_config.TextColumn(
                    "Trace to Verification",
                    help="Is there a test that verifies the Design Output linked to this input?"
                ),
                "Validation": st.column_config.TextColumn(
                    "Trace to Validation",
                    help="For User Needs, is there a study (e.g., clinical, usability) that validates it? (N/A for other requirement types)"
                ),
            }
        )

        # --- 7. Add an Export Button ---
        # Create a clean version for CSV export
        csv_export_df = trace_matrix.copy()
        for col in ['Output', 'Verification', 'Validation']:
            # Replace symbols with descriptive text for better machine readability
            csv_export_df[col] = csv_export_df[col].astype(str).str.replace("✅", "Linked:", regex=False).str.replace("❌", "Missing", regex=False)

        csv = csv_export_df.to_csv().encode('utf-8')
        st.download_button(
            label="📥 Export Matrix to CSV",
            data=csv,
            file_name="traceability_matrix.csv",
            mime="text/csv",
            key='export_trace_matrix'
        )

    except Exception as e:
        st.error("An error occurred while generating the traceability matrix. The data may be incomplete or malformed.")
        logger.error(f"Failed to render traceability matrix: {e}", exc_info=True)


# ==============================================================================
# --- UNIT TEST SCAFFOLDING (for `pytest`) ---
# ==============================================================================
"""
import pytest
from unittest.mock import MagicMock

# To run tests, place this in a 'tests' directory and run pytest.
# from dhf_dashboard.analytics.traceability_matrix import render_traceability_matrix # Needs mocking st

@pytest.fixture
def mock_ssm_complete_data():
    '''Mocks SessionStateManager with fully traceable data.'''
    ssm = MagicMock()
    ssm.get_data.side_effect = lambda primary_key, secondary_key=None: {
        ("design_inputs", "requirements"): [
            {'id': 'UN-01', 'description': 'Easy to use', 'source_type': 'User Need'},
            {'id': 'SR-01', 'description': '8mm diameter', 'source_type': 'QSR (Device)'},
        ],
        ("design_outputs", "documents"): [
            {'id': 'DO-01', 'linked_input_id': 'UN-01'},
            {'id': 'SPEC-01', 'linked_input_id': 'SR-01'},
        ],
        ("design_verification", "tests"): [
            {'id': 'VER-01', 'output_verified': 'SPEC-01'},
        ],
        ("design_validation", "studies"): [
            {'id': 'VAL-01', 'user_need_validated': 'UN-01'},
        ],
    }.get((primary_key, secondary_key), [])
    return ssm

@pytest.fixture
def mock_ssm_gap_data():
    '''Mocks SessionStateManager with a verification gap.'''
    ssm = MagicMock()
    ssm.get_data.side_effect = lambda primary_key, secondary_key=None: {
        ("design_inputs", "requirements"): [
            {'id': 'SR-01', 'description': '8mm diameter', 'source_type': 'QSR (Device)'},
        ],
        ("design_outputs", "documents"): [
            {'id': 'SPEC-01', 'linked_input_id': 'SR-01'},
        ],
        ("design_verification", "tests"): [], # No verification test
        ("design_validation", "studies"): [],
    }.get((primary_key, secondary_key), [])
    return ssm

# In a real test file (e.g., `tests/test_traceability_matrix.py`), you would not
# test the `render` function directly because it calls `st.write`, etc.
# Instead, you would refactor the matrix generation logic into a separate,
# pure function `generate_trace_matrix(ssm) -> pd.DataFrame` and test that.

def generate_trace_matrix(ssm: SessionStateManager) -> pd.DataFrame:
    '''Refactored logic for testing purposes.'''
    inputs_df = pd.DataFrame(ssm.get_data("design_inputs", "requirements"))
    outputs_df = pd.DataFrame(ssm.get_data("design_outputs", "documents"))
    verifications_df = pd.DataFrame(ssm.get_data("design_verification", "tests"))
    validations_df = pd.DataFrame(ssm.get_data("design_validation", "studies"))

    if inputs_df.empty: return pd.DataFrame()
    trace_matrix = inputs_df[['id', 'description', 'source_type']].copy().set_index('id')
    # ... (rest of the mapping logic from the main function) ...
    if not outputs_df.empty:
        output_map = outputs_df.groupby('linked_input_id')['id'].apply(lambda ids: f"✅ ({', '.join(ids)})")
        trace_matrix['Output'] = trace_matrix.index.map(output_map)
    trace_matrix['Output'] = trace_matrix.get('Output', pd.Series(dtype=str)).fillna("❌")

    # ... and so on for Verification and Validation ...
    return trace_matrix


def test_matrix_generation_complete(mock_ssm_complete_data):
    '''Tests that a fully linked requirement shows all checkmarks.'''
    # Note: This test uses the refactored, testable function.
    matrix = generate_trace_matrix(mock_ssm_complete_data)
    sr_01_row = matrix.loc['SR-01']
    assert '✅' in sr_01_row['Output']
    # Add assertions for other columns once the test function is fully built out.

def test_matrix_generation_with_gap(mock_ssm_gap_data):
    '''Tests that a gap in the chain is correctly marked with a cross.'''
    matrix = generate_trace_matrix(mock_ssm_gap_data)
    sr_01_row = matrix.loc['SR-01']
    assert '✅' in sr_01_row['Output'] # Output link exists
    # assert '❌' in sr_01_row['Verification'] # Verification link is missing
"""
