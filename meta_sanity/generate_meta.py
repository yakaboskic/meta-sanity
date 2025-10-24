import yaml
import re
import argparse
import sys
import itertools
import logging
from collections import defaultdict

# Configure logging to output to console with timestamp
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Load YAML
def load_yaml(yaml_path):
    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)

# Resolve ${} references in strings
def resolve_keys(val, keys):
    if not isinstance(val, str):
        return val
    pattern = re.compile(r'\$\{(\w+)\}')
    while True:
        match = pattern.search(val)
        if not match:
            break
        key = match.group(1)
        if key not in keys:
            raise ValueError(f"Undefined key: '{key}' referenced in '{val}'")
        val = val.replace(f"${{{key}}}", keys[key])
    return val

def process_ignore_class(ignore_class):
    if not ignore_class:
        return {}
    ignore_class_dict = {}
    for ignore_class_item in ignore_class:
        if ":" not in ignore_class_item:
            logger.warning(f"Will ignore all instances of class '{ignore_class_item}'")
            ignore_class_dict[ignore_class_item] = ".*"
        else:
            class_name, regex_pattern = ignore_class_item.split(':', 1)
            if class_name in ignore_class_dict:
                raise ValueError(f"Duplicate ignore class: '{class_name}'")
            ignore_class_dict[class_name] = regex_pattern
    return ignore_class_dict

def should_ignore_class(class_name, instance_name, ignore_class_dict):
    if class_name in ignore_class_dict:
        return re.match(ignore_class_dict[class_name], instance_name)
    return False

def normalize_value(value):
    """
    Normalize values to strings for meta file output.
    Handles numbers, booleans, None, and strings consistently.

    Args:
        value: Any value type (str, int, float, bool, None)

    Returns:
        str: Normalized string representation
    """
    if value is None:
        return "null"
    elif isinstance(value, bool):
        # YAML treats 'true'/'false' as booleans, so we preserve that
        return "true" if value else "false"
    elif isinstance(value, (int, float)):
        # Convert numbers to strings, preserving int format when possible
        if isinstance(value, float) and value == int(value):
            return str(int(value))
        return str(value)
    elif isinstance(value, str):
        return value
    else:
        # For any other type, convert to string
        logger.warning(f"Unexpected value type {type(value).__name__}: {value}, converting to string")
        return str(value)

def validate_template_input(template_name, template_def, required_fields):
    """
    Validate that a template has all required fields.

    Args:
        template_name: Name of the template being validated
        template_def: Template definition dictionary
        required_fields: List of required field names

    Raises:
        ValueError: If any required field is missing
    """
    for field in required_fields:
        if field not in template_def:
            raise ValueError(f"Template '{template_name}' is missing required field '{field}'")

def validate_nested_field(template_name, template_def, parent_field, nested_field):
    """
    Validate that a nested field exists within a parent field.

    Args:
        template_name: Name of the template being validated
        template_def: Template definition dictionary
        parent_field: Name of parent field (e.g., 'pattern')
        nested_field: Name of nested field (e.g., 'name')

    Raises:
        ValueError: If the nested field is missing
    """
    if parent_field not in template_def:
        raise ValueError(f"Template '{template_name}' is missing required field '{parent_field}'")
    if not isinstance(template_def[parent_field], dict):
        raise ValueError(f"Template '{template_name}' field '{parent_field}' must be a dictionary, got {type(template_def[parent_field]).__name__}")
    if nested_field not in template_def[parent_field]:
        raise ValueError(f"Template '{template_name}' is missing '{nested_field}' in '{parent_field}'")

