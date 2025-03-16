#!/usr/bin/env python3

import yaml
import argparse
import os
import subprocess

def find_openapi_yaml(repo_path):
    for root, dirs, files in os.walk(repo_path):
        # Ignore the target directory
        if 'target' in root:
            continue
        if 'openapi.yaml' in files:
            return os.path.join(root, 'openapi.yaml')
    return None

def extract_endpoints(spec):
    endpoints = {}  # key: (path, method), value: tags
    paths = spec.get('paths', {})
    for path, path_item in paths.items():
        for method, operation in path_item.items():
            if method.lower() in ['get', 'put', 'post', 'delete', 'options', 'head', 'patch', 'trace']:
                tags = operation.get('tags', ['No Tag'])
                endpoint = (path, method.upper())
                endpoints[endpoint] = tags
    return endpoints

def get_file_content(branch, filepath):
    cmd = ['git', 'show', f'{branch}:{filepath}']
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error retrieving file from branch '{branch}': {result.stderr.strip()}")
        return None
    return result.stdout

def main():
    parser = argparse.ArgumentParser(description='Compare OpenAPI YAML files between two branches.')
    parser.add_argument('base_branch', help='The base branch name (e.g., main)')
    parser.add_argument('feature_branch', help='The feature branch name to compare')

    args = parser.parse_args()

    repo_path = '.'  # Assuming the script is run in the repo root
    openapi_file = find_openapi_yaml(repo_path)

    if not openapi_file:
        print("openapi.yaml not found in the repository.")
        return


    old_spec_content = get_file_content(args.base_branch, openapi_file)
    new_spec_content = get_file_content(args.feature_branch, openapi_file)

    if old_spec_content is None:
        print(f"Failed to retrieve the OpenAPI spec from the base branch '{args.base_branch}'.")
        return

    if new_spec_content is None:
        print(f"Failed to retrieve the OpenAPI spec from the feature branch '{args.feature_branch}'.")
        return

    old_spec = yaml.safe_load(old_spec_content)
    new_spec = yaml.safe_load(new_spec_content)

    old_endpoints = extract_endpoints(old_spec)
    new_endpoints = extract_endpoints(new_spec)

    old_endpoints_set = set(old_endpoints.keys())
    new_endpoints_set = set(new_endpoints.keys())

    added_endpoints = new_endpoints_set - old_endpoints_set
    removed_endpoints = old_endpoints_set - new_endpoints_set

    added_endpoints_by_tag = {}
    for endpoint in added_endpoints:
        tags = new_endpoints[endpoint]
        for tag in tags:
            if tag not in added_endpoints_by_tag:
                added_endpoints_by_tag[tag] = []
            added_endpoints_by_tag[tag].append(endpoint)

    removed_endpoints_by_tag = {}
    for endpoint in removed_endpoints:
        tags = old_endpoints[endpoint]
        for tag in tags:
            if tag not in removed_endpoints_by_tag:
                removed_endpoints_by_tag[tag] = []
            removed_endpoints_by_tag[tag].append(endpoint)

    all_tags = set(added_endpoints_by_tag.keys()).union(removed_endpoints_by_tag.keys())

    output = []
    output.append("## API-endpoints\n")
    for tag in sorted(all_tags):
        output.append(f"### {tag}:\n")
        if tag in added_endpoints_by_tag and added_endpoints_by_tag[tag]:
            output.append("#### New endpoints:\n")
            output.append("```\n")
            for endpoint in sorted(added_endpoints_by_tag[tag], key=lambda e: (e[0], e[1])):
                output.append(f"- [{endpoint[1]}] {endpoint[0]}\n")
            output.append("```\n")
        if tag in removed_endpoints_by_tag and removed_endpoints_by_tag[tag]:
            output.append("#### Removed endpoints:\n")
            output.append("```\n")
            for endpoint in sorted(removed_endpoints_by_tag[tag], key=lambda e: (e[0], e[1])):
                output.append(f"- [{endpoint[1]}] {endpoint[0]}\n")
            output.append("```\n")
        output.append("\n")

    return ''.join(output)

if __name__ == '__main__':
    main()
