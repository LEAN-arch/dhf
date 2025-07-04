# File: dhf_dashboard/analytics/traceability_matrix.py
# --- Enhanced Version (Unabridged) ---
"""
Renders the DHF Traceability Matrix.

This module provides the logic for generating and displaying a full traceability
matrix, a critical compliance artifact that demonstrates the linkage between all
Design Control elements, from user needs to validation.
"""

# --- Standard Library Imports ---
import logging

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
    - ✅: A direct link exists. Hover over the column header for details.
    - ❌: A link is missing, representing a potential compliance gap.
    - N/A: The link is not applicable for this type of requirement.
    """)

    try:
        # --- 1. Gather all relevant data from the session state ---
        inputs_df = pd.DataFrame(ssm.get_data("design_inputs", "requirements"))
        outputs_df = pd.DataFrame(ssm.get_data("design_outputs", "documents"))
        verifications_df = pd.DataFrame(ssm.get_data("design_verification", "tests"))
        validations_df = pd.DataFrame(ssm.get_data("design_validation", "studies"))
        logger.info("Successfully loaded data for traceability matrix generation.")

        if inputs_df.empty:
            st.warning("No Design Inputs found. Please add requirements in the 'DHF Sections Explorer' tab to build the matrix.")
            return

        # --- 2. Generate the matrix using a testable helper function ---
        trace_matrix = generate_trace_matrix(inputs_df, outputs_df, verifications_df, validations_df)
        logger.info(f"Generated traceability matrix with {len(trace_matrix)} rows.")

        # --- 3. Style and Display the Matrix ---
        def style_trace_cell(cell_value: str) -> str:
            """Applies CSS styling to a cell based on its content."""
            color = 'inherit'
            if isinstance(cell_value, str):
                if '❌' in cell_value:
                    color = '#d62728'  # Red for missing
                elif '✅' in cell_value:
                    color = '#2ca02c'  # Green for linked
            return f'color: {color}; font-weight: bold; text-align: center;'

        st.dataframe(
            trace_matrix.style.applymap(style_trace_cell, subset=['Output', 'Verification', 'Validation']),
            use_container_width=True,
            column_config={
                "id": st.column_config.TextColumn("Requirement ID", width="medium"),
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

        # --- 4. Add an Export Button ---
        csv = trace_matrix_to_csv(trace_matrix)
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


def generate_trace_matrix(
    inputs_df: pd.DataFrame,
    outputs_df: pd.DataFrame,
    verifications_df: pd.DataFrame,
    validations_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Generates a traceability matrix DataFrame from DHF component DataFrames.
    This pure function is easily testable.

    Args:
        inputs_df: DataFrame of design inputs.
        outputs_df: DataFrame of design outputs.
        verifications_df: DataFrame of design verifications.
        validations_df: DataFrame of design validations.

    Returns:
        A styled DataFrame representing the traceability matrix.
    """
    if inputs_df.empty:
        return pd.DataFrame()

    trace_matrix = inputs_df[['id', 'description', 'source_type']].copy()
    
    # --- Map Design Outputs to Inputs ---
    if not outputs_df.empty and 'linked_input_id' in outputs_df.columns:
        output_map = outputs_df.groupby('linked_input_id')['id'].apply(lambda ids: f"✅ ({', '.join(ids)})")
        trace_matrix['Output'] = trace_matrix['id'].map(output_map)
    trace_matrix['Output'] = trace_matrix.get('Output', pd.Series(dtype=str)).fillna("❌")

    # --- Map Verification to Inputs (Multi-step: Verification -> Output -> Input) ---
    if not verifications_df.empty and not outputs_df.empty and 'output_verified' in verifications_df.columns:
        ver_to_out_df = pd.merge(
            verifications_df[['id', 'output_verified']],
            outputs_df[['id', 'linked_input_id']],
            left_on='output_verified', right_on='id',
            suffixes=('_ver', '_out'), how='inner'
        )
        ver_map = ver_to_out_df.groupby('linked_input_id')['id_ver'].apply(lambda ids: f"✅ ({', '.join(ids)})")
        trace_matrix['Verification'] = trace_matrix['id'].map(ver_map)
    trace_matrix['Verification'] = trace_matrix.get('Verification', pd.Series(dtype=str)).fillna("❌")

    # --- Map Validation to User Needs ---
    # Validation is only applicable to 'User Need' type requirements.
    if not validations_df.empty and 'user_need_validated' in validations_df.columns:
        val_map = validations_df.groupby('user_need_validated')['id'].apply(lambda ids: f"✅ ({', '.join(ids)})")
        trace_matrix['Validation'] = trace_matrix['id'].map(val_map)
    
    is_user_need = trace_matrix['source_type'] == 'User Need'
    trace_matrix['Validation'] = trace_matrix.get('Validation', pd.Series(dtype=str))
    trace_matrix.loc[is_user_need, 'Validation'] = trace_matrix.loc[is_user_need, 'Validation'].fillna("❌")
    trace_matrix.loc[~is_user_need, 'Validation'] = "N/A"

    return trace_matrix.drop(columns=['source_type'])

def trace_matrix_to_csv(trace_matrix_df: pd.DataFrame) -> bytes:
    """Prepares the trace matrix DataFrame for CSV export."""
    export_df = trace_matrix_df.copy()
    for col in ['Output', 'Verification', 'Validation']:
        if col in export_df.columns:
            export_df[col] = export_df[col].astype(str).str.replace("✅", "Linked:", regex=False).str.replace("❌", "Missing", regex=False)
    return export_df.to_csv(index=True).encode('utf-8')
