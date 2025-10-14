import json
import re
from pathlib import Path
from collections import defaultdict

# Point to the tasklist/plan directory where JSON files are located
BASE = Path(__file__).parent.parent.parent.parent / 'tasklist' / 'plan'

def load_files_list():
    """Load the files_list.json file."""
    with open(BASE / 'files_list.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def patterns_overlap(pattern1, type1, pattern2, type2):
    """
    Check if two file patterns could potentially overlap.
    Returns True if they might match the same files.
    """
    # Exact matches - only overlap if identical
    if type1 == 'exact' and type2 == 'exact':
        return pattern1 == pattern2
    
    # If one is exact and one is regex, check if exact matches the regex
    if type1 == 'exact' and type2 == 'regex':
        try:
            return bool(re.match(pattern2, pattern1))
        except re.error:
            return False
    
    if type1 == 'regex' and type2 == 'exact':
        try:
            return bool(re.match(pattern1, pattern2))
        except re.error:
            return False
    
    # Both are regex - need to be more precise
    if type1 == 'regex' and type2 == 'regex':
        # Extract the fixed directory prefix (before any regex wildcards)
        prefix1 = re.split(r'[.*+?\[\\(|]', pattern1)[0]
        prefix2 = re.split(r'[.*+?\[\\(|]', pattern2)[0]
        
        # Check if one prefix is a parent of the other
        # Only consider conflict if one path could actually match the other
        if prefix1 and prefix2:
            # If prefixes are identical or one contains the other as a directory prefix
            if prefix1 == prefix2:
                return True
            # Check if one is a subdirectory of the other
            if prefix1.startswith(prefix2 + '/') or prefix2.startswith(prefix1 + '/'):
                # Only conflict if the wildcard could actually reach the other pattern
                # For example: "src/.*" and "src/services/.*" could overlap
                # But "src/config/file.ts" and "src/services/.*" cannot
                shorter = prefix1 if len(prefix1) < len(prefix2) else prefix2
                longer = prefix2 if shorter == prefix1 else prefix1
                shorter_pattern = pattern1 if shorter == prefix1 else pattern2
                
                # If the shorter pattern has a wildcard that could match into subdirs
                if '.*' in shorter_pattern or '.+' in shorter_pattern:
                    return True
        
        # If both patterns have wildcards in the same directory level, check overlap
        # Extract path components before wildcards
        parts1 = prefix1.rstrip('/').split('/')
        parts2 = prefix2.rstrip('/').split('/')
        
        # They only conflict if they share all directory components up to where wildcards start
        min_len = min(len(parts1), len(parts2))
        if min_len > 0 and parts1[:min_len] == parts2[:min_len]:
            # Same directory path before wildcards - check if wildcards could overlap
            if '.*' in pattern1 or '.*' in pattern2:
                return True
    
    return False

def find_conflicts(tasks):
    """
    Find conflicts between tasks based on file pattern overlaps.
    Returns a list of conflict entries for each task.
    """
    # Build a mapping of task_id to its file patterns
    task_files = {}
    for task in tasks:
        task_id = task['task_id']
        files = task.get('files', [])
        task_files[task_id] = files
    
    # For each task, find other tasks that might conflict
    conflict_graph = []
    
    for task in tasks:
        task_id = task['task_id']
        my_files = task_files[task_id]
        conflicts = []
        
        # Check against all other tasks
        for other_task in tasks:
            other_id = other_task['task_id']
            if other_id == task_id:
                continue
            
            other_files = task_files[other_id]
            
            # Check if any file patterns overlap
            has_conflict = False
            conflicting_patterns = []
            
            for my_file in my_files:
                my_pattern = my_file['pattern']
                my_type = my_file['type']
                
                for other_file in other_files:
                    other_pattern = other_file['pattern']
                    other_type = other_file['type']
                    
                    if patterns_overlap(my_pattern, my_type, other_pattern, other_type):
                        has_conflict = True
                        conflicting_patterns.append({
                            'my_pattern': my_pattern,
                            'other_pattern': other_pattern
                        })
            
            if has_conflict:
                conflicts.append({
                    'task_id': other_id,
                    'conflicting_patterns': conflicting_patterns
                })
        
        conflict_graph.append({
            'task_id': task_id,
            'conflicts_with': conflicts,
            'conflict_count': len(conflicts),
            'files': my_files
        })
    
    return conflict_graph

def main():
    """Generate conflict_graph.json from files_list.json"""
    print("Loading files_list.json...")
    data = load_files_list()
    # Handle both array and object with 'tasks' key
    tasks = data if isinstance(data, list) else data.get('tasks', [])
    
    print(f"Analyzing {len(tasks)} tasks for conflicts...")
    conflict_graph = find_conflicts(tasks)
    
    # Sort by conflict count (descending) for easier analysis
    conflict_graph.sort(key=lambda x: x['conflict_count'], reverse=True)
    
    # Prepare output
    output = {
        'metadata': {
            'generated_from': 'files_list.json',
            'total_tasks': len(tasks),
            'description': 'Lists file pattern conflicts between tasks'
        },
        'conflicts': conflict_graph
    }
    
    # Write to conflict_graph.json
    output_path = BASE / 'conflict_graph.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✓ Generated {output_path}")
    
    # Print summary statistics
    total_conflicts = sum(entry['conflict_count'] for entry in conflict_graph)
    max_conflicts = max((entry['conflict_count'] for entry in conflict_graph), default=0)
    avg_conflicts = total_conflicts / len(tasks) if tasks else 0
    
    print(f"\nConflict Statistics:")
    print(f"  Total conflict relationships: {total_conflicts}")
    print(f"  Average conflicts per task: {avg_conflicts:.2f}")
    print(f"  Maximum conflicts (single task): {max_conflicts}")
    
    # Show top 5 most conflicted tasks
    print(f"\nTop 5 most conflicted tasks:")
    for entry in conflict_graph[:5]:
        task_id = entry['task_id']
        count = entry['conflict_count']
        conflicts = [c['task_id'] for c in entry['conflicts_with']]
        print(f"  {task_id}: {count} conflicts")
        if count <= 5:
            print(f"    Conflicts with: {', '.join(conflicts)}")

if __name__ == '__main__':
    main()
