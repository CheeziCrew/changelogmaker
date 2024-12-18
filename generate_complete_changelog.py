#!/usr/bin/env python3

import subprocess
import os
import sys

def run_script(script_name, *args):
    """Run a script and return its output."""
    result = subprocess.run([script_name] + list(args), capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running {script_name}: {result.stderr.strip()}")
        sys.exit(1)
    return result.stdout

def main():
    if len(sys.argv) != 3:
        print("Usage: generate_complete_changelog.py <firstbranch> <secondbranch>")
        sys.exit(1)

    first_branch = sys.argv[1]
    second_branch = sys.argv[2]
    changelog_file = 'changelog.md'

    # Read existing changelog content if it exists
    existing_content = ""
    if os.path.exists(changelog_file):
        with open(changelog_file, 'r') as f:
            existing_content = f.read()

    # Open changelog_file for writing
    with open(changelog_file, 'w') as f:
        f.write(f"# API-Changelog: version {second_branch}\n\n")

        # Define output files
        jira_file = 'jira_output.md'
        api_file = 'api_output.md'
        class_file = 'class_output.md'

        # Call extract_jira.py
        run_script('extract_jira.py', first_branch, second_branch)
        
        # Open jira_file for reading
        with open(jira_file, 'r') as jira_f:
            jira_output = jira_f.read()
            f.write(jira_output)
            f.write("\n")
        
        # Call compare_api.py
        run_script('compare_api.py', first_branch, second_branch)
        with open(api_file, 'r') as api_f:  # Ensure this is opened for reading
            api_output = api_f.read()
            f.write(api_output)  # Write to changelog_file while it's open
            f.write("\n")
        # Call generate_changelog.py
        run_script('generate_changelog.py', first_branch, second_branch)
        with open(class_file, 'r') as class_f:  # Ensure this is opened for reading
            class_output = class_f.read()
            f.write(class_output)  # Write to changelog_file while it's open
            f.write("\n")

        # Append the existing content
        f.write(existing_content)

        # Clean up the output files
        for file in [jira_file, api_file, class_file]:
            os.remove(file)

if __name__ == '__main__':
    main()