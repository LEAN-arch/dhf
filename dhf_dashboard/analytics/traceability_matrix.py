# --- Definitive, Corrected, and Unabridged Optimized Version ---
"""
Module for rendering the Design History File (DHF) Traceability Matrix.

This component provides a critical view for compliance, showing the linkage
between design inputs (requirements), design outputs (via verification), and
user needs (via validation).
"""

# --- Standard Library Imports ---
import logging
from typing import Dict, List

# --- Third-party Imports ---
import pandas as pd
import streamlit as st

# --- Local Application Imports ---
from dhf_dashboard.utils.session_state_manager import SessionStateManager

# --- Setup Logging ---
logger = logging.getLogger(__name__)


def style_trace_cell(val: str) -> str:
    """Applies CSS styling to a cell in the traceability matrix DataFrame."""
    if '✅' in str(val):
        return 'background-color: #eaf5ea; color: #2a633a; font-weight: bold; text-align: center;'
    elif '🔵' in str(val):
        return 'background-color: #e9f5ff; color: #0056b3; font-weight: bold; text-align: center;'
    return 'background-color: #f8f9fa; text-align: center;'


@st.cache_data
def generate_traceability_data(
    requirements: List[Dict],
    verifications: List[Dict],
    validations: List[Dict]
) -> pd.DataFrame:
    """
    Loads, merges, and pivots data to create the traceability matrix.
    This expensive data processing step is cached for performance.

    Returns:
        pd.DataFrame: A DataFrame representing the traceability matrix, or an
                      empty DataFrame if source data is missing.
    """
    logger.info("Generating traceability matrix data...")
    if not requirements:
        return pd.DataFrame()

    reqs_df = pd.DataFrame(requirements)
    ver_df = pd.DataFrame(verifications)
    val_df = pd.DataFrame(validations)

    # --- Verification Trace ---
    # Merge requirements with verification tests that trace to them
    ver_trace_df = pd.DataFrame()
    if not ver_df.empty and 'input_verified_id' in ver_df.columns:
        ver_trace_df = pd.merge(
            reqs_df, ver_df,
            left_on='id', right_on='input_verified_id',
            how='left', suffixes=('_req', '_ver')
        )
        ver_trace_df['trace_link'] = ver_trace_df.apply(
            lambda row: '✅' if pd.notna(row['id_ver']) and not row['is_risk_control'] else
                        '🔵' if pd.notna(row['id_ver']) and row['is_risk_control'] else '',
            axis=1
        )
    else:
        ver_trace_df = reqs_df.copy()
        ver_trace_df['id_ver'] = None
        ver_trace_df['trace_link'] = ''

    # --- Validation Trace ---
    # This block is now robust against empty validation data.
    full_trace_df = pd.DataFrame()
    if not val_df.empty and 'user_need_validated' in val_df.columns and 'id' in val_df.columns:
        full_trace_df = pd.merge(
            ver_trace_df, val_df,
            left_on='id_req', right_on='user_need_validated',
            how='left', suffixes=('', '_val')
        )
    else:
        # FIX: Ensure DataFrame schema is consistent even if val_df is empty.
        # Create a copy and manually add the columns that the merge would have created.
        full_trace_df = ver_trace_df.copy()
        full_trace_df['id_val'] = None # This is the critical missing column.

    # Now, 'id_val' is guaranteed to exist in full_trace_df.
    # The apply function can safely access it.
    full_trace_df['trace_link'] = full_trace_df.apply(
        lambda row: '✅' if pd.notna(row['id_val']) else row['trace_link'],
        axis=1
    )
    # Combine test/study IDs into a single column for pivoting
    full_trace_df['test_id'] = full_trace_df['id_ver'].fillna(full_trace_df['id_val'])

    # --- Pivot to create the matrix ---
    if 'test_id' in full_trace_df.columns and not full_trace_df['test_id'].dropna().empty:
        matrix_df = full_trace_df.pivot_table(
            index=['id_req', 'description'],
            columns='test_id',
            values='trace_link',
            aggfunc='first'
        ).fillna('')
        matrix_df.index.names = ['Requirement ID', 'Description']
        logger.info(f"Generated traceability matrix with {len(matrix_df)} rows.")
        return matrix_df
    
    # Fallback for when there are no tests/studies at all
    else:
        matrix_df = reqs_df[['id', 'description']].set_index(['id', 'description'])
        matrix_df.index.names = ['Requirement ID', 'Description']
        logger.info("Generated traceability matrix with requirements but no test columns.")
        return matrix_df


def render_traceability_matrix(ssm: SessionStateManager):
    """
    Renders the full Traceability Matrix component.
    """
    st.header("Requirement Traceability Matrix")
    st.markdown("This matrix provides end-to-end traceability from **User Needs** and **Requirements** (rows) to the **Verification** and **Validation** activities (columns) that satisfy them. This is a critical artifact for regulatory submissions and internal quality audits.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.success("✅ **Verification/Validation Link:** Confirms a design input is met.")
    with col2:
        st.info("🔵 **Risk Control Link:** Confirms a specific risk control measure is effective.")
    st.divider()

    try:
        # Call the cached data generation function
        styled_matrix_df = generate_traceability_data(
            ssm.get_data("design_inputs", "requirements"),
            ssm.get_data("design_verification", "tests"),
            ssm.get_data("design_validation", "studies")
        )
        
        if not styled_matrix_df.empty:
            test_columns = [col for col in styled_matrix_df.columns]
            
            # Use .style.map() for modern pandas compatibility.
            st.dataframe(
                styled_matrix_df.style.map(
                    style_trace_cell,
                    subset=test_columns
                ),
                use_container_width=True,
                height=max(300, len(styled_matrix_df) * 40) # Dynamically adjust height
            )
        else:
            st.warning("No requirements data found. Cannot generate traceability matrix.", icon="⚠️")

    except Exception as e:
        st.error("An error occurred while generating the traceability matrix.", icon="🚨")
        logger.error(f"Error in render_traceability_matrix: {e}", exc_info=True)
