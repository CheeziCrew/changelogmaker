#!/usr/bin/env python3

import argparse
import subprocess
import os
import sys
import javalang
import difflib

def get_file_list(branch, folder):
    """
    Get the list of files in a given folder for a specific branch.
    """
    cmd = ['git', 'ls-tree', '-r', '--name-only', branch, folder]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error getting file list from branch {branch}: {result.stderr}")
        sys.exit(1)
    files = result.stdout.strip().split('\n')
    return files

def get_file_content(branch, filepath):
    """
    Get the content of a file at a specific branch.
    """
    cmd = ['git', 'show', f'{branch}:{filepath}']
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return result.stdout

def type_to_string(type_node):
    """
    Convert a type node to a string representation, handling generics and arrays.
    """
    if isinstance(type_node, javalang.tree.BasicType):
        base_type = type_node.name
    elif isinstance(type_node, javalang.tree.ReferenceType):
        base_type = type_node.name
        if type_node.arguments:
            args = ', '.join([type_to_string(arg.type) for arg in type_node.arguments])
            base_type += f'<{args}>'
    else:
        base_type = 'UnknownType'

    if type_node.dimensions:
        base_type += '[]' * len(type_node.dimensions)
    return base_type

def extract_class_info(tree):
    """
    Extract class names and their fields (names and types) from the AST.
    """
    classes = {}
    for path, node in tree.filter(javalang.tree.ClassDeclaration):
        class_name = node.name
        fields = {}
        for member in node.body:
            if isinstance(member, javalang.tree.FieldDeclaration):
                field_type = type_to_string(member.type)
                for decl in member.declarators:
                    fields[decl.name] = field_type
        classes[class_name] = fields
    return classes
    
def parse_java_code(code):
    """
    Parse Java code and return the Abstract Syntax Tree (AST).
    """
    try:
        tree = javalang.parse.parse(code)
        return tree
    except javalang.parser.JavaSyntaxError as e:
        print(f"Syntax error in code: {e}")
        return None
def similarity_score(a, b):
    """
    Compute the similarity score between two strings using SequenceMatcher.
    """
    return difflib.SequenceMatcher(None, a, b).ratio()

def jaccard_similarity(set1, set2):
    """
    Compute the Jaccard similarity between two sets.
    """
    if not set1 and not set2:
        return 1.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union

