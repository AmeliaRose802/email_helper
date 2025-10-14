#!/usr/bin/env python3
"""
Optimal Parallel Execution Plan Generator

This script generates an optimal parallel execution plan that:
1. Maximizes parallel task execution
2. Respects dependency order (prerequisites before dependents)
3. Groups tasks of similar sizes in the same wave
4. Prevents file conflicts within the same wave
5. Supports regex patterns for file matching
"""

import json
import re
from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FilePattern:
    pattern: str
    type: str  # 'exact', 'regex', or 'glob'
    
    def matches(self, file_path: str) -> bool:
        """Check if a file path matches this pattern"""
        if self.type == 'exact':
            return self.pattern == file_path
        elif self.type == 'regex':
            try:
                return bool(re.search(self.pattern, file_path))
            except re.error:
                return False
        elif self.type == 'glob':
            # Convert glob to regex
            regex_pattern = self.pattern.replace('**/', '.*').replace('*', '[^/]*')
            try:
                return bool(re.search(regex_pattern, file_path))
            except re.error:
                return False
        return False


@dataclass
class Task:
    task_id: str
    size: str
    expected_runtime_min: int
    depends_on: List[str]
    conflicts_with: List[str]
    file_patterns: List[FilePattern]
    tags: List[str]
    enabler: bool = False
    
    def __hash__(self):
        return hash(self.task_id)


