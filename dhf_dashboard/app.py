# --- Definitive, Corrected, and Unabridged Enhanced Version ---
"""
Main application entry point for the DHF Command Center.

This Streamlit application serves as a comprehensive dashboard for managing and
visualizing a Design History File (DHF) for a medical device, specifically a
combination product. It orchestrates various modules to display project health,
explore DHF sections, run advanced analytics, and provide educational and
predictive machine learning content on Quality Engineering and regulatory compliance.
"""

# --- Standard Library Imports ---
import logging
import os
import sys
import copy
from datetime import timedelta
from typing import Any, Dict, List, Tuple
import hashlib # For deterministic seeding

# --- Third-party Imports ---
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scipy import stats
import matplotlib.pyplot as plt

# --- Robust Path Correction Block ---
# This ensures that the application can find its own modules when run as a script.
try:
    current_file_path = os.path.abspath(__file__)
    project_root = os.path.dirname(os.path.dirname(current_file_path))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
except Exception as e:
    # Use st.warning for non-blocking path issues, critical error is too severe
    st.warning(f"Could not adjust system path. Module imports may fail. Error: {e}")
# --- End of Path Correction Block ---

# --- Local Application Imports (with error handling) ---
try:
    from dhf_dashboard.analytics.action_item_tracker import render_action_item_tracker
    from dhf_dashboard.analytics.traceability_matrix import render_traceability_matrix
    from dhf_dashboard.dhf_sections import (
        design_changes, design_inputs, design_outputs, design_plan, design_reviews,
        design_risk_management, design_transfer, design_validation,
        design_verification, human_factors
    )
    from dhf_dashboard.utils.critical_path_utils import find_critical_path
    from dhf_dashboard.utils.plot_utils import (
        _RISK_CONFIG,
        create_action_item_chart, create_progress_donut, create_risk_profile_chart)
    from dhf_dashboard.utils.session_state_manager import SessionStateManager
except ImportError as e:
    st.error(f"Fatal Error: A required local module could not be imported: {e}. "
             "Please ensure the application is run from the correct directory and all submodules exist.")
    logging.critical(f"Fatal module import error: {e}", exc_info=True)
    st.stop()


# --- Setup Logging ---
# Consolidated logging configuration to a single, definitive block.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    # Force setup even if already configured by a library
    force=True
)
logger = logging.getLogger(__name__)

# --- Module-Level Constants ---
# Centralizes page navigation logic for the DHF Explorer.
DHF_EXPLORER_PAGES = {
    "1. Design Plan": design_plan.render_design_plan,
    "2. Risk Management": design_risk_management.render_design_risk_management,
    "3. Human Factors": human_factors.render_human_factors,
    "4. Design Inputs": design_inputs.render_design_inputs,
    "5. Design Outputs": design_outputs.render_design_outputs,
    "6. Design Reviews": design_reviews.render_design_reviews,
    "7. Design Verification": design_verification.render_design_verification,
    "8. Design Validation": design_validation.render_design_validation,
    "9. Design Transfer": design_transfer.render_design_transfer,
    "10. Design Changes": design_changes.render_design_changes
}

# ==============================================================================
# --- DATA PRE-PROCESSING & CACHING ---
# ==============================================================================

