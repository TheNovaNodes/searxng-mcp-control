# Contributing to SearXNG MCP Control

Thank you for your interest in contributing to the **SearXNG MCP Control** server! This project is part of the **TheNovaNodes Antigravity Agent Ecosystem**.

## How to Contribute

1. **Fork the Repository**: Create your own fork of the repository.
2. **Create a Branch**: Create a feature or bugfix branch from `main`.
3. **Make Changes**: Implement your changes. Ensure all documentation and comments are written in high-quality English.
4. **Add Tests**: Add unit tests for your changes. Tests are located in the `tests/` directory and use `pytest`. Ensure they pass.
5. **Submit a Pull Request**: Submit a PR to the `main` branch of the original repository. Provide a clear description of the problem you are solving and how your changes address it.

## Development Environment Setup

Ensure you have Python 3.10+ installed.

```bash
# Install the package in editable mode with development dependencies
pip install -e .[dev]

# Run tests
python -m pytest tests/ --cov=searxng_mcp_control
```

## Quality Standards

As part of the TheNovaNodes ecosystem, we maintain high standards:
* **Documentation**: Must be clear, precise, and in high-quality English.
* **Code**: Must be clean, well-typed, and include docstrings.
* **Testing**: High test coverage is expected for any new logic.

We appreciate your contributions!
