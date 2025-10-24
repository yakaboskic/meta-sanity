# Meta-Sanity Testing & Type Handling

## Overview

This document describes the comprehensive test framework and improved type handling that has been added to meta-sanity.

## Key Improvements

### 1. Type Handling

**Problem**: YAML parses numbers, booleans, and null values as their native types, but the meta file format requires string output. Previously, you had to quote everything to ensure proper handling.

**Solution**: Added automatic type normalization:

```python
# Now you can write:
properties:
  count: 42           # Integer
  ratio: 3.14         # Float
  enabled: true       # Boolean
  placeholder: null   # Null value

# Instead of:
properties:
  count: "42"
  ratio: "3.14"
  enabled: "true"
  placeholder: "null"
```

**Type Conversion Rules**:
- Integers → strings (e.g., `42` → `"42"`)
- Floats → strings, with whole numbers simplified (e.g., `3.0` → `"3"`, `3.14` → `"3.14"`)
- Booleans → `"true"` or `"false"`
- None/null → `"null"`
- Strings → unchanged

### 2. Expression Evaluation

**Problem**: Template expressions like `${len(item)}` or `${int(item) * 2}` weren't being evaluated.

**Solution**: Enhanced template expression processor that supports:

```yaml
templates:
  samples:
    operation: for_each_item
    input: ['test', 'hello']
    pattern:
      name: "sample__${item}"
      properties:
        length: "${len(item)}"           # Evaluates to 4, 5
        upper: "${item.upper()}"          # Evaluates to TEST, HELLO
        doubled: "${int(item) * 2}"       # For numeric items
```

**Supported Functions** in expressions:
- `str`, `int`, `float` - Type conversions
- `len` - Length function
- `abs`, `round` - Math functions
- All string methods (`.upper()`, `.lower()`, etc.)

### 3. Comprehensive Error Messages

**Before**:
```
ValueError: Template error
```

**After**:
```
ValueError: Template 'my_samples' failed to process property 'count' for item 'sample_1':
Failed to evaluate expression '${int(item) * 2}' with item='sample_1': invalid literal for int()
```

Error messages now include:
- Template name
- Operation type
- Specific field that failed
- Item being processed
- Actual error with context

### 4. Input Validation

All template operations now validate:
- Required fields are present
- Field types are correct (list vs dict)
- Nested fields exist
- Numeric ranges are valid (for range operation)

Examples of validation errors:
```
Template 'test' with operation 'for_each_item' is missing required field 'input'
Template 'test' with operation 'for_each_item' field 'input' must be a list, got str
Template 'test' with operation 'for_each_class' is missing 'class_name' in 'input'
Template 'test' with operation 'range' has 'inc' value of 0, which would create an infinite loop
Template 'test' with operation 'range' has positive 'inc' but 'start' (10.0) > 'end' (1.0)
```

## Test Suite

### Running Tests

```bash
# Install test dependencies
uv pip install -e ".[dev]"

# Run all tests
pytest

# Run specific test file
pytest tests/test_type_handling.py

# Run with coverage
pytest --cov=meta_sanity --cov-report=html
```

### Test Organization

```
tests/
├── conftest.py                    # Fixtures and configuration
├── test_basic.py                  # Basic functionality and validation
├── test_type_handling.py          # Type conversion and normalization
├── test_template_operations.py   # All template operations
└── test_edge_cases.py             # Edge cases and complex scenarios
```

### Test Coverage

**70 tests** covering:

1. **Type Handling** (15 tests)
   - String, int, float, boolean, None normalization
   - Template expression substitution
   - Expression evaluation
   - Mixed type properties

2. **Template Operations** (20 tests)
   - `for_each_item`: basic, subsets, error cases
   - `for_each_class`: basic, filters, error cases
   - `iter.combination`: basic, error cases
   - `range`: ascending, descending, floats, error cases

3. **Edge Cases** (20 tests)
   - Key resolution and undefined keys
   - Multiple root classes
   - Empty inputs
   - Special characters
   - Chained templates
   - Complex scenarios

4. **Error Handling** (15 tests)
   - Missing required fields
   - Invalid field types
   - Unclosed expressions
   - Invalid operations
   - Invalid numeric values

## Examples

### Using Numeric Types

```yaml
classes:
  lab_project:
    class: project
    parent: null
    properties:
      budget: 1000000        # Number, no quotes needed
      success_rate: 0.95      # Float, no quotes needed
      active: true            # Boolean, no quotes needed
```

### Using Range with Expressions

```yaml
templates:
  numbered_samples:
    operation: range
    input:
      start: 1
      end: 10
      inc: 1
    pattern:
      name: "sample__${item}"
      properties:
        id: "${item}"                    # Simple substitution
        doubled: "${item * 2}"           # Expression
        formatted: "ID_${str(item).zfill(3)}"  # Complex expression
```

### Handling Mixed Input Types

```yaml
templates:
  samples:
    operation: for_each_item
    input: [1, 2.5, "text", true]  # Mixed types work!
    pattern:
      name: "sample__${item}"
      properties:
        value: "${item}"
        type: "${type(item).__name__}"
```

## Common Issues & Solutions

### Issue: Expressions Not Evaluated

**Problem**: `${len(item)}` appears literally in output

**Cause**: Expression doesn't contain the word 'item'

**Solution**: Ensure expressions reference `item`:
```yaml
# Wrong:
length: "${len('test')}"  # Doesn't reference item

# Right:
length: "${len(item)}"    # References item
```

### Issue: Type Mismatch Errors

**Problem**: `TypeError: unsupported operand type(s)`

**Cause**: Trying to use math operations on strings

**Solution**: Use explicit type conversion:
```yaml
# If item might be a string:
doubled: "${int(item) * 2}"  # Convert to int first
```

### Issue: Unclosed Expression

**Problem**: `ValueError: Unclosed ${} expression`

**Cause**: Missing closing brace

**Solution**: Check all `${...}` have matching braces:
```yaml
# Wrong:
name: "test_${item"

# Right:
name: "test_${item}"
```

## Best Practices

1. **Don't quote numbers unless you need them as strings**:
   ```yaml
   # Good
   count: 42

   # Only if you specifically need the string "42"
   id: "42"
   ```

2. **Use expressions for complex logic**:
   ```yaml
   # Instead of pre-processing data
   properties:
     padded_id: "${str(item).zfill(5)}"
     uppercase: "${item.upper()}"
   ```

3. **Test with edge cases**:
   - Empty lists
   - Single items
   - Special characters
   - Numbers vs strings

4. **Check error messages**:
   - They now tell you exactly what went wrong
   - Include the template name and item being processed
   - Show the exact expression that failed

## Future Enhancements

Potential additions:
- More built-in functions (e.g., `min`, `max`, `sum`)
- Custom validation rules per template
- Template inheritance/composition
- Conditional template execution