@st.cache_data
def preprocess_task_data(tasks_data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Processes raw task data into a DataFrame ready for Gantt chart plotting.
    This expensive operation is cached to improve app performance.
    """
    if not tasks_data:
        logger.warning("Project management tasks data is empty during preprocessing.")
        return pd.DataFrame()

    tasks_df = pd.DataFrame(tasks_data)
    tasks_df['start_date'] = pd.to_datetime(tasks_df['start_date'], errors='coerce')
    tasks_df['end_date'] = pd.to_datetime(tasks_df['end_date'], errors='coerce')
    tasks_df.dropna(subset=['start_date', 'end_date'], inplace=True)

    if tasks_df.empty:
        return pd.DataFrame()

    critical_path_ids = find_critical_path(tasks_df.copy())
    status_colors = {"Completed": "#2ca02c", "In Progress": "#1f77b4", "Not Started": "#7f7f7f", "At Risk": "#d62728"}
    tasks_df['color'] = tasks_df['status'].map(status_colors).fillna('#7f7f7f')
    tasks_df['is_critical'] = tasks_df['id'].isin(critical_path_ids)
    tasks_df['line_color'] = np.where(tasks_df['is_critical'], 'red', '#FFFFFF')
    tasks_df['line_width'] = np.where(tasks_df['is_critical'], 4, 0)

    # OPTIMIZATION: Replaced slow .apply() with fast, vectorized string operations.
    tasks_df['display_text'] = "<b>" + tasks_df['name'].fillna('').astype(str) + "</b> (" + \
                               tasks_df['completion_pct'].fillna(0).astype(int).astype(str) + "%)"
    return tasks_df

@st.cache_data
def get_cached_df(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """Generic function to cache the creation of DataFrames from lists of dicts."""
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


# ==============================================================================
# --- DASHBOARD DEEP-DIVE COMPONENT FUNCTIONS ---
# ==============================================================================

# OPTIMIZATION: Added docs_by_phase parameter to avoid re-calculating in a loop.
def render_dhf_completeness_panel(ssm: SessionStateManager, tasks_df: pd.DataFrame, docs_by_phase: Dict[str, pd.DataFrame]) -> None:
    """
    Renders the DHF completeness and gate readiness panel.
    Displays DHF phases as subheaders and a project timeline Gantt chart.
    """
    st.subheader("1. DHF Completeness & Gate Readiness")
    st.markdown("Monitor the flow of Design Controls from inputs to outputs, including cross-functional sign-offs and DHF document status.")

    try:
        tasks_raw = ssm.get_data("project_management", "tasks")

        if not tasks_raw:
            st.warning("No project management tasks found.")
            return

        for task in tasks_raw:
            task_name = task.get('name', 'N/A')
            st.subheader(f"Phase: {task_name}")
            st.caption(f"Status: {task.get('status', 'N/A')} - {task.get('completion_pct', 0)}% Complete")

            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown("**Associated DHF Documents:**")
                # OPTIMIZATION: Use the pre-grouped dictionary for an O(1) lookup.
                phase_docs = docs_by_phase.get(task_name)
                if phase_docs is not None and not phase_docs.empty:
                    st.dataframe(phase_docs[['id', 'title', 'status']], use_container_width=True, hide_index=True)
                else:
                    st.caption("No documents for this phase yet.")
            with col2:
                st.markdown("**Cross-Functional Sign-offs:**")
                sign_offs = task.get('sign_offs', {})
                if isinstance(sign_offs, dict) and sign_offs:
                    for team, status in sign_offs.items():
                        color = "green" if status == "✅" else "orange" if status == "In Progress" else "grey"
                        st.markdown(f"- **{team}:** <span style='color:{color};'>{status}</span>", unsafe_allow_html=True)
                else:
                    st.caption("No sign-off data for this phase.")
            st.divider()

        st.markdown("---")
        st.subheader("Project Phase Timeline (Gantt Chart)")
        if not tasks_df.empty:
            gantt_fig = px.timeline(
                tasks_df, x_start="start_date", x_end="end_date", y="name",
                color="color", color_discrete_map="identity",
                title="<b>Project Timeline and Critical Path</b>",
                hover_name="name", custom_data=['status', 'completion_pct']
            )
            gantt_fig.update_traces(
                text=tasks_df['display_text'], textposition='inside', insidetextanchor='middle',
                marker_line_color=tasks_df['line_color'], marker_line_width=tasks_df['line_width'],
                hovertemplate="<b>%{hover_name}</b><br>Status: %{customdata[0]}<br>Complete: %{customdata[1]}%<extra></extra>"
            )
            gantt_fig.update_layout(
                showlegend=False, title_x=0.5, xaxis_title="Date", yaxis_title="DHF Phase", height=400,
                yaxis_categoryorder='array', yaxis_categoryarray=tasks_df.sort_values("start_date", ascending=False)["name"].tolist()
            )
            st.plotly_chart(gantt_fig, use_container_width=True)
            legend_html = """
            <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin-top: 15px; font-size: 0.9em;">
                <span><span style="display:inline-block; width:15px; height:15px; background-color:#2ca02c; margin-right: 5px; vertical-align: middle;"></span>Completed</span>
                <span><span style="display:inline-block; width:15px; height:15px; background-color:#1f77b4; margin-right: 5px; vertical-align: middle;"></span>In Progress</span>
                <span><span style="display:inline-block; width:15px; height:15px; background-color:#d62728; margin-right: 5px; vertical-align: middle;"></span>At Risk</span>
                <span><span style="display:inline-block; width:15px; height:15px; background-color:#7f7f7f; margin-right: 5px; vertical-align: middle;"></span>Not Started</span>
                <span><span style="display:inline-block; width:11px; height:11px; border: 2px solid red; margin-right: 5px; vertical-align: middle;"></span>On Critical Path</span>
            </div>
            """
            st.markdown(legend_html, unsafe_allow_html=True)
    except Exception as e:
        st.error("Could not render DHF Completeness Panel. Data may be missing or malformed.")
        logger.error(f"Error in render_dhf_completeness_panel: {e}", exc_info=True)

def render_risk_and_fmea_dashboard(ssm: SessionStateManager) -> None:
    """
    Renders the risk analysis dashboard, including a Sankey plot for overall
    risk flow and advanced, interactive Risk Matrix Bubble Charts for FMEA analysis.
    """
    st.subheader("2. DHF Risk Artifacts (ISO 14971, FMEA)")
    st.markdown("Analyze the project's risk profile via the Risk Mitigation Flow and Failure Mode and Effects Analysis (FMEA) highlights.")
    
    risk_tabs = st.tabs(["Risk Mitigation Flow (System Level)", "dFMEA Risk Matrix", "pFMEA Risk Matrix"])
    with risk_tabs[0]:
        try:
            hazards_data = ssm.get_data("risk_management_file", "hazards")
            if not hazards_data:
                st.warning("No hazard analysis data available.")
                return
            df = get_cached_df(hazards_data)
            
            risk_config = _RISK_CONFIG
            get_level = lambda s, o: risk_config['levels'].get((s, o), 'High')
            df['initial_level'] = df.apply(lambda x: get_level(x.get('initial_S'), x.get('initial_O')), axis=1)
            df['final_level'] = df.apply(lambda x: get_level(x.get('final_S'), x.get('final_O')), axis=1)

            all_nodes = [f"Initial {level}" for level in risk_config['order']] + [f"Residual {level}" for level in risk_config['order']]
            node_map = {name: i for i, name in enumerate(all_nodes)}
            node_colors = [risk_config['colors'][name.split(' ')[1]] for name in all_nodes]
            
            links = df.groupby(['initial_level', 'final_level', 'hazard_id']).size().reset_index(name='count')
            sankey_data = links.groupby(['initial_level', 'final_level']).agg(count=('count', 'sum'), hazards=('hazard_id', lambda x: ', '.join(x))).reset_index()

            sankey_fig = go.Figure(data=[go.Sankey(
                node=dict(pad=15, thickness=20, line=dict(color="black", width=0.5), label=all_nodes, color=node_colors),
                link=dict(
                    source=[node_map.get(f"Initial {row['initial_level']}") for _, row in sankey_data.iterrows()],
                    target=[node_map.get(f"Residual {row['final_level']}") for _, row in sankey_data.iterrows()],
                    value=[row['count'] for _, row in sankey_data.iterrows()],
                    color=[risk_config['colors'][row['final_level']] for _, row in sankey_data.iterrows()],
                    customdata=[f"<b>{row['count']} risk(s)</b> moved from {row['initial_level']} to {row['final_level']}:<br>{row['hazards']}" for _, row in sankey_data.iterrows()],
                    hovertemplate='%{customdata}<extra></extra>'
                ))])
            sankey_fig.update_layout(title_text="<b>Risk Mitigation Flow: Initial vs. Residual State</b>", font_size=12, height=500, title_x=0.5)
            st.plotly_chart(sankey_fig, use_container_width=True)
        except Exception as e:
            st.error("Could not render Risk Mitigation Flow. Data may be missing or malformed.")
            logger.error(f"Error in render_risk_and_fmea_dashboard (Sankey): {e}", exc_info=True)


    def render_fmea_risk_matrix_plot(fmea_data: List[Dict[str, Any]], title: str) -> None:
        """
        Renders an advanced, interactive Risk Matrix Bubble Chart for FMEA data.
        """
        st.info(f"""
        **How to read this chart:** This is not a simple chart. It's a professional risk analysis tool.
        - **X-axis (Severity):** How bad is the failure? Further right is worse.
        - **Y-axis (Occurrence):** How often does it happen? Higher up is more frequent.
        - **Bubble Size (RPN):** Overall risk score. Bigger bubbles have higher RPN.
        - **Bubble Color (Detection):** How easy is it to catch? **Bright red bubbles are hard to detect** and are particularly dangerous.
        
        **Your Priority:** Address items in the **top-right red zone** first. Then, investigate any large, bright red bubbles regardless of their position.
        """, icon="💡")

        try:
            if not fmea_data:
                st.warning(f"No {title} data available.")
                return

            df = pd.DataFrame(fmea_data)
            df['RPN'] = df['S'] * df['O'] * df['D']
            
            # Use deterministic seeding for jitter to prevent flickering UI
            rng = np.random.default_rng(0)
            df['S_jitter'] = df['S'] + rng.uniform(-0.1, 0.1, len(df))
            df['O_jitter'] = df['O'] + rng.uniform(-0.1, 0.1, len(df))

            fig = go.Figure()

            fig.add_shape(type="rect", x0=0.5, y0=0.5, x1=5.5, y1=5.5, line=dict(width=0), fillcolor='rgba(44, 160, 44, 0.1)', layer='below') 
            fig.add_shape(type="rect", x0=2.5, y0=2.5, x1=5.5, y1=5.5, line=dict(width=0), fillcolor='rgba(255, 215, 0, 0.15)', layer='below') 
            fig.add_shape(type="rect", x0=3.5, y0=3.5, x1=5.5, y1=5.5, line=dict(width=0), fillcolor='rgba(255, 127, 14, 0.15)', layer='below')
            fig.add_shape(type="rect", x0=4.5, y0=4.5, x1=5.5, y1=5.5, line=dict(width=0), fillcolor='rgba(214, 39, 40, 0.15)', layer='below')

            fig.add_trace(go.Scatter(
                x=df['S_jitter'], y=df['O_jitter'],
                mode='markers+text', text=df['id'], textposition='top center', textfont=dict(size=9, color='#444'),
                marker=dict(
                    size=df['RPN'], sizemode='area', sizeref=2. * max(df['RPN']) / (40.**2), sizemin=4,
                    color=df['D'], colorscale='YlOrRd', colorbar=dict(title='Detection'),
                    showscale=True, line_width=1, line_color='black'
                ),
                customdata=df[['failure_mode', 'potential_effect', 'S', 'O', 'D', 'RPN', 'mitigation']],
                hovertemplate="""<b>%{customdata[0]}</b><br>--------------------------------<br><b>Effect:</b> %{customdata[1]}<br><b>S:</b> %{customdata[2]} | <b>O:</b> %{customdata[3]} | <b>D:</b> %{customdata[4]}<br><b>RPN: %{customdata[5]}</b><br><b>Mitigation:</b> %{customdata[6]}<extra></extra>"""
            ))
            
            fig.update_layout(
                title=f"<b>{title} Risk Landscape</b>", xaxis_title="Severity (S)", yaxis_title="Occurrence (O)",
                xaxis=dict(range=[0.5, 5.5], tickvals=list(range(1, 6))), yaxis=dict(range=[0.5, 5.5], tickvals=list(range(1, 6))),
                height=600, title_x=0.5, showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        except (KeyError, TypeError) as e:
            st.error(f"Could not render {title} Risk Matrix. Data may be malformed or missing S, O, D columns.")
            logger.error(f"Error in render_fmea_risk_matrix_plot for {title}: {e}", exc_info=True)
    with risk_tabs[1]:
        render_fmea_risk_matrix_plot(ssm.get_data("risk_management_file", "dfmea"), "dFMEA")
    with risk_tabs[2]:
        render_fmea_risk_matrix_plot(ssm.get_data("risk_management_file", "pfmea"), "pFMEA")

def render_qbd_and_cgmp_panel(ssm: SessionStateManager) -> None:
    """Renders the Quality by Design and cGMP readiness panel."""
    st.subheader("3. DHF to Manufacturing Readiness")
    st.markdown("This section tracks key activities that bridge the design with a robust, manufacturable product, including Quality by Design (QbD) and CGMP compliance.")
    qbd_tabs = st.tabs(["Quality by Design (QbD) Linkages", "CGMP Readiness"])
    with qbd_tabs[0]:
        try:
            qbd_elements = ssm.get_data("quality_by_design", "elements")
            if not qbd_elements: st.warning("No Quality by Design elements have been defined.")
            else:
                for element in qbd_elements:
                    st.subheader(f"CQA: {element.get('cqa', 'N/A')}")
                    st.caption(f"(Links to Requirement: {element.get('links_to_req', 'N/A')})")
                    st.markdown(f"**Critical Material Attributes (CMAs):** `{' | '.join(element.get('cm_attributes', []))}`")
                    st.markdown(f"**Critical Process Parameters (CPPs):** `{' | '.join(element.get('cp_parameters', []))}`")
                    st.divider()
            st.info("💡 FTR (First-Time-Right) initiatives are driven by deeply understanding and controlling the CMAs and CPPs that affect the product's CQAs.", icon="💡")
        except Exception as e:
            st.error("Could not render QbD linkages."); logger.error(f"Error in render_qbd_and_cgmp_panel (QbD): {e}", exc_info=True)
    with qbd_tabs[1]:
        try:
            cgmp_data = ssm.get_data("quality_system", "cgmp_compliance")
            if not cgmp_data: st.warning("No CGMP compliance data available.")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Pilot Batch Record Review**")
                    brr = cgmp_data.get('batch_record_review', {})
                    total, passed = brr.get('total', 0), brr.get('passed', 0)
                    pass_rate = (passed / total) * 100 if total > 0 else 0
                    st.metric(f"Batch Pass Rate", f"{pass_rate:.1f}%", f"{passed}/{total} Passed")
                    st.progress(pass_rate / 100)
                with col2:
                    st.markdown("**Drug-Device Stability Studies**")
                    stability_df = get_cached_df(cgmp_data.get('stability_studies', []))
                    if not stability_df.empty: st.dataframe(stability_df, use_container_width=True, hide_index=True)
                    else: st.caption("No stability study data.")
            st.info("💡 For combination products, successful Design Transfer is contingent on passing stability studies and demonstrating a capable manufacturing process under CGMP.", icon="💡")
        except Exception as e:
            st.error("Could not render CGMP readiness."); logger.error(f"Error in render_qbd_and_cgmp_panel (CGMP): {e}", exc_info=True)


def render_audit_and_improvement_dashboard(ssm: SessionStateManager) -> None:
    """Renders the audit readiness and continuous improvement dashboard."""
    st.subheader("4. Audit & Continuous Improvement Readiness")
    st.markdown("A high-level assessment of QMS health and process efficiency to gauge readiness for audits and track improvement initiatives.")
    audit_tabs = st.tabs(["Audit Readiness Scorecard", "FTR & COPQ Dashboard"])
    with audit_tabs[0]:
        try:
            docs_df = get_cached_df(ssm.get_data("design_outputs", "documents"))
            doc_readiness = (len(docs_df[docs_df['status'] == 'Approved']) / len(docs_df)) * 100 if not docs_df.empty else 0
            capas_df = get_cached_df(ssm.get_data("quality_system", "capa_records"))
            open_capas = len(capas_df[capas_df['status'] == 'Open']) if not capas_df.empty else 0
            capa_score = max(0, 100 - (open_capas * 20))
            suppliers_df = get_cached_df(ssm.get_data("quality_system", "supplier_audits"))
            supplier_pass_rate = (len(suppliers_df[suppliers_df['status'] == 'Pass']) / len(suppliers_df)) * 100 if not suppliers_df.empty else 100
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("DHF Document Readiness", f"{doc_readiness:.1f}% Approved")
                st.progress(doc_readiness / 100)
            with col2:
                st.metric("Open CAPA Score", f"{int(capa_score)}/100", help=f"{open_capas} open CAPA(s). Score degrades with each open item.")
                st.progress(capa_score / 100)
            with col3:
                st.metric("Supplier Audit Pass Rate", f"{supplier_pass_rate:.1f}%")
                st.progress(supplier_pass_rate / 100)
            st.success("Bonus: Next mock internal audit scheduled for Q4 2025.")
        except Exception as e:
            st.error("Could not render Audit Readiness Scorecard."); logger.error(f"Error in render_audit_and_improvement_dashboard (Scorecard): {e}", exc_info=True)
    with audit_tabs[1]:
        try:
            improvements_df = get_cached_df(ssm.get_data("quality_system", "continuous_improvement"))
            spc_data = ssm.get_data("quality_system", "spc_data")
            st.info("This dashboard tracks First-Time-Right (FTR) rates and the associated Cost of Poor Quality (COPQ), demonstrating a commitment to proactive quality.")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**FTR & COPQ Trends**")
                if not improvements_df.empty:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=improvements_df['date'], y=improvements_df['ftr_rate'], name='FTR Rate (%)', yaxis='y1'))
                    fig.add_trace(go.Scatter(x=improvements_df['date'], y=improvements_df['copq_cost'], name='COPQ ($)', yaxis='y2', line=dict(color='red')))
                    fig.update_layout(height=300, margin=dict(l=10, r=10, t=40, b=10), yaxis=dict(title='FTR Rate (%)'), yaxis2=dict(title='COPQ ($)', overlaying='y', side='right'))
                    st.plotly_chart(fig, use_container_width=True)
                else: st.caption("No improvement data available for trending.")
            with col2:
                st.markdown("**Calculated Process Capability**")
                if spc_data and spc_data.get('measurements'):
                    meas = np.array(spc_data['measurements']); usl, lsl = spc_data['usl'], spc_data['lsl']
                    mu, sigma = meas.mean(), meas.std()
                    cpk = min((usl - mu) / (3 * sigma), (mu - lsl) / (3 * sigma)) if sigma > 0 else 0
                    st.metric("Process Capability (Cpk)", f"{cpk:.2f}", delta=f"{cpk-1.33:.2f} vs. target 1.33", delta_color="normal", help="A Cpk > 1.33 indicates a capable process. This is calculated live from SPC data.")
                else: st.metric("Process Capability (Cpk)", "N/A", help="SPC data missing.")
                st.caption("Increased Cpk from process optimization (DOE) directly reduces COPQ.")
        except Exception as e:
            st.error("Could not render FTR & COPQ Dashboard."); logger.error(f"Error in render_audit_and_improvement_dashboard (FTR/COPQ): {e}", exc_info=True)

# ==============================================================================
# --- TAB RENDERING FUNCTIONS ---
# ==============================================================================

def render_health_dashboard_tab(ssm: SessionStateManager, tasks_df: pd.DataFrame, docs_by_phase: Dict[str, pd.DataFrame]):
    """
    Renders the main DHF Health Dashboard tab, enhanced for executive-level
    at-a-glance assessment and deep-dive analysis.
    """
    st.header("Executive Health Summary")

    # --- Health Score & KHI Calculation ---
    schedule_score = 0
    if not tasks_df.empty:
        today = pd.Timestamp.now().floor('D') # Use a stable timestamp
        overdue_in_progress = tasks_df[(tasks_df['status'] == 'In Progress') & (tasks_df['end_date'] < today)]
        total_in_progress = tasks_df[tasks_df['status'] == 'In Progress']
        schedule_score = (1 - (len(overdue_in_progress) / len(total_in_progress))) * 100 if not total_in_progress.empty else 100

    hazards_df = get_cached_df(ssm.get_data("risk_management_file", "hazards")); risk_score = 0
    if not hazards_df.empty and all(c in hazards_df.columns for c in ['initial_S', 'initial_O', 'initial_D', 'final_S', 'final_O', 'final_D']):
        hazards_df['initial_rpn'] = hazards_df['initial_S'] * hazards_df['initial_O'] * hazards_df['initial_D']
        hazards_df['final_rpn'] = hazards_df['final_S'] * hazards_df['final_O'] * hazards_df['final_D']
        initial_rpn_sum = hazards_df['initial_rpn'].sum(); final_rpn_sum = hazards_df['final_rpn'].sum()
        risk_reduction_pct = ((initial_rpn_sum - final_rpn_sum) / initial_rpn_sum) * 100 if initial_rpn_sum > 0 else 100
        risk_score = max(0, risk_reduction_pct)

    reviews_data = ssm.get_data("design_reviews", "reviews")
    original_action_items = [item for r in reviews_data for item in r.get("action_items", [])]
    action_items_df = get_cached_df(original_action_items)

    execution_score = 100
    if not action_items_df.empty:
        open_items = action_items_df[action_items_df['status'] != 'Completed']
        if not open_items.empty:
            overdue_items_count = len(open_items[open_items['status'] == 'Overdue'])
            execution_score = (1 - (overdue_items_count / len(open_items))) * 100

    weights = {'schedule': 0.4, 'quality': 0.4, 'execution': 0.2}
    overall_health_score = (schedule_score * weights['schedule']) + (risk_score * weights['quality']) + (execution_score * weights['execution'])
    ver_tests_df = get_cached_df(ssm.get_data("design_verification", "tests")); val_studies_df = get_cached_df(ssm.get_data("design_validation", "studies"))
    total_vv = len(ver_tests_df) + len(val_studies_df); passed_vv = len(ver_tests_df[ver_tests_df['status'] == 'Completed']) + len(val_studies_df[val_studies_df['result'] == 'Pass'])
    vv_pass_rate = (passed_vv / total_vv) * 100 if total_vv > 0 else 0
    reqs_df = get_cached_df(ssm.get_data("design_inputs", "requirements")); ver_tests_with_links = ver_tests_df.dropna(subset=['input_verified_id'])['input_verified_id'].nunique()
    total_reqs = reqs_df['id'].nunique(); trace_coverage = (ver_tests_with_links / total_reqs) * 100 if total_reqs > 0 else 0
    capas_df = get_cached_df(ssm.get_data("quality_system", "capa_records")); open_capas_df = capas_df[capas_df['status'] == 'Open'] if not capas_df.empty else pd.DataFrame()
    critical_capas_count = len(open_capas_df)
    overdue_actions_count = len(action_items_df[action_items_df['status'] == 'Overdue']) if not action_items_df.empty else 0

    # --- Render Dashboard ---
    col1, col2 = st.columns([1.5, 2])
    with col1:
        fig = go.Figure(go.Indicator(
            mode = "gauge+number", value = overall_health_score, title = {'text': "<b>Overall Project Health Score</b>"},
            number = {'font': {'size': 48}}, domain = {'x': [0, 1], 'y': [0, 1]},
            gauge = {'axis': {'range': [None, 100]}, 'bar': {'color': "green" if overall_health_score > 80 else "orange" if overall_health_score > 60 else "red"},
                     'steps' : [{'range': [0, 60], 'color': "#fdecec"}, {'range': [60, 80], 'color': "#fef3e7"}, {'range': [80, 100], 'color': "#eaf5ea"}]}))
        fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20)); st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown("<br>", unsafe_allow_html=True); sub_col1, sub_col2, sub_col3 = st.columns(3)
        sub_col1.metric("Schedule Performance", f"{schedule_score:.0f}/100", help=f"Weighted at {weights['schedule']*100}%. Based on adherence of active tasks to their planned end dates.")
        sub_col2.metric("Quality & Risk Posture", f"{risk_score:.0f}/100", help=f"Weighted at {weights['quality']*100}%. Based on the percentage of initial RPN that has been mitigated.")
        sub_col3.metric("Execution & Compliance", f"{execution_score:.0f}/100", help=f"Weighted at {weights['execution']*100}%. Based on the ratio of overdue items to all open action items.")
        st.caption("The Overall Health Score is a weighted average of these three key performance domains.")
    st.divider()
    st.subheader("Key Health Indicators (KHIs)"); khi_col1, khi_col2, khi_col3, khi_col4 = st.columns(4)
    with khi_col1:
        st.metric(label="V&V Pass Rate", value=f"{vv_pass_rate:.1f}%", help="Percentage of all Verification and Validation protocols that are complete and passing."); st.progress(vv_pass_rate / 100)
    with khi_col2:
        st.metric(label="Traceability Coverage", value=f"{trace_coverage:.1f}%", help="Percentage of requirements that are linked to at least one verification test."); st.progress(trace_coverage / 100)
    with khi_col3:
        st.metric(label="Open CAPAs", value=critical_capas_count, delta=critical_capas_count, delta_color="inverse", help="Count of open CAPAs. Lower is better.")
    with khi_col4:
        st.metric(label="Overdue Action Items", value=overdue_actions_count, delta=overdue_actions_count, delta_color="inverse", help="Total number of action items from all design reviews that are past their due date.")
    st.divider()
    st.subheader("Action Item Health (Last 30 Days)")
    st.markdown("This chart shows the trend of open action items. A healthy project shows a downward or stable trend. A rising red area indicates a growing backlog of overdue work, which requires management attention.")

    @st.cache_data
    def generate_burndown_data(_reviews_data: Tuple, _action_items_data: Tuple):
        """
        Generates deterministic, cached burndown chart data from action items.
        - review/action data is passed as tuples of frozensets to be hashable for caching.
        - date simulation is seeded with item IDs for a stable, non-flickering UI.
        """
        if not _action_items_data:
            return pd.DataFrame()

        # Convert back to list of dicts for processing
        action_items_list = [dict(fs) for fs in _action_items_data]
        reviews_list = [dict(fs) for fs in _reviews_data]

        df = pd.DataFrame(action_items_list)
        for review in reviews_list:
            review_date = pd.to_datetime(review.get('date'))
            # Handle nested action items which are now frozensets of tuples
            action_items_in_review = [dict(item_fs) for item_fs in review.get("action_items", [])]
            for item in action_items_in_review:
                if 'id' in item:
                    df.loc[df['id'] == item['id'], 'review_date'] = review_date

        df['due_date'] = pd.to_datetime(df['due_date'], errors='coerce')
        df['created_date'] = pd.to_datetime(df.get('review_date'), errors='coerce')
        df.dropna(subset=['created_date', 'due_date', 'id'], inplace=True)

        # Add a small, deterministic offset to created_date
        def get_deterministic_offset(item_id):
            return int(hashlib.md5(str(item_id).encode()).hexdigest(), 16) % 3
        df['created_date'] += df['id'].apply(lambda x: pd.to_timedelta(get_deterministic_offset(x), unit='d'))

        df['completion_date'] = pd.NaT
        completed_mask = df['status'] == 'Completed'
        if completed_mask.any():
            completed_items = df.loc[completed_mask].copy()
            lifespan = (completed_items['due_date'] - completed_items['created_date']).dt.days.fillna(1).astype(int)
            lifespan = lifespan.apply(lambda d: max(1, d))
            
            # BUG FIX: Corrected the seeding function for ValueError
            def get_deterministic_completion(row):
                # 1. Generate the full 128-bit integer from the hash
                full_hash_int = int(hashlib.md5(str(row['id']).encode()).hexdigest(), 16)
                # 2. Constrain it to the valid 32-bit unsigned integer range for the seed
                seed_value = full_hash_int % (2**32)
                # 3. BEST PRACTICE: Use the modern, isolated Generator API
                rng = np.random.default_rng(seed_value)
                # 4. Use the generator to get a random integer
                # Note: .integers is exclusive of the high end, so add 1
                return rng.integers(1, row['lifespan'] + 1) if row['lifespan'] >= 1 else 1

            completed_items['lifespan'] = lifespan
            completion_days = completed_items.apply(get_deterministic_completion, axis=1)
            df.loc[completed_mask, 'completion_date'] = completed_items['created_date'] + pd.to_timedelta(completion_days, unit='d')

        today = pd.Timestamp.now().floor('D')
        date_range = pd.date_range(end=today, periods=30, freq='D')

        daily_counts = []
        for day in date_range:
            created_mask = df['created_date'] <= day
            completed_mask = (df['completion_date'].notna()) & (df['completion_date'] <= day)
            open_on_day_df = df[created_mask & ~completed_mask]
            
            if not open_on_day_df.empty:
                overdue_count = (open_on_day_df['due_date'] < day).sum()
                ontime_count = len(open_on_day_df) - overdue_count
            else:
                overdue_count = 0; ontime_count = 0
            daily_counts.append({'date': day, 'Overdue': overdue_count, 'On-Time': ontime_count})

        return pd.DataFrame(daily_counts)

    if original_action_items:
        # Convert data to hashable types for caching
        immutable_actions = tuple(frozenset(d.items()) for d in original_action_items)
        # Handle nested lists in reviews_data by making them hashable tuples
        immutable_reviews = tuple(frozenset(
            (k, tuple(frozenset(i.items()) for i in v) if isinstance(v, list) else v)
            for k, v in r.items()
        ) for r in reviews_data)

        burndown_df = generate_burndown_data(immutable_reviews, immutable_actions)

        if not burndown_df.empty:
            fig = px.area(burndown_df, x='date', y=['On-Time', 'Overdue'],
                          color_discrete_map={'On-Time': 'seagreen', 'Overdue': 'crimson'},
                          title="Trend of Open Action Items by Status",
                          labels={'value': 'Number of Open Items', 'date': 'Date', 'variable': 'Status'})
            fig.update_layout(height=350, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig, use_container_width=True)
        else:
             st.caption("No action item data to generate a burn-down chart.")
    else:
        st.caption("No action item data to generate a burn-down chart.")
    
    st.divider()
    st.header("Deep Dives")
    with st.expander("Expand to see Phase Gate Readiness & Timeline Details"):
        render_dhf_completeness_panel(ssm, tasks_df, docs_by_phase)
    with st.expander("Expand to see Risk & FMEA Details"):
        render_risk_and_fmea_dashboard(ssm)
    with st.expander("Expand to see QbD and Manufacturing Readiness Details"):
        render_qbd_and_cgmp_panel(ssm)
    with st.expander("Expand to see Audit & Continuous Improvement Details"):
        render_audit_and_improvement_dashboard(ssm)

def render_dhf_explorer_tab(ssm: SessionStateManager):
    """Renders the DHF Sections Explorer tab and its sidebar navigation."""
    st.header("🗂️ Design History File Explorer")
    st.markdown("Select a DHF section from the sidebar to view or edit its contents.")
    with st.sidebar:
        st.header("DHF Section Navigation")
        dhf_selection = st.radio("Select a section to edit:", DHF_EXPLORER_PAGES.keys(), key="sidebar_dhf_selection")
    st.divider()
    page_function = DHF_EXPLORER_PAGES[dhf_selection]
    page_function(ssm)

def render_advanced_analytics_tab(ssm: SessionStateManager):
    """Renders the Advanced Analytics tab."""
    st.header("🔬 Advanced Compliance & Project Analytics")
    analytics_tabs = st.tabs(["Traceability Matrix", "Action Item Tracker", "Project Task Editor"])
    with analytics_tabs[0]: render_traceability_matrix(ssm)
    with analytics_tabs[1]: render_action_item_tracker(ssm)
    with analytics_tabs[2]:
        st.subheader("Project Timeline and Task Editor")
        st.warning("Directly edit project timelines, statuses, and dependencies. Changes are saved automatically.", icon="⚠️")
        try:
            tasks_data_to_edit = ssm.get_data("project_management", "tasks")
            if not tasks_data_to_edit:
                st.info("No tasks to display or edit.")
                return

            tasks_df_to_edit = pd.DataFrame(tasks_data_to_edit)
            tasks_df_to_edit['start_date'] = pd.to_datetime(tasks_df_to_edit['start_date'], errors='coerce')
            tasks_df_to_edit['end_date'] = pd.to_datetime(tasks_df_to_edit['end_date'], errors='coerce')
            
            original_df = tasks_df_to_edit.copy()
            edited_df = st.data_editor(
                tasks_df_to_edit, key="main_task_editor", num_rows="dynamic", use_container_width=True,
                column_config={"start_date": st.column_config.DateColumn("Start Date", format="YYYY-MM-DD", required=True), "end_date": st.column_config.DateColumn("End Date", format="YYYY-MM-DD", required=True)})
            
            if not original_df.equals(edited_df):
                df_to_save = edited_df.copy()
                df_to_save['start_date'] = pd.to_datetime(df_to_save['start_date']).dt.strftime('%Y-%m-%d')
                df_to_save['end_date'] = pd.to_datetime(df_to_save['end_date']).dt.strftime('%Y-%m-%d')
                
                # Replace NaT representations with None for JSON compatibility
                df_to_save = df_to_save.replace({pd.NaT: None})

                ssm.update_data(df_to_save.to_dict('records'), "project_management", "tasks")
                st.toast("Project tasks updated! Rerunning...", icon="✅")
                st.rerun()
        except Exception as e: 
            st.error("Could not load the Project Task Editor.")
            logger.error(f"Error in task editor: {e}", exc_info=True)

def render_statistical_tools_tab(ssm: SessionStateManager):
    """Renders the Statistical Workbench tab with professionally enhanced tools."""
    st.header("📈 Statistical Workbench")
    st.info("Utilize this interactive workbench to apply rigorous statistical methods, moving from raw data to actionable, data-driven decisions.")
    try:
        import statsmodels.api as sm
        from statsmodels.formula.api import ols
        from scipy.stats import shapiro, mannwhitneyu, chi2_contingency, pearsonr
    except ImportError:
        st.error("This tab requires `statsmodels` and `scipy`. Please install them (`pip install statsmodels scipy`) to enable statistical tools.", icon="🚨"); return
    
    # --- EXTENDED: Added four new tools to the tab list ---
    tool_tabs = st.tabs([
        "Process Control (SPC)", "Hypothesis Testing (A/B Test)", "Pareto Analysis (FMEA)", "Design of Experiments (DOE)",
        "Gauge R&R (MSA)", "Chi-Squared Test", "Correlation Analysis", "Equivalence Test (TOST)"
    ])

    with tool_tabs[0]: # SPC
        st.subheader("Statistical Process Control (SPC) with Rule Checking")
        st.markdown("Monitor process stability by distinguishing natural variation from signals that require investigation.")
        with st.expander("The Purpose, Math Basis, Procedure, and Significance"):
            # --- EXPANDED EXPLANATION ---
            st.markdown("#### Purpose: Control and Monitor a Process")
            st.markdown("The primary purpose of SPC is to monitor a process over time to ensure it remains stable and predictable, operating within its natural limits. It helps distinguish between **common cause variation** (the natural, inherent 'noise' of a process) and **special cause variation** (unexpected, external factors that signal a process change or problem). By reacting only to special causes, we avoid over-adjusting the process and making things worse.")
            st.markdown("#### The Mathematical Basis: Mean and Standard Deviation")
            st.markdown("SPC charts are built upon fundamental statistics. For an Individuals and Moving Range (I-MR) chart or an X-bar chart:\n- **Centerline (CL):** This is the process average (mean, μ), representing the central tendency.\n- **Control Limits (UCL/LCL):** These are calculated as `μ ± 3σ` (the mean plus or minus three standard deviations, σ). Under the assumption of a normal distribution, approximately 99.73% of all common cause variation will fall within these limits. A point outside these limits is a strong signal of a special cause.")
            st.markdown("#### The Procedure: Charting and Rule Application")
            st.markdown("1.  **Data Collection:** Collect data from the process in time-ordered sequence.\n2.  **Calculation:** Calculate the mean (μ) and standard deviation (σ) from a stable period of the process.\n3.  **Plotting:** Plot the data points chronologically. Draw horizontal lines for the centerline, Upper Control Limit (UCL), and Lower Control Limit (LCL). Specification Limits (USL/LSL) are also often added to show the 'voice of the customer'.\n4.  **Rule Checking:** Programmatically apply a set of rules (like the Nelson Rules) to detect non-random patterns that indicate a process shift, even if no points are outside the control limits.")
            st.markdown("#### Significance of the Results: In-Control vs. Out-of-Control")
            st.markdown("- **In-Control (Stable):** No points are outside the control limits, and no non-random patterns are detected. The process is predictable. This is a prerequisite for calculating process capability (Cpk).\n- **Out-of-Control (Unstable):** One or more points are outside the control limits or a rule is violated. This indicates a special cause is present. The appropriate action is to **investigate the cause**, correct it, and prevent its recurrence. An out-of-control process is unpredictable, and its capability cannot be meaningfully assessed.")
        def check_spc_rules(data: np.ndarray, mu: float, sigma: float) -> List[str]:
            violations = []
            if np.any(data > mu + 3 * sigma) or np.any(data < mu - 3 * sigma): violations.append("Rule 1: Point(s) exist beyond ±3σ from the centerline.")
            for i in range(len(data) - 8):
                if all(data[i:i+9] > mu) or all(data[i:i+9] < mu):
                    violations.append("Rule 2: 9 consecutive points on one side of the centerline."); break
            return violations
        try:
            spc_data = ssm.get_data("quality_system", "spc_data")
            if spc_data and all(k in spc_data for k in ['measurements', 'target', 'usl', 'lsl']):
                meas = np.array(spc_data['measurements']); mu, sigma = meas.mean(), meas.std(); ucl, lcl = mu + 3 * sigma, mu - 3 * sigma
                violations = check_spc_rules(meas, mu, sigma)
                if violations:
                    st.error(f"**Process Status: UNSTABLE**\n\nViolations Detected:", icon="🚨")
                    for v in violations: st.markdown(f"- {v}")
                else: st.success("**Process Status: STABLE**\n\nNo common rule violations were detected.", icon="✅")
                fig = go.Figure()
                fig.add_trace(go.Scatter(y=meas, name='Measurements', mode='lines+markers', line=dict(color='#1f77b4')))
                fig.add_hline(y=spc_data['target'], line_dash="dash", line_color="green", annotation_text="Target")
                fig.add_hline(y=spc_data['usl'], line_dash="dot", line_color="red", annotation_text="USL")
                fig.add_hline(y=spc_data['lsl'], line_dash="dot", line_color="red", annotation_text="LSL")
                fig.add_hline(y=ucl, line_dash="dashdot", line_color="orange", annotation_text="UCL (Process Voice)")
                fig.add_hline(y=lcl, line_dash="dashdot", line_color="orange", annotation_text="LCL (Process Voice)")
                fig.update_layout(title="SPC Chart for Pill Casing Diameter", yaxis_title="Diameter (mm)"); st.plotly_chart(fig, use_container_width=True)
            else: st.warning("SPC data is incomplete or missing.")
        except Exception as e: st.error("Could not render SPC chart."); logger.error(f"Error in SPC tool: {e}", exc_info=True)
    
    with tool_tabs[1]: # Hypothesis Testing
        st.subheader("Hypothesis Testing with Assumption Checks")
        st.markdown("Rigorously determine if a statistically significant difference exists between two groups (e.g., Supplier A vs. Supplier B).")
        with st.expander("The Purpose, Math Basis, Procedure, and Significance"):
            # --- EXPANDED EXPLANATION ---
            st.markdown("#### Purpose: Make Decisions Under Uncertainty")
            st.markdown("Hypothesis testing provides a formal framework for comparing groups or testing claims about a population based on sample data. It's used to make objective, data-driven decisions instead of relying on intuition. For example, it can determine if a new manufacturing process is truly better than the old one, or if a change in supplier has a significant impact on product performance.")
            st.markdown("#### The Mathematical Basis: Null vs. Alternative Hypothesis")
            st.markdown("Every test is structured around two competing hypotheses:\n- **Null Hypothesis (H₀):** The default assumption, usually stating there is *no effect* or *no difference* (e.g., the means of Group A and Group B are equal).\n- **Alternative Hypothesis (H₁ or Hₐ):** The claim we want to prove, stating there *is an effect* or *a difference* (e.g., the means are not equal).\nThe test calculates a **test statistic** (like a t-statistic or a z-score) that measures how far our sample data deviates from what the null hypothesis would predict.")
            st.markdown("#### The Procedure: From Question to Conclusion")
            st.markdown("1.  **Formulate Hypotheses:** State the null (H₀) and alternative (H₁) hypotheses.\n2.  **Check Assumptions:** Verify that the conditions for the chosen statistical test are met (e.g., normality of data for a t-test). If not, switch to a non-parametric alternative (like the Mann-Whitney U test).\n3.  **Calculate Test Statistic:** Compute the test statistic based on the sample data.\n4.  **Determine P-value:** The p-value is calculated from the test statistic. It represents the probability of observing our data (or more extreme data) *if the null hypothesis were true*.")
            st.markdown("#### Significance of the Results: The P-Value and Alpha (α)")
            st.markdown("We compare the p-value to a pre-defined significance level, called **alpha (α)**, which is typically set to 0.05.\n- **`p < α` (e.g., p < 0.05):** The result is **statistically significant**. We **reject the null hypothesis** because our observed data is very unlikely to have occurred by random chance alone. We conclude in favor of the alternative hypothesis (i.e., a difference exists).\n- **`p ≥ α` (e.g., p ≥ 0.05):** The result is **not statistically significant**. We **fail to reject the null hypothesis**. This does *not* prove the null is true, but rather that we lack sufficient evidence to claim a difference exists.")
        try:
            ht_data = ssm.get_data("quality_system", "hypothesis_testing_data")
            # --- FALLBACK DATA ---
            if not ht_data:
                st.info("Displaying example data. To use your own, ensure 'hypothesis_testing_data' is in the data model.", icon="ℹ️")
                rng = np.random.default_rng(0)
                ht_data = {
                    'line_a': list(rng.normal(10.2, 0.5, 30)),
                    'line_b': list(rng.normal(10.0, 0.5, 30))
                }
            
            if ht_data and all(k in ht_data for k in ['line_a', 'line_b']):
                line_a, line_b = ht_data['line_a'], ht_data['line_b']
                shapiro_a = shapiro(line_a); shapiro_b = shapiro(line_b); is_normal = shapiro_a.pvalue > 0.05 and shapiro_b.pvalue > 0.05
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**1. Assumption Check (Normality)**"); st.caption(f"Shapiro-Wilk p-value for Line A: {shapiro_a.pvalue:.3f}"); st.caption(f"Shapiro-Wilk p-value for Line B: {shapiro_b.pvalue:.3f}")
                    st.markdown("**2. Statistical Test Execution**")
                    if is_normal:
                        st.info("Data appears normally distributed. Performing Welch's t-test.", icon="✅"); stat, p_value = stats.ttest_ind(line_a, line_b, equal_var=False); test_name = "Welch's t-test"
                    else:
                        st.warning("Data may not be normal. Switching to non-parametric Mann-Whitney U test.", icon="⚠️"); stat, p_value = mannwhitneyu(line_a, line_b); test_name = "Mann-Whitney U test"
                    st.metric(f"{test_name} Statistic", f"{stat:.3f}"); st.metric("P-value", f"{p_value:.3f}")
                    st.markdown("**3. Conclusion**")
                    if p_value < 0.05: st.success(f"**Conclusion:** A statistically significant difference exists between the two lines (p < 0.05).")
                    else: st.warning(f"**Conclusion:** We cannot conclude a statistically significant difference exists (p >= 0.05).")
                with col2:
                    df_ht = pd.concat([pd.DataFrame({'value': line_a, 'line': 'Line A'}), pd.DataFrame({'value': line_b, 'line': 'Line B'})])
                    fig = px.box(df_ht, x='line', y='value', title="Distribution Comparison", points="all", labels={'value': 'Seal Strength'}); st.plotly_chart(fig, use_container_width=True)
            else: st.warning("Hypothesis testing data is incomplete or missing.")
        except Exception as e: st.error("Could not perform Hypothesis Test."); logger.error(f"Error in Hypothesis Testing tool: {e}", exc_info=True)
    
    with tool_tabs[2]: # Pareto Analysis
        st.subheader("Pareto Analysis of FMEA Risk")
        st.markdown("Applies the 80/20 rule to FMEA data to identify the 'vital few' failure modes that drive the majority of risk, enabling focused mitigation efforts.")
        with st.expander("The Purpose, Math Basis, Procedure, and Significance"):
            # --- EXPANDED EXPLANATION ---
            st.markdown("#### Purpose: Prioritize Efforts for Maximum Impact")
            st.markdown("Pareto Analysis is a simple but powerful decision-making tool based on the **Pareto Principle**, also known as the 80/20 rule. This principle states that for many events, roughly 80% of the effects come from 20% of the causes. In quality engineering, this means that a small number of failure modes (the 'vital few') are typically responsible for the majority of the risk or defects. The purpose of the analysis is to identify these vital few so that corrective actions can be focused where they will have the greatest impact.")
            st.markdown("#### The Mathematical Basis: Cumulative Percentage")
            st.markdown("The analysis is not mathematically complex. It relies on sorting and calculating cumulative percentages:\n1.  **Measure:** A metric is chosen to quantify the impact of each category (e.g., RPN for FMEA, count of defects, cost of scrap).\n2.  **Sort:** The categories are sorted in descending order based on their impact.\n3.  **Calculate Cumulative Percentage:** A running total of the impact is calculated and expressed as a percentage of the total impact across all categories.")
            st.markdown("#### The Procedure: Creating the Chart")
            st.markdown("1.  **Data Aggregation:** Data is collected and grouped by category (e.g., failure mode).\n2.  **Calculation:** The impact metric (e.g., RPN) is calculated for each category.\n3.  **Sorting & Cumulation:** The categories are sorted from highest to lowest impact, and the cumulative percentage is calculated.\n4.  **Plotting:** A bar chart is created showing the impact of each category. A line chart is overlaid on a secondary Y-axis to show the cumulative percentage.")
            st.markdown("#### Significance of the Results: Identifying the 'Vital Few'")
            st.markdown("The Pareto chart visually separates the vital few from the 'trivial many'.\n- **The 'Vital Few':** These are the bars on the left side of the chart that account for a large portion of the initial steep rise in the cumulative percentage line. Corrective actions should be focused on these items.\n- **The 'Trivial Many':** These are the smaller bars on the right side of the chart where the cumulative line begins to flatten out. While these issues may still need to be addressed, they are a lower priority.\nTypically, the cut-off point is around the 80% mark on the cumulative line, guiding teams to focus their resources efficiently.")
        try:
            fmea_df = pd.concat([get_cached_df(ssm.get_data("risk_management_file", "dfmea")), get_cached_df(ssm.get_data("risk_management_file", "pfmea"))], ignore_index=True)
            if not fmea_df.empty and all(c in fmea_df.columns for c in ['S', 'O', 'D']):
                fmea_df['RPN'] = fmea_df['S'] * fmea_df['O'] * fmea_df['D']; fmea_df = fmea_df.sort_values('RPN', ascending=False)
                fmea_df['cumulative_pct'] = (fmea_df['RPN'].cumsum() / fmea_df['RPN'].sum()) * 100
                fig = go.Figure(); fig.add_trace(go.Bar(x=fmea_df['failure_mode'], y=fmea_df['RPN'], name='RPN', marker_color='#1f77b4'))
                fig.add_trace(go.Scatter(x=fmea_df['failure_mode'], y=fmea_df['cumulative_pct'], name='Cumulative %', yaxis='y2', line=dict(color='#d62728')))
                fig.update_layout(title="FMEA Pareto Chart: Prioritizing Risk", yaxis=dict(title='RPN'), yaxis2=dict(title='Cumulative %', overlaying='y', side='right', range=[0, 105]), xaxis_title='Failure Mode', showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            else: st.warning("No FMEA data available for Pareto analysis.")
        except Exception as e: st.error("Could not generate Pareto chart."); logger.error(f"Error in Pareto Analysis tool: {e}", exc_info=True)
    
    with tool_tabs[3]: # Design of Experiments
        st.subheader("Design of Experiments (DOE) with ANOVA")
        st.markdown("Efficiently determine which process inputs (**factors**) and their interactions significantly impact a key output (**response**).")
        with st.expander("The Purpose, Math Basis, Procedure, and Significance"):
            # --- EXPANDED EXPLANATION ---
            st.markdown("#### Purpose: Understand and Optimize Processes")
            st.markdown("Design of Experiments (DOE) is a structured statistical method for efficiently determining the relationship between factors affecting a process and the output of that process. Its purpose is to move beyond 'one-factor-at-a-time' (OFAT) testing, which is inefficient and cannot detect **interactions** (where the effect of one factor depends on the level of another). DOE allows you to screen for significant factors, build a mathematical model of your process, and find the optimal settings to improve performance and robustness.")
            st.markdown("#### The Mathematical Basis: Regression and ANOVA")
            st.markdown("DOE is built on linear regression and Analysis of Variance (ANOVA).\n1.  **Linear Model:** We fit a model that represents the response as a function of the input factors. For example: `Response = β₀ + β₁(FactorA) + β₂(FactorB) + β₁₂(FactorA*FactorB) + ε`. The `β` terms are the coefficients that quantify the size of each effect, and `ε` is the random error.\n2.  **ANOVA:** After fitting the model, ANOVA is used to decompose the total variability in the response into portions attributable to each factor and interaction. It calculates an **F-statistic** for each factor, which is a ratio of the variation explained by that factor to the unexplained variation (error).")
            st.markdown("#### The Procedure: Design, Execute, Analyze")
            st.markdown("1.  **Design:** Select factors, their levels (e.g., high/low settings), and a design structure (e.g., full factorial, fractional factorial). This creates a 'recipe sheet' of experimental runs.\n2.  **Execute:** Run the experiments according to the design matrix in a randomized order to prevent bias.\n3.  **Analyze:** Fit the linear model to the experimental data. Generate an ANOVA table to identify significant effects. Create plots (Main Effects, Interaction, Contour) to visualize the results.")
            st.markdown("#### Significance of the Results: Identifying Key Drivers and Optimal Settings")
            st.markdown("The key output is the **ANOVA table**, which contains a **p-value (PR(>F))** for each factor and interaction.\n- **`p < 0.05`:** The factor or interaction has a **statistically significant effect** on the response. It is a key driver of the process output.\n- **`p ≥ 0.05`:** The factor's effect cannot be distinguished from random noise. It is likely not a primary driver.\n- **Visualization:** Contour plots use the model to create a 'map' of the response, allowing you to visually identify the factor settings that lead to a desired outcome (e.g., maximum strength, minimum defects).")
        try:
            doe_df = get_cached_df(ssm.get_data("quality_system", "doe_data"))
            if not doe_df.empty:
                formula = 'seal_strength ~ temperature * pressure'; model = ols(formula, data=doe_df).fit()
                anova_table = sm.stats.anova_lm(model, typ=2)
                st.markdown("**Analysis of Variance (ANOVA) Table**"); st.caption("This table shows which factors significantly impact Seal Strength. Look for p-values (PR(>F)) < 0.05.")
                st.dataframe(anova_table.style.map(lambda x: 'background-color: #eaf5ea' if x < 0.05 else '', subset=['PR(>F)']))
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Main Effects Plot**"); st.caption("Visualizes the average effect of changing each factor from low to high.")
                    main_effects_data = doe_df.melt(id_vars='seal_strength', value_vars=['temperature', 'pressure'], var_name='factor', value_name='level')
                    main_effects = main_effects_data.groupby(['factor', 'level'])['seal_strength'].mean().reset_index()
                    fig = px.line(main_effects, x='level', y='seal_strength', color='factor', title="Main Effects on Seal Strength", markers=True, labels={'level': 'Factor Level (-1: Low, 1: High)', 'seal_strength': 'Mean Seal Strength'}); st.plotly_chart(fig, use_container_width=True)
                with col2:
                    st.markdown("**Response Surface Contour Plot**"); st.caption("Visualizes the predicted response across the entire design space.")
                    t_range, p_range = np.linspace(-1.5, 1.5, 30), np.linspace(-1.5, 1.5, 30); t_grid, p_grid = np.meshgrid(t_range, p_range)
                    grid = pd.DataFrame({'temperature': t_grid.ravel(), 'pressure': p_grid.ravel()}); strength_grid = model.predict(grid).values.reshape(t_grid.shape)
                    opt_idx = np.unravel_index(np.argmax(strength_grid), strength_grid.shape)
                    opt_temp, opt_press = t_range[opt_idx[1]], p_range[opt_idx[0]]; opt_strength = strength_grid.max()
                    fig = go.Figure(data=[go.Contour(z=strength_grid, x=t_range, y=p_range, colorscale='Viridis', contours_coloring='lines', line_width=1)])
                    fig.add_trace(go.Scatter(x=doe_df['temperature'], y=doe_df['pressure'], mode='markers', marker=dict(color='black', size=10, symbol='x'), name='DOE Runs'))
                    fig.add_trace(go.Scatter(x=[opt_temp], y=[opt_press], mode='markers+text', marker=dict(color='red', size=16, symbol='star'), text=[' Optimum'], textposition="top right", name='Predicted Optimum'))
                    fig.update_layout(xaxis_title="Temperature", yaxis_title="Pressure", title=f"Predicted Seal Strength (Max: {opt_strength:.1f})"); st.plotly_chart(fig, use_container_width=True)
            else: st.warning("DOE data is not available.")
        except Exception as e: st.error("Could not generate DOE plots."); logger.error(f"Error in DOE Analysis tool: {e}", exc_info=True)

    # --- NEW TOOL 1: GAUGE R&R ---
    with tool_tabs[4]:
        st.subheader("Measurement System Analysis (Gauge R&R)")
        st.markdown("Determine if your measurement system is adequate by quantifying its variability relative to the total process variation.")
        with st.expander("The 'Why', 'How', and 'So What?'"):
            st.markdown("#### Purpose: Can You Trust Your Measurement?")
            st.markdown("Before you can improve a process, you must be able to measure it accurately and precisely. A Gauge R&R study answers a critical question: **Is the variation I see in my data coming from the product, or from my measurement system?** If the measurement system is a large source of variation, you may misinterpret good parts as bad (or vice-versa) and waste resources trying to 'fix' a process that is actually fine.")
            st.markdown("#### The Math Basis: Analysis of Variance (ANOVA)")
            st.markdown("We use ANOVA to partition the total observed variation into its sources: variation from the **Parts** (the real process variation we want to see), variation from the **Operators** (reproducibility), and variation from the **Gauge** itself (repeatability).")
            st.markdown("#### The Procedure: Study Execution & Analysis")
            st.markdown("1.  A study is conducted where multiple operators measure multiple (randomly selected) parts multiple times.\n2.  The data is fed into an ANOVA model.\n3.  From the ANOVA table's Mean Squares (MS), we calculate the variance components for each source.\n4.  Key metrics are calculated: **%Contribution**, **%Study Variation**, and the **Number of Distinct Categories (ndc)**.")
            st.markdown("#### Significance of the Results: Go / No-Go Decision")
            st.markdown("""
            - **%Contribution:** The percentage of total variance caused by the measurement system.
              - **< 1%:** Excellent.
              - **1% - 9%:** Acceptable.
              - **> 9%:** Unacceptable. The gauge needs improvement.
            - **Number of Distinct Categories (ndc):** How many distinct groups of parts the system can reliably distinguish.
              - **`ndc` < 2:** Useless. Cannot even tell parts apart.
              - **2 <= `ndc` < 5:** Marginally acceptable, may need improvement.
              - **`ndc` >= 5:** Acceptable. The system is effective for process control.
            """)
        try:
            msa_data_list = ssm.get_data("quality_system", "msa_data")
            # --- FALLBACK DATA ---
            if not msa_data_list:
                st.info("Displaying example data. To use your own, ensure 'msa_data' is in the data model.", icon="ℹ️")
                rng = np.random.default_rng(0)
                parts_mock = np.repeat(np.arange(1, 11), 6) # 10 parts
                operators_mock = np.tile(np.repeat(['A', 'B', 'C'], 2), 10) # 3 operators, 2 reps
                part_means = np.linspace(5.0, 5.5, 10)
                op_bias = {'A': -0.02, 'B': 0, 'C': 0.03}
                measurements = []
                for i, part_id in enumerate(parts_mock):
                    op_name = operators_mock[i]
                    base_val = part_means[part_id - 1] + op_bias[op_name]
                    measurements.append(base_val + rng.normal(0, 0.05)) # 0.05 is gauge error
                msa_data_list = pd.DataFrame({'part': parts_mock, 'operator': operators_mock, 'measurement': measurements}).to_dict('records')

            if msa_data_list and all(k in msa_data_list[0] for k in ['part', 'operator', 'measurement']):
                df = pd.DataFrame(msa_data_list)
                
                model = ols('measurement ~ C(part) + C(operator) + C(part):C(operator)', data=df).fit()
                anova_table = sm.stats.anova_lm(model, typ=2)
                
                # --- BUG FIX: Manually calculate 'mean_sq' and standardize column names ---
                anova_table.columns = [col.lower().strip().replace('pr(>f)', 'p_value') for col in anova_table.columns]
                anova_table['mean_sq'] = anova_table['sum_sq'] / anova_table['df']
                
                ms_operator = anova_table.loc['C(operator)', 'mean_sq']
                ms_part = anova_table.loc['C(part)', 'mean_sq']
                ms_interact = anova_table.loc['C(part):C(operator)', 'mean_sq']
                ms_error = anova_table.loc['Residual', 'mean_sq']
                
                n_parts, n_ops = df['part'].nunique(), df['operator'].nunique()
                n_reps = len(df) / (n_parts * n_ops) if (n_parts * n_ops) > 0 else 0

                var_repeat = ms_error
                var_reprod = max(0, (ms_operator - ms_interact) / (n_parts * n_reps))
                var_interact = max(0, (ms_interact - ms_error) / n_reps)
                var_op_total = var_reprod + var_interact
                var_gaugeRR = var_repeat + var_op_total
                var_part = max(0, (ms_part - ms_interact) / (n_ops * n_reps))
                var_total = var_gaugeRR + var_part

                if var_total > 1e-9:
                    contrib_gauge = (var_gaugeRR / var_total) * 100
                    contrib_part = (var_part / var_total) * 100
                    ndc = int(1.41 * (np.sqrt(var_part) / np.sqrt(var_gaugeRR))) if var_gaugeRR > 1e-9 else float('inf')

                    st.markdown("**Gauge R&R Results**")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Gauge R&R % Contribution", f"{contrib_gauge:.2f}%", help="Percentage of total variation from the measurement system. <9% is acceptable.")
                        st.metric("Number of Distinct Categories (ndc)", f"{ndc}", help="How many groups the system can distinguish. >=5 is acceptable.")
                        if contrib_gauge > 9 or ndc < 5:
                            st.error("**Conclusion: Measurement System is UNACCEPTABLE.**", icon="🚨")
                        else:
                            st.success("**Conclusion: Measurement System is ACCEPTABLE.**", icon="✅")
                    with col2:
                        var_df = pd.DataFrame({
                            'Source': ['Gauge R&R', 'Part-to-Part'],
                            'Contribution (%)': [contrib_gauge, contrib_part]
                        })
                        fig = px.bar(var_df, x='Source', y='Contribution (%)', title="Variance Contribution", text_auto='.2f', color='Source', color_discrete_map={'Gauge R&R': 'crimson', 'Part-to-Part': 'seagreen'})
                        fig.update_layout(showlegend=False)
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Could not calculate variance components. Check data for variability.")
            else:
                st.warning("Gauge R&R data (`msa_data`) is missing or incomplete.")
        except Exception as e:
            st.error(f"Could not perform Gauge R&R Analysis. Error: {e}")
            logger.error(f"Error in Gauge R&R tool: {e}", exc_info=True)

    # --- NEW TOOL 2: CHI-SQUARED TEST ---
    with tool_tabs[5]:
        st.subheader("Chi-Squared Test of Independence")
        st.markdown("Test for a statistically significant association between two categorical variables (e.g., Supplier vs. Defect Type).")
        with st.expander("The 'Why', 'How', and 'So What?'"):
            st.markdown("#### Purpose: Finding Relationships in Categorical Data")
            st.markdown("While t-tests compare averages of continuous data, the Chi-Squared (χ²) test works with counts of categorical data. It helps answer questions like: *'Is one production line producing a different mix of defect types than another?'* or *'Is there a relationship between the shift and the pass/fail outcome?'* It's a key tool for root cause analysis.")
            st.markdown("#### The Math Basis: Observed vs. Expected")
            st.markdown("The test is based on the **Chi-Squared (χ²) statistic**. It works by:\n1.  Creating a **contingency table** of the observed counts for your two variables.\n2.  Calculating the counts you would **expect** to see in each cell *if there were no relationship* between the variables.\n3.  The χ² statistic summarizes the difference between the observed and expected counts across all cells. A large χ² value suggests the observed data is very different from what you'd expect by chance.")
            st.markdown("#### The Procedure: From Data to P-Value")
            st.markdown("1.  Raw data (e.g., a list of inspection results with supplier and outcome) is aggregated into a contingency table.\n2.  The `scipy.stats.chi2_contingency` function calculates the χ² statistic, the p-value, and the degrees of freedom (df).\n3.  The result is interpreted.")
            st.markdown("#### Significance of the Results: Is the Association Real?")
            st.markdown("The **p-value** is the key output. It tells you the probability of observing an association as strong as the one in your data, assuming the variables are actually independent.\n- **`p < 0.05`:** You **reject the null hypothesis**. There is a statistically significant association between the variables. This does *not* prove causation, but it's a strong signal to investigate further.\n- **`p >= 0.05`:** You **fail to reject the null hypothesis**. You do not have enough evidence to conclude that an association exists.")
        try:
            chi_data = ssm.get_data("quality_system", "chi_squared_data")
            # --- FALLBACK DATA ---
            if not chi_data:
                st.info("Displaying example data. To use your own, ensure 'chi_squared_data' is in the data model.", icon="ℹ️")
                rng = np.random.default_rng(1)
                data = []
                for _ in range(100): data.append({'supplier': 'Supplier A', 'outcome': rng.choice(['Pass', 'Fail', 'Rework'], p=[0.9, 0.05, 0.05])})
                for _ in range(100): data.append({'supplier': 'Supplier B', 'outcome': rng.choice(['Pass', 'Fail', 'Rework'], p=[0.7, 0.2, 0.1])})
                chi_data = data

            if chi_data and all(k in chi_data[0] for k in ['supplier', 'outcome']):
                df = pd.DataFrame(chi_data)
                contingency_table = pd.crosstab(df['supplier'], df['outcome'])
                
                st.markdown("**Contingency Table (Observed Counts)**")
                st.dataframe(contingency_table)

                if contingency_table.size > 1:
                    chi2, p, dof, expected = chi2_contingency(contingency_table)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Chi-Squared Statistic", f"{chi2:.3f}")
                        st.metric("P-value", f"{p:.4f}")
                        if p < 0.05:
                            st.success("**Conclusion:** A statistically significant association exists between Supplier and Outcome (p < 0.05).", icon="✅")
                        else:
                            st.warning("**Conclusion:** No significant association detected (p >= 0.05).", icon="⚠️")
                    with col2:
                        ct_percent = contingency_table.div(contingency_table.sum(axis=1), axis=0) * 100
                        fig = px.imshow(ct_percent, text_auto='.1f', aspect="auto",
                                        title="Heatmap of Outcomes by Supplier (%)",
                                        labels=dict(x="Outcome", y="Supplier", color="% of Row Total"),
                                        color_continuous_scale=px.colors.sequential.Greens)
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Not enough data to form a valid contingency table.")
            else:
                st.warning("Chi-Squared data (`chi_squared_data`) is missing or incomplete.")
        except Exception as e:
            st.error(f"Could not perform Chi-Squared Test. Error: {e}")
            logger.error(f"Error in Chi-Squared tool: {e}", exc_info=True)

    # --- NEW TOOL 3: CORRELATION ANALYSIS ---
    with tool_tabs[6]:
        st.subheader("Correlation Analysis")
        st.markdown("Explore the strength and direction of the linear relationship between two continuous variables.")
        with st.expander("The 'Why', 'How', and 'So What?'"):
            st.markdown("#### Purpose: Quantifying Relationships")
            st.markdown("Correlation analysis is a quick and powerful way to see if two variables move together. It's often a first step before more complex modeling like DOE or regression. It helps answer questions like: *'As we increase process temperature, does seal strength also increase?'* or *'Is there a relationship between material hardness and component lifetime?'*")
            st.markdown("#### The Math Basis: Pearson's Correlation Coefficient (r)")
            st.markdown("The analysis centers on **Pearson's r**, which measures the strength and direction of a *linear* relationship. It ranges from **-1 to +1**:\n- **+1:** Perfect positive linear correlation (as X increases, Y increases).\n- **-1:** Perfect negative linear correlation (as X increases, Y decreases).\n- **0:** No linear correlation. **Important:** A correlation of 0 does not mean there is no relationship, only that there is no *linear* one (e.g., a U-shaped relationship could have r=0).")
            st.markdown("#### The Procedure: Visualize and Calculate")
            st.markdown("1.  Two columns of continuous data are selected.\n2.  A **scatter plot** is generated to visually inspect the relationship. This is the most important step!\n3.  The `scipy.stats.pearsonr` function is used to calculate the Pearson's r coefficient and its p-value.")
            st.markdown("#### Significance of the Results: Strength and Confidence")
            st.markdown("You get two key outputs:\n- **Correlation Coefficient (r):** The strength of the relationship. General rules of thumb: |r| > 0.7 is strong, 0.4 < |r| < 0.7 is moderate, |r| < 0.4 is weak.\n- **P-value:** The confidence in the result. It tests the hypothesis that r=0. If **`p < 0.05`**, you can be confident that the relationship you see is not just due to random chance. **Crucially, statistical significance does not equal practical importance.** A tiny but very consistent correlation in a huge dataset can be statistically significant but practically useless.")
        try:
            corr_data_dict = ssm.get_data("quality_system", "correlation_data")
            # --- FALLBACK DATA ---
            if not corr_data_dict:
                st.info("Displaying example data. To use your own, ensure 'correlation_data' is in the data model.", icon="ℹ️")
                rng = np.random.default_rng(42)
                temperature = np.linspace(20, 100, 50)
                strength = 5 + 0.5 * temperature + rng.normal(0, 5, 50)
                corr_data_dict = {'temperature': list(temperature), 'strength': list(strength)}

            if corr_data_dict and all(k in corr_data_dict for k in ['temperature', 'strength']):
                df = pd.DataFrame(corr_data_dict)
                if len(df) > 2:
                    r, p = pearsonr(df['temperature'], df['strength'])

                    fig = px.scatter(df, x='temperature', y='strength',
                                     title=f"Correlation Analysis (r = {r:.3f})",
                                     trendline="ols", trendline_color_override="red",
                                     labels={'temperature': 'Process Temperature (°C)', 'strength': 'Seal Strength (N)'})
                    st.plotly_chart(fig, use_container_width=True)

                    st.metric("Pearson Correlation (r)", f"{r:.4f}")
                    st.metric("P-value", f"{p:.4f}")

                    if p < 0.05:
                        st.success(f"**Conclusion:** A statistically significant {'positive' if r > 0 else 'negative'} correlation exists.", icon="✅")
                    else:
                        st.warning("**Conclusion:** The observed correlation is not statistically significant.", icon="⚠️")
                else:
                    st.warning("Need at least 3 data points for correlation analysis.")
            else:
                st.warning("Correlation data (`correlation_data`) is missing or incomplete.")
        except Exception as e:
            st.error(f"Could not perform Correlation Analysis. Error: {e}")
            logger.error(f"Error in Correlation tool: {e}", exc_info=True)

    # --- NEW TOOL 4: EQUIVALENCE TESTING (TOST) ---
    with tool_tabs[7]:
        st.subheader("Equivalence Testing (TOST)")
        st.markdown("Rigorously prove that two groups are 'practically the same' within a pre-defined margin of equivalence.")
        with st.expander("The 'Why', 'How', and 'So What?'"):
            st.markdown("#### Purpose: Proving Sameness, Not Difference")
            st.markdown("Standard hypothesis tests (like the t-test) are designed to find a difference. Failing to find a difference is *not* the same as proving equivalence. **Equivalence Testing** is the correct statistical method when you need to demonstrate that a change (e.g., a new supplier, a modified process) results in a product that is practically the same as the old one. This is critical for regulatory submissions and change control justifications.")
            st.markdown("#### The Math Basis: Two One-Sided Tests (TOST)")
            st.markdown("Instead of one null hypothesis (`mean_A = mean_B`), TOST uses two. We define an **equivalence interval** `[-δ, +δ]` around zero. We must prove that the true difference between the means is *not* outside this interval. We test two null hypotheses:\n1.  `H₀₁: difference <= -δ` (The new process is worse)\n2.  `H₀₂: difference >= +δ` (The new process is better... or different in the other direction)\nWe must **reject both** of these null hypotheses to claim equivalence.")
            st.markdown("#### The Procedure: Define, Test, Conclude")
            st.markdown("1.  The engineer defines a **practically significant difference (delta, δ)**. This is the most critical step and must be based on scientific or engineering knowledge.\n2.  Two separate one-sided t-tests are performed against the lower and upper equivalence bounds.\n3.  The final p-value for the TOST is the **maximum** of the p-values from the two individual tests.\n4.  The 90% confidence interval of the difference is calculated and compared to the equivalence interval.")
            st.markdown("#### Significance of the Results: A Stronger Claim")
            st.markdown("- **`p < 0.05`:** You **reject both nulls and claim equivalence**. The data provides strong evidence that the true difference between the groups is within your defined equivalence margin `[-δ, +δ]`.\n- **`p >= 0.05`:** You **cannot claim equivalence**. The difference might be outside your acceptable range, or you don't have enough data to be sure.\nVisually, you have equivalence if the **90% confidence interval** of the difference lies entirely **within** the equivalence bounds.")
        try:
            ht_data = ssm.get_data("quality_system", "hypothesis_testing_data")
            # --- FALLBACK DATA (same as Hypothesis Test) ---
            if not ht_data:
                rng = np.random.default_rng(0)
                ht_data = {
                    'line_a': list(rng.normal(10.2, 0.5, 30)),
                    'line_b': list(rng.normal(10.0, 0.5, 30))
                }
            
            if ht_data and all(k in ht_data for k in ['line_a', 'line_b']):
                line_a, line_b = np.array(ht_data['line_a']), np.array(ht_data['line_b'])
                
                st.markdown("**1. Define Equivalence Margin**")
                delta = st.number_input("Enter the equivalence margin (delta, δ):", min_value=0.0, value=0.5, step=0.1, help="The maximum difference between the groups that you would still consider 'practically the same'.")

                n1, n2 = len(line_a), len(line_b)
                mean_diff = np.mean(line_a) - np.mean(line_b)
                s1, s2 = np.var(line_a, ddof=1), np.var(line_b, ddof=1)
                
                if n1 + n2 > 2:
                    pooled_sd = np.sqrt(((n1 - 1) * s1 + (n2 - 1) * s2) / (n1 + n2 - 2))
                    se_diff = pooled_sd * np.sqrt(1/n1 + 1/n2) if (n1 > 0 and n2 > 0) else 0

                    if se_diff > 0:
                        t_stat_lower = (mean_diff - (-delta)) / se_diff
                        t_stat_upper = (mean_diff - delta) / se_diff
                        dof = n1 + n2 - 2
                        
                        p_lower = stats.t.sf(t_stat_lower, df=dof)
                        p_upper = stats.t.cdf(t_stat_upper, df=dof)
                        tost_p_value = max(p_lower, p_upper)
                        
                        ci_90 = stats.t.interval(0.90, df=dof, loc=mean_diff, scale=se_diff)

                        st.markdown("**2. Test Results**")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Difference in Means (A - B)", f"{mean_diff:.3f}")
                            st.metric("TOST P-Value", f"{tost_p_value:.4f}")
                            st.markdown(f"**90% Confidence Interval:** `[{ci_90[0]:.3f}, {ci_90[1]:.3f}]`")
                        with col2:
                            st.markdown("**3. Conclusion**")
                            is_equivalent = tost_p_value < 0.05
                            if is_equivalent:
                                st.success(f"**Conclusion: The groups ARE statistically equivalent** within a margin of ±{delta}.", icon="✅")
                            else:
                                st.error(f"**Conclusion: Equivalence CANNOT be claimed** within a margin of ±{delta}.", icon="🚨")

                        fig = go.Figure()
                        fig.add_shape(type="rect", x0=-delta, y0=0, x1=delta, y1=1, line=dict(width=0), fillcolor="rgba(44, 160, 44, 0.2)", layer="below", name="Equivalence Zone")
                        fig.add_trace(go.Scatter(x=[ci_90[0], ci_90[1]], y=[0.5, 0.5], mode="lines", line=dict(color="blue", width=4), name="90% CI of Difference"))
                        fig.add_trace(go.Scatter(x=[mean_diff], y=[0.5], mode="markers", marker=dict(color="blue", size=12, symbol="x"), name="Observed Difference"))
                        fig.update_layout(title="Equivalence Test Visualization", xaxis_title="Difference Between Groups", yaxis=dict(showticklabels=False, range=[0,1]),
                                          shapes=[dict(type='line', x0=0, y0=0, x1=0, y1=1, line=dict(color='black', dash='dash'))])
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Could not perform test. Check for zero variance or empty data groups.")
                else:
                    st.warning("Not enough data points to perform the test.")
            else:
                st.warning("Equivalence testing data (`hypothesis_testing_data`) is incomplete or missing.")
        except Exception as e:
            st.error(f"Could not perform Equivalence Test. Error: {e}")
            logger.error(f"Error in TOST tool: {e}", exc_info=True)


def render_machine_learning_lab_tab(ssm: SessionStateManager):
    """Renders the Machine Learning Lab tab with professionally enhanced, interactive visualizations."""
    st.header("🤖 Machine Learning Lab")
    st.info("Utilize predictive models to forecast outcomes, enabling proactive quality control and project management.")

    try:
        from sklearn.ensemble import RandomForestClassifier, IsolationForest
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import confusion_matrix
        from sklearn.cluster import KMeans
        from sklearn.datasets import make_blobs
        from statsmodels.tsa.arima.model import ARIMA
        import shap
    except ImportError:
        st.error("This tab requires `scikit-learn`, `statsmodels` and `shap`. Please install them (`pip install scikit-learn statsmodels shap`) to enable ML features.", icon="🚨")
        return

    # --- VISUALIZATION UPGRADE: Replaced Matplotlib with beautiful Plotly plots ---
    ml_tabs = st.tabs([
        "Predictive Quality (Batch Failure)", "Predictive Project Risk (Task Delay)",
        "Clustering (K-Means)", "Anomaly Detection (Isolation Forest)", "Time Series Forecasting"
    ])

    with ml_tabs[0]:
        st.subheader("Predictive Quality: Manufacturing Batch Failure")
        st.markdown("This model predicts whether a manufacturing batch will **Pass** or **Fail** based on its process parameters, *before* the batch is run.")

        with st.expander("The Purpose, Math Basis, Procedure, and Significance"):
            st.markdown("#### Purpose: Proactive Quality Control")
            st.markdown("The goal of this tool is to shift from reactive to proactive quality control. Instead of waiting for a batch to fail final inspection, this model predicts the outcome based on in-process parameters. This allows engineers to intervene *before* resources are wasted, significantly reducing the Cost of Poor Quality (COPQ) associated with scrap and rework. It's a classic binary classification problem.")
            st.markdown("#### The Mathematical Basis & Method: Random Forest and SHAP")
            st.markdown("- **Random Forest:** An *ensemble* learning method that constructs a multitude of decision trees at training time. For a classification task, the final prediction is the mode of the classes predicted by individual trees. It is robust to overfitting and can capture complex, non-linear relationships between process parameters and the outcome.\n- **SHAP (SHapley Additive exPlanations):** A game-theoretic approach to explain the output of any machine learning model. It calculates the contribution of each feature to the prediction for an individual instance. The 'SHAP value' for a feature is its average marginal contribution across all possible feature coalitions, providing both global (average impact) and local (individual prediction) explainability.")
            st.markdown("#### The Procedure: From Data to Insight")
            st.markdown("1.  **Data Preparation:** Historical batch data with process parameters (features) and a binary outcome (Pass/Fail) is used.\n2.  **Train/Test Split:** The data is split into a training set (to build the model) and a test set (to evaluate its performance on unseen data).\n3.  **Model Training:** A `RandomForestClassifier` is trained on the training data.\n4.  **Performance Evaluation:** The model's accuracy is evaluated on the test set using a **Confusion Matrix**, which shows True/False Positives and Negatives.\n5.  **Model Interpretation:** A SHAP explainer is created. SHAP values are calculated to understand feature importances and how they drive individual predictions.")
            st.markdown("#### Significance of the Results: Actionable Insights")
            st.markdown("- **Confusion Matrix:** Gives a detailed breakdown of performance. High accuracy, precision, and recall are desired. False Negatives (predicting Pass when it was a Fail) are often the most costly error.\n- **Feature Importance Plot:** Tells engineers which process parameters are the most influential drivers of batch success or failure. This guides process improvement and DOE efforts.\n- **SHAP Summary Plot:** Provides deep, actionable insights. It shows *not only* which features are important but *how* their values affect the outcome (e.g., 'High `temperature` values strongly push the model to predict 'Fail''). This is crucial for root cause analysis and process optimization.")

        @st.cache_data
        def get_quality_model_and_data():
            np.random.seed(42); n_samples = 500
            data = {'temperature': np.random.normal(90, 5, n_samples), 'pressure': np.random.normal(300, 20, n_samples), 'viscosity': np.random.normal(50, 3, n_samples)}
            df = pd.DataFrame(data)
            fail_conditions = (df['temperature'] > 98) | (df['temperature'] < 82) | (df['pressure'] > 330) | (df['viscosity'] < 45)
            df['status'] = np.where(fail_conditions, 'Fail', 'Pass'); df['status_code'] = df['status'].apply(lambda x: 1 if x == 'Fail' else 0)
            X = df[['temperature', 'pressure', 'viscosity']]; y = df['status_code']
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
            model = RandomForestClassifier(n_estimators=100, random_state=42); model.fit(X_train, y_train)
            return model, X_test, y_test

        @st.cache_data
        def get_shap_explanation(_model, _X_test):
            explainer = shap.TreeExplainer(_model)
            shap_explanation = explainer(_X_test)
            return shap_explanation

        model, X_test, y_test = get_quality_model_and_data()
        shap_explanation = get_shap_explanation(model, X_test)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Model Performance (Test Set)**")
            y_pred = model.predict(X_test)
            cm = confusion_matrix(y_test, y_pred)
            cm_percent = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
            labels = [["True Negative", "False Positive"], ["False Negative", "True Positive"]]
            annotations = [[f"{labels[i][j]}<br>{cm[i][j]}<br>({cm_percent[i][j]:.2%})" for j in range(2)] for i in range(2)]
            fig_cm = go.Figure(data=go.Heatmap(
                   z=cm, x=['Predicted Pass', 'Predicted Fail'], y=['Actual Pass', 'Actual Fail'],
                   hoverongaps=False, colorscale='Blues', showscale=False,
                   text=annotations, texttemplate="%{text}"))
            fig_cm.update_layout(height=350, margin=dict(l=10, r=10, t=40, b=10), title_x=0.5, title_text="<b>Confusion Matrix</b>", title_font_size=16)
            st.plotly_chart(fig_cm, use_container_width=True)

        with col2:
            st.markdown("**Overall Feature Importance**")
            # --- VISUALIZATION UPGRADE: Plotly Bar Chart ---
            shap_values_fail = shap_explanation[:, :, 1]
            mean_abs_shap = np.abs(shap_values_fail.values).mean(axis=0)
            importance_df = pd.DataFrame({'feature': X_test.columns, 'importance': mean_abs_shap}).sort_values('importance')
            fig_bar = px.bar(importance_df, x='importance', y='feature', orientation='h', 
                             title='Average Impact on Model Output', text_auto='.3f')
            fig_bar.update_layout(height=350, margin=dict(l=10, r=10, t=40, b=10), title_font_size=16)
            fig_bar.update_traces(marker_color='#1f77b4')
            st.plotly_chart(fig_bar, use_container_width=True)

        st.subheader("Deep Dive: How Feature Values Drive Failure")
        # --- VISUALIZATION UPGRADE: Interactive Plotly Beeswarm Chart ---
        shap_df = pd.DataFrame(shap_values_fail.values, columns=X_test.columns)
        feature_vals = pd.DataFrame(shap_values_fail.data, columns=X_test.columns)
        
        fig_summary = go.Figure()
        for i, feature in enumerate(X_test.columns):
            # Normalize feature values for color mapping
            norm_vals = (feature_vals[feature] - feature_vals[feature].min()) / (feature_vals[feature].max() - feature_vals[feature].min())
            
            # Add jitter for beeswarm effect
            jitter = np.random.uniform(-0.15, 0.15, len(shap_df))
            
            fig_summary.add_trace(go.Scatter(
                x=shap_df[feature],
                y=np.full(len(shap_df), i) + jitter,
                mode='markers',
                marker=dict(
                    color=norm_vals,
                    colorscale='RdBu',
                    reversescale=True,
                    showscale=True,
                    colorbar=dict(title='Feature Value', x=1.15, tickvals=[0,1], ticktext=['Low', 'High'])
                ),
                customdata=feature_vals[feature],
                hovertemplate=f"<b>{feature}</b><br>SHAP Value: %{{x:.3f}}<br>Feature Value: %{{customdata:.2f}}<extra></extra>",
                name=feature
            ))

        fig_summary.update_layout(
            title="<b>SHAP Summary Plot: Impact of each feature on individual predictions</b>",
            xaxis_title="SHAP Value (Impact on prediction towards 'Fail')",
            showlegend=False,
            yaxis=dict(
                tickvals=list(range(len(X_test.columns))),
                ticktext=X_test.columns,
                title='Feature'
            ),
            height=400
        )
        st.plotly_chart(fig_summary, use_container_width=True)

    with ml_tabs[1]:
        st.subheader("Predictive Project Risk: Interactive Analysis")
        st.markdown("This tool uses a trained model to forecast task delays and allows you to **drill down into the specific risk factors** for each task.")

        with st.expander("The Purpose, Math Basis, Procedure, and Significance"):
            st.markdown("#### Purpose: Proactive Project Management")
            st.markdown("The goal is to move from reactive fire-fighting to proactive risk mitigation in project management. This tool predicts the likelihood that a future project task will become 'At Risk' (i.e., delayed). This allows project managers to identify high-risk tasks early, investigate the root causes of the risk, and allocate resources to prevent delays before they impact the overall project timeline.")
            st.markdown("#### The Mathematical Basis & Method: Logistic Regression")
            st.markdown("- **Logistic Regression:** A fundamental and highly interpretable classification algorithm. It models the probability of a binary outcome (e.g., At-Risk vs. Not-At-Risk) by fitting the data to a logistic (sigmoid) function. The model learns a set of **coefficients** for each input feature.\n- **Coefficient Analysis:** The learned coefficients are directly interpretable. A positive coefficient means an increase in the feature's value (e.g., more `duration_days`) increases the predicted probability of the task being 'At-Risk'. The magnitude of the coefficient indicates the strength of this relationship. This interpretability is key for the drill-down analysis.")
            st.markdown("#### The Procedure: From History to Forecast")
            st.markdown("1.  **Feature Engineering:** Historical task data is processed to create numerical features, such as `duration_days`, `num_dependencies`, and `is_critical` (a binary flag).\n2.  **Model Training:** A `LogisticRegression` model is trained on completed tasks where the outcome ('At Risk' or 'Completed') is known. The `class_weight='balanced'` parameter is used to handle the likely scenario where 'At Risk' tasks are less common than successfully completed ones.\n3.  **Prediction:** The trained model is used to predict the `risk_probability` for all tasks that are 'Not Started'.\n4.  **Drill-Down Analysis:** For a selected high-risk task, the model's coefficients are multiplied by that task's specific feature values to calculate the individual **risk contribution** of each factor.")
            st.markdown("#### Significance of the Results: From 'What' to 'Why'")
            st.markdown("- **Risk Probability Forecast:** The primary bar chart answers the question, **'What should I worry about?'** by providing a prioritized list of tasks that require immediate management attention.\n- **Risk Factor Contribution Plot (Drill-Down):** The second, interactive plot answers the more important question, **'Why should I worry about *this specific* task?'**. It shows the project manager whether the risk is driven by the task's long duration, its high number of dependencies, or its position on the critical path. This enables targeted, effective mitigation strategies rather than generic concern.")

        @st.cache_data
        def train_and_predict_risk(tasks: Tuple):
            df = pd.DataFrame([dict(fs) for fs in tasks])
            df['start_date'] = pd.to_datetime(df['start_date']); df['end_date'] = pd.to_datetime(df['end_date'])
            df['duration_days'] = (df['end_date'] - df['start_date']).dt.days
            df['num_dependencies'] = df['dependencies'].apply(lambda x: len(x.split(',')) if isinstance(x, str) and x else 0)
            critical_path_ids = find_critical_path(df.copy()); df['is_critical'] = df['id'].isin(critical_path_ids).astype(int)
            train_df = df[df['status'].isin(['Completed', 'At Risk'])].copy(); train_df['target'] = (train_df['status'] == 'At Risk').astype(int)
            if len(train_df['target'].unique()) < 2: return None, None, None
            features = ['duration_days', 'num_dependencies', 'is_critical']; X_train = train_df[features]; y_train = train_df['target']
            model = LogisticRegression(random_state=42, class_weight='balanced'); model.fit(X_train, y_train)
            predict_df = df[df['status'] == 'Not Started'].copy()
            if predict_df.empty: return None, None, None
            X_predict = predict_df[features]; predict_df['risk_probability'] = model.predict_proba(X_predict)[:, 1]
            return predict_df, model, features

        tasks_raw_data = ssm.get_data("project_management", "tasks")
        # Convert to hashable type for caching
        immutable_tasks = tuple(frozenset(d.items()) for d in tasks_raw_data)
        risk_predictions_df, risk_model, risk_features = train_and_predict_risk(immutable_tasks)

        if risk_predictions_df is not None:
            st.markdown("**Forecasted Delay Probability for Future Tasks**")
            sorted_risk_df = risk_predictions_df.sort_values('risk_probability', ascending=False)
            fig = px.bar(sorted_risk_df, x='risk_probability', y='name', orientation='h',
                         title="Forecasted Risk for 'Not Started' Tasks",
                         labels={'risk_probability': 'Probability of Being "At-Risk"', 'name': 'Task'},
                         color='risk_probability', color_continuous_scale=px.colors.sequential.Reds,
                         text='risk_probability')
            fig.update_traces(texttemplate='%{text:.0%}', textposition='outside')
            fig.update_layout(height=400, yaxis={'categoryorder':'total ascending'}, uniformtext_minsize=8, uniformtext_mode='hide'); 
            st.plotly_chart(fig, use_container_width=True)
            
            st.divider()
            st.subheader("Drill-Down: Analyze a Specific Task's Risk Factors")
            high_risk_tasks = sorted_risk_df[sorted_risk_df['risk_probability'] > 0.5]['name'].tolist()
            if not high_risk_tasks:
                st.info("No tasks are currently predicted to be at high risk (>50% probability).")
            else:
                selected_task_name = st.selectbox("Select a high-risk task to analyze:", options=high_risk_tasks)
                
                task_data = risk_predictions_df[risk_predictions_df['name'] == selected_task_name].iloc[0]
                task_features_values = task_data[risk_features].values
                
                contributions = task_features_values * risk_model.coef_[0]
                contribution_df = pd.DataFrame({'feature': risk_features, 'contribution': contributions}).sort_values('contribution', ascending=True)
                
                fig_contrib = px.bar(contribution_df, x='contribution', y='feature', orientation='h',
                                     title=f'Risk Factor Contributions for "{selected_task_name}"',
                                     labels={'contribution': 'Impact on Risk (Log-Odds)', 'feature': 'Risk Factor'},
                                     color='contribution',
                                     color_continuous_scale=px.colors.sequential.RdBu_r,
                                     text_auto='.2f')
                fig_contrib.update_layout(showlegend=False, coloraxis_showscale=False)
                st.plotly_chart(fig_contrib, use_container_width=True)
                st.caption("Positive values increase the predicted risk of delay, while negative values decrease it.")

        else:
            st.info("Not enough historical data (e.g., tasks marked 'At Risk') to train a predictive model yet.")
    
    with ml_tabs[2]: # Clustering
        st.subheader("Clustering with K-Means")
        st.markdown("Automatically discover natural groupings or segments in your data using the K-Means algorithm. This is an example of **unsupervised learning** as no pre-existing labels are required.")
        with st.expander("The Purpose, Math Basis, Procedure, and Significance"):
            st.markdown("#### Purpose: Identify Hidden Structures")
            st.markdown("The primary goal of clustering is to partition data points into a number of groups (clusters) such that points in the same group are very similar to each other and different from points in other groups. This is useful for market segmentation (finding customer groups), anomaly detection (anomalies may form their own tiny cluster), or identifying distinct modes of process failure.")
            st.markdown("#### The Math Basis: Centroids and Euclidean Distance")
            st.markdown("K-Means works by minimizing the **within-cluster sum of squares (WCSS)**, also known as inertia. The algorithm iterates through these steps:\n1.  **Initialization:** `k` initial 'centroids' (the center point of a cluster) are chosen at random.\n2.  **Assignment Step:** Each data point is assigned to its nearest centroid, typically based on Euclidean distance.\n3.  **Update Step:** The centroids are moved to the center (mean) of all the data points assigned to them.\nSteps 2 and 3 are repeated until the centroids no longer move significantly, meaning the clusters have stabilized.")
            st.markdown("#### The Procedure: Choosing 'k' and Fitting")
            st.markdown("1.  **Select Features:** Choose the input variables (features) for clustering.\n2.  **Determine Optimal `k`:** A key challenge is choosing the right number of clusters (`k`). The **Elbow Method** is a common heuristic. We run K-Means for a range of `k` values (e.g., 1 to 10) and plot the inertia for each. The 'elbow' of the curve—the point where the rate of decrease in inertia sharply slows—suggests a good value for `k`.\n3.  **Fit and Visualize:** With the chosen `k`, the final model is trained, and the results are visualized on a scatter plot, with each point colored by its assigned cluster label.")
            st.markdown("#### Significance of the Results: Actionable Segments")
            st.markdown("The output is a label for each data point, indicating which cluster it belongs to. The significance lies in interpreting these clusters. By analyzing the characteristics of each cluster (e.g., 'Cluster 0 has high temperature and high pressure'), you can define actionable segments. For example, you might discover three distinct types of batch failures, each requiring a different corrective action, that were previously undiagnosed.")
        
        @st.cache_data
        def generate_clustering_data():
            X, _ = make_blobs(n_samples=300, centers=4, n_features=2, cluster_std=0.8, random_state=42)
            return pd.DataFrame(X, columns=['Feature A', 'Feature B'])

        @st.cache_data
        def find_optimal_k(data):
            inertia = []
            k_range = range(1, 11)
            for k in k_range:
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10).fit(data)
                inertia.append(kmeans.inertia_)
            return pd.DataFrame({'k': k_range, 'inertia': inertia})

        cluster_df = generate_clustering_data()
        inertia_df = find_optimal_k(cluster_df)
        
        st.markdown("**1. Determine Optimal Number of Clusters (`k`)**")
        fig_elbow = px.line(inertia_df, x='k', y='inertia', title='Elbow Method for Optimal k', markers=True)
        fig_elbow.add_annotation(x=4, y=inertia_df.loc[3, 'inertia'], text="Elbow point suggests k=4", showarrow=True, arrowhead=1)
        st.plotly_chart(fig_elbow, use_container_width=True)
        
        st.markdown("**2. Fit Model and Visualize Clusters**")
        k = st.slider("Select number of clusters (k)", min_value=2, max_value=10, value=4)
        
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10).fit(cluster_df)
        cluster_df['Cluster'] = kmeans.labels_.astype(str)
        centroids = kmeans.cluster_centers_

        fig_cluster = px.scatter(cluster_df, x='Feature A', y='Feature B', color='Cluster',
                                 title=f'K-Means Clustering Results (k={k})',
                                 color_discrete_sequence=px.colors.qualitative.Plotly)
        fig_cluster.add_trace(go.Scatter(x=centroids[:,0], y=centroids[:,1], mode='markers',
                                         marker=dict(symbol='star', color='black', size=15, line=dict(color='white', width=1)),
                                         name='Centroids'))
        st.plotly_chart(fig_cluster, use_container_width=True)

    with ml_tabs[3]: # Anomaly Detection
        st.subheader("Anomaly Detection with Isolation Forest")
        st.markdown("Identify unusual data points (outliers) that do not conform to the expected pattern of the majority of the data.")
        with st.expander("The Purpose, Math Basis, Procedure, and Significance"):
            st.markdown("#### Purpose: Find the 'Needle in a Haystack'")
            st.markdown("Anomaly detection is critical for finding manufacturing defects, fraudulent transactions, network intrusions, or any rare event that requires investigation. Unlike clustering, the goal is not to find groups, but to find the individual points that are 'different' from all groups.")
            st.markdown("#### The Math Basis: The 'Ease of Isolation'")
            st.markdown("The Isolation Forest algorithm is built on an intuitive principle: **anomalies are easier to 'isolate' from the rest of the data than normal points.** The algorithm works by:\n1.  Building a collection of 'Isolation Trees' (hence the 'Forest').\n2.  For each tree, the data is randomly sub-sampled and partitioned by selecting a random feature and a random split value for that feature.\n3.  This splitting continues until the data point of interest is isolated in its own node.\n4.  The **path length** (number of splits) to isolate a point is averaged across all trees. Anomalies, being few and different, will have very short average path lengths, while normal points will require many splits to isolate.")
            st.markdown("#### The Procedure: Training and Prediction")
            st.markdown("1.  **Select Features:** Choose the input variables for the model.\n2.  **Set Contamination:** The user provides an estimate of the proportion of outliers in the data (the `contamination` hyperparameter). This acts as a threshold for the decision function.\n3.  **Train Model:** An `IsolationForest` model is trained on the data.\n4.  **Predict:** The model predicts a label for each data point: `1` for an inlier (normal) and `-1` for an outlier (anomaly).")
            st.markdown("#### Significance of the Results: Actionable Flags")
            st.markdown("The primary output is a flag identifying each data point as either an inlier or an outlier. This allows for immediate action:\n- **Process Control:** Outliers in manufacturing data can be automatically flagged for quality inspection.\n- **Root Cause Analysis:** Investigating the characteristics of the identified outliers can reveal underlying problems in a process or system.\n- **Data Cleaning:** Outliers can be reviewed and potentially removed before training other machine learning models to improve their performance.")

        @st.cache_data
        def generate_anomaly_data():
            rng = np.random.default_rng(10)
            X_inliers, _ = make_blobs(n_samples=300, centers=[[0,0]], cluster_std=0.5, random_state=0)
            X_outliers = rng.uniform(low=-4, high=4, size=(15, 2))
            X = np.concatenate([X_inliers, X_outliers])
            return pd.DataFrame(X, columns=['Process Parameter 1', 'Process Parameter 2'])

        anomaly_df = generate_anomaly_data()
        st.markdown("**1. Set Anomaly Detection Threshold**")
        contamination = st.slider("Select contamination percentage:", min_value=0.01, max_value=0.25, value=0.05, step=0.01, format="%.2f")

        st.markdown("**2. Fit Model and Visualize Outliers**")
        iso_forest = IsolationForest(contamination=contamination, random_state=42)
        predictions = iso_forest.fit_predict(anomaly_df)
        anomaly_df['Status'] = np.where(predictions == -1, 'Outlier', 'Inlier')
        
        fig_anomaly = px.scatter(anomaly_df, x='Process Parameter 1', y='Process Parameter 2', color='Status',
                                 title=f"Anomaly Detection Results ({contamination:.0%} Contamination)",
                                 color_discrete_map={'Inlier': '#1f77b4', 'Outlier': '#d62728'},
                                 symbol='Status', symbol_map={'Inlier': 'circle', 'Outlier': 'x'})
        fig_anomaly.update_traces(selector=dict(name='Outlier'), marker_size=12)
        st.plotly_chart(fig_anomaly, use_container_width=True)

    with ml_tabs[4]: # Time Series
        st.subheader("Time Series Forecasting with SARIMA")
        st.markdown("Predict future values of a metric based on its historical behavior, accounting for trends, seasonality, and other time-based patterns.")
        with st.expander("The Purpose, Math Basis, Procedure, and Significance"):
            st.markdown("#### Purpose: Predict the Future")
            st.markdown("Time series forecasting is used to predict future events based on time-ordered historical data. It is vital for demand planning, capacity management, financial forecasting, and predicting trends in quality metrics like complaint rates or defect counts.")
            st.markdown("#### The Math Basis: SARIMA")
            st.markdown("SARIMA stands for **Seasonal AutoRegressive Integrated Moving Average**. It is a powerful statistical model that breaks a time series down into several components:\n- **AR (AutoRegressive):** A regression of the series against its own past values (lags).\n- **I (Integrated):** The use of differencing to make the series stationary (i.e., remove trends and seasonality).\n- **MA (Moving Average):** A model that uses the dependency between an observation and the residual errors from a moving average model applied to lagged observations.\n- **S (Seasonal):** The extension of the AR, I, and MA components to handle seasonality (patterns that repeat at regular intervals, e.g., yearly, quarterly).")
            st.markdown("#### The Procedure: Fit, Predict, Visualize")
            st.markdown("1.  **Data Preparation:** The data must be a time-ordered sequence.\n2.  **Model Identification:** In a full analysis, one would analyze ACF and PACF plots to determine the optimal model orders (p, d, q) and (P, D, Q, s). For this tool, we use a common set of parameters as an example.\n3.  **Fitting:** A SARIMA model is fitted to the historical data.\n4.  **Forecasting:** The fitted model is used to predict future values. It also generates confidence intervals, which represent the uncertainty in the forecast.")
            st.markdown("#### Significance of the Results: Planning and Proactive Action")
            st.markdown("The output is a forecast of future values along with an uncertainty band.\n- **The Forecast:** Provides a quantitative estimate for future planning. For example, a forecast of rising complaints can trigger a proactive investigation *before* the problem becomes severe.\n- **The Confidence Interval:** This is equally important. A wide interval indicates high uncertainty in the forecast, while a narrow interval indicates high confidence. This helps in risk assessment and understanding the reliability of the prediction.")

        @st.cache_data
        def generate_ts_data():
            t = np.arange(100)
            trend = 0.5 * t
            seasonality = 10 * np.sin(2 * np.pi * t / 12) # 12-month seasonality
            noise = np.random.normal(0, 5, 100)
            series = 50 + trend + seasonality + noise
            dates = pd.date_range(start='2020-01-01', periods=100, freq='MS')
            return pd.Series(series, index=dates)

        ts_data = generate_ts_data()
        st.markdown("**1. Historical Data (Example: Monthly Complaints)**")
        st.line_chart(ts_data)
        
        st.markdown("**2. Fit Model and Generate Forecast**")
        n_forecast = st.slider("Select number of periods to forecast:", min_value=12, max_value=48, value=24)
        
        # Fit SARIMA model (example orders)
        model = ARIMA(ts_data, order=(1,1,1), seasonal_order=(1,1,1,12)).fit()
        forecast = model.get_forecast(steps=n_forecast)
        forecast_mean = forecast.predicted_mean
        forecast_ci = forecast.conf_int()

        fig_ts = go.Figure()
        fig_ts.add_trace(go.Scatter(x=ts_data.index, y=ts_data, mode='lines', name='Historical Data'))
        fig_ts.add_trace(go.Scatter(x=forecast_mean.index, y=forecast_mean, mode='lines', name='Forecast', line=dict(dash='dash', color='red')))
        fig_ts.add_trace(go.Scatter(x=forecast_ci.index, y=forecast_ci.iloc[:, 0], mode='lines', name='Lower CI', line=dict(width=0), showlegend=False))
        fig_ts.add_trace(go.Scatter(x=forecast_ci.index, y=forecast_ci.iloc[:, 1], mode='lines', name='95% Confidence Interval', line=dict(width=0), fill='tonexty', fillcolor='rgba(255, 0, 0, 0.1)'))
        fig_ts.update_layout(title="Time Series Forecast with SARIMA", yaxis_title="Number of Complaints")
        st.plotly_chart(fig_ts, use_container_width=True)


def render_compliance_guide_tab():
    """Renders the static educational content for the QE & Compliance Guide tab."""
    st.header("🏛️ A Guide to Design Controls & the Regulatory Landscape")
    st.markdown("This section provides a high-level overview of the Design Controls methodology and the key regulations and standards governing medical device development.")
    st.subheader("Navigating the Regulatory Maze for Combination Products")
    st.info("A 'Combination Product' like the Smart-Pill contains both device and drug components, so it must comply with regulations for both.")
    with st.expander("▶️ **21 CFR Part 4: The 'Rulebook for Rulebooks'**"): st.markdown("Part 4 governs combination products. It doesn't add new requirements, but instead tells you **which existing regulations to apply**. For the Smart-Pill, this means:\n- The **device aspects** (casing, electronics, software) must follow the **Quality System Regulation (QSR) for devices**.\n- The **drug aspects** (formulation, stability, purity) must follow the **Current Good Manufacturing Practices (cGMP) for drugs**.\n- Design Controls (part of the QSR) must consider the entire system, including how the device and drug interact.")
    with st.expander("▶️ **21 CFR Part 820: The Quality System Regulation (QSR) for Devices**"): st.markdown("This is the FDA's rulebook for medical device manufacturing and design. The Design Controls section (`820.30`) is the foundation of this entire application. It mandates a systematic approach to design to ensure the final product is safe and effective.\n- **Applies to:** The physical pill, its electronics, the embedded software, and the companion mobile app.\n- **Key Principle:** You must document everything to prove you designed the device in a state of control. The DHF is that proof.")
    with st.expander("▶️ **21 CFR Parts 210/211 & CGMP in a Design Context**"): st.markdown("This is the FDA's rulebook for pharmaceutical products. While this app focuses on the DHF (a device concept), design decisions for the device constituent part must be made with CGMP in mind. The goal is to ensure the final, combined product can be manufactured reliably, safely, and consistently.\n- **Material Compatibility:** The pill casing cannot contaminate or react with the drug. This is a design choice verified during V&V.\n- **Stability:** The device cannot cause the drug to degrade over its shelf life. This is confirmed via **Stability Studies**, a key CGMP activity.\n- **Sterilizability:** The design materials and construction must be compatible with the chosen sterilization method (e.g., EtO, gamma) without damaging the device or the drug.\n- **Aseptic Processing:** If applicable, the device must be designed to be assembled and filled in a sterile environment without introducing contamination.")
    with st.expander("▶️ **ISO 13485:2016: Quality Management Systems (International Standard)**"): st.markdown("ISO 13485 is the internationally recognized standard for a medical device Quality Management System (QMS). It is very similar to the FDA's QSR but is required for market access in many other regions, including Europe (as part of MDR), Canada, and Australia.\n- **Relationship to QSR:** Following the QSR gets you very close to ISO 13485 compliance. The key difference is that ISO 13485 places a stronger emphasis on **risk management** throughout the entire QMS.\n- **Why it matters:** A DHF built to QSR standards is easily adaptable for ISO 13485 audits, enabling global market strategies.")
    with st.expander("▶️ **ISO 14971:2019: Risk Management for Medical Devices (International Standard)**"): st.markdown("This is the global 'how-to' guide for risk management. Both the FDA and international regulators consider it the state-of-the-art process for ensuring device safety.\n- **Process:** It defines a lifecycle approach: identify hazards, estimate and evaluate risks, implement controls, and monitor the effectiveness of those controls.\n- **Role in this App:** The **'2. Risk Management'** section of the DHF Explorer is a direct implementation of the documentation required by ISO 14971.")
    st.divider(); st.subheader("The Role of a Design Assurance Quality Engineer")
    st.markdown("A Design Assurance QE is the steward of the DHF, ensuring compliance, quality, and safety are designed into the product from day one. This tool is designed to be their primary workspace. Key responsibilities within this framework include:")
    with st.expander("✅ **Owning the Design History File (DHF)**"): st.markdown("The QE is responsible for the **creation, remediation, and maintenance** of the DHF. It's not just a repository; it's a living document that tells the story of the product's development.\n- This application serves as the DHF's active workspace.\n- **Key QE Goal:** Ensure the DHF is complete, coherent, and audit-ready at all times. The Traceability Matrix is the QE's primary tool for identifying gaps.")
    with st.expander("✅ **Driving Verification & Validation (V&V) Strategy**"): st.markdown("The QE doesn't just witness tests; they help architect the entire V&V strategy.\n- **V&V Master Plan:** This is a high-level document, referenced in the Design Plan, that outlines the scope, methods, and acceptance criteria for all V&V activities.\n- **Protocol & Report Review:** The QE reviews and approves all test protocols (to ensure they are adequate) and reports (to ensure they are accurate and complete). The 'Design Verification' and 'Design Validation' sections track these deliverables.")
    with st.expander("✅ **Advanced Quality Engineering Concepts**"):
        st.markdown("""Beyond foundational Design Controls, a Senior QE leverages advanced methodologies to ensure quality is built into the product proactively, not inspected in later. This is the core of **First-Time-Right (FTR)** initiatives, which aim to reduce the **Cost of Poor Quality (COPQ)**—the significant expenses associated with scrap, rework, complaints, and recalls.
- **Quality by Design (QbD):** A systematic approach that begins with predefined objectives and emphasizes product and process understanding and control. The key is to identify **Critical Quality Attributes (CQAs)**—the physical, chemical, or biological characteristics that must be within a specific limit to ensure the desired product quality. These CQAs are then linked to the **Critical Material Attributes (CMAs)** of the raw materials and the **Critical Process Parameters (CPPs)** of the manufacturing process. The **QbD Tracker** on the main dashboard visualizes these crucial linkages.
- **Failure Mode and Effects Analysis (FMEA):** A bottom-up, systematic tool for analyzing potential failure modes in a system. It is a core part of the risk management process.
- **Design of Experiments (DOE):** A statistical tool used to systematically determine the relationship between inputs (factors) and outputs of a process. Instead of testing one factor at a time, DOE allows for efficient exploration of the **design space**. It is used to identify the most critical CPPs and optimize their settings to ensure the process robustly produces products that meet their CQAs. The **DOE Analysis** tool in the `AI & Statistical Tools` tab provides a practical example.
- **Statistical Process Control (SPC):** A method of quality control which employs statistical methods to monitor and control a process. This helps to ensure that the process operates efficiently, producing more specification-conforming product with less waste. The **SPC Chart** in the `AI & Statistical Tools` tab is a practical implementation.
- **Process Capability (Cpk):** A statistical measure of a process's ability to produce output within specification limits. A Cpk value of **1.33 is considered capable**, while **1.67 is considered highly capable (6-sigma level)**. The 'Audit & Continuous Improvement' dashboard tracks this metric.""")
    st.divider(); st.subheader("Visualizing the Process: The V-Model")
    st.markdown("The V-Model is a powerful way to visualize the Design Controls process, emphasizing the critical link between design (left side) and testing (right side).")
    try:
        v_model_image_path = os.path.join(project_root, "dhf_dashboard", "v_model_diagram.png")
        if os.path.exists(v_model_image_path):
            _, img_col, _ = st.columns([1, 2, 1])
            img_col.image(v_model_image_path, caption="The V-Model illustrates the relationship between design decomposition and integration/testing.", width=600)
        else:
            st.error(f"Image Not Found: Ensure `v_model_diagram.png` is in the `dhf_dashboard` directory.", icon="🚨"); logger.warning(f"Could not find v_model_diagram.png at path: {v_model_image_path}")
    except Exception as e: st.error("An error occurred while trying to display the V-Model image."); logger.error(f"Error loading V-Model image: {e}", exc_info=True)
    col1, col2 = st.columns(2)
    with col1: st.subheader("Left Side: Decomposition & Design"); st.markdown("- **User Needs & Intended Use:** What problem does the user need to solve?\n- **Design Inputs (Requirements):** How must the device perform to meet those needs? This includes technical, functional, and safety requirements.\n- **System & Architectural Design:** How will the components be structured to meet the requirements?\n- **Detailed Design (Outputs):** At the lowest level, these are the final drawings, code, and specifications that are used to build the device.")
    with col2: st.subheader("Right Side: Integration & Testing"); st.markdown("- **Unit/Component Verification:** Does each individual part meet its detailed design specification?\n- **Integration & System Verification:** Do the assembled parts work together as defined in the architectural design?\n- **Design Validation:** Does the final, complete device meet the high-level User Needs? This is the ultimate test.")
    st.success("""#### The Core Principle: Verification vs. Validation
- **Verification (Horizontal Arrows):** Answers the question, **"Are we building the product right?"** It is the process of confirming that a design output meets its specified input requirements (e.g., does the code correctly implement the detailed design?).
- **Validation (Top-Level Arrow):** Answers the question, **"Are we building the right product?"** It is the process of confirming that the final, finished product meets the user's actual needs and its intended use.""")


# ==============================================================================
# --- MAIN APPLICATION LOGIC ---
# ==============================================================================
def main() -> None:
    """Main function to configure and run the Streamlit application."""
    st.set_page_config(layout="wide", page_title="DHF Command Center", page_icon="🚀")
    
    try:
        ssm = SessionStateManager()
        logger.info("Application initialized. Session State Manager loaded.")
    except Exception as e:
        st.error("Fatal Error: Could not initialize Session State. The application cannot continue.")
        logger.critical(f"Failed to instantiate SessionStateManager: {e}", exc_info=True)
        st.stop()

    try:
        tasks_raw = ssm.get_data("project_management", "tasks")
        tasks_df_processed = preprocess_task_data(tasks_raw)
        
        # OPTIMIZATION: Pre-group document data for efficient lookup.
        docs_df = get_cached_df(ssm.get_data("design_outputs", "documents"))
        if 'phase' in docs_df.columns:
            # Create a dictionary mapping each phase to its corresponding DataFrame slice
            docs_by_phase = {phase: data for phase, data in docs_df.groupby('phase')}
        else:
            docs_by_phase = {}

    except Exception as e:
        st.error("Failed to process initial project data for dashboard.")
        logger.error(f"Error during initial data pre-processing: {e}", exc_info=True)
        tasks_df_processed = pd.DataFrame()
        docs_by_phase = {}

    st.title("🚀 DHF Command Center")
    project_name = ssm.get_data("design_plan", "project_name")
    st.caption(f"Live monitoring for the **{project_name or 'N/A'}** project.")

    tab_names = ["📊 **DHF Health Dashboard**", "🗂️ **DHF Sections Explorer**", "🔬 **Advanced Analytics**", "📈 **Statistical Workbench**", "🤖 **Machine Learning Lab**", "🏛️ **QE & Compliance Guide**"]
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(tab_names)

    with tab1: render_health_dashboard_tab(ssm, tasks_df_processed, docs_by_phase)
    with tab2: render_dhf_explorer_tab(ssm)
    with tab3: render_advanced_analytics_tab(ssm)
    with tab4: render_statistical_tools_tab(ssm)
    with tab5: render_machine_learning_lab_tab(ssm)
    with tab6: render_compliance_guide_tab()

# ==============================================================================
# --- SCRIPT EXECUTION ---
# ==============================================================================
if __name__ == "__main__":
    main()
