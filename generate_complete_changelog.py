#!/usr/bin/env python3

import os
import subprocess
import sys
import importlib.util

def import_script(script_name):
    """Import a Python script as a module."""
    # Get the directory where the current script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Join with the target script name to get full path
    script_path = os.path.join(script_dir, script_name)
    spec = importlib.util.spec_from_file_location(script_name, script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main():
    if len(sys.argv) != 3:
        print("Usage: generate_complete_changelog.py <firstbranch> <secondbranch>")
        sys.exit(1)

    first_branch = sys.argv[1]
    second_branch = sys.argv[2]
    
    # Create changelog directory if it doesn't exist
    changelog_dir = os.path.join(os.getcwd(), 'changelog')
    os.makedirs(changelog_dir, exist_ok=True)
    
    changelog_file = os.path.join(changelog_dir, f'changelog-{second_branch}.md')

    # Read existing changelog content if it exists
    existing_content = ""
    if os.path.exists(changelog_file):
        with open(changelog_file, 'r') as f:
            existing_content = f.read()

    # Import the comparison modules
    compare_api = import_script('compare_api.py')
    compare_components = import_script('compare_components.py')

    # Get the outputs
    api_output = compare_api.main()
    components_output = compare_components.main()

    # Write the complete changelog
    with open(changelog_file, 'w') as f:
        f.write(f"# API-Changelog: version {second_branch}\n\n")
        if api_output:
            f.write(api_output)
            f.write("\n")
        if components_output:
            f.write(components_output)
            f.write("\n")
        f.write(existing_content)

if __name__ == '__main__':
    main()