# Meta Sanity

A tool for generating structured meta files with support for templating and inheritance patterns. This tool helps reduce repetition and enforce consistency in meta file generation.

> ⚠️ **Warning**  
> This tool requires Python 3.8 or higher.

## Installation

There are two ways to install meta-sanity:

### 1. Using pip (recommended) with development mode (in case you want to make changes)

```bash
pip install -e .
```

> 💡 **Tip**  
> Using `-e` flag installs the package in "editable" mode, which means you can modify the source code and see changes immediately without reinstalling.

### 2. Using requirements.txt

```bash
pip install -r requirements.txt
python -m meta_sanity.generate_meta -y your_config.yaml -o output.meta
```

## Usage

Once installed, you can use the tool in two ways:

1. Using the command-line tool:
```bash
generate-meta your_config.yaml output.meta
```

2. Using the Python module:
```python
from meta_sanity.generate_meta import generate_meta
import yaml

with open('your_config.yaml', 'r') as f:
    config = yaml.safe_load(f)
    
meta_content = generate_meta(config)
with open('output.meta', 'w') as f:
    f.write(meta_content)
```

> 🔍 **Note**  
> Check the `examples/` directory for complete working examples of configuration files.

## Basic Structure

A meta-sanity configuration consists of three main sections:
- `keys`: Global variables and paths
- `subsets`: Tags for filtering and grouping
- `classes`: Basic class definitions and templates
- `templates`: Expandable templates that can be used to programatically generate meta configuration blocks.

### Keys

Define global variables and paths that can be referenced throughout your configuration:

```yaml
keys:
  base_dir: "/path/to/project"
  data_dir: "${base_dir}/data"  # Reference other keys using ${key_name}
  results_dir: "${base_dir}/results"
```

### Basic Class Syntax

For classes that don't fit a template pattern (like root classes or unique instances), use the basic class syntax:

```yaml
classes:
  root_project:
    class: project      # The class type
    parent: null        # null for root classes
    properties:         # Class-specific properties
      project_lead: "smith_jane"
      start_date: "20240101"

  unique_equipment:
    class: equipment
    parent: root_project    # Reference parent class
    properties:
      location: "room_101"
      maintenance_schedule: "weekly"
```

Best Practices for Basic Classes:
- Use snake_case for all identifiers
- Avoid spaces and special characters in values
- Use `null` explicitly for root classes
- Keep properties consistent across similar classes

## Generation Order

> 🔄 **Critical Understanding**  
> Meta file generation happens **sequentially** in a specific order. Understanding this order is crucial for proper template configuration.

The generation sequence is as follows:

1. **Keys** (`keys` section)
   - Global variables and paths are processed first
   - All key references must be defined before they are used

2. **Classes** (`classes` section)
   - Basic class definitions are processed next
   - All classes in this section are generated before any templates

3. **Templates** (`templates` section)
   - Templates are processed one at a time, in the order they appear
   - Each template must only reference objects that already exist from:
     - Previously defined classes
     - Objects generated by earlier templates

> ⚠️ **Common Pitfall**  
> A template cannot reference objects that will be generated by a subsequent template. For example:
> ```yaml
> templates:
>   analysis_tasks:     # This template runs first
>     operation: for_each_class
>     class_name: sample    # ❌ Error: 'sample' classes don't exist yet
>     ...
>   
>   standard_samples:   # This template runs second
>     operation: for_each_item
>     class: sample
>     ...
> ```
> To fix this, reorder the templates so `standard_samples` comes before `analysis_tasks`.

## Ignoring Classes for Faster Development

> 🚀 **Performance Tip**  
> When working with large meta files, the web UI can become slow to refresh. The `ignore-class` feature lets you generate smaller, focused meta files for development while maintaining the ability to generate the complete meta file when needed.

The `ignore-class` feature supports two syntax patterns:

1. **Simple Class Ignore**: Ignore all instances of a specific class
   ```bash
   generate-meta config.yaml output.meta --ignore-class analysis
   ```

2. **Pattern-Based Ignore**: Ignore specific instances using regex patterns
   ```bash
   # Ignore analysis classes that contain 'qc' in their name
   generate-meta -y config.yaml -o output.meta --ignore-class "analysis:.*qc.*"
   
   # Ignore sample classes starting with 'control'
   generate-meta -y config.yaml -o output.meta --ignore-class "sample:^control.*"
   ```

You can combine multiple ignore patterns:
```bash
# Ignore all QC analyses and control samples
generate-meta config.yaml output.meta \
  --ignore-class "analysis:.*qc.*" \
  --ignore-class "sample:^control.*"
```

In Python:
```python
# Simple class ignore
meta_content = generate_meta(config, ignore_classes=['analysis'])

# Pattern-based ignore
meta_content = generate_meta(config, ignore_classes=[
    'analysis:.*qc.*',
    'sample:^control.*'
])
```

