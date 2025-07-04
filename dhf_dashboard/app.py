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
from datetime import timedelta
from typing import Any, Dict, List

# --- Third-party Imports ---
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scipy import stats

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
# --- DASHBOARD COMPONENT FUNCTIONS ---
# ==============================================================================

def render_dhf_completeness_panel(ssm: SessionStateManager, tasks_df: pd.DataFrame) -> None:
    """
    Renders the DHF completeness and gate readiness panel.
    Displays DHF phases as expanders and a project timeline Gantt chart.
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
            expander_title = f"**{task_name}** (Status: {task.get('status', 'N/A')} - {task.get('completion_pct', 0)}%)"
            with st.expander(expander_title):
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
                    if isinstance(sign_offs, dict):
                        for team, status in sign_offs.items():
                            color = "green" if status == "✅" else "orange" if status == "In Progress" else "grey"
                            st.markdown(f"- **{team}:** <span style='color:{color};'>{status}</span>", unsafe_allow_html=True)
                    else:
                        st.caption("Sign-off data is not in the correct format.")
        
        st.markdown("---")
        st.markdown("##### Project Phase Timeline (Gantt Chart)")
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
    """Renders the risk analysis dashboard (Sankey plot and FMEA highlights)."""
    st.subheader("2. DHF Risk Artifacts (ISO 14971, FMEA)")
    st.markdown("Analyze the project's risk profile via the Risk Mitigation Flow and Failure Mode and Effects Analysis (FMEA) highlights.")
    risk_tabs = st.tabs(["Risk Mitigation Flow (System Level)", "dFMEA Highlights", "pFMEA Highlights"])

    with risk_tabs[0]:
        try:
            hazards_data = ssm.get_data("risk_management_file", "hazards")
            if not hazards_data:
                st.warning("No hazard analysis data available.")
                return
            df = get_cached_df(hazards_data)
            
            # Use canonical risk config for consistency
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

    def render_fmea_highlights(fmea_data: List[Dict[str, Any]], title: str) -> None:
        """Helper to render FMEA bar charts."""
        try:
            df = get_cached_df(fmea_data)
            if df.empty:
                st.warning(f"No {title} data available.")
                return
            df['RPN'] = df['S'] * df['O'] * df['D']
            top_items = df.sort_values('RPN', ascending=False).head(5)
            fig = px.bar(top_items, x='RPN', y='failure_mode', orientation='h', title=f"<b>Top 5 {title} Items by RPN</b>", labels={'failure_mode': 'Failure Mode'}, text='RPN')
            fig.update_layout(yaxis={'categoryorder': 'total ascending'}, title_x=0.5)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Could not render {title} highlights. Data may be malformed.")
            logger.error(f"Error in render_fmea_highlights for {title}: {e}", exc_info=True)

    with risk_tabs[1]: render_fmea_highlights(ssm.get_data("risk_management_file", "dfmea"), "dFMEA")
    with risk_tabs[2]: render_fmea_highlights(ssm.get_data("risk_management_file", "pfmea"), "pFMEA")


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
                    with st.expander(f"**CQA:** {element.get('cqa', 'N/A')} (links to Requirement: {element.get('links_to_req', 'N/A')})"):
                        st.markdown(f"**Critical Material Attributes (CMAs):** `{' | '.join(element.get('cm_attributes', []))}`")
                        st.markdown(f"**Critical Process Parameters (CPPs):** `{' | '.join(element.get('cp_parameters', []))}`")
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
                    st.progress(pass_rate)
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
            # Lower is better for CAPAs, so score is inverted
            capa_score = max(0, 100 - (open_capas * 20))

            suppliers_df = get_cached_df(ssm.get_data("quality_system", "supplier_audits"))
            supplier_pass_rate = (len(suppliers_df[suppliers_df['status'] == 'Pass']) / len(suppliers_df)) * 100 if not suppliers_df.empty else 100

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("DHF Document Readiness", f"{doc_readiness:.1f}% Approved")
                st.progress(int(doc_readiness))
            with col2:
                st.metric("Open CAPA Score", f"{int(capa_score)}/100", help=f"{open_capas} open CAPA(s). Score degrades with each open item.")
                st.progress(int(capa_score))
            with col3:
                st.metric("Supplier Audit Pass Rate", f"{supplier_pass_rate:.1f}%")
                st.progress(int(supplier_pass_rate))
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
                    meas = np.array(spc_data['measurements'])
                    usl, lsl = spc_data['usl'], spc_data['lsl']
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
    """Renders the main DHF Health Dashboard tab."""
    st.header("Project Health At-a-Glance")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        completion_pct = tasks_df['completion_pct'].mean() if not tasks_df.empty else 0
        st.plotly_chart(create_progress_donut(completion_pct), use_container_width=True)
    
    with col2:
        hazards_df = get_cached_df(ssm.get_data("risk_management_file", "hazards"))
        st.plotly_chart(create_risk_profile_chart(hazards_df), use_container_width=True)
    
    with col3:
        reviews = ssm.get_data("design_reviews", "reviews")
        actions = [item for r in reviews for item in r.get("action_items", [])]
        actions_df = get_cached_df(actions)
        st.plotly_chart(create_action_item_chart(actions_df), use_container_width=True)

    st.divider()
    render_dhf_completeness_panel(ssm, tasks_df)
    st.divider()
    render_risk_and_fmea_dashboard(ssm)
    st.divider()
    render_qbd_and_cgmp_panel(ssm)
    st.divider()
    render_audit_and_improvement_dashboard(ssm)

def render_dhf_explorer_tab(ssm: SessionStateManager):
    """Renders the DHF Sections Explorer tab and its sidebar navigation."""
    st.header("Design History File Explorer")
    st.markdown("Select a DHF section from the sidebar to view or edit its contents.")
    with st.sidebar:
        st.header("DHF Section Navigation")
        dhf_selection = st.radio("Select a section to edit:", DHF_EXPLORER_PAGES.keys(), key="sidebar_dhf_selection")
    st.divider()
    page_function = DHF_EXPLORER_PAGES[dhf_selection]
    page_function(ssm)

def render_advanced_analytics_tab(ssm: SessionStateManager):
    """Renders the Advanced Analytics tab."""
    st.header("Advanced Compliance & Project Analytics")
    analytics_tabs = st.tabs(["Traceability Matrix", "Action Item Tracker", "Project Task Editor"])
    with analytics_tabs[0]: render_traceability_matrix(ssm)
    with analytics_tabs[1]: render_action_item_tracker(ssm)
    with analytics_tabs[2]:
        st.subheader("Project Timeline and Task Editor")
        st.warning("Directly edit project timelines, statuses, and dependencies. Changes are saved automatically.", icon="⚠️")
        try:
            tasks_df_to_edit = pd.DataFrame(ssm.get_data("project_management", "tasks"))
            # Convert to datetime for the editor widget
            tasks_df_to_edit['start_date'] = pd.to_datetime(tasks_df_to_edit['start_date'], errors='coerce')
            tasks_df_to_edit['end_date'] = pd.to_datetime(tasks_df_to_edit['end_date'], errors='coerce')

            edited_df = st.data_editor(
                tasks_df_to_edit, key="main_task_editor", num_rows="dynamic", use_container_width=True,
                column_config={"start_date": st.column_config.DateColumn("Start Date", format="YYYY-MM-DD", required=True),
                               "end_date": st.column_config.DateColumn("End Date", format="YYYY-MM-DD", required=True)}
            )
            # Convert back to string for JSON serialization if changes were made
            if not tasks_df_to_edit.equals(edited_df):
                df_to_save = edited_df.copy()
                df_to_save['start_date'] = df_to_save['start_date'].dt.strftime('%Y-%m-%d').replace({pd.NaT: None})
                df_to_save['end_date'] = df_to_save['end_date'].dt.strftime('%Y-%m-%d').replace({pd.NaT: None})
                ssm.update_data(df_to_save.to_dict('records'), "project_management", "tasks")
                st.toast("Project tasks updated! Rerunning...", icon="✅")
                st.rerun()
        except Exception as e:
            st.error("Could not load the Project Task Editor."); logger.error(f"Error in task editor: {e}", exc_info=True)

def render_statistical_tools_tab(ssm: SessionStateManager):
    """Renders the Statistical Analysis Tools tab."""
    st.header("📈 Statistical Analysis Tools")
    st.info("Leverage classical statistical methods to monitor processes, compare samples, and focus improvement efforts.")
    tool_tabs = st.tabs(["Process Control (SPC)", "Hypothesis Testing (A/B Test)", "Pareto Analysis (FMEA)", "Design of Experiments (DOE)"])
    
    with tool_tabs[0]:
        st.subheader("Statistical Process Control (SPC) Chart")
        st.markdown("Monitors the stability of a critical process parameter over time to detect shifts before they result in out-of-specification products.")
        with st.expander("The 'Why' and the 'How'"):
            st.markdown("##### The 'Why': Mathematical Foundation")
            st.markdown("SPC distinguishes between common cause variation (natural process noise) and special cause variation (an external factor). Control limits are the voice of the process, while specification limits are the voice of the engineer.")
            st.latex(r''' UCL = \mu + 3\sigma \quad | \quad LCL = \mu - 3\sigma ''')
            st.markdown("Where `μ` (mu) is the process mean and `σ` (sigma) is the standard deviation. A process is 'out of control' if points fall outside these limits or show non-random patterns.")
            st.markdown("##### The 'How': In This Application")
            st.markdown("We monitor pill casing diameter. `Target`, `USL`, and `LSL` are engineering specs. This chart adds the calculated `UCL` and `LCL` (Control Limits) based on the data itself, which is the key to assessing process stability.")
        try:
            spc_data = ssm.get_data("quality_system", "spc_data")
            if spc_data and all(k in spc_data for k in ['measurements', 'target', 'usl', 'lsl']):
                meas = np.array(spc_data['measurements'])
                mu, sigma = meas.mean(), meas.std()
                ucl, lcl = mu + 3 * sigma, mu - 3 * sigma
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(y=meas, name='Measurements', mode='lines+markers', line=dict(color='#1f77b4')))
                # Engineering/Specification Limits
                fig.add_hline(y=spc_data['target'], line_dash="dash", line_color="green", annotation_text="Target")
                fig.add_hline(y=spc_data['usl'], line_dash="dot", line_color="red", annotation_text="USL")
                fig.add_hline(y=spc_data['lsl'], line_dash="dot", line_color="red", annotation_text="LSL")
                # Statistical/Control Limits
                fig.add_hline(y=ucl, line_dash="dashdot", line_color="orange", annotation_text="UCL")
                fig.add_hline(y=lcl, line_dash="dashdot", line_color="orange", annotation_text="LCL")
                fig.update_layout(title="SPC Chart for Pill Casing Diameter", yaxis_title="Diameter (mm)")
                st.plotly_chart(fig, use_container_width=True)
            else: st.warning("SPC data is incomplete or missing.")
        except Exception as e: st.error("Could not render SPC chart."); logger.error(f"Error in SPC tool: {e}", exc_info=True)

    with tool_tabs[1]:
        st.subheader("Hypothesis Testing: Process Comparison")
        st.markdown("Uses a two-sample t-test to determine if there is a *statistically significant* difference between two groups (e.g., manufacturing lines).")
        with st.expander("The 'Why' and the 'How'"):
            st.markdown("##### The 'Why': Mathematical Foundation")
            st.markdown("A two-sample t-test assesses if two independent samples likely came from populations with equal means. We test two hypotheses: **Null (H₀):** No difference ($ \mu_A = \mu_B $), and **Alternative (H₁):** A difference exists ($ \mu_A \\neq \mu_B $). The test yields a **p-value**; if `p < 0.05`, we reject H₀ and conclude the difference is significant.")
            st.markdown("##### The 'How': In This Application")
            st.markdown("We compare seal strength from 'Line A' vs. 'Line B'. `scipy.stats.ttest_ind` calculates the p-value. The app interprets this to provide a clear, data-driven conclusion.")
        try:
            ht_data = ssm.get_data("quality_system", "hypothesis_testing_data")
            if ht_data and all(k in ht_data for k in ['line_a', 'line_b']):
                line_a, line_b = ht_data['line_a'], ht_data['line_b']
                t_stat, p_value = stats.ttest_ind(line_a, line_b, equal_var=False) # Welch's t-test
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Test Results:**")
                    st.metric("T-statistic", f"{t_stat:.3f}")
                    st.metric("P-value", f"{p_value:.3f}")
                    if p_value < 0.05:
                        st.success(f"**Conclusion:** Significant difference detected (p < 0.05).")
                    else:
                        st.warning(f"**Conclusion:** No significant difference detected (p >= 0.05).")
                with col2:
                    df_ht = pd.concat([pd.DataFrame({'value': line_a, 'line': 'Line A'}), pd.DataFrame({'value': line_b, 'line': 'Line B'})])
                    fig = px.box(df_ht, x='line', y='value', title="Distribution Comparison", points="all", labels={'value': 'Seal Strength'})
                    st.plotly_chart(fig, use_container_width=True)
            else: st.warning("Hypothesis testing data is incomplete or missing.")
        except Exception as e: st.error("Could not perform Hypothesis Test."); logger.error(f"Error in Hypothesis Testing tool: {e}", exc_info=True)

    with tool_tabs[2]:
        st.subheader("Pareto Analysis of FMEA Risk")
        st.markdown("Applies the 80/20 rule to FMEA data to identify the 'vital few' failure modes that contribute to the majority of the risk (by RPN).")
        with st.expander("The 'Why' and the 'How'"):
            st.markdown("##### The 'Why': Mathematical Foundation")
            st.markdown("The Pareto Principle states that roughly 80% of effects come from 20% of causes. We calculate `RPN = S × O × D`, sort by RPN, and plot the RPN values alongside their cumulative percentage of the total.")
            st.markdown("##### The 'How': In This Application")
            st.markdown("We combine dFMEA and pFMEA data and generate a Pareto chart. The bars show RPN per failure mode, and the line shows the cumulative percentage. This directs mitigation efforts to the highest-impact items on the left.")
        try:
            fmea_df = pd.concat([get_cached_df(ssm.get_data("risk_management_file", "dfmea")), get_cached_df(ssm.get_data("risk_management_file", "pfmea"))], ignore_index=True)
            if not fmea_df.empty:
                fmea_df['RPN'] = fmea_df['S'] * fmea_df['O'] * fmea_df['D']
                fmea_df = fmea_df.sort_values('RPN', ascending=False)
                fmea_df['cumulative_pct'] = (fmea_df['RPN'].cumsum() / fmea_df['RPN'].sum()) * 100
                fig = go.Figure()
                fig.add_trace(go.Bar(x=fmea_df['failure_mode'], y=fmea_df['RPN'], name='RPN', marker_color='#1f77b4'))
                fig.add_trace(go.Scatter(x=fmea_df['failure_mode'], y=fmea_df['cumulative_pct'], name='Cumulative %', yaxis='y2', line=dict(color='#d62728')))
                fig.update_layout(title="FMEA Pareto Chart", yaxis=dict(title='RPN'), yaxis2=dict(title='Cumulative %', overlaying='y', side='right', range=[0, 105]), xaxis_title='Failure Mode', showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            else: st.warning("No FMEA data available for Pareto analysis.")
        except Exception as e: st.error("Could not generate Pareto chart."); logger.error(f"Error in Pareto Analysis tool: {e}", exc_info=True)
    
    with tool_tabs[3]:
        st.subheader("Design of Experiments (DOE) Analysis")
        st.markdown("Analyzes the effect of process inputs (**factors**) on an output (**response**), such as Molding Temperature and Pressure on Seal Strength.")
        with st.expander("The 'Why' and the 'How'"):
            st.markdown("##### The 'Why': Mathematical Foundation")
            st.markdown("DOE uses a regression model to quantify factor effects: $Y = \\beta_0 + \\beta_1 X_1 + \\beta_2 X_2 + \\beta_{12} X_1 X_2 + \\epsilon$. A large `β` (beta) coefficient indicates a strong influence.")
            st.markdown("##### The 'How': In This Application")
            st.markdown("- **Main Effects Plot:** Shows the average response at low (-1) and high (+1) factor levels. Steeper lines mean more significant effects.\n- **Contour Plot (Illustrative):** A 2D map of the predicted response surface to find optimal settings. This is a visualization based on a simplified model to demonstrate the concept.")
        try:
            doe_df = get_cached_df(ssm.get_data("quality_system", "doe_data"))
            if not doe_df.empty:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Main Effects Plot**")
                    main_effects_data = doe_df.melt(id_vars='seal_strength', value_vars=['temperature', 'pressure'], var_name='factor', value_name='level')
                    main_effects = main_effects_data.groupby(['factor', 'level'])['seal_strength'].mean().reset_index()
                    fig = px.line(main_effects, x='level', y='seal_strength', color='factor', title="Main Effects on Seal Strength", markers=True, labels={'level': 'Factor Level (-1: Low, 1: High)', 'seal_strength': 'Mean Seal Strength'})
                    st.plotly_chart(fig, use_container_width=True)
                with col2:
                    st.markdown("**Contour Plot (Illustrative)**")
                    # Simplified model for illustration: fit a 2D polynomial surface
                    from sklearn.preprocessing import PolynomialFeatures
                    from sklearn.linear_model import LinearRegression
                    from sklearn.pipeline import make_pipeline
                    X = doe_df[['temperature', 'pressure']]
                    y = doe_df['seal_strength']
                    model = make_pipeline(PolynomialFeatures(2), LinearRegression())
                    model.fit(X, y)
                    t_range, p_range = np.linspace(-1.5, 1.5, 30), np.linspace(-1.5, 1.5, 30)
                    t_grid, p_grid = np.meshgrid(t_range, p_range)
                    grid = np.c_[t_grid.ravel(), p_grid.ravel()]
                    strength_grid = model.predict(grid).reshape(t_grid.shape)
                    
                    fig = go.Figure(data=[go.Contour(z=strength_grid, x=t_range, y=p_range, colorscale='Viridis'), go.Scatter(x=doe_df['temperature'], y=doe_df['pressure'], mode='markers', marker=dict(color='red', size=10, symbol='x'), name='DOE Runs')])
                    fig.update_layout(xaxis_title="Temperature", yaxis_title="Pressure", title="Predicted Seal Strength Surface")
                    st.plotly_chart(fig, use_container_width=True)
            else: st.warning("DOE data is not available.")
        except ImportError: st.error("Please install scikit-learn (`pip install scikit-learn`) for advanced DOE visualization.")
        except Exception as e: st.error("Could not generate DOE plots."); logger.error(f"Error in DOE Analysis tool: {e}", exc_info=True)
    

def render_machine_learning_lab_tab(ssm: SessionStateManager):
    """Renders the Machine Learning Lab tab with predictive models."""
    st.header("🤖 Machine Learning Lab")
    st.info("Utilize predictive models to forecast outcomes, enabling proactive quality control and project management.")

    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import confusion_matrix
    except ImportError:
        st.error("This tab requires scikit-learn. Please install it (`pip install scikit-learn`) to enable ML features.", icon="🚨")
        return

    ml_tabs = st.tabs(["Predictive Quality (Batch Failure)", "Predictive Project Risk (Task Delay)"])

    with ml_tabs[0]:
        st.subheader("Predictive Quality: Manufacturing Batch Failure")
        st.markdown("This model predicts whether a manufacturing batch will **Pass** or **Fail** based on its process parameters, *before* the batch is run.")

        with st.expander("The 'Why' and the 'How'"):
            st.markdown("#### The 'Why': Business Justification")
            st.markdown("""
            - **Proactive vs. Reactive:** Instead of discovering a failed batch during final inspection (reactive), this model predicts failure ahead of time (proactive).
            - **COPQ Reduction:** It significantly reduces the Cost of Poor Quality (COPQ) by preventing scrap, rework, and wasted materials.
            - **Process Understanding:** The model's *feature importances* tell engineers which process parameters have the biggest impact on quality, guiding process optimization efforts (like a DOE).
            """)
            st.markdown("#### The 'How': Methodological Approach")
            st.markdown("""
            We use a **Random Forest Classifier**. This is an *ensemble* model, meaning it builds many individual Decision Trees and then aggregates their votes to make a final prediction.
            - **Decision Tree:** A simple, flowchart-like model that makes decisions based on feature values (e.g., "Is `temperature` > 95°C?").
            - **Random Forest:** By combining hundreds of trees, each trained on a random subset of the data and features, the model becomes much more robust and accurate, reducing the risk of overfitting to the training data.
            """)
            st.markdown("#### The 'How': In This Application")
            st.markdown("1. We generate a synthetic dataset of 500 manufacturing batches with features like `temperature`, `pressure`, and `viscosity` and a `status` (Pass/Fail).\n2. We train a Random Forest Classifier on 80% of this data.\n3. We evaluate its performance on the remaining 20% (the test set) and display a **Confusion Matrix**.\n4. We show the **Feature Importances**, revealing which factors the model learned were most predictive of failure.")

        @st.cache_data
        def generate_and_train_quality_model():
            """Generates synthetic quality data and trains a Random Forest model."""
            np.random.seed(42)
            n_samples = 500
            data = {
                'temperature': np.random.normal(90, 5, n_samples),
                'pressure': np.random.normal(300, 20, n_samples),
                'viscosity': np.random.normal(50, 3, n_samples)
            }
            df = pd.DataFrame(data)
            # Failures are more likely at the extremes
            fail_conditions = (df['temperature'] > 98) | (df['temperature'] < 82) | (df['pressure'] > 330) | (df['viscosity'] < 45)
            df['status'] = np.where(fail_conditions, 'Fail', 'Pass')
            df['status_code'] = df['status'].apply(lambda x: 1 if x == 'Fail' else 0)

            X = df[['temperature', 'pressure', 'viscosity']]
            y = df['status_code']
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
            
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)
            return model, X, y_test, X_test
        
        model, X, y_test, X_test = generate_and_train_quality_model()
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Feature Importances**")
            st.caption("Which process parameters most predict failure?")
            importances = pd.DataFrame({'feature': X.columns, 'importance': model.feature_importances_}).sort_values('importance', ascending=True)
            fig = px.bar(importances, x='importance', y='feature', orientation='h', title="Model Feature Importances")
            fig.update_layout(height=300, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("**Model Performance (Test Set)**")
            st.caption("How well did the model predict on unseen data?")
            y_pred = model.predict(X_test)
            cm = confusion_matrix(y_test, y_pred)
            fig = px.imshow(cm, text_auto=True, aspect="auto",
                            labels=dict(x="Predicted", y="Actual", color="Count"),
                            x=['Pass', 'Fail'], y=['Pass', 'Fail'],
                            title="Confusion Matrix")
            fig.update_layout(height=300, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)

    with ml_tabs[1]:
        st.subheader("Predictive Project Risk: Task Delay")
        st.markdown("This model uses historical data to predict the probability of future project tasks becoming **At-Risk** (i.e., delayed).")

        with st.expander("The 'Why' and the 'How'"):
            st.markdown("#### The 'Why': Business Justification")
            st.markdown("""
            - **Early Warning System:** Provides a data-driven forecast of which tasks are most likely to cause bottlenecks, allowing managers to intervene early.
            - **Improved Resource Allocation:** Helps focus management attention and resources on the highest-risk tasks.
            - **Beyond the Gantt Chart:** While a Gantt chart shows the plan, this model predicts deviations from the plan based on learned patterns.
            """)
            st.markdown("#### The 'How': Methodological Approach")
            st.markdown("We use **Logistic Regression**. Unlike linear regression which predicts a continuous value, logistic regression predicts a probability that an event will occur. It models the probability using the **sigmoid function**:")
            st.latex(r''' P(\text{At-Risk}) = \frac{1}{1 + e^{-z}} \quad \text{where} \quad z = \beta_0 + \beta_1 X_1 + \dots + \beta_n X_n ''')
            st.markdown("The model learns the `β` (beta) coefficients for each feature (e.g., `duration`, `num_dependencies`) to best predict the outcome.")
            st.markdown("#### The 'How': In This Application")
            st.markdown("1. We use the project's own task data, including completed and in-progress tasks, as a training set.\n2. We engineer features: `duration_days`, `num_dependencies`, and `is_critical`.\n3. We train a Logistic Regression model to distinguish between 'At Risk' and 'On Time' tasks.\n4. We use the trained model to predict the probability of delay for all 'Not Started' tasks, visualizing the results for easy interpretation.")

        @st.cache_data
        def train_and_predict_risk(tasks: List[Dict]):
            """Trains a logistic regression model and predicts risk on future tasks."""
            df = pd.DataFrame(tasks)
            df['start_date'] = pd.to_datetime(df['start_date'])
            df['end_date'] = pd.to_datetime(df['end_date'])
            df['duration_days'] = (df['end_date'] - df['start_date']).dt.days
            df['num_dependencies'] = df['dependencies'].apply(lambda x: len(x.split(',')) if x else 0)
            
            critical_path_ids = find_critical_path(df.copy())
            df['is_critical'] = df['id'].isin(critical_path_ids).astype(int)

            # Train on tasks that have a definitive status
            train_df = df[df['status'].isin(['Completed', 'At Risk'])].copy()
            train_df['target'] = (train_df['status'] == 'At Risk').astype(int)
            
            if len(train_df['target'].unique()) < 2: return None # Cannot train if only one class exists

            features = ['duration_days', 'num_dependencies', 'is_critical']
            X_train = train_df[features]
            y_train = train_df['target']
            
            model = LogisticRegression(random_state=42, class_weight='balanced')
            model.fit(X_train, y_train)

            # Predict on future tasks
            predict_df = df[df['status'] == 'Not Started'].copy()
            if predict_df.empty: return None

            X_predict = predict_df[features]
            predict_df['risk_probability'] = model.predict_proba(X_predict)[:, 1]
            return predict_df[['name', 'risk_probability']].sort_values('risk_probability', ascending=False)

        risk_predictions = train_and_predict_risk(ssm.get_data("project_management", "tasks"))

        if risk_predictions is not None:
            st.markdown("**Predicted Delay Probability for Future Tasks**")
            fig = px.bar(risk_predictions, x='risk_probability', y='name', orientation='h',
                         title="Forecasted Risk for 'Not Started' Tasks",
                         labels={'risk_probability': 'Probability of Being "At-Risk"', 'name': 'Task'},
                         color='risk_probability', color_continuous_scale=px.colors.sequential.Reds)
            fig.update_layout(height=350, yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
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
    st.divider()
    st.subheader("The Role of a Design Assurance Quality Engineer")
    st.markdown("A Design Assurance QE is the steward of the DHF, ensuring compliance, quality, and safety are designed into the product from day one. This tool is designed to be their primary workspace. Key responsibilities within this framework include:")
    with st.expander("✅ **Owning the Design History File (DHF)**"): st.markdown("The QE is responsible for the **creation, remediation, and maintenance** of the DHF. It's not just a repository; it's a living document that tells the story of the product's development.\n- This application serves as the DHF's active workspace.\n- **Key QE Goal:** Ensure the DHF is complete, coherent, and audit-ready at all times. The Traceability Matrix is the QE's primary tool for identifying gaps.")
    with st.expander("✅ **Driving Verification & Validation (V&V) Strategy**"): st.markdown("The QE doesn't just witness tests; they help architect the entire V&V strategy.\n- **V&V Master Plan:** This is a high-level document, referenced in the Design Plan, that outlines the scope, methods, and acceptance criteria for all V&V activities.\n- **Protocol & Report Review:** The QE reviews and approves all test protocols (to ensure they are adequate) and reports (to ensure they are accurate and complete). The 'Design Verification' and 'Design Validation' sections track these deliverables.")
    with st.expander("✅ **Advanced Quality Engineering Concepts**"):
        st.markdown("""Beyond foundational Design Controls, a Senior QE leverages advanced methodologies to ensure quality is built into the product proactively, not inspected in later. This is the core of **First-Time-Right (FTR)** initiatives, which aim to reduce the **Cost of Poor Quality (COPQ)**—the significant expenses associated with scrap, rework, complaints, and recalls.