class ParallelExecutionPlanner:
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.file_conflicts: Dict[Tuple[str, str], bool] = {}
        self.task_descriptions: Dict[str, Dict] = {}
        self.task_files: Dict[str, List[Dict]] = {}
        
    def load_data(self, dependency_file: str, conflict_file: str, 
                  descriptions_file: str, files_file: str):
        """Load task data from JSON files"""
        
        # Load dependencies (contains task metadata)
        with open(dependency_file, 'r') as f:
            dependency_data = json.load(f)
            # Handle both formats: array or object with 'dependencies' key
            if isinstance(dependency_data, dict) and 'dependencies' in dependency_data:
                dependencies = dependency_data['dependencies']
            else:
                dependencies = dependency_data
        
        # Load conflicts (contains conflict info)
        with open(conflict_file, 'r') as f:
            conflict_data = json.load(f)
            # Handle both formats: array or object with 'conflicts' key
            if isinstance(conflict_data, dict) and 'conflicts' in conflict_data:
                conflicts = conflict_data['conflicts']
            else:
                conflicts = conflict_data
        
        # Load task descriptions
        with open(descriptions_file, 'r') as f:
            descriptions_data = json.load(f)
            if isinstance(descriptions_data, dict) and 'tasks' in descriptions_data:
                descriptions = descriptions_data['tasks']
            else:
                descriptions = descriptions_data
            
            for desc in descriptions:
                self.task_descriptions[desc['task_id']] = {
                    'summary': desc.get('summary', ''),
                    'description': desc.get('description', '')
                }
        
        # Load files list
        with open(files_file, 'r') as f:
            files_data = json.load(f)
            if isinstance(files_data, dict) and 'tasks' in files_data:
                files_tasks = files_data['tasks']
            else:
                files_tasks = files_data
            
            for file_task in files_tasks:
                self.task_files[file_task['task_id']] = file_task.get('files', [])
        
        # Build conflicts_with map from conflicts data
        conflicts_map = {}
        task_ids_set = set(t['task_id'] for t in dependencies)
        for task_conflict in conflicts:
            task_id = task_conflict['task_id']
            conflicts_with = []
            for conflict_info in task_conflict.get('conflicts_with', []):
                # Only include conflicts with tasks that actually exist
                conflict_task_id = conflict_info['task_id']
                if conflict_task_id in task_ids_set:
                    conflicts_with.append(conflict_task_id)
            conflicts_map[task_id] = conflicts_with
        
        # Build task objects from dependency data
        for task_data in dependencies:
            task_id = task_data['task_id']
            
            # Filter out dependencies that don't exist in the task list
            depends_on = [dep for dep in task_data.get('depends_on', []) 
                         if any(t['task_id'] == dep for t in dependencies)]
            
            task = Task(
                task_id=task_id,
                size=task_data.get('size', 'M'),
                expected_runtime_min=task_data.get('expected_runtime_min', 20),
                depends_on=depends_on,
                conflicts_with=conflicts_map.get(task_id, []),
                file_patterns=[],  # Not used anymore, relying on conflicts_with
                tags=task_data.get('tags', []),
                enabler=task_data.get('enabler', False)
            )
            
            self.tasks[task_id] = task
            
            # Build dependency graphs
            for dep in task.depends_on:
                self.dependency_graph[task_id].add(dep)
                self.reverse_dependency_graph[dep].add(task_id)
    
    def _normalize_file_paths(self, files: List[str]) -> List[str]:
        """Keep file paths as-is - we'll use explicit conflicts only"""
        # Don't normalize - keep exact paths for precise conflict detection
        return files
    
    def _check_file_conflict(self, task1: Task, task2: Task) -> bool:
        """Check if two tasks have file conflicts using explicit conflicts list"""
        if task1.task_id == task2.task_id:
            return False
            
        # Check explicit conflicts from conflict graph
        if task2.task_id in task1.conflicts_with or task1.task_id in task2.conflicts_with:
            return True
        
        return False
    
    def _get_task_priority(self, task: Task) -> Tuple[int, int]:
        """Calculate task priority for scheduling (lower = higher priority)"""
        # NO PRIORITY CONSIDERATIONS - just pack for maximum parallelism
        # 1. Number of dependents (more dependents = schedule earlier to unblock)
        # 2. Task ID for deterministic ordering
        
        dependent_count = len(self.reverse_dependency_graph.get(task.task_id, set()))
        
        return (-dependent_count, task.task_id)
    
    def _topological_sort_with_priority(self) -> List[str]:
        """Perform topological sort with priority-based ordering"""
        in_degree = defaultdict(int)
        for task_id in self.tasks:
            in_degree[task_id] = len(self.dependency_graph[task_id])
        
        # Use priority queue (simulate with sorted list)
        available_tasks = []
        for task_id, degree in in_degree.items():
            if degree == 0:
                available_tasks.append(task_id)
        
        result = []
        
        while available_tasks:
            # Sort available tasks by priority
            available_tasks.sort(key=lambda tid: self._get_task_priority(self.tasks[tid]))
            
            # Take the highest priority task
            current_task = available_tasks.pop(0)
            result.append(current_task)
            
            # Update in-degrees for dependent tasks
            for dependent in self.reverse_dependency_graph[current_task]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    available_tasks.append(dependent)
        
        if len(result) != len(self.tasks):
            raise ValueError("Circular dependency detected!")
        
        return result
    
    def generate_execution_plan(self) -> Dict:
        """Generate the optimal parallel execution plan"""
        # Get topologically sorted task order
        sorted_tasks = self._topological_sort_with_priority()
        
        waves = []
        completed_tasks = set()
        
        while completed_tasks != set(self.tasks.keys()):
            # Find all tasks whose dependencies are completed
            available_tasks = []
            for task_id in sorted_tasks:
                if task_id not in completed_tasks:
                    task = self.tasks[task_id]
                    if all(dep in completed_tasks for dep in task.depends_on):
                        available_tasks.append(task)
            
            if not available_tasks:
                raise ValueError("No available tasks - possible circular dependency!")
            
            # GREEDY PACKING: Add as many tasks as possible without conflicts
            wave_tasks = []
            used_task_ids = set()
            
            # Sort available tasks to try to pack efficiently
            # Sort by: fewer conflicts first, then by ID for determinism
            available_tasks.sort(key=lambda t: (len(t.conflicts_with), t.task_id))
            
            for task in available_tasks:
                if task.task_id in used_task_ids:
                    continue
                
                # Check if this task conflicts with any already selected task
                can_add = True
                for selected_task_dict in wave_tasks:
                    selected_task = self.tasks[selected_task_dict['task_id']]
                    if self._check_file_conflict(task, selected_task):
                        can_add = False
                        break
                
                if can_add:
                    # Get task description and files
                    task_desc = self.task_descriptions.get(task.task_id, {})
                    task_files_list = self.task_files.get(task.task_id, [])
                    
                    wave_tasks.append({
                        'task_id': task.task_id,
                        'summary': task_desc.get('summary', ''),
                        'description': task_desc.get('description', ''),
                        'size': task.size,
                        'expected_runtime_min': task.expected_runtime_min,
                        'tags': task.tags,
                        'enabler': task.enabler,
                        'files': task_files_list,
                        'depends_on': task.depends_on,
                        'conflicts_with': task.conflicts_with
                    })
                    used_task_ids.add(task.task_id)
                    completed_tasks.add(task.task_id)
            
            # Calculate wave stats
            wave_total_time = max((t['expected_runtime_min'] for t in wave_tasks), default=0)
            
            if wave_tasks:
                waves.append({
                    'wave_number': len(waves) + 1,
                    'tasks': wave_tasks,
                    'parallel_task_count': len(wave_tasks),
                    'estimated_wave_time_min': wave_total_time,
                    'size_distribution': self._get_size_distribution(wave_tasks)
                })
        
        # Calculate summary statistics
        total_time = sum(wave['estimated_wave_time_min'] for wave in waves)
        total_tasks = len(self.tasks)
        avg_parallelism = total_tasks / len(waves) if waves else 0
        
        return {
            'execution_plan': {
                'waves': waves,
                'summary': {
                    'total_waves': len(waves),
                    'total_tasks': total_tasks,
                    'estimated_total_time_min': total_time,
                    'average_parallelism': round(avg_parallelism, 2),
                    'max_parallelism': max(wave['parallel_task_count'] for wave in waves) if waves else 0,
                    'efficiency_metrics': {
                        'sequential_time_min': sum(task.expected_runtime_min for task in self.tasks.values()),
                        'parallel_time_min': total_time,
                        'time_savings_percent': round((1 - total_time / sum(task.expected_runtime_min for task in self.tasks.values())) * 100, 1) if sum(task.expected_runtime_min for task in self.tasks.values()) > 0 else 0
                    }
                }
            }
        }
    
    def _get_size_distribution(self, tasks: List[Dict]) -> Dict[str, int]:
        """Get the distribution of task sizes in a wave"""
        distribution = defaultdict(int)
        for task in tasks:
            distribution[task['size']] += 1
        return dict(distribution)


