# API Changelog Generator

This project contains scripts to generate changelogs for API and model updates between two branches in a Git repository. It includes the following scripts:

- `compare_api.py`: Compares OpenAPI YAML files between two branches and generates a report of added and removed endpoints.
- `compare_components.py`: Generates a changelog for API components.
- `generate_complete_changelog.py`: Combines the outputs of the other scripts into a single changelog file.

## Prerequisites

- Python 3.x
- Git
- `pyyaml` library
- `javalang` library
  
## Installation

### Using Packaged Versions
You can download the packaged versions of the scripts from the [Releases](https://github.com/CheeziCrew/changelogmaker/releases) tab. These executables do not require Python to be installed on your machine.

1. Download the appropriate executable for your operating system (Windows or macOS) from the [Releases](https://github.com/CheeziCrew/changelogmaker/releases) tab.
2. Run the executable to generate the changelog.

### From Source

1. Clone the repository:
    ```sh
    git clone git@github.com:CheeziCrew/changelogmaker.git
    cd changelogmaker
    ```

2. Install the required Python libraries:
    ```sh
    pip install pyyaml javalang
    ```

## Usage

### Using Packaged Versions
1. Run the downloaded packaged version in a terminal
 
    Mac: 

    ```sh
    ./generate_complete_changelog_mac <base_branch> <feature_branch>
    ```

    Linux: 

    ```sh
    ./generate_complete_changelog_linux <base_branch> <feature_branch>
    ```

    Windows: 

    ```sh
    .\generate_complete_changelog.exe <base_branch> <feature_branch>
    ```

3. The script will generate a changelog.md file with the combined changelog.

### From Source
1. Run the generate_complete_changelog.py script with the base and feature branch names:
    ```sh
    python generate_complete_changelog.py <base_branch> <feature_branch>
    ```

2. The script will generate a changelog.md file with the combined changelog.

## License

This project is licensed under the MIT License - see the [LICENSE](#license) file for details.