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
import copy # Import the copy module for deep copying
from datetime import timedelta
from typing import Any, Dict, List

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
        logging.basicConfig(level=logging.INFO)
        logging.info(f"Added project root to sys.path: {project_root}")
except Exception as e:
    st.error(f"Critical Error: Could not adjust system path. {e}")
    logging.critical(f"Error adjusting system path: {e}", exc_info=True)
# --- End of Path Correction Block ---

# --- Local Application Imports ---
from dhf_dashboard.analytics.action_item_tracker import render_action_item_tracker
from dhf_dashboard.analytics.traceability_matrix import render_traceability_matrix
from dhf_dashboard.dhf_sections import (
    design_changes, design_inputs, design_outputs, design_plan, design_reviews,
    design_risk_management, design_transfer, design_validation,
    design_verification, human_factors
)
from dhf_dashboard.utils.critical_path_utils import find_critical_path
from dhf_dashboard.utils.plot_utils import (
    _RISK_CONFIG,  # Import the canonical risk configuration
    create_action_item_chart, create_progress_donut, create_risk_profile_chart)
from dhf_dashboard.utils.session_state_manager import SessionStateManager

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
    tasks_df['display_text'] = tasks_df.apply(lambda r: f"<b>{r.get('name', '')}</b> ({r.get('completion_pct', 0)}%)", axis=1)
    return tasks_df

