# Meta-Sanity Quick Reference

## Template Operations

### 1. for_each_item
Create instances from a list.

```yaml
templates:
  samples:
    operation: for_each_item
    input: [control, treatment1, treatment2]
    pattern:
      name: "sample__${item}"
      properties:
        type: "${item}"
        length: "${len(item)}"  # Can use expressions!
    parent: root_project
```

### 2. for_each_class
Create instances based on existing classes.

```yaml
templates:
  analyses:
    operation: for_each_class
    input:
      class_name: sample
      if_subset: [automated]  # Optional filter
    pattern:
      name: "analysis__${item}"
      properties:
        target: "${item}"
    parent: root_project
```

### 3. iter.combination
Create all combinations of multiple inputs.

```yaml
templates:
  experiments:
    operation: iter.combination
    input:
      # Three input types available:

      # 1. From existing classes
      - name: sample
        class_name: sample
        if_subset: [test]

      # 2. Fixed values
      - name: temp
        values: ["4c", "22c", "37c"]

      # 3. Range expansion (NEW!)
      - name: time
        operation: range
        start: 0
        end: 24
        inc: 6
    pattern:
      name: "exp__${item:sample}__${item:temp}__t${item:time}h"
      properties:
        sample_id: "${item:sample}"
        temperature: "${item:temp}"
        hours: "${item:time}"
    parent: root_project
```

### 4. range
Create numbered sequences.

```yaml
templates:
  numbered:
    operation: range
    input:
      start: 1
      end: 100
      inc: 1
    pattern:
      name: "item__${item}"
      properties:
        id: "${item}"
        padded: "${str(item).zfill(3)}"  # 001, 002, 003...
    parent: root_project
```

## Expression Capabilities

All patterns support Python expressions with `${...}`:

### Simple Substitution
```yaml
id: "${item}"                    # Direct substitution
```

### String Methods
```yaml
upper: "${item.upper()}"         # HELLO
lower: "${item.lower()}"         # hello
capitalized: "${item.title()}"   # Hello World
```

### String Operations
```yaml
length: "${len(item)}"           # 5
padded: "${str(item).zfill(5)}"  # 00042
sliced: "${item[:3]}"            # First 3 chars
```

### Math Operations (for numeric items)
```yaml
doubled: "${item * 2}"           # 84
incremented: "${item + 10}"      # 52
squared: "${item ** 2}"          # 1764
```

### Type Conversions
```yaml
as_string: "${str(item)}"        # "42"
as_int: "${int(item)}"           # 42
as_float: "${float(item)}"       # 42.0
```

### Combining Operations
```yaml
# Zero-pad and uppercase a number
formatted: "${str(item).zfill(3).upper()}"  # 042

# Calculate and format
percent: "${int(item * 100)}%"              # 75%
```

## Type Handling

Use native YAML types without quotes:

```yaml
properties:
  # Numbers
  count: 42                # Integer
  ratio: 3.14              # Float

  # Booleans
  enabled: true
  active: false

  # Null
  placeholder: null

  # Strings (when you need them)
  id: "sample_001"
  name: "My Sample"
```

## Common Patterns

### Sequential IDs with Padding
```yaml
numbered_items:
  operation: range
  input: {start: 1, end: 100, inc: 1}
  pattern:
    name: "item_${str(item).zfill(3)}"  # item_001, item_002, ...
    properties:
      numeric_id: "${item}"              # 1, 2, 3, ...
      string_id: "${str(item).zfill(3)}" # 001, 002, 003, ...
```

### Time Series
```yaml
timeseries:
  operation: iter.combination
  input:
    - name: sample
      class_name: sample
    - name: hour
      operation: range
      start: 0
      end: 48
      inc: 6
  pattern:
    name: "ts__${item:sample}__t${item:hour}h"
```

### Concentration Gradients
```yaml
concentrations:
  operation: range
  input:
    start: 0.1
    end: 1.0
    inc: 0.1
  pattern:
    name: "conc_${item}"  # conc_0.1, conc_0.2, ...
```

### Factorial Experiments
```yaml
factorial:
  operation: iter.combination
  input:
    - name: factor_a
      values: [low, medium, high]
    - name: factor_b
      values: [off, on]
    - name: replicate
      operation: range
      start: 1
      end: 3
      inc: 1
  # Creates 3×2×3 = 18 combinations
```

## Error Handling

All operations provide detailed error messages:

```yaml
# Missing field
✗ Template 'test' is missing required field 'input'

# Wrong type
✗ Template 'test' field 'input' must be a list, got str

# Invalid range
✗ Template 'test' has 'inc' value of 0, which would create an infinite loop

# Expression error
✗ Template 'test' failed to process property 'count' for item 'sample_1':
  Failed to evaluate expression '${int(item) * 2}' with item='sample_1'
```

## Testing

Run tests to verify everything works:

```bash
# All tests
pytest

# Specific test file
pytest tests/test_range_in_combination.py

# With coverage
pytest --cov=meta_sanity
```

## Tips

1. **Use expressions freely** - They're evaluated safely and efficiently
2. **Don't quote numbers** - Let YAML parse them naturally
3. **Check error messages** - They tell you exactly what's wrong
4. **Test incrementally** - Build complex templates step by step
5. **Use range in combinations** - Great for factorial designs and time series

## Common Issues

### Issue: Expression not evaluated
```yaml
# Wrong: Expression doesn't reference 'item'
length: "${len('test')}"

# Right: Must reference item variable
length: "${len(item)}"
```

### Issue: Type mismatch
```yaml
# If item might be a string, convert it first:
doubled: "${int(item) * 2}"  # Not just: ${item * 2}
```

### Issue: Range direction mismatch
```yaml
# Wrong: Positive inc with start > end
start: 10, end: 1, inc: 1

# Right: Use negative inc for descending
start: 10, end: 1, inc: -1
```

## More Help

- See `README.md` for full documentation
- See `TESTING.md` for type handling details
- See `examples/templating.meta.yaml` for working examples
- See `CHANGELOG.md` for recent updates