> 💡 **Development Workflow**  
> 1. During development, generate a smaller meta file by ignoring specific patterns:
>    ```bash
>    # Quick refresh for UI testing - ignore heavy analysis tasks
>    generate-meta config.yaml my.meta --ignore-class "analysis:(?!quick).*"
>    ```
>    This example keeps only analyses with "quick" in their name.
> 
> 2. When ready for production, generate the complete meta file:
>    ```bash
>    # Full generation for actual runs
>    generate-meta config.yaml my.meta
>    ```
>
> 
> The generation remains **deterministic**, meaning file structures and relationships stay consistent between partial and complete generations.

### Example Use Case

```yaml
classes:
  experiment:
    class: project
    parent: null
    properties:
      name: "large_scale_analysis"

templates:
  # These templates generate thousands of analysis tasks
  qc_analysis:
    class: analysis  # Can ignore with "analysis:.*qc.*"
    operation: for_each_class
    input:
      class_name: sample
    pattern:
      name: "qc_${item}"
    ...

  heavy_analysis:
    class: analysis  # Can ignore with "analysis:^heavy.*"
    operation: for_each_class
    input:
      class_name: sample
    pattern:
      name: "heavy_${item}"
    ...

  # This template generates core sample definitions
  core_samples:
    class: sample   # Keep this for basic testing
    operation: for_each_item
    input: ...
```

> ⚡ **Important**  
> When using `ignore-class`:
> - Templates generating ignored classes are skipped entirely
> - Pattern matching uses standard regex syntax
> - Multiple patterns for the same class are combined with OR logic
> - References to ignored classes in parent fields are treated as null
> - The meta file structure remains valid, just with fewer entries

## Templating Features

Currently, this generation script has three core operations that can be used fairly generally and described below. 

### 1. for_each_item Operation

Use when you need to create multiple instances of a class with different values from a list:

```yaml
templates:
  standard_samples:
    class: sample
    operation: for_each_item
    input:
      - control_a
      - control_b
      - treatment_1
    pattern:
      name: "sample__${item}"    # Creates: sample__control_a, sample__control_b, etc.
      properties:
        sample_type: "${item}"
    parent: root_project         # All instances inherit from this parent
    subsets:                     # Optional tags for filtering
      - automated
```

### 2. for_each_class Operation

Use when you need to create instances based on existing class instances:

```yaml
templates:
  analysis_tasks:
    class: analysis
    operation: for_each_class
    input:
      class_name: sample           # Reference existing class
      if_subset: [automated]       # Filter by subset/tag
    prefix: analysis
    pattern:
      name: "${prefix}__${item}"   # Creates: analysis__sample_1, etc.
      properties:
        target: "${item}"
    parent: 
      - equipment_type             # Can specify single or multiple parents
```

> ⚡ **Important**  
> The class instances you are referencing in `class_name` must exist already in the meta context before using this operation. Further, the generation happens **sequentially**, meaning if you define some classes in a `for_each_item` template, after your `for_each_class` template that references those classes, then you'll get an error. 

### 3. iter.combination Operation

Use when you need to create instances from combinations of multiple inputs:

```yaml
templates:
  experiment_matrix:
    class: experiment
    operation: iter.combination
    input:
      - name: sample               # From existing class
        class_name: sample
        if_subset: [automated]
      - name: temperature          # Fixed values
        values:
          - "4c"
          - "22c"
      - name: duration
        values:
          - "12h"
          - "24h"
    prefix: exp
    pattern:
      name: "${prefix}__${item:sample}__temp_${item:temperature}__dur_${item:duration}"
      properties:
        sample_id: "${item:sample}"
        temp: "${item:temperature}"
    parent: "analysis__${item:sample}"   # Dynamic parent based on input
```

## Best Practices

1. **Naming Conventions**:
   - Use snake_case for all identifiers
   - Use double underscores (`__`) to separate pattern components
   - Avoid spaces and special characters

2. **Pattern Structure**:
   - Keep patterns consistent within similar templates
   - Use descriptive prefixes
   - Include relevant identifiers in names

3. **Properties**:
   - Keep property names consistent across similar classes
   - Use full words rather than abbreviations
   - Document any special property requirements

4. **Parent Relationships**:
   - Explicitly specify `null` for root classes
   - Use lists for multiple parents
   - Consider dependency order

5. **Subsets/Tags**:
   - Use meaningful subset names
   - Document subset purposes
   - Consider subset relationships

> ⚡ **Important**  
> Always use `null` explicitly for root classes and ensure only one root class exists in your configuration.

## Examples
You can view complete examples in the `examples/` folder. 

> 🔍 **Note:** 
> I have not developed a accompaning config file tho, so it is just generating the meta alone, without ensuring that it is consistent with a config. May add this feature soon.