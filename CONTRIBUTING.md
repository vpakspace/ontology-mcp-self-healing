# Contributing to Self-Healing Ontology MCP Agent System

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/ontology-mcp-self-healing.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Test your changes: `pytest tests/ -v`
6. Submit a pull request

## Development Setup

Follow the setup instructions in [SETUP_GUIDE.md](SETUP_GUIDE.md).

## Code Style

- Use Python 3.10+ features
- Follow PEP 8 style guide
- Use type hints throughout
- Add docstrings (Google style) for all functions and classes
- Format code with Black: `black src/ tests/`
- Lint with Ruff: `ruff check src/ tests/`

## Testing

- Write tests for all new features
- Ensure all tests pass: `pytest tests/ -v`
- Maintain or improve test coverage
- Add integration tests for new features

## Commit Messages

Use clear, descriptive commit messages:
- `feat: add new feature`
- `fix: fix bug`
- `docs: update documentation`
- `test: add tests`
- `refactor: refactor code`

## Pull Request Process

1. Update README.md if needed
2. Add tests for new features
3. Ensure all tests pass
4. Update documentation
5. Submit PR with clear description

## Questions?

Open an issue for questions or discussions.
