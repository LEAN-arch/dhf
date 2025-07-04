# --- Definitive, Corrected, and Unabridged Optimized Version ---
"""
Module for rendering the Design History File (DHF) Traceability Matrix.

This component provides a critical view for compliance, showing the linkage
between design inputs (requirements), design outputs (via verification), and
user needs (via validation). This version is hardened against data-dependent
schema errors.
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
    This expensive data processing step is cached for performance and is robust
    against missing verification or validation data.

    Returns:
        pd.DataFrame: A DataFrame representing the traceability matrix, or an
                      empty DataFrame if source data is missing.
    """
    logger.info("Generating traceability matrix data...")
    if not requirements:
        return pd.DataFrame()

    reqs_df = pd.DataFrame(requirements)[['id', 'description', 'is_risk_control']]
    ver_df = pd.DataFrame(verifications)
    val_df = pd.DataFrame(validations)

    # --- FIX: The entire data shaping logic is re-architected for robustness ---
    # We will create two separate trace DataFrames and then merge them.

    # 1. Create Verification Trace
    ver_trace = pd.DataFrame()
    if not ver_df.empty and 'input_verified_id' in ver_df.columns:
        # Link requirements to their verification tests
        ver_trace = pd.merge(
            reqs_df,
            ver_df[['id', 'input_verified_id']],
            left_on='id',
            right_on='input_verified_id',
            how='inner' # Only keep requirements that have a verification
        )
        ver_trace = ver_trace[['id_x', 'description', 'is_risk_control', 'id_y']]
        ver_trace.columns = ['req_id', 'req_desc', 'is_risk_control', 'test_id']
        ver_trace['trace_link'] = ver_trace['is_risk_control'].apply(lambda x: '🔵' if x else '✅')

    # 2. Create Validation Trace
    val_trace = pd.DataFrame()
    if not val_df.empty and 'user_need_validated' in val_df.columns:
        # Link requirements (specifically user needs) to their validation studies
        val_trace = pd.merge(
            reqs_df,
            val_df[['id', 'user_need_validated']],
            left_on='id',
            right_on='user_need_validated',
            how='inner'
        )
        val_trace = val_trace[['id_x', 'description', 'is_risk_control', 'id_y']]
        val_trace.columns = ['req_id', 'req_desc', 'is_risk_control', 'test_id']
        val_trace['trace_link'] = '✅' # Validation is always a standard check mark

    # 3. Combine Traces
    # Concatenate the two trace types into a single long-form DataFrame
    if not ver_trace.empty and not val_trace.empty:
        long_form_trace = pd.concat([ver_trace, val_trace], ignore_index=True)
    elif not ver_trace.empty:
        long_form_trace = ver_trace
    elif not val_trace.empty:
        long_form_trace = val_trace
    else:
        # If there are no links at all, just return the requirements list
        matrix_df = reqs_df.set_index(['id', 'description'])
        matrix_df.index.names = ['Requirement ID', 'Description']
        return matrix_df

    # 4. Pivot to create the final matrix
    # This is now safe because the schema is consistent.
    matrix_df = long_form_trace.pivot_table(
        index=['req_id', 'req_desc'],
        columns='test_id',
        values='trace_link',
        aggfunc='first'
    ).fillna('')
    matrix_df.index.names = ['Requirement ID', 'Description']
    
    # Add back any requirements that have no links at all
    full_matrix = matrix_df.reindex(pd.MultiIndex.from_frame(reqs_df[['id', 'description']])).fillna('')
    
    logger.info(f"Generated traceability matrix with {len(full_matrix)} rows.")
    return full_matrix


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
