# API Changelog Generator

This project contains scripts to generate changelogs for API and model updates between two branches in a Git repository. It includes the following scripts:

- `compare_api.py`: Compares OpenAPI YAML files between two branches and generates a report of added and removed endpoints.
- `generate_changelog.py`: Generates a changelog for Java classes, detecting added, removed, renamed, and modified classes and fields.
- `generate_complete_changelog.py`: Combines the outputs of the other scripts into a single changelog file.
- `extract_jira.py`: Extracts Jira ticket numbers from commit messages between two branches.

## Prerequisites

- Python 3.x
- Git
- `pyyaml` library
- `javalang` library

## Installation

1. Clone the repository:
    ```sh
    git clone <repository-url>
    cd <repository-directory>
    ```

2. Install the required Python libraries:
    ```sh
    pip install pyyaml javalang
    ```

## Usage

1. Run the generate_complete_changelog.py script with the base and feature branch names:
    ```sh
    python generate_complete_changelog.py <base_branch> <feature_branch>
    ```

2. The script will generate a changelog.md file with the combined changelog.

## License

This project is licensed under the MIT License - see the [LICENSE](#license) file for details.