# File: dhf_dashboard/utils/critical_path_utils.py
# --- Enhanced Version ---
"""
Utility for calculating the critical path of a project plan.

This module provides the core logic for implementing the Critical Path Method (CPM)
on a set of tasks defined in a pandas DataFrame.
"""

# --- Standard Library Imports ---
import logging
from typing import Dict, List, Set

# --- Third-party Imports ---
import pandas as pd

# --- Setup Logging ---
logger = logging.getLogger(__name__)

# --- Type Aliases for clarity ---
TaskId = str
TaskMap = Dict[TaskId, Dict]


def find_critical_path(tasks_df: pd.DataFrame) -> List[TaskId]:
    """
    Identifies the critical path in a project task list using the Critical Path Method (CPM).

    This implementation performs a forward and backward pass to calculate the
    earliest and latest start/finish times for each task. Tasks with zero
    "slack" or "float" (where Early Start equals Late Start) are considered
    to be on the critical path.

    SME Note:
    This is a simplified implementation for demonstration purposes. It assumes:
    - The task dependency graph is a Directed Acyclic Graph (DAG). It does not
      contain circular dependencies (e.g., Task A -> Task B -> Task A).
      The presence of cycles will lead to incorrect results.
    - Task durations are calculated in whole days.
    - The 'dependencies' column is a comma-separated string of task IDs.

    Args:
        tasks_df (pd.DataFrame):
            A DataFrame of tasks. It must contain the following columns:
            - 'id': A unique identifier for the task (str).
            - 'start_date': The task's start date (datetime object).
            - 'end_date': The task's end date (datetime object).
            - 'dependencies': A comma-separated string of prerequisite task IDs.

    Returns:
        List[TaskId]: A list of task IDs that form the critical path. Returns
                      an empty list if the input DataFrame is empty or if an
                      error occurs.
    """
    if tasks_df.empty:
        logger.info("tasks_df is empty, returning no critical path.")
        return []

    try:
        # --- 1. Initialization ---
        # Ensure required columns are present
        required_cols = {'id', 'start_date', 'end_date', 'dependencies'}
        if not required_cols.issubset(tasks_df.columns):
            missing_cols = required_cols - set(tasks_df.columns)
            logger.error(f"Input DataFrame is missing required columns: {missing_cols}")
            return []

        # Create a copy to avoid modifying the original DataFrame
        df = tasks_df.copy()

        # Drop tasks with invalid dates to prevent calculation errors
        df = df.dropna(subset=['start_date', 'end_date'])
        if df.empty:
            logger.warning("All tasks were dropped due to invalid start/end dates.")
            return []

        # CPM convention: duration includes the start day. If a task starts and
        # ends on the same day, its duration is 1.
        df['duration'] = (df['end_date'] - df['start_date']).dt.days + 1

        # Filter out tasks with non-positive duration, which are invalid for CPM
        df = df[df['duration'] > 0]
        if df.empty:
            logger.warning("All tasks were filtered out due to non-positive durations.")
            return []

        task_map: TaskMap = df.set_index('id').to_dict('index')
        task_ids: List[TaskId] = df['id'].tolist()

        logger.info(f"Starting CPM analysis on {len(task_ids)} tasks.")

        # --- 2. Forward Pass: Calculate Early Start (ES) and Early Finish (EF) ---
        logger.debug("Performing forward pass to calculate ES and EF...")
        for task_id in task_ids:
            # Safely parse dependencies from comma-separated string
            dep_str = str(task_map[task_id].get('dependencies', ''))
            dependencies: Set[TaskId] = {d.strip() for d in dep_str.split(',') if d.strip()}

            if not dependencies:
                task_map[task_id]['es'] = 0  # Tasks with no dependencies start at time 0
            else:
                # ES is the maximum of the Early Finishes of all its dependencies
                max_ef_of_deps = max(
                    (task_map[dep_id].get('ef', 0) for dep_id in dependencies if dep_id in task_map),
                    default=0
                )
                task_map[task_id]['es'] = max_ef_of_deps

            task_map[task_id]['ef'] = task_map[task_id]['es'] + task_map[task_id]['duration']

        # --- 3. Backward Pass: Calculate Late Finish (LF) and Late Start (LS) ---
        logger.debug("Performing backward pass to calculate LF and LS...")
        try:
            project_finish_time = max(task['ef'] for task in task_map.values())
            logger.debug(f"Calculated project finish time: {project_finish_time} days.")
        except ValueError:
            logger.error("Could not determine project finish time. The task map might be empty after processing.")
            return []

        # Iterate through tasks in reverse topological order (simplified as reversed list)
        for task_id in reversed(task_ids):
            # Find all tasks that have the current task as a dependency
            successor_ids: List[TaskId] = [
                succ_id for succ_id, succ_task in task_map.items()
                if task_id in {d.strip() for d in str(succ_task.get('dependencies', '')).split(',') if d.strip()}
            ]

            if not successor_ids:
                task_map[task_id]['lf'] = project_finish_time
            else:
                # LF is the minimum of the Late Starts of all its successors
                min_ls_of_succs = min(
                    (task_map[succ_id].get('ls', project_finish_time) for succ_id in successor_ids if succ_id in task_map),
                    default=project_finish_time
                )
                task_map[task_id]['lf'] = min_ls_of_succs

            task_map[task_id]['ls'] = task_map[task_id]['lf'] - task_map[task_id]['duration']

        # --- 4. Identify Critical Path ---
        # Critical tasks are those with zero slack (LS - ES = 0)
        logger.debug("Identifying critical path tasks (slack = 0)...")
        critical_path: List[TaskId] = []
        for task_id, task_data in task_map.items():
            # Check for existence of keys to avoid KeyErrors
            if 'es' in task_data and 'ls' in task_data:
                # Using a small tolerance for float comparison, though these should be integers
                if abs(task_data['es'] - task_data['ls']) < 1e-9:
                    critical_path.append(task_id)

        logger.info(f"Critical path identified with {len(critical_path)} tasks: {critical_path}")
        return critical_path

    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"An error occurred during critical path calculation: {e}", exc_info=True)
        return []


