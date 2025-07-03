# File: dhf_dashboard/utils/critical_path_utils.py

import pandas as pd

def find_critical_path(tasks_df: pd.DataFrame) -> list:
    """
    Identifies the critical path in a project task list using a simplified forward/backward pass.

    SME Note: This is a simplified implementation for demonstration. It calculates Early Start (ES),
    Early Finish (EF), Late Start (LS), and Late Finish (LF) to find tasks with zero "slack",
    which defines the critical path. This is more robust than the previous implementation.

    Args:
        tasks_df (pd.DataFrame): DataFrame of tasks with columns
                                 ['id', 'start_date', 'end_date', 'dependencies'].
                                 It is assumed start_date and end_date are already datetime objects.

    Returns:
        list: A list of task IDs that form the critical path.
    """
    if tasks_df.empty:
        return []

    # Ensure duration is calculated correctly
    tasks_df['duration'] = (tasks_df['end_date'] - tasks_df['start_date']).dt.days
    task_map = tasks_df.set_index('id').to_dict('index')
    task_ids = tasks_df['id'].tolist()

    # --- Forward Pass: Calculate Early Start (ES) and Early Finish (EF) ---
    for task_id in task_ids:
        deps = str(task_map[task_id].get('dependencies', '')).replace(' ', '').split(',')
        deps = [d for d in deps if d] # Clean empty strings

        if not deps:
            task_map[task_id]['es'] = 0  # Starts at day 0
        else:
            # ES is the max of the EFs of all its dependencies
            max_ef_of_deps = max(task_map[dep_id].get('ef', 0) for dep_id in deps if dep_id in task_map)
            task_map[task_id]['es'] = max_ef_of_deps

        task_map[task_id]['ef'] = task_map[task_id]['es'] + task_map[task_id]['duration']

    # --- Backward Pass: Calculate Late Finish (LF) and Late Start (LS) ---
    project_finish_date = max(task['ef'] for task in task_map.values())

    for task_id in reversed(task_ids):
        # Find all tasks that depend on the current task
        successor_ids = [succ_id for succ_id, succ_task in task_map.items()
                         if task_id in str(succ_task.get('dependencies', '')).replace(' ', '').split(',')]

        if not successor_ids:
            task_map[task_id]['lf'] = project_finish_date # Ends at project finish
        else:
            # LF is the min of the LSs of all its successors
            min_ls_of_succs = min(task_map[succ_id].get('ls', project_finish_date) for succ_id in successor_ids if succ_id in task_map)
            task_map[task_id]['lf'] = min_ls_of_succs

        task_map[task_id]['ls'] = task_map[task_id]['lf'] - task_map[task_id]['duration']

    # --- Identify Critical Path ---
    # The critical path consists of tasks where Early Start equals Late Start (zero slack).
    critical_path = []
    for task_id, task in task_map.items():
        if task.get('es') == task.get('ls'):
            critical_path.append(task_id)

    return critical_path