def compare_classes(old_classes, new_classes):
    """
    Compare classes and their fields between old and new versions,
    detecting renames of classes and fields, and changes in field types.
    """
    changelog = {}
    old_class_names = set(old_classes.keys())
    new_class_names = set(new_classes.keys())

    # Matched classes
    matched_old_classes = set()
    matched_new_classes = set()

    # First, process classes with the same name
    for class_name in old_class_names & new_class_names:
        old_fields = old_classes[class_name]
        new_fields = new_classes[class_name]
        old_field_names = set(old_fields.keys())
        new_field_names = set(new_fields.keys())

        added_fields = new_field_names - old_field_names
        removed_fields = old_field_names - new_field_names
        unchanged_fields = old_field_names & new_field_names

        # Detect renamed fields
        field_renames = []
        unmatched_old_fields = old_field_names - unchanged_fields
        unmatched_new_fields = new_field_names - unchanged_fields
        used_old_fields = set()
        used_new_fields = set()
        for new_field in unmatched_new_fields:
            best_match = None
            best_score = 0
            for old_field in unmatched_old_fields:
                score = similarity_score(new_field, old_field)
                if score > best_score:
                    best_score = score
                    best_match = old_field
            if best_score > 0.8:  # Threshold for field rename
                field_renames.append((best_match, new_field))
                used_old_fields.add(best_match)
                used_new_fields.add(new_field)
        unmatched_old_fields -= used_old_fields
        unmatched_new_fields -= used_new_fields
        added_fields -= used_new_fields
        removed_fields -= used_old_fields

        # Detect fields with changed types
        changed_type_fields = []
        for field in unchanged_fields:
            old_type = old_fields[field]
            new_type = new_fields[field]
            if old_type != new_type:
                changed_type_fields.append((field, old_type, new_type))

        # Only add to changelog if there are changes
        if added_fields or removed_fields or field_renames or changed_type_fields:
            changelog[class_name] = {
                'status': 'modified',
                'fields': new_fields,
                'added_fields': {field: new_fields[field] for field in added_fields},
                'removed_fields': {field: old_fields[field] for field in removed_fields},
                'unchanged_fields': {field: new_fields[field] for field in unchanged_fields - set(f for f, _, _ in changed_type_fields)},
                'renamed_fields': field_renames,
                'changed_type_fields': changed_type_fields
            }

        matched_old_classes.add(class_name)
        matched_new_classes.add(class_name)

    # Now, process unmatched new_classes
    unmatched_new_classes = new_class_names - matched_new_classes
    unmatched_old_classes = old_class_names - matched_old_classes

    # Build similarity matrix between unmatched new classes and unmatched old classes
    similarity_matrix = []
    for new_class in unmatched_new_classes:
        new_fields = new_classes[new_class]
        new_field_names = set(new_fields.keys())
        for old_class in unmatched_old_classes:
            old_fields = old_classes[old_class]
            old_field_names = set(old_fields.keys())
            # Combine class name similarity and field similarity
            name_sim = similarity_score(new_class, old_class)
            fields_sim = jaccard_similarity(new_field_names, old_field_names)
            combined_sim = (name_sim + fields_sim) / 2  # Simple average
            similarity_matrix.append((combined_sim, new_class, old_class, name_sim, fields_sim))

    # Sort similarity_matrix by descending combined similarity
    similarity_matrix.sort(reverse=True)

    # Map new classes to old classes based on highest similarity, avoiding duplicates
    class_mapping = {}
    used_old_classes = set()
    used_new_classes = set()
    for combined_sim, new_class, old_class, name_sim, fields_sim in similarity_matrix:
        if combined_sim > 0.6 and new_class not in used_new_classes and old_class not in used_old_classes:
            # Consider as renamed class
            class_mapping[new_class] = old_class
            used_new_classes.add(new_class)
            used_old_classes.add(old_class)
        else:
            continue

    # Process renamed classes
    for new_class, old_class in class_mapping.items():
        old_fields = old_classes[old_class]
        new_fields = new_classes[new_class]
        old_field_names = set(old_fields.keys())
        new_field_names = set(new_fields.keys())

        added_fields = new_field_names - old_field_names
        removed_fields = old_field_names - new_field_names
        unchanged_fields = old_field_names & new_field_names

        # Detect renamed fields
        field_renames = []
        unmatched_old_fields = old_field_names - unchanged_fields
        unmatched_new_fields = new_field_names - unchanged_fields
        used_old_fields = set()
        used_new_fields = set()
        for new_field in unmatched_new_fields:
            best_match = None
            best_score = 0
            for old_field in unmatched_old_fields:
                score = similarity_score(new_field, old_field)
                if score > best_score:
                    best_score = score
                    best_match = old_field
            if best_score > 0.8:
                field_renames.append((best_match, new_field))
                used_old_fields.add(old_field)
                used_new_fields.add(new_field)
        unmatched_old_fields -= used_old_fields
        unmatched_new_fields -= used_new_fields
        added_fields -= used_new_fields
        removed_fields -= used_old_fields

        # Detect fields with changed types
        changed_type_fields = []
        for field in unchanged_fields:
            old_type = old_fields[field]
            new_type = new_fields[field]
            if old_type != new_type:
                changed_type_fields.append((field, old_type, new_type))

        # Only add to changelog if there are changes
        if added_fields or removed_fields or field_renames or changed_type_fields or old_class != new_class:
            changelog[new_class] = {
                'status': 'renamed',
                'old_name': old_class,
                'fields': new_fields,
                'added_fields': {field: new_fields[field] for field in added_fields},
                'removed_fields': {field: old_fields[field] for field in removed_fields},
                'unchanged_fields': {field: new_fields[field] for field in unchanged_fields - set(f for f, _, _ in changed_type_fields)},
                'renamed_fields': field_renames,
                'changed_type_fields': changed_type_fields
            }

        matched_old_classes.add(old_class)
        matched_new_classes.add(new_class)

    # Remaining unmatched new_classes are added classes
    for new_class in unmatched_new_classes - matched_new_classes:
        fields = new_classes[new_class]
        changelog[new_class] = {
            'status': 'added',
            'fields': fields,
            'added_fields': fields,
            'removed_fields': {},
            'unchanged_fields': {},
            'renamed_fields': [],
            'changed_type_fields': []
        }

    # Remaining unmatched old_classes are removed classes
    for old_class in unmatched_old_classes - matched_old_classes:
        fields = old_classes[old_class]
        changelog[old_class] = {
            'status': 'removed',
            'fields': fields,
            'added_fields': {},
            'removed_fields': fields,
            'unchanged_fields': {},
            'renamed_fields': [],
            'changed_type_fields': []
        }

    return changelog

