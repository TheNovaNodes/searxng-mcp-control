# AGENTS.md

Welcome, fellow agents! This repository is a part of the **TheNovaNodes Antigravity Agent Ecosystem**.

## Agent Guidelines

When working in this repository, please observe the following guidelines:

1. **High-Quality English**: Ensure all documentation, comments, and communications are in high-quality English.
2. **Repository Structure**: Maintain the standard repository structure, ensuring `README.md`, `AGENTS.md`, and `CONTRIBUTING.md` are present and up to date.
3. **Unit Testing**: All new features or bug fixes must include unit tests. Use `pytest` for testing, and ensure high test coverage (aim for >95%). Tests are located in the `tests/` directory.
4. **Ecosystem Alignment**: When making changes, keep in mind this tool's role in the Antigravity ecosystem, which is to provide reliable and robust MCP server endpoints for SearXNG management.
5. **Code Style**: We use standard Python formatting. Ensure clean, readable code with appropriate type hints and docstrings.

## Running Tests

To run the test suite:

```bash
python -m pytest tests/ --cov=searxng_mcp_control
```
