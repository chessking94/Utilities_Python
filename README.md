# Utilities_Python
This project is a package of oft-used utilities. It is not stored in PyPI, so it needs to be installed from source.

## Publishing a New Version
To publish a version, follow the below instructions:

1. Create a new branch.
2. Make changes and commit them.
3. When all squared away, ensure the following files are updated as necessary and committed:
    - `src/__init__py` - version number
    - `CHANGELOG.rst` - detail the changes made
    - `requirements.txt` - dependencies
    - `setup.py` - mirror the dependencies
4. Execute the `build_release.py` script to build a new `*.tar.gz` file package and commit it.
5. Create the PR.
6. Once the PR is approved and the branch is merged into master, add a tag to the most recent commit via the web UI.
    - This tag should be in alignment with the version number in the commit, following the semantic versioning standard.
    - Example: `1.2.3`

## Installing/Updating the Package
Use pip, with the syntax `pip install git+https://git.example.com/username/Utilities_Python.git@1.2.3` syntax.