- **Quality by Design (QbD):** A systematic approach that begins with predefined objectives and emphasizes product and process understanding and control. The key is to identify **Critical Quality Attributes (CQAs)**—the physical, chemical, or biological characteristics that must be within a specific limit to ensure the desired product quality. These CQAs are then linked to the **Critical Material Attributes (CMAs)** of the raw materials and the **Critical Process Parameters (CPPs)** of the manufacturing process. The **QbD Tracker** on the main dashboard visualizes these crucial linkages.
- **Failure Mode and Effects Analysis (FMEA):** A bottom-up, systematic tool for analyzing potential failure modes in a system. It is a core part of the risk management process.
    - **Design FMEA (dFMEA):** Focuses on failures that can result from the **design** of the product (e.g., incorrect material choice, software bug).
    - **Process FMEA (pFMEA):** Focuses on failures that can result from the **manufacturing process** (e.g., incorrect machine setting, operator error).
    - The **Risk & FMEA Dashboard** shows highlights from both.
- **Fault Tree Analysis (FTA):** A top-down, deductive failure analysis where a high-level system failure (e.g., 'Patient receives no therapy') is traced back to all the potential root causes. It's a powerful risk management tool used to understand complex failure modes, complementing the bottom-up FMEA. The project's `FTA-001` document would be part of the Risk Management File.
- **Design of Experiments (DOE):** A statistical tool used to systematically determine the relationship between inputs (factors) and outputs of a process. Instead of testing one factor at a time, DOE allows for efficient exploration of the **design space**. It is used to identify the most critical CPPs and optimize their settings to ensure the process robustly produces products that meet their CQAs. The **DOE Analysis** tool in the `AI & Statistical Tools` tab provides a practical example.
- **Statistical Process Control (SPC):** A method of quality control which employs statistical methods to monitor and control a process. This helps to ensure that the process operates efficiently, producing more specification-conforming product with less waste. The **SPC Chart** in the `AI & Statistical Tools` tab is a practical implementation.
- **Hypothesis Testing:** A statistical method used to make decisions using data. For example, a t-test can determine if a new supplier's material is significantly stronger than the old one. The **Hypothesis Testing** tool in the `AI & Statistical Tools` tab demonstrates this.
- **Process Capability (Cpk):** A statistical measure of a process's ability to produce output within specification limits. A Cpk value of **1.33 is considered capable**, while **1.67 is considered highly capable (6-sigma level)**. The 'Audit & Continuous Improvement' dashboard tracks this metric.
- **Process Validation (IQ/OQ/PQ):** A cornerstone of CGMP and Design Transfer. It provides documented evidence that a process will consistently produce a product meeting its predetermined specifications.
    - **Installation Qualification (IQ):** Confirms that the equipment has been installed correctly.
    - **Operational Qualification (OQ):** Confirms that the equipment operates correctly across its entire operational range.
    - **Performance Qualification (PQ):** Confirms that the equipment, under normal operating conditions, consistently produces product that meets all specifications. The 'DHF Sections Explorer' tracks these activities.""")
    st.divider()
    st.subheader("Visualizing the Process: The V-Model")
    st.markdown("The V-Model is a powerful way to visualize the Design Controls process, emphasizing the critical link between design (left side) and testing (right side).")
    try:
        v_model_image_path = os.path.join(project_root, "dhf_dashboard", "v_model_diagram.png")
        if os.path.exists(v_model_image_path):
            st.image(v_model_image_path, caption="The V-Model illustrates the relationship between design decomposition and integration/testing.", use_column_width=True)
        else:
            st.error(f"Image Not Found: Ensure `v_model_diagram.png` is in the `dhf_dashboard` directory.", icon="🚨")
            logger.warning(f"Could not find v_model_diagram.png at path: {v_model_image_path}")
    except Exception as e:
        st.error("An error occurred while trying to display the V-Model image.")
        logger.error(f"Error loading V-Model image: {e}", exc_info=True)
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
    """
    Main function to configure and run the Streamlit application.
    """
    st.set_page_config(layout="wide", page_title="DHF Command Center", page_icon="🚀")
    
    try:
        ssm = SessionStateManager()
        logger.info("Application initialized. Session State Manager loaded.")
    except Exception as e:
        st.error("Fatal Error: Could not initialize Session State. The application cannot continue.")
        logger.critical(f"Failed to instantiate SessionStateManager: {e}", exc_info=True)
        st.stop()

    # --- Pre-process data (cached for performance) ---
    try:
        tasks_raw = ssm.get_data("project_management", "tasks")
        tasks_df_processed = preprocess_task_data(tasks_raw)
    except Exception as e:
        st.error("Failed to process project task data for dashboard.")
        logger.error(f"Error during task data pre-processing: {e}", exc_info=True)
        tasks_df_processed = pd.DataFrame()

    # --- HEADER ---
    st.title("🚀 DHF Command Center")
    project_name = ssm.get_data("design_plan", "project_name")
    st.caption(f"Live monitoring for the **{project_name}** project.")

    # --- MAIN TABS ---
    tab_names = [
        "📊 **DHF Health Dashboard**", "🗂️ **DHF Sections Explorer**",
        "🔬 **Advanced Analytics**", "📈 **Statistical Analysis Tools**",
        "🤖 **Machine Learning Lab**", "🏛️ **QE & Compliance Guide**"
    ]
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
