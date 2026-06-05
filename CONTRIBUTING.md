# Contributing to Arkhe

First off, thank you for considering contributing to Arkhe! It's people like you that make Arkhe such a great tool.

## Code of Conduct

By participating in this project, you are expected to uphold our Code of Conduct. Please be welcoming and respectful to all contributors.

## How Can I Contribute?

### Reporting Bugs

This section guides you through submitting a bug report for Arkhe. Following these guidelines helps maintainers and the community understand your report, reproduce the behavior, and find related reports.

- **Check if the bug has already been reported.**
- **Use a clear and descriptive title** for the issue to identify the problem.
- **Describe the exact steps which reproduce the problem** in as many details as possible.
- **Provide specific examples to demonstrate the steps.** Include links to files or copy/paste snippets, which you use in those examples.

### Suggesting Enhancements

This section guides you through submitting an enhancement suggestion for Arkhe, including completely new features and minor improvements to existing functionality.

- **Use a clear and descriptive title** for the issue to identify the suggestion.
- **Provide a step-by-step description of the suggested enhancement** in as many details as possible.
- **Describe the current behavior** and **explain which behavior you expected to see instead** and why.

### Pull Requests

The process described here has several goals:
- Maintain Arkhe's quality
- Fix problems that are important to users
- Engage the community in working toward the best possible Arkhe

Please follow these steps to have your contribution considered by the maintainers:

1. **Fork the repository** and create your branch from `main`.
2. If you've added code that should be tested, **add tests**.
3. If you've changed APIs, **update the documentation**.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

## Setting Up the Development Environment

Arkhe uses `uv` for dependency management and packaging.

1. **Clone your fork:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/arkhe.git
   cd arkhe
   ```

2. **Set up the virtual environment and install dependencies:**
   Ensure you have `uv` installed, then run:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   uv sync
   ```

3. **Running Tests:**
   We use `pytest` for running tests.
   ```bash
   pytest tests/
   ```

4. **Code Quality:**
   Please ensure your code conforms to our styling guidelines. We use standard Python formatting tools.

## Styleguides

### Git Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

### Python Styleguide

- All Python code must adhere to PEP 8.
- Use type hints wherever possible to improve code readability and maintainability.

Thank you for contributing!
