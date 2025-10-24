# Changelog

## Recent Updates

### New Features

#### 1. Range Expansion in iter.combination ✨

You can now use `operation: range` within `iter.combination` input specs to dynamically generate numeric sequences that combine with other inputs.

**Example**:
```yaml
templates:
  time_series:
    class: experiment
    operation: iter.combination
    input:
      - name: sample
        values: ["A", "B"]
      - name: timepoint
        operation: range
        start: 0
        end: 24
        inc: 6
    pattern:
      name: "exp__${item:sample}__t${item:timepoint}h"
```

This creates: exp__A__t0h, exp__A__t6h, exp__A__t12h, exp__A__t18h, exp__A__t24h, exp__B__t0h, etc.

**Benefits**:
- No need to manually list long sequences
- Easy to adjust ranges (change start/end/inc without listing all values)
- Works with floats (e.g., concentration gradients: 0.1, 0.2, 0.3...)
- Combines seamlessly with class_name and values inputs

#### 2. Enhanced Expression Support 🚀

Templates now support powerful Python expressions in pattern properties:

**String Operations**:
```yaml
properties:
  uppercase: "${item.upper()}"              # TEST
  lowercase: "${item.lower()}"              # test
  length: "${len(item)}"                    # 4
  padded: "${str(item).zfill(5)}"          # 00042
```

**Math Operations** (for numeric items):
```yaml
properties:
  doubled: "${item * 2}"
  incremented: "${item + 10}"
  calculated: "${int(item) ** 2}"
```

**Type Conversions**:
```yaml
properties:
  as_string: "${str(item)}"
  as_int: "${int(item)}"
  as_float: "${float(item)}"
```

**Supported functions**: `str`, `int`, `float`, `len`, `abs`, `round`, plus all string methods

#### 3. Native YAML Type Support 🎯

No more quoting numbers! YAML types are automatically normalized:

**Before**:
```yaml
properties:
  count: "42"
  ratio: "3.14"
  enabled: "true"
```

**After**:
```yaml
properties:
  count: 42           # Integer - no quotes!
  ratio: 3.14         # Float
  enabled: true       # Boolean
  placeholder: null   # Null
```

**Type Conversion Rules**:
- Integers → strings (42 → "42")
- Floats → strings, simplified when whole (3.0 → "3", 3.14 → "3.14")
- Booleans → "true" or "false"
- null → "null"

#### 4. Comprehensive Error Messages 📋

Errors now include full context:

**Before**:
```
ValueError: Template error
```

**After**:
```
ValueError: Template 'my_samples' failed to process property 'count' for item 'sample_1':
Failed to evaluate expression '${int(item) * 2}' with item='sample_1':
invalid literal for int() with base 10: 'sample_1'
```

Error messages include:
- Template name
- Operation type
- Which field failed
- Item being processed
- Actual error with context

### Validation Improvements

All template operations now validate:
- Required fields are present
- Field types are correct (list vs dict)
- Nested fields exist
- Numeric ranges are valid
- Expressions are well-formed

**Examples**:
```
Template 'test' with operation 'range' has 'inc' value of 0, which would create an infinite loop
Template 'test' with operation 'for_each_item' field 'input' must be a list, got str
Template 'test' with operation 'iter.combination' has input spec 'time' with operation 'range' missing 'start' field
```

### Test Suite 🧪

**79 comprehensive tests** covering:
- All template operations
- Type handling edge cases
- Range expansion in combinations
- Expression evaluation
- Complex real-world scenarios
- Error conditions

Run tests with: `pytest`

### Documentation

Updated documentation:
- **README.md**: Complete guide with all new features
- **TESTING.md**: Testing guide and type handling reference
- **tests/README.md**: Test suite overview
- **examples/templating.meta.yaml**: Working examples of all features

## Migration Guide

### Using Numeric Types

**Old way** (still works):
```yaml
properties:
  count: "42"
```

**New way** (recommended):
```yaml
properties:
  count: 42
```

### Using Expressions

**Old way** (limited):
```yaml
properties:
  name: "${item}"
```

**New way** (powerful):
```yaml
properties:
  name: "${item}"
  name_upper: "${item.upper()}"
  name_length: "${len(item)}"
  padded_id: "${str(item).zfill(5)}"
```

### Using Range in Combinations

**Old way** (manual list):
```yaml
- name: replicate
  values: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
```

**New way** (dynamic):
```yaml
- name: replicate
  operation: range
  start: 1
  end: 10
  inc: 1
```

## Breaking Changes

None! All changes are backwards compatible. Existing configurations will continue to work.

## Performance

- Expression evaluation is fast and safe (restricted eval context)
- Range expansion happens at template processing time
- No impact on existing functionality

## Future Enhancements

Potential additions:
- More built-in functions (min, max, sum)
- Custom validation rules
- Template inheritance
- Conditional template execution