@st.cache_data
def get_cached_df(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """Generic function to cache the creation of DataFrames from lists of dicts."""
    return pd.DataFrame(data) if data else pd.DataFrame()


# ==============================================================================
# --- DASHBOARD DEEP-DIVE COMPONENT FUNCTIONS ---
# ==============================================================================

def render_dhf_completeness_panel(ssm: SessionStateManager, tasks_df: pd.DataFrame) -> None:
    """
    Renders the DHF completeness and gate readiness panel.
    Displays DHF phases as subheaders and a project timeline Gantt chart.
    """
    st.subheader("1. DHF Completeness & Gate Readiness")
    st.markdown("Monitor the flow of Design Controls from inputs to outputs, including cross-functional sign-offs and DHF document status.")

    try:
        tasks_raw = ssm.get_data("project_management", "tasks")
        docs_df = get_cached_df(ssm.get_data("design_outputs", "documents"))

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
                phase_docs = docs_df[docs_df['phase'] == task_name] if 'phase' in docs_df.columns else pd.DataFrame()
                if not phase_docs.empty:
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
            
            df['S_jitter'] = df['S'] + np.random.uniform(-0.1, 0.1, len(df))
            df['O_jitter'] = df['O'] + np.random.uniform(-0.1, 0.1, len(df))

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

def render_health_dashboard_tab(ssm: SessionStateManager, tasks_df: pd.DataFrame):
    """
    Renders the main DHF Health Dashboard tab, enhanced for executive-level
    at-a-glance assessment and deep-dive analysis.
    """
    st.header("Executive Health Summary")
    
    # --- Health Score & KHI Calculation ---
    schedule_score = 0
    if not tasks_df.empty:
        today = pd.to_datetime('today'); overdue_in_progress = tasks_df[(tasks_df['status'] == 'In Progress') & (tasks_df['end_date'] < today)]
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
    
    # FIX: Use a deep copy of the action items to prevent session state mutation.
    action_items_for_burndown = []
    if reviews_data:
        for review in copy.deepcopy(reviews_data):
            review_date = pd.to_datetime(review.get('date'))
            for item_data in review.get('action_items', []):
                item_data['review_date'] = review_date
                action_items_for_burndown.append(item_data)
            
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
    st.subheader("Action Item Burn-down (Last 30 Days)")
    burndown_df_source = get_cached_df(action_items_for_burndown)
    if not burndown_df_source.empty:
        df = burndown_df_source.copy()
        # FIX: Ensure all date columns are consistently converted to datetime objects
        df['created_date'] = pd.to_datetime(df['review_date']) + pd.to_timedelta(np.random.randint(0, 2, len(df)), unit='d')
        df['due_date'] = pd.to_datetime(df['due_date'], errors='coerce')
        df['completion_date'] = pd.NaT 
        
        completed_mask = df['status'] == 'Completed'
        if completed_mask.any():
            completed_items = df[completed_mask].copy()
            lifespan = (completed_items['due_date'] - completed_items['created_date']).dt.days.fillna(1).astype(int)
            lifespan = lifespan.apply(lambda d: max(1, d))
            completion_days = [np.random.randint(1, d + 1) for d in lifespan]
            df.loc[completed_mask, 'completion_date'] = completed_items['created_date'] + pd.to_timedelta(completion_days, unit='d')

        today = pd.to_datetime('today'); date_range = pd.date_range(end=today, periods=30, freq='D')
        daily_open_counts = []
        for day in date_range:
            created_on_or_before = df['created_date'] <= day
            completed_on_or_before = df['completion_date'].notna() & (df['completion_date'] <= day)
            net_open = created_on_or_before.sum() - completed_on_or_before.sum()
            daily_open_counts.append(net_open)
        
        burndown_df = pd.DataFrame({'date': date_range, 'open_items': daily_open_counts})
        fig = go.Figure(); fig.add_trace(go.Scatter(x=burndown_df['date'], y=burndown_df['open_items'], mode='lines+markers', name='Open Items', fill='tozeroy', line=dict(color='rgb(0,100,80)'), hovertemplate='<b>%{x|%Y-%m-%d}</b><br>Open Items: %{y}<extra></extra>'))
        fig.update_layout(title="Trend of Total Open Action Items", yaxis_title="Number of Open Items", height=300); st.plotly_chart(fig, use_container_width=True)
    else: st.caption("No action item data to generate a burn-down chart.")
    st.divider()
    st.header("Deep Dives")
    with st.expander("Expand to see Phase Gate Readiness & Timeline Details"):
        render_dhf_completeness_panel(ssm, tasks_df)
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
            tasks_df_to_edit = pd.DataFrame(ssm.get_data("project_management", "tasks"))
            tasks_df_to_edit['start_date'] = pd.to_datetime(tasks_df_to_edit['start_date'], errors='coerce'); tasks_df_to_edit['end_date'] = pd.to_datetime(tasks_df_to_edit['end_date'], errors='coerce')
            original_df = tasks_df_to_edit.copy()
            edited_df = st.data_editor(
                tasks_df_to_edit, key="main_task_editor", num_rows="dynamic", use_container_width=True,
                column_config={"start_date": st.column_config.DateColumn("Start Date", format="YYYY-MM-DD", required=True), "end_date": st.column_config.DateColumn("End Date", format="YYYY-MM-DD", required=True)})
            if not original_df.equals(edited_df):
                df_to_save = edited_df.copy()
                df_to_save['start_date'] = df_to_save['start_date'].dt.strftime('%Y-%m-%d').replace({pd.NaT: None})
                df_to_save['end_date'] = df_to_save['end_date'].dt.strftime('%Y-%m-%d').replace({pd.NaT: None})
                ssm.update_data(df_to_save.to_dict('records'), "project_management", "tasks")
                st.toast("Project tasks updated! Rerunning...", icon="✅"); st.rerun()
        except Exception as e: st.error("Could not load the Project Task Editor."); logger.error(f"Error in task editor: {e}", exc_info=True)

def render_statistical_tools_tab(ssm: SessionStateManager):
    """Renders the Statistical Workbench tab with professionally enhanced tools."""
    st.header("📈 Statistical Workbench")
    st.info("Utilize this interactive workbench to apply rigorous statistical methods, moving from raw data to actionable, data-driven decisions.")
    try:
        import statsmodels.api as sm
        from statsmodels.formula.api import ols
        from scipy.stats import shapiro, mannwhitneyu
    except ImportError:
        st.error("This tab requires `statsmodels` and `scipy`. Please install them (`pip install statsmodels scipy`) to enable statistical tools.", icon="🚨"); return
    tool_tabs = st.tabs(["Process Control (SPC)", "Hypothesis Testing (A/B Test)", "Pareto Analysis (FMEA)", "Design of Experiments (DOE)"])
    with tool_tabs[0]:
        st.subheader("Statistical Process Control (SPC) with Rule Checking")
        st.markdown("Monitor process stability by distinguishing natural variation from signals that require investigation.")
        with st.expander("The 'Why' and the 'How'"):
            st.markdown("##### The 'Why': Voice of the Process vs. Voice of the Customer")
            st.markdown("""- **Specification Limits (USL/LSL):** The 'voice of the customer' or engineer. They define what is acceptable for the product to function.\n- **Control Limits (UCL/LCL):** The 'voice of the process'. Calculated from the data, they define the bounds of natural, expected variation.\n**A process can be *in control* but still produce parts *out of specification*, and vice-versa.** This tool helps diagnose both issues.""")
            st.markdown("##### The 'How': Automated Rule Checking")
            st.markdown("Beyond just plotting, this tool programmatically applies common **Nelson Rules** to detect instability. A process is flagged as 'UNSTABLE' if, for example:\n- **Rule 1:** One or more points fall outside the control limits (±3σ).\n- **Rule 2:** Nine or more consecutive points fall on the same side of the centerline.")
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
    with tool_tabs[1]:
        st.subheader("Hypothesis Testing with Assumption Checks")
        st.markdown("Rigorously determine if a statistically significant difference exists between two groups (e.g., Supplier A vs. Supplier B).")
        with st.expander("The 'Why' and the 'How'"):
            st.markdown("##### The 'Why': Data-Driven Sourcing and Process Changes")
            st.markdown("This tool prevents decisions based on 'gut feel'. For example, before committing to a more expensive supplier, you can prove their material is *statistically stronger*, justifying the cost. It provides objective evidence for change control records.")
            st.markdown("##### The 'How': A Statistically Robust Workflow")
            st.markdown("""1.  **Check for Normality:** Many statistical tests, like the t-test, assume the data is normally distributed. We first use the **Shapiro-Wilk test**. If the p-value is high (> 0.05), we can assume normality.\n2.  **Select the Right Test:**\n    - If data is **normal**, we use **Welch's t-test**, a robust version of the t-test that doesn't assume equal variances.\n    - If data is **not normal**, we automatically switch to the **Mann-Whitney U test**, a non-parametric equivalent that compares medians instead of means.\n3.  **Interpret the Result:** We compare the final p-value to our significance level (α = 0.05) to conclude if a significant difference exists.""")
        try:
            ht_data = ssm.get_data("quality_system", "hypothesis_testing_data")
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
    with tool_tabs[2]:
        st.subheader("Pareto Analysis of FMEA Risk")
        st.markdown("Applies the 80/20 rule to FMEA data to identify the 'vital few' failure modes that drive the majority of risk, enabling focused mitigation efforts.")
        with st.expander("The 'Why' and the 'How'"):
            st.markdown("##### The 'Why': Maximize Impact with Limited Resources")
            st.markdown("In any complex system, not all failure modes are created equal. This tool prevents wasting time on low-risk issues by identifying the 20% of failure modes that are causing 80% of the risk (as measured by RPN). It's a key tool for prioritizing design changes and process improvements.")
            st.markdown("##### The 'How': In This Application")
            st.markdown("We combine dFMEA and pFMEA data, calculate `RPN = S × O × D` for each, and sort them in descending order. The bar chart shows the RPN for each failure mode, while the line shows the cumulative percentage of total RPN. **Action is focused on the items on the left** until the cumulative line begins to flatten, typically around the 80% mark.")
        try:
            fmea_df = pd.concat([get_cached_df(ssm.get_data("risk_management_file", "dfmea")), get_cached_df(ssm.get_data("risk_management_file", "pfmea"))], ignore_index=True)
            if not fmea_df.empty:
                fmea_df['RPN'] = fmea_df['S'] * fmea_df['O'] * fmea_df['D']; fmea_df = fmea_df.sort_values('RPN', ascending=False)
                fmea_df['cumulative_pct'] = (fmea_df['RPN'].cumsum() / fmea_df['RPN'].sum()) * 100
                fig = go.Figure(); fig.add_trace(go.Bar(x=fmea_df['failure_mode'], y=fmea_df['RPN'], name='RPN', marker_color='#1f77b4'))
                fig.add_trace(go.Scatter(x=fmea_df['failure_mode'], y=fmea_df['cumulative_pct'], name='Cumulative %', yaxis='y2', line=dict(color='#d62728')))
                fig.update_layout(title="FMEA Pareto Chart: Prioritizing Risk", yaxis=dict(title='RPN'), yaxis2=dict(title='Cumulative %', overlaying='y', side='right', range=[0, 105]), xaxis_title='Failure Mode', showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            else: st.warning("No FMEA data available for Pareto analysis.")
        except Exception as e: st.error("Could not generate Pareto chart."); logger.error(f"Error in Pareto Analysis tool: {e}", exc_info=True)
    with tool_tabs[3]:
        st.subheader("Design of Experiments (DOE) with ANOVA")
        st.markdown("Efficiently determine which process inputs (**factors**) and their interactions significantly impact a key output (**response**).")
        with st.expander("The 'Why' and the 'How'"):
            st.markdown("##### The 'Why': Optimize Your Process, Don't Just Guess")
            st.markdown("Instead of testing 'one factor at a time' (OFAT), which is inefficient and misses interactions, DOE allows you to explore the entire **design space**. It provides a mathematical model of your process, enabling you to find the optimal settings to maximize performance and robustness.")
            st.markdown("##### The 'How': Regression Modeling and ANOVA")
            st.markdown("""1.  **Fit a Model:** We use a statistical technique called Ordinary Least Squares (OLS) to fit a linear model to the data. The formula `seal_strength ~ temperature * pressure` tells the model to consider the main effects of Temperature, Pressure, and their **interaction effect (Temp:Pressure)**.\n2.  **Analyze Variance (ANOVA):** We then generate an ANOVA table from the model. This table is the core result. It breaks down the variance in the response and attributes it to each factor. **A low p-value (< 0.05) for a factor in the ANOVA table means it has a statistically significant effect on the response.**\n3.  **Visualize and Optimize:** The Main Effects plot shows the direction of influence, while the Contour Plot visualizes the modeled response surface. We then programmatically find and display the settings that yield the predicted maximum response.""")
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

def render_machine_learning_lab_tab(ssm: SessionStateManager):
    """Renders the Machine Learning Lab tab with professionally enhanced, interactive visualizations."""
    st.header("🤖 Machine Learning Lab")
    st.info("Utilize predictive models to forecast outcomes, enabling proactive quality control and project management.")

    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import confusion_matrix
        import shap
    except ImportError:
        st.error("This tab requires `scikit-learn` and `shap`. Please install them (`pip install scikit-learn shap`) to enable ML features.", icon="🚨")
        return

    ml_tabs = st.tabs(["Predictive Quality (Batch Failure)", "Predictive Project Risk (Task Delay)"])

    with ml_tabs[0]:
        st.subheader("Predictive Quality: Manufacturing Batch Failure")
        st.markdown("This model predicts whether a manufacturing batch will **Pass** or **Fail** based on its process parameters, *before* the batch is run.")

        with st.expander("The 'Why' and the 'How'"):
            st.markdown("#### The 'Why': Business Justification")
            st.markdown("""- **Proactive vs. Reactive:** Instead of discovering a failed batch during final inspection (reactive), this model predicts failure ahead of time (proactive).\n- **COPQ Reduction:** It significantly reduces the Cost of Poor Quality (COPQ) by preventing scrap, rework, and wasted materials.\n- **Process Understanding:** The model's *feature importances* tell engineers which process parameters have the biggest impact on quality, guiding process optimization efforts (like a DOE).""")
            st.markdown("#### The 'How': Advanced Interpretation with SHAP")
            st.markdown("""We train a **Random Forest Classifier** and then use **SHAP (SHapley Additive exPlanations)** to interpret its predictions.\n- **Feature Importance Plot:** This bar chart shows the average impact of each feature on the model's prediction. Higher values mean more importance.\n- **SHAP Summary Plot:** This is a major upgrade that shows not only *which* features are important but also *how* their values impact the prediction. Red dots indicate high feature values, blue dots indicate low values. Dots to the right push the model towards predicting "Fail", while dots to the left push towards "Pass".\n- **Enhanced Confusion Matrix:** Our new matrix is a professional heatmap that includes clear labels and percentages for intuitive performance assessment.""")

        @st.cache_data
        def generate_and_train_quality_model():
            """Generates synthetic quality data and trains a Random Forest model."""
            np.random.seed(42); n_samples = 500
            data = {'temperature': np.random.normal(90, 5, n_samples), 'pressure': np.random.normal(300, 20, n_samples), 'viscosity': np.random.normal(50, 3, n_samples)}
            df = pd.DataFrame(data)
            fail_conditions = (df['temperature'] > 98) | (df['temperature'] < 82) | (df['pressure'] > 330) | (df['viscosity'] < 45)
            df['status'] = np.where(fail_conditions, 'Fail', 'Pass'); df['status_code'] = df['status'].apply(lambda x: 1 if x == 'Fail' else 0)
            X = df[['temperature', 'pressure', 'viscosity']]; y = df['status_code']
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
            model = RandomForestClassifier(n_estimators=100, random_state=42); model.fit(X_train, y_train)
            return model, X_train, X_test, y_train, y_test
        
        model, X_train, X_test, y_train, y_test = generate_and_train_quality_model()
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Model Performance (Test Set)**")
            st.caption("How well did the model predict on unseen data?")
            y_pred = model.predict(X_test)
            cm = confusion_matrix(y_test, y_pred)
            cm_percent = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
            
            labels = [["True Negative", "False Positive"], ["False Negative", "True Positive"]]
            annotations = [[f"{labels[i][j]}<br>{cm[i][j]}<br>({cm_percent[i][j]:.2%})" for j in range(2)] for i in range(2)]

            fig = go.Figure(data=go.Heatmap(
                   z=cm, x=['Predicted Pass', 'Predicted Fail'], y=['Actual Pass', 'Actual Fail'],
                   hoverongaps=False, colorscale='Blues', showscale=False,
                   text=annotations, texttemplate="%{text}"))
            fig.update_layout(height=300, margin=dict(l=10, r=10, t=40, b=10), title_x=0.5, title_text="<b>Confusion Matrix</b>")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("**Overall Feature Importance**")
            st.caption("Which factors have the largest average impact?")
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X_test)
            
            # --- DEFINITIVE FIX ---
            # 1. Calculate the mean absolute SHAP values for the "Fail" class (class 1)
            mean_abs_shap = np.abs(shap_values[1]).mean(axis=0)
            feature_names = X_test.columns
            importance_df = pd.DataFrame({'feature': feature_names, 'importance': mean_abs_shap}).sort_values('importance', ascending=True)
            
            # 2. Plot the results using Plotly Express for robustness and better aesthetics
            fig = px.bar(importance_df, x='importance', y='feature', orientation='h',
                         title="Average Impact on Model Output")
            fig.update_layout(height=300, margin=dict(l=10, r=10, t=40, b=10), yaxis_title=None, xaxis_title="Mean Absolute SHAP Value")
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Deep Dive: How Feature Values Drive Failure")
        st.markdown("The plot below shows each individual prediction from the test set. Red dots are high feature values, blue are low. For `temperature`, you can see high (red) values push the prediction towards failure (positive SHAP value), while low (blue) values push it towards passing.")
        
        # This is the "beeswarm" plot, which needs the same single-class SHAP values but uses the original function.
        fig_shap_summary, ax_shap_summary = plt.subplots()
        shap.summary_plot(shap_values[1], X_test, show=False, plot_size=(10, 4))
        ax_shap_summary.set_xlabel("SHAP value (impact on model output towards 'Fail')")
        st.pyplot(fig_shap_summary)

    with ml_tabs[1]:
        st.subheader("Predictive Project Risk: Interactive Analysis")
        st.markdown("This tool uses a trained model to forecast task delays and allows you to **drill down into the specific risk factors** for each task.")

        with st.expander("The 'Why' and the 'How'"):
            st.markdown("#### The 'Why': From Prediction to Actionable Insight")
            st.markdown("""- **Beyond Forecasting:** It's not enough to know a task is at risk. A project manager must know *why* to take effective action.\n- **Interactive Drill-Down:** This tool lets you select a high-risk task and immediately see a breakdown of the factors contributing to its risk score. This focuses conversations and mitigation efforts on the root causes.""")
            st.markdown("#### The 'How': Logistic Regression + Coefficient Analysis")
            st.markdown("""1.  A **Logistic Regression** model is trained on historical tasks to learn the relationship between task features and the likelihood of delay.\n2.  The model calculates a risk probability for all 'Not Started' tasks.\n3.  **When you select a task**, we analyze its specific features (e.g., its `duration_days`) and multiply them by the model's learned coefficients (`model.coef_`). This gives us the **Risk Contribution** of each factor.\n4.  A bar chart visualizes these contributions, showing you exactly which factors are driving the risk for the selected task.""")

        @st.cache_data
        def train_and_predict_risk(tasks: List[Dict]):
            df = pd.DataFrame(tasks); df['start_date'] = pd.to_datetime(df['start_date']); df['end_date'] = pd.to_datetime(df['end_date'])
            df['duration_days'] = (df['end_date'] - df['start_date']).dt.days; df['num_dependencies'] = df['dependencies'].apply(lambda x: len(x.split(',')) if x else 0)
            critical_path_ids = find_critical_path(df.copy()); df['is_critical'] = df['id'].isin(critical_path_ids).astype(int)
            train_df = df[df['status'].isin(['Completed', 'At Risk'])].copy(); train_df['target'] = (train_df['status'] == 'At Risk').astype(int)
            if len(train_df['target'].unique()) < 2: return None, None, None
            features = ['duration_days', 'num_dependencies', 'is_critical']; X_train = train_df[features]; y_train = train_df['target']
            model = LogisticRegression(random_state=42, class_weight='balanced'); model.fit(X_train, y_train)
            predict_df = df[df['status'] == 'Not Started'].copy()
            if predict_df.empty: return None, None, None
            X_predict = predict_df[features]; predict_df['risk_probability'] = model.predict_proba(X_predict)[:, 1]
            return predict_df, model, features

        risk_predictions_df, risk_model, risk_features = train_and_predict_risk(ssm.get_data("project_management", "tasks"))

        if risk_predictions_df is not None:
            st.markdown("**Forecasted Delay Probability for Future Tasks**")
            sorted_risk_df = risk_predictions_df.sort_values('risk_probability', ascending=False)
            fig = px.bar(sorted_risk_df, x='risk_probability', y='name', orientation='h',
                         title="Forecasted Risk for 'Not Started' Tasks",
                         labels={'risk_probability': 'Probability of Being "At-Risk"', 'name': 'Task'},
                         color='risk_probability', color_continuous_scale=px.colors.sequential.Reds)
            fig.update_layout(height=350, yaxis={'categoryorder':'total ascending'}); st.plotly_chart(fig, use_container_width=True)
            
            st.divider()
            st.subheader("Drill-Down: Analyze a Specific Task's Risk Factors")
            high_risk_tasks = sorted_risk_df[sorted_risk_df['risk_probability'] > 0.5]['name'].tolist()
            if not high_risk_tasks:
                st.info("No tasks are currently predicted to be at high risk (>50% probability).")
            else:
                selected_task_name = st.selectbox("Select a high-risk task to analyze:", options=high_risk_tasks)
                
                task_data = risk_predictions_df[risk_predictions_df['name'] == selected_task_name].iloc[0]
                task_features = task_data[risk_features]
                
                contributions = task_features * risk_model.coef_[0]
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
    
    try: ssm = SessionStateManager(); logger.info("Application initialized. Session State Manager loaded.")
    except Exception as e:
        st.error("Fatal Error: Could not initialize Session State. The application cannot continue.")
        logger.critical(f"Failed to instantiate SessionStateManager: {e}", exc_info=True); st.stop()

    try: tasks_raw = ssm.get_data("project_management", "tasks"); tasks_df_processed = preprocess_task_data(tasks_raw)
    except Exception as e:
        st.error("Failed to process project task data for dashboard."); logger.error(f"Error during task data pre-processing: {e}", exc_info=True)
        tasks_df_processed = pd.DataFrame()

    st.title("🚀 DHF Command Center"); project_name = ssm.get_data("design_plan", "project_name")
    st.caption(f"Live monitoring for the **{project_name}** project.")

    tab_names = ["📊 **DHF Health Dashboard**", "🗂️ **DHF Sections Explorer**", "🔬 **Advanced Analytics**", "📈 **Statistical Workbench**", "🤖 **Machine Learning Lab**", "🏛️ **QE & Compliance Guide**"]
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(tab_names)

    with tab1: render_health_dashboard_tab(ssm, tasks_df_processed)
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