def generate_markdown(changelog):
    """
    Generate the changelog in Markdown format.
    """
    md_lines = []
    for class_name, changes in changelog.items():
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
            if changes['renamed_fields']:
                md_lines.append("   - **Renamed Fields:**")
                for old_field, new_field in changes['renamed_fields']:
                    old_type = changes['fields'].get(new_field, changes['removed_fields'].get(old_field, 'UnknownType'))  # Try new field first
                    new_type = changes['fields'].get(new_field, 'UnknownType')  # Fetch from new_fields
                    md_lines.append(f"      - {old_field}: `{old_type}`) -> {new_field}: `{new_type}`")
            if changes['changed_type_fields']:
                md_lines.append("   - **Fields with Changed Types:**")
                for field, old_type, new_type in changes['changed_type_fields']:
                    md_lines.append(f"      - {field}: `{old_type}` -> `{new_type}`")
            md_lines.append("")
        elif status == 'renamed':
            old_name = changes['old_name']
            md_lines.append(f"- **{old_name}** *(Renamed to {class_name})*")
            if changes['added_fields']:
                md_lines.append("   - **Added Fields:**")
                for field, field_type in sorted(changes['added_fields'].items()):
                    md_lines.append(f"      - {field}: `{field_type}`")
            if changes['removed_fields']:
                md_lines.append("   - **Removed Fields:**")
                for field, field_type in sorted(changes['removed_fields'].items()):
                    md_lines.append(f"      - {field}: `{field_type}`")
            if changes['renamed_fields']:
                md_lines.append("   - **Renamed Fields:**")
                for old_field, new_field in changes['renamed_fields']:
                    old_type = changes['fields'].get(new_field, changes['removed_fields'].get(old_field, 'UnknownType'))  # Try new field first
                    new_type = changes['fields'].get(new_field, 'UnknownType')  # Fetch from new_fields
                    md_lines.append(f"      - {old_field}: `{old_type}` -> {new_field}: `{new_type}`")
            if changes['changed_type_fields']:
                md_lines.append("   - **Fields with Changed Types:**")
                for field, old_type, new_type in changes['changed_type_fields']:
                    md_lines.append(f"      - {field}: `{old_type}` -> `{new_type}`")
            md_lines.append("")
    return '\n'.join(md_lines)

def main():
    parser = argparse.ArgumentParser(description='Generate a changelog based on changes in the api/model folder between two branches.')
    parser.add_argument('base_branch', help='The base branch name (e.g., main)')
    parser.add_argument('feature_branch', help='The feature branch name to compare')

    args = parser.parse_args()

    base_branch = args.base_branch
    feature_branch = args.feature_branch
    folder = "src/main/java/se/sundsvall/casedata/api/model"

    # Ensure we're in a git repository
    if not os.path.isdir('.git'):
        print("This script must be run in the root of a git repository.")
        sys.exit(1)

    # Collect all files from both branches
    base_files = set(get_file_list(base_branch, folder))
    feature_files = set(get_file_list(feature_branch, folder))

    all_files = base_files.union(feature_files)

    # Collect all classes from both branches
    all_old_classes = {}
    all_new_classes = {}

    for filepath in sorted(all_files):
        # Get file contents from base branch
        old_content = get_file_content(base_branch, filepath)
        if old_content:
            old_tree = parse_java_code(old_content)
            if old_tree:
                old_classes = extract_class_info(old_tree)
                all_old_classes.update(old_classes)

        # Get file contents from feature branch
        new_content = get_file_content(feature_branch, filepath)
        if new_content:
            new_tree = parse_java_code(new_content)
            if new_tree:
                new_classes = extract_class_info(new_tree)
                all_new_classes.update(new_classes)

    # Compare classes
    changelog = compare_classes(all_old_classes, all_new_classes)

    # Generate and print the changelog
    markdown = generate_markdown(changelog)
    
    # Write the changelog to class_output.md
    with open('class_output.md', 'w') as f:
        f.write('## API-Model updates\n\n')
        f.write(markdown)

if __name__ == '__main__':
    main()
