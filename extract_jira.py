#!/usr/bin/env python3

import subprocess
import re
import sys

def extract_jira_tickets(branch1, branch2):
    try:
        # Get the commit logs for the two branches
        commits = subprocess.check_output(['git', 'log', f'{branch1}..{branch2}', '--pretty=format:%s']).decode('utf-8')
        
        # Regex to find Jira ticket numbers
        jira_pattern = r'UF-\d+'
        tickets = re.findall(jira_pattern, commits)
        
        # Return unique ticket numbers
        return set(tickets)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.output.decode('utf-8')}")
        return set()

def write_tickets_to_md(tickets, filename='jira_output.md'):
    with open(filename, 'w') as f:
        f.write("## Jira issues referenced\n\n")
        # Sort tickets numerically based on the number part
        sorted_tickets = sorted(tickets, key=lambda x: int(x.split('-')[1]))
        for ticket in sorted_tickets:
            f.write(f"- [Link to {ticket}](https://jira.sundsvall.se/browse/{ticket})\n")

# Example usage
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: extract_jira.py <branch1> <branch2>")
        sys.exit(1)

    branch1 = sys.argv[1]
    branch2 = sys.argv[2]
    tickets = extract_jira_tickets(branch1, branch2)
    write_tickets_to_md(tickets)  # New function call to write to .md
