# File: dhf_dashboard/utils/critical_path_utils.py

import pandas as pd
from datetime import timedelta

def find_critical_path(tasks_df: pd.DataFrame):
    """
    Identifies the critical path in a project task list.

    This is a simplified implementation for demonstration. It calculates the
    longest path through the task dependencies based on task end dates.
    In a real-world scenario, a more robust algorithm like PERT or CPM would be used.

    Args:
        tasks_df (pd.DataFrame): DataFrame of tasks with columns 
                                 ['id', 'start_date', 'end_date', 'dependencies'].

    Returns:
        list: A list of task IDs that form the critical path.
    """
    if tasks_df.empty:
        return []

    # Ensure dates are datetime objects
    tasks_df['start_date'] = pd.to_datetime(tasks_df['start_date'])
    tasks_df['end_date'] = pd.to_datetime(tasks_df['end_date'])

    # Create a dictionary for easy lookup
    task_map = tasks_df.set_index('id').to_dict('index')

    paths = {}
    for task_id, task in task_map.items():
        # Find the latest end date of all dependencies
        dep_ids = str(task.get('dependencies', '')).replace(' ', '').split(',')
        latest_dependency_end = pd.Timestamp.min
        
        if dep_ids and dep_ids[0] != '':
            for dep_id in dep_ids:
                if dep_id in task_map:
                    latest_dependency_end = max(latest_dependency_end, task_map[dep_id]['end_date'])
        
        # This task's path ends on its own end_date
        path_end_date = task['end_date']
        
        # A simple proxy for path length: the final end date
        paths[task_id] = path_end_date

    # Find the task that finishes last, which terminates the critical path
    if not paths:
        return []
    
    last_task_id = max(paths, key=paths.get)

    # Trace back the critical path from the last task
    critical_path = []
    current_task_id = last_task_id

    while current_task_id:
        critical_path.insert(0, current_task_id)
        task_info = task_map.get(current_task_id)
        if not task_info or pd.isna(task_info.get('dependencies')) or not task_info.get('dependencies'):
            break

        dep_ids = str(task_info.get('dependencies', '')).replace(' ', '').split(',')
        
        # Find the dependency with the latest end date, as that determined the start of the current task
        latest_dep_id = None
        latest_dep_end = pd.Timestamp.min
        for dep_id in dep_ids:
            if dep_id in task_map and task_map[dep_id]['end_date'] > latest_dep_end:
                latest_dep_end = task_map[dep_id]['end_date']
                latest_dep_id = dep_id
        
        current_task_id = latest_dep_id

    return critical_path
