#!/usr/bin/env python3

import yaml
import argparse
import os
import subprocess
from typing import Dict, Any, List, Tuple

def get_file_content(branch: str, filepath: str) -> str:
    # Normalize filepath to use forward slashes
    normalized_path = filepath.replace('\\', '/')
    cmd = ['git', 'show', f'{branch}:{normalized_path}']
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error retrieving file from branch '{branch}': {result.stderr.strip()}")
        return None
    return result.stdout

def extract_components(spec: Dict[str, Any]) -> Dict[str, Any]:
    return spec.get('components', {}).get('schemas', {})

def get_component_fields(component: Dict) -> Dict[str, str]:
    """Extract fields and their types from a component"""
    properties = component.get('properties', {})
    return {field: prop.get('type', 'object') for field, prop in properties.items()}

def compare_fields(old_fields: Dict[str, str], new_fields: Dict[str, str]) -> Tuple[Dict[str, str], Dict[str, str], List[Tuple[str, str]], List[Tuple[str, str, str]]]:
    """Compare fields between old and new versions of a component"""
    old_field_names = set(old_fields.keys())
    new_field_names = set(new_fields.keys())
    
    added_fields = {field: new_fields[field] for field in new_field_names - old_field_names}
    removed_fields = {field: old_fields[field] for field in old_field_names - new_field_names}
    
    # Detect renamed fields (simple heuristic - matching types)
    renamed_fields = []
    changed_type_fields = []
    
    common_fields = old_field_names & new_field_names
    for field in common_fields:
        if old_fields[field] != new_fields[field]:
            changed_type_fields.append((field, old_fields[field], new_fields[field]))
    
    return added_fields, removed_fields, renamed_fields, changed_type_fields

def analyze_components(old_components: Dict[str, Any], new_components: Dict[str, Any]) -> Dict[str, Dict]:
    """Analyze changes between components and return a structured changelog"""
    changelog = {}
    
    # Handle added and modified components
    for name, component in new_components.items():
        if name not in old_components:
            changelog[name] = {
                'status': 'added',
                'fields': get_component_fields(component)
            }
        else:
            old_fields = get_component_fields(old_components[name])
            new_fields = get_component_fields(component)
            
            added_fields, removed_fields, renamed_fields, changed_type_fields = compare_fields(old_fields, new_fields)
            
            if any([added_fields, removed_fields, renamed_fields, changed_type_fields]):
                changelog[name] = {
                    'status': 'modified',
                    'fields': new_fields,
                    'added_fields': added_fields,
                    'removed_fields': removed_fields,
                    'renamed_fields': renamed_fields,
                    'changed_type_fields': changed_type_fields
                }
    
    # Handle removed components
    for name, component in old_components.items():
        if name not in new_components:
            changelog[name] = {
                'status': 'removed',
                'fields': get_component_fields(component)
            }
    
    return changelog

def generate_markdown(changelog: Dict) -> str:
    """Generate the changelog in Markdown format"""
    md_lines = ["## API-Model updates\n"]
    
    for class_name, changes in sorted(changelog.items()):
        status = changes['status']
        
        if status == 'added':
            md_lines.append(f"- **{class_name}** *(Added)*")
            if changes['fields']:
                md_lines.append("   - **Fields:**")
                for field, field_type in sorted(changes['fields'].items()):
                    md_lines.append(f"      - {field}: `{field_type}`")
                md_lines.append("")
            else:
                md_lines.append("   - No fields\n")
        
        elif status == 'removed':
            md_lines.append(f"- **{class_name}** *(Removed)*")
            if changes['fields']:
                md_lines.append("   - **Fields:**")
                for field, field_type in sorted(changes['fields'].items()):
                    md_lines.append(f"      - {field}: `{field_type}`")
                md_lines.append("")
        
        elif status == 'modified':
            md_lines.append(f"- **{class_name}**")
            if changes['added_fields']:
                md_lines.append("   - **Added Fields:**")
                for field, field_type in sorted(changes['added_fields'].items()):
                    md_lines.append(f"      - {field}: `{field_type}`")
            if changes['removed_fields']:
                md_lines.append("   - **Removed Fields:**")
                for field, field_type in sorted(changes['removed_fields'].items()):
                    md_lines.append(f"      - {field}: `{field_type}`")
            if changes['changed_type_fields']:
                md_lines.append("   - **Fields with Changed Types:**")
                for field, old_type, new_type in sorted(changes['changed_type_fields']):
                    md_lines.append(f"      - {field}: `{old_type}` -> `{new_type}`")
            md_lines.append("")
    
    return '\n'.join(md_lines)

def find_openapi_yaml(repo_path):
    for root, dirs, files in os.walk(repo_path):
        # Ignore the target directory
        if 'target' in root:
            continue
        if 'openapi.yaml' in files:
            # Normalize the path before returning
            return os.path.normpath(os.path.join(root, 'openapi.yaml')).replace('\\', '/')
    return None

def main():
    parser = argparse.ArgumentParser(description='Compare OpenAPI components between two branches.')
    parser.add_argument('base_branch', help='The base branch name (e.g., main)')
    parser.add_argument('feature_branch', help='The feature branch name to compare')

    args = parser.parse_args()

    repo_path = '.'
    openapi_file = find_openapi_yaml(repo_path)

    if not openapi_file:
        print("openapi.yaml not found in the repository.")
        return

    old_spec_content = get_file_content(args.base_branch, openapi_file)
    new_spec_content = get_file_content(args.feature_branch, openapi_file)

    if not all([old_spec_content, new_spec_content]):
        return

    old_spec = yaml.safe_load(old_spec_content)
    new_spec = yaml.safe_load(new_spec_content)

    old_components = extract_components(old_spec)
    new_components = extract_components(new_spec)

    changelog = analyze_components(old_components, new_components)
    return generate_markdown(changelog)

if __name__ == '__main__':
    print(main())