def process_template_expr(template: str, item) -> str:
    """Process template expressions containing 'item' variable.

    Supports both simple substitution (${item}) and expressions (${len(item)}, ${item.upper()}, etc.)

    Args:
        template: String containing ${...} expressions that reference 'item'
        item: The item value to substitute (can be any type)
    Returns:
        Processed string with all expressions evaluated
    Raises:
        ValueError: If expression is invalid or evaluation fails
    """
    if not isinstance(template, str):
        raise ValueError(f"Template must be a string, got {type(template).__name__}: {template}")

    result = template
    # Process all ${...} expressions that contain 'item'
    pos = 0
    while True:
        start = result.find('${', pos)
        if start == -1:
            break
        end = result.find('}', start)
        if end == -1:
            raise ValueError(f"Unclosed ${{}} expression in template: {template}")
        expr = result[start+2:end]

        # Only process if expression contains 'item' variable
        if 'item' not in expr:
            # Skip this expression, it doesn't reference item
            # Move past it and continue
            pos = end + 1
            continue

        if expr == 'item':
            # Simple replacement - normalize the value to string
            value = normalize_value(item)
        else:
            # Evaluate Python expression
            # For safety, provide limited context with safe built-ins
            try:
                safe_namespace = {
                    '__builtins__': {
                        'str': str,
                        'int': int,
                        'float': float,
                        'abs': abs,
                        'round': round,
                        'len': len,
                    },
                    'item': item,
                }
                value = eval(expr, safe_namespace)
                value = normalize_value(value)
            except Exception as e:
                raise ValueError(f"Failed to evaluate expression '${{'{expr}'}}' with item={repr(item)}: {e}")
        result = result[:start] + value + result[end+1:]
        # Continue searching from where we just inserted the value
        pos = start + len(value)

    return result

