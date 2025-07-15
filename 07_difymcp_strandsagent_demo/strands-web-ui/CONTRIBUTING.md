# Contributing to Strands Web UI

Thank you for your interest in contributing to Strands Web UI! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md) to foster an open and welcoming environment.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment
4. Create a new branch for your feature or bug fix

## Development Environment

To set up the development environment:

```bash
# Clone the repository
git clone https://github.com/yourusername/strands-web-ui.git
cd strands-web-ui

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

## Making Changes

1. Create a new branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and ensure they follow the project's coding style
3. Add tests for your changes if applicable
4. Run the tests to ensure they pass:
   ```bash
   pytest
   ```

5. Format your code:
   ```bash
   black .
   isort .
   ```

## Submitting Changes

1. Commit your changes with a descriptive commit message:
   ```bash
   git commit -m "Add feature: your feature description"
   ```

2. Push your branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

3. Create a pull request from your fork to the main repository

## Pull Request Guidelines

- Provide a clear description of the changes in your pull request
- Include any relevant issue numbers in the PR description
- Ensure all tests pass
- Update documentation if necessary
- Keep pull requests focused on a single topic

## Code Style

This project uses:
- [Black](https://black.readthedocs.io/) for code formatting
- [isort](https://pycqa.github.io/isort/) for import sorting
- [mypy](http://mypy-lang.org/) for type checking

## License

By contributing to this project, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
