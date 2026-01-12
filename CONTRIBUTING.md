# Contributing to json2graph

Thank you for your interest in contributing to json2graph!

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/FalkorDB/json2graph.git
cd json2graph
```

2. Install dependencies:

Using uv (recommended):
```bash
uv pip install -e .
```

Or using pip:
```bash
pip install -e .
```

3. Run tests:
```bash
python -m unittest discover tests
```

## Running Tests

### All Tests
```bash
python -m unittest discover tests -v
```

### Specific Test File
```bash
python -m unittest tests.test_json_importer -v
```

### Single Test
```bash
python -m unittest tests.test_json_importer.TestJSONImporter.test_convert_simple_dict -v
```

## Code Style

- Follow PEP 8 style guide
- Use type hints for function parameters and returns
- Add docstrings for all public methods
- Keep line length under 100 characters

## Testing Guidelines

- Write tests for new features
- Ensure all tests pass before submitting PR
- Use mocks for database operations in unit tests
- Add integration tests for complex scenarios

## Security

- Always escape user input in Cypher queries
- Never use string interpolation for user data without escaping
- Test for SQL/Cypher injection vulnerabilities
- Report security issues privately to maintainers

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests to ensure they pass
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to your fork (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Pull Request Guidelines

- Provide a clear description of changes
- Reference any related issues
- Include tests for new functionality
- Update documentation as needed
- Ensure all tests pass

## Documentation

- Update README.md for user-facing changes
- Add docstrings for new methods/classes
- Update examples if API changes
- Keep IMPLEMENTATION.md in sync with architecture changes

## Reporting Issues

When reporting issues, please include:

- Python version
- FalkorDB version
- json2graph version
- Minimal reproduction example
- Expected vs actual behavior
- Error messages and stack traces

## Questions?

Feel free to open an issue for questions or discussions about:
- Feature requests
- API design
- Performance improvements
- Documentation clarifications

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
