# Meta-Sanity Test Suite

This directory contains comprehensive tests for the meta-sanity package.

## Running Tests

### Install test dependencies

```bash
# Using pip
pip install -e ".[dev]"

# Using uv
uv pip install -e ".[dev]"
```

### Run all tests

```bash
pytest
```

### Run specific test files

```bash
pytest tests/test_type_handling.py
pytest tests/test_template_operations.py
pytest tests/test_edge_cases.py
pytest tests/test_basic.py
```

### Run with coverage

```bash
pytest --cov=meta_sanity --cov-report=html
```

## Test Organization

### `test_basic.py`
- Basic meta file generation
- Configuration validation
- Error message quality

### `test_type_handling.py`
- Type normalization (int, float, bool, str, None)
- Numeric values in templates
- Type conversions in properties
- Boolean and null handling

### `test_template_operations.py`
- `for_each_item` operation
- `for_each_class` operation
- `iter.combination` operation
- `range` operation
- Validation and error handling for each

### `test_edge_cases.py`
- Key resolution
- Multiple root classes
- Empty inputs
- Special characters
- Chained templates
- Complex scenarios
- ignore-class functionality

## What's Being Tested

### Type Handling
The tests ensure that YAML type handling works correctly:
- Numbers (int/float) can be used directly without quotes
- Booleans (`true`/`false`) work properly
- `null` values are handled
- Type conversions happen automatically
- Mixed types in properties work correctly

### Error Messages
All error messages should be:
- Descriptive (tell you what's wrong)
- Contextual (tell you where it happened)
- Actionable (tell you how to fix it)

### Template Operations
Each template operation is tested for:
- Basic functionality
- Edge cases (empty inputs, special chars, etc.)
- Required field validation
- Type validation
- Error handling

### Real-World Scenarios
Tests include complex scenarios that mimic real usage:
- Chained templates (output of one feeds into another)
- Combinations of all operations
- Large template hierarchies