def main():
    """Main execution function"""
    planner = ParallelExecutionPlanner()
    
    # File paths - input files are in tasklist/plan, output goes there too
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent.parent  # Go up to project root (.github/dev/dev_scripts -> .github/dev -> .github -> root)
    plan_dir = project_root / "tasklist" / "plan"
    
    dependency_file = plan_dir / "dependency_graph.json"
    conflict_file = plan_dir / "conflict_graph.json"
    descriptions_file = plan_dir / "task_descriptions.json"
    files_file = plan_dir / "files_list.json"
    output_file = plan_dir / "parallel_execution_plan.json"
    
    try:
        print("Loading task data...")
        planner.load_data(str(dependency_file), str(conflict_file), 
                         str(descriptions_file), str(files_file))
        print(f"Loaded {len(planner.tasks)} tasks")
        
        print("Generating optimal parallel execution plan...")
        execution_plan = planner.generate_execution_plan()
        
        print("Saving execution plan...")
        with open(output_file, 'w') as f:
            json.dump(execution_plan, f, indent=2)
        
        # Print summary
        summary = execution_plan['execution_plan']['summary']
        print(f"\n=== EXECUTION PLAN SUMMARY ===")
        print(f"Total Tasks: {summary['total_tasks']}")
        print(f"Total Waves: {summary['total_waves']}")
        print(f"Estimated Total Time: {summary['estimated_total_time_min']} minutes")
        print(f"Average Parallelism: {summary['average_parallelism']} tasks/wave")
        print(f"Maximum Parallelism: {summary['max_parallelism']} tasks/wave")
        print(f"Time Savings: {summary['efficiency_metrics']['time_savings_percent']}%")
        print(f"Sequential Time: {summary['efficiency_metrics']['sequential_time_min']} minutes")
        print(f"Parallel Time: {summary['efficiency_metrics']['parallel_time_min']} minutes")
        
        print(f"\n=== WAVE BREAKDOWN ===")
        for wave in execution_plan['execution_plan']['waves']:
            size_dist = wave['size_distribution']
            size_str = ', '.join([f"{size}:{count}" for size, count in size_dist.items()])
            print(f"Wave {wave['wave_number']}: {wave['parallel_task_count']} tasks, {wave['estimated_wave_time_min']}min ({size_str})")
            
            # Show task IDs for each wave
            task_ids = [task['task_id'] for task in wave['tasks']]
            print(f"  Tasks: {', '.join(task_ids)}")
        
        print(f"\nExecution plan saved to: {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()