# Main meta-generation function
def generate_meta(yaml_cfg, ignore_class=None):
    lines = [f"!config {yaml_cfg['config']}"]
    keys = yaml_cfg.get('keys', {})
    ignore_class_dict = process_ignore_class(ignore_class)

    # Write keys
    for k, v in keys.items():
        resolved_v = resolve_keys(v, keys)
        lines.append(f"!key {k} {normalize_value(resolved_v)}")

    classes = yaml_cfg.get('classes', {})
    subset_map = {}

    all_classes = {}
    all_parents = defaultdict(set)
    all_instance_properties = defaultdict(lambda: {})
    class_last_line_idx = {}

    root_class_count = 0
    for cname, cdef in classes.items():
        if should_ignore_class(cdef['class'], cname, ignore_class_dict):
            continue
        parent = cdef.get('parent')
        if parent in [None, 'null']:
            root_class_count += 1
            if root_class_count > 1:
                raise ValueError(f"Multiple root classes found: '{cname}' is an additional root class")

        lines.append(f"\n{cname} class {cdef['class']}")
        all_classes[cname] = cdef['class']
        if parent not in [None, 'null']:
            if isinstance(parent, str):
                parent = [parent]
            for p in parent:
                lines.append(f"{cname} parent {p}")
                all_parents[cname].add(p)
        elif root_class_count == 0:
            raise ValueError(f"Class '{cname}' must specify a parent unless it's explicitly the single root class")
        for pk, pv in cdef.get('properties', {}).items():
            resolved_pv = resolve_keys(normalize_value(pv), keys)
            lines.append(f"{cname} {pk} {resolved_pv}")
            all_instance_properties[cname][pk] = resolved_pv
        class_last_line_idx[cname] = len(lines)

    templates = yaml_cfg.get('templates', {})

    for tmpl_name, tmpl in templates.items():
        try:
            operation = tmpl.get('operation')
            if not operation:
                raise ValueError(f"Template '{tmpl_name}' is missing required field 'operation'")

            def get_template_parent():
                pattern_parent = tmpl.get('pattern', {}).get('parent')
                top_parent = tmpl.get('parent')
                if pattern_parent and top_parent:
                    raise ValueError(f"Template '{tmpl_name}' specifies both 'parent' and 'pattern.parent'; use only one.")
                return pattern_parent or top_parent

            if operation == 'for_each_item':
                validate_template_input(tmpl_name, tmpl, ['input', 'pattern', 'class'])
                validate_nested_field(tmpl_name, tmpl, 'pattern', 'name')

                if not isinstance(tmpl['input'], list):
                    raise ValueError(f"Template '{tmpl_name}' field 'input' must be a list, got {type(tmpl['input']).__name__}")

                parent = get_template_parent()
                if isinstance(parent, str):
                    parent = [parent]
                for idx, item in enumerate(tmpl['input']):
                    try:
                        instance_name = process_template_expr(tmpl['pattern']['name'], item)
                    except Exception as e:
                        raise ValueError(f"Template '{tmpl_name}' failed to process item at index {idx} (value={repr(item)}): {e}")
                    if should_ignore_class(tmpl['class'], instance_name, ignore_class_dict):
                        continue
                    # Check if the instance name already exists and is the same class (if so, it'll just try to add new parents)
                    is_duplicate = False
                    if instance_name in all_classes and all_classes[instance_name] == tmpl['class']:
                        is_duplicate = True
                        logger.warning(f"Duplicate instance name: '{instance_name}' with class '{tmpl['class']}', will attempt to add new parents")
                    else:
                        lines.append(f"\n{instance_name} class {tmpl['class']}")
                    if parent:
                        for p in parent:
                            if is_duplicate:
                                lines.insert(class_last_line_idx[instance_name], f"{instance_name} parent {p}")
                                # Update the class last line index
                                class_last_line_idx[instance_name] += 1
                            else:
                                lines.append(f"{instance_name} parent {p}")
                            all_parents[instance_name].add(p)
                    if 'properties' in tmpl['pattern']:
                        for prop_key, prop_val in tmpl['pattern']['properties'].items():
                            try:
                                prop_val_str = normalize_value(prop_val) if not isinstance(prop_val, str) else prop_val
                                resolved_val = resolve_keys(process_template_expr(prop_val_str, item), keys)
                            except Exception as e:
                                raise ValueError(f"Template '{tmpl_name}' failed to process property '{prop_key}' for item {repr(item)}: {e}")
                            if is_duplicate:
                                if prop_key in all_instance_properties[instance_name] and all_instance_properties[instance_name][prop_key] == resolved_val:
                                    continue
                                else:
                                    logger.warning(f"Duplicate instance name: '{instance_name}' with class '{tmpl['class']}', will attempt to add new property")
                                    lines.insert(class_last_line_idx[instance_name], f"{instance_name} {prop_key} {resolved_val}")
                                    # Update the class last line index
                                    class_last_line_idx[instance_name] += 1
                                    continue
                            lines.append(f"{instance_name} {prop_key} {resolved_val}")
                            all_instance_properties[instance_name][prop_key] = resolved_val
                    if not is_duplicate:
                        class_last_line_idx[instance_name] = len(lines)
                    for subset in tmpl.get('subsets', []):
                        subset_map.setdefault(subset, []).append(instance_name)
                    all_classes[instance_name] = tmpl['class']

            elif operation == 'for_each_class':
                validate_template_input(tmpl_name, tmpl, ['input', 'pattern', 'class'])
                validate_nested_field(tmpl_name, tmpl, 'pattern', 'name')
                validate_nested_field(tmpl_name, tmpl, 'pattern', 'properties')

                if not isinstance(tmpl['input'], dict):
                    raise ValueError(f"Template '{tmpl_name}' with operation 'for_each_class' requires 'input' to be a dictionary, got {type(tmpl['input']).__name__}")
                if 'class_name' not in tmpl['input']:
                    raise ValueError(f"Template '{tmpl_name}' with operation 'for_each_class' is missing 'class_name' in 'input'")

                prefix = tmpl.get('prefix', '')
                parent = get_template_parent()
                if isinstance(parent, str):
                    parent = [parent]
                subset_filter = tmpl['input'].get('if_subset', None)
                items = []
                if subset_filter:
                    for subset in subset_filter:
                        items.extend(subset_map.get(subset, []))
                else:
                    items = [item for item in all_classes.keys() if all_classes[item] == tmpl['input']['class_name']]

                if not items:
                    logger.warning(f"Template '{tmpl_name}' with operation 'for_each_class' found no instances of class '{tmpl['input']['class_name']}'{' with subset filter ' + str(subset_filter) if subset_filter else ''}")

                for item in items:
                    try:
                        instance_name = process_template_expr(tmpl['pattern']['name'].replace("${prefix}", prefix), item)
                    except Exception as e:
                        raise ValueError(f"Template '{tmpl_name}' failed to process class instance '{item}': {e}")

                    if should_ignore_class(tmpl['class'], instance_name, ignore_class_dict):
                        continue
                    lines.append(f"\n{instance_name} class {tmpl['class']}")
                    all_classes[instance_name] = tmpl['class']
                    if parent:
                        for p in parent:
                            lines.append(f"{instance_name} parent {p}")
                    for prop_key, prop_val in tmpl['pattern']['properties'].items():
                        try:
                            prop_val_str = normalize_value(prop_val) if not isinstance(prop_val, str) else prop_val
                            resolved_val = resolve_keys(process_template_expr(prop_val_str, item), keys)
                        except Exception as e:
                            raise ValueError(f"Template '{tmpl_name}' failed to process property '{prop_key}' for item '{item}': {e}")
                        lines.append(f"{instance_name} {prop_key} {resolved_val}")
                    for subset in tmpl.get('subsets', []):
                        subset_map.setdefault(subset, []).append(instance_name)

            elif operation == 'iter.combination':
                validate_template_input(tmpl_name, tmpl, ['input', 'pattern', 'class'])
                validate_nested_field(tmpl_name, tmpl, 'pattern', 'name')

                if not isinstance(tmpl['input'], list):
                    raise ValueError(f"Template '{tmpl_name}' with operation 'iter.combination' requires 'input' to be a list, got {type(tmpl['input']).__name__}")
                if len(tmpl['input']) == 0:
                    raise ValueError(f"Template '{tmpl_name}' with operation 'iter.combination' has empty 'input' list")

                input_sets = []
                names = []
                prefix = tmpl.get('prefix', '')
                for input_spec in tmpl['input']:
                    if 'name' not in input_spec:
                        raise ValueError(f"Template '{tmpl_name}' with operation 'iter.combination' has input spec missing 'name' field")
                    name = input_spec['name']
                    names.append(name)
                    if 'class_name' in input_spec:
                        subset_filter = input_spec.get('if_subset', None)
                        items = []
                        if subset_filter:
                            for subset in subset_filter:
                                items.extend(subset_map.get(subset, []))
                        else:
                            # If no subset filter, get all items that match the class name
                            items = [item for item in all_classes.keys() if all_classes[item] == input_spec['class_name']]
                        if not items:
                            logger.warning(f"Template '{tmpl_name}' with operation 'iter.combination' found no instances of class '{input_spec['class_name']}' for input '{name}'{' with subset filter ' + str(subset_filter) if subset_filter else ''}")
                        input_sets.append(items)
                    elif 'values' in input_spec:
                        input_sets.append(input_spec['values'])
                    else:
                        raise ValueError(f"Template '{tmpl_name}' with operation 'iter.combination' has input spec '{name}' missing both 'class_name' and 'values' fields")
                parent = get_template_parent()
                for combination in itertools.product(*input_sets):
                    item_dict = dict(zip(names, combination))
                    instance_name = tmpl['pattern']['name'].replace("${prefix}", prefix)

                    for k, v in item_dict.items():
                        instance_name = instance_name.replace(f"${{item:{k}}}", str(v))
                    if should_ignore_class(tmpl['class'], instance_name, ignore_class_dict):
                        continue
                    lines.append(f"\n{instance_name} class {tmpl['class']}")
                    all_classes[instance_name] = tmpl['class']
                    if not parent:
                        raise ValueError(f"Template '{tmpl_name}' with operation 'iter.combination' requires a parent (either in pattern or at top level)")

                    resolved_parent = parent
                    if isinstance(resolved_parent, str):
                        resolved_parent = [resolved_parent]
                    for p in resolved_parent:
                        for k, v in item_dict.items():
                            p = p.replace(f"${{item:{k}}}", str(v))
                        lines.append(f"{instance_name} parent {p}")

                    if 'properties' in tmpl['pattern']:
                        for prop_key, prop_val in tmpl['pattern']['properties'].items():
                            val = prop_val
                            for k, v in item_dict.items():
                                val = val.replace(f"${{item:{k}}}", str(v))
                                # Find any other ${} references in the value and resolve them
                                val = resolve_keys(val, keys)
                            lines.append(f"{instance_name} {prop_key} {val}")
                    for subset in tmpl.get('subsets', []):
                        subset_map.setdefault(subset, []).append(instance_name)

            elif operation == 'range':
                validate_template_input(tmpl_name, tmpl, ['input', 'pattern', 'class'])
                validate_nested_field(tmpl_name, tmpl, 'pattern', 'name')

                if not isinstance(tmpl['input'], dict):
                    raise ValueError(f"Template '{tmpl_name}' with operation 'range' requires 'input' to be a dictionary, got {type(tmpl['input']).__name__}")

                # Validate required input fields
                required_input_fields = ['start', 'end', 'inc']
                for field in required_input_fields:
                    if field not in tmpl['input']:
                        raise ValueError(f"Template '{tmpl_name}' with operation 'range' is missing '{field}' in 'input'")

                # Get range parameters
                try:
                    start = float(tmpl['input']['start'])
                    end = float(tmpl['input']['end'])
                    inc = float(tmpl['input']['inc'])
                except (ValueError, TypeError) as e:
                    raise ValueError(f"Template '{tmpl_name}' with operation 'range' has invalid numeric values in 'input': {e}")

                if inc == 0:
                    raise ValueError(f"Template '{tmpl_name}' with operation 'range' has 'inc' value of 0, which would create an infinite loop")
                if inc > 0 and start > end:
                    raise ValueError(f"Template '{tmpl_name}' with operation 'range' has positive 'inc' but 'start' ({start}) > 'end' ({end})")
                if inc < 0 and start < end:
                    raise ValueError(f"Template '{tmpl_name}' with operation 'range' has negative 'inc' but 'start' ({start}) < 'end' ({end})")

                parent = get_template_parent()
                if isinstance(parent, str):
                    parent = [parent]

                # Generate range values
                values = []
                current = start
                if inc > 0:
                    while current <= end:
                        values.append(current)
                        current += inc
                else:
                    while current >= end:
                        values.append(current)
                        current += inc

                if not values:
                    logger.warning(f"Template '{tmpl_name}' with operation 'range' generated no values with start={start}, end={end}, inc={inc}")

                # Process each value in the range
                for value in values:
                    # Convert to int if it's a whole number, otherwise keep as float
                    item = int(value) if value == int(value) else value
                    try:
                        instance_name = process_template_expr(tmpl['pattern']['name'], item)
                    except Exception as e:
                        raise ValueError(f"Template '{tmpl_name}' failed to process range value {item}: {e}")
                    if should_ignore_class(tmpl['class'], instance_name, ignore_class_dict):
                        continue
                    # Check if the instance name already exists and is the same class
                    is_duplicate = False
                    if instance_name in all_classes and all_classes[instance_name] == tmpl['class']:
                        is_duplicate = True
                        logger.warning(f"Duplicate instance name: '{instance_name}' with class '{tmpl['class']}', will attempt to add new parents")
                    else:
                        lines.append(f"\n{instance_name} class {tmpl['class']}")
                    if parent:
                        for p in parent:
                            if is_duplicate:
                                lines.insert(class_last_line_idx[instance_name], f"{instance_name} parent {p}")
                                class_last_line_idx[instance_name] += 1
                            else:
                                lines.append(f"{instance_name} parent {p}")
                            all_parents[instance_name].add(p)
                    if 'properties' in tmpl['pattern']:
                        for prop_key, prop_val in tmpl['pattern']['properties'].items():
                            try:
                                prop_val_str = normalize_value(prop_val) if not isinstance(prop_val, str) else prop_val
                                resolved_val = resolve_keys(process_template_expr(prop_val_str, item), keys)
                            except Exception as e:
                                raise ValueError(f"Template '{tmpl_name}' failed to process property '{prop_key}' for range value {item}: {e}")
                            if is_duplicate:
                                if prop_key in all_instance_properties[instance_name] and all_instance_properties[instance_name][prop_key] == resolved_val:
                                    continue
                                else:
                                    logger.warning(f"Duplicate instance name: '{instance_name}' with class '{tmpl['class']}', will attempt to add new property")
                                    lines.insert(class_last_line_idx[instance_name], f"{instance_name} {prop_key} {resolved_val}")
                                    class_last_line_idx[instance_name] += 1
                                    continue
                            lines.append(f"{instance_name} {prop_key} {resolved_val}")
                            all_instance_properties[instance_name][prop_key] = resolved_val
                    if not is_duplicate:
                        class_last_line_idx[instance_name] = len(lines)
                    for subset in tmpl.get('subsets', []):
                        subset_map.setdefault(subset, []).append(instance_name)
                    all_classes[instance_name] = tmpl['class']

            else:
                raise ValueError(f"Unsupported operation '{operation}' in template '{tmpl_name}'")
        except Exception as e:
            logger.error(f"Error processing template '{tmpl_name}': {e}")
            raise
    return "\n".join(lines)


# Argparse interface
def main():
    parser = argparse.ArgumentParser(description="Generate meta file from YAML config")
    parser.add_argument("yaml", help="Path to input YAML config")
    parser.add_argument("output", help="Path to output meta file")
    parser.add_argument("-y", "--yaml", dest="yaml", help=argparse.SUPPRESS)  # Hidden alias
    parser.add_argument("-o", "--output", dest="output", help=argparse.SUPPRESS)  # Hidden alias
    parser.add_argument("--ignore-class", action="append", default=None, help="Ignore a class based on a regex pattern match on the class name in the format {class_name}:{regex_pattern}")
    args = parser.parse_args()

    try:
        cfg = load_yaml(args.yaml)
        meta_content = generate_meta(cfg, args.ignore_class)
        with open(args.output, 'w') as f:
            f.write(meta_content)
        logger.info(f"Meta file '{args.output}' generated successfully.")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