# ==============================================================================
# --- UNIT TEST SCAFFOLDING (for `pytest`) ---
# ==============================================================================
"""
import pytest
from datetime import datetime
import pandas as pd

# To run tests, place this in a 'tests' directory and run pytest.
# from dhf_dashboard.utils.critical_path_utils import find_critical_path

def test_find_critical_path_simple_chain():
    '''Tests a simple sequential project plan where all tasks are critical.'''
    tasks_data = [
        {'id': 'A', 'start_date': datetime(2023, 1, 1), 'end_date': datetime(2023, 1, 5), 'dependencies': ''},
        {'id': 'B', 'start_date': datetime(2023, 1, 6), 'end_date': datetime(2023, 1, 10), 'dependencies': 'A'},
        {'id': 'C', 'start_date': datetime(2023, 1, 11), 'end_date': datetime(2023, 1, 15), 'dependencies': 'B'},
    ]
    tasks_df = pd.DataFrame(tasks_data)
    tasks_df['start_date'] = pd.to_datetime(tasks_df['start_date'])
    tasks_df['end_date'] = pd.to_datetime(tasks_df['end_date'])

    expected_path = ['A', 'B', 'C']
    actual_path = find_critical_path(tasks_df)

    assert sorted(actual_path) == sorted(expected_path)

def test_find_critical_path_with_non_critical_branch():
    '''Tests a project with a parallel branch that has slack and is not on the critical path.'''
    tasks_data = [
        # Durations calculated as (end-start).days + 1
        {'id': 'A', 'start_date': datetime(2023, 1, 1), 'end_date': datetime(2023, 1, 5), 'dependencies': ''},         # 5 days
        {'id': 'B', 'start_date': datetime(2023, 1, 6), 'end_date': datetime(2023, 1, 15), 'dependencies': 'A'},        # 10 days (critical branch)
        {'id': 'C', 'start_date': datetime(2023, 1, 6), 'end_date': datetime(2023, 1, 8), 'dependencies': 'A'},         # 3 days (non-critical branch)
        {'id': 'D', 'start_date': datetime(2023, 1, 16), 'end_date': datetime(2023, 1, 20), 'dependencies': 'B,C'},   # 5 days
    ]
    tasks_df = pd.DataFrame(tasks_data)
    tasks_df['start_date'] = pd.to_datetime(tasks_df['start_date'])
    tasks_df['end_date'] = pd.to_datetime(tasks_df['end_date'])

    expected_path = ['A', 'B', 'D']
    actual_path = find_critical_path(tasks_df)

    assert sorted(actual_path) == sorted(expected_path)

def test_find_critical_path_empty_dataframe():
    '''Tests that an empty DataFrame returns an empty list.'''
    tasks_df = pd.DataFrame(columns=['id', 'start_date', 'end_date', 'dependencies'])
    assert find_critical_path(tasks_df) == []

def test_find_critical_path_with_invalid_dates():
    '''Tests that tasks with NaT dates are handled gracefully and excluded from calculation.'''
    tasks_data = [
        {'id': 'A', 'start_date': datetime(2023, 1, 1), 'end_date': datetime(2023, 1, 5), 'dependencies': ''},
        {'id': 'B', 'start_date': pd.NaT, 'end_date': pd.NaT, 'dependencies': 'A'},
    ]
    tasks_df = pd.DataFrame(tasks_data)
    tasks_df['start_date'] = pd.to_datetime(tasks_df['start_date'], errors='coerce')
    tasks_df['end_date'] = pd.to_datetime(tasks_df['end_date'], errors='coerce')

    expected_path = ['A'] # Only task A is valid
    actual_path = find_critical_path(tasks_df)

    assert actual_path == expected_path

def test_find_critical_path_no_dependencies():
    '''Tests tasks with no dependencies. The longest task should be on the critical path.'''
    tasks_data = [
        {'id': 'A', 'start_date': datetime(2023, 1, 1), 'end_date': datetime(2023, 1, 5), 'dependencies': ''}, # 5 days
        {'id': 'B', 'start_date': datetime(2023, 1, 1), 'end_date': datetime(2023, 1, 10), 'dependencies': ''}, # 10 days
    ]
    tasks_df = pd.DataFrame(tasks_data)
    tasks_df['start_date'] = pd.to_datetime(tasks_df['start_date'])
    tasks_df['end_date'] = pd.to_datetime(tasks_df['end_date'])

    # Task A has slack (it can finish on day 5 but doesn't have to until day 10).
    # Only task B, which defines the project length, has zero slack.
    expected_path = ['B']
    actual_path = find_critical_path(tasks_df)

    assert actual_path == expected_path

def test_find_critical_path_with_missing_dependency_id():
    '''Tests graceful handling of a dependency ID that does not exist in the task list.'''
    tasks_data = [
        {'id': 'A', 'start_date': datetime(2023, 1, 1), 'end_date': datetime(2023, 1, 5), 'dependencies': 'Z'}, # Depends on non-existent task
    ]
    tasks_df = pd.DataFrame(tasks_data)
    tasks_df['start_date'] = pd.to_datetime(tasks_df['start_date'])
    tasks_df['end_date'] = pd.to_datetime(tasks_df['end_date'])
    
    # Task A should be treated as having no valid dependencies, thus it becomes critical.
    expected_path = ['A']
    actual_path = find_critical_path(tasks_df)

    assert actual_path == expected_path
"""
