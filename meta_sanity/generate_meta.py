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

# Main meta-generation function
def generate_meta(yaml_cfg):
    lines = [f"!config {yaml_cfg['config']}"]
    keys = yaml_cfg.get('keys', {})

    # Write keys
    for k, v in keys.items():
        lines.append(f"!key {k} {resolve_keys(v, keys)}")

    classes = yaml_cfg.get('classes', {})
    subset_map = {}

    all_classes = {}
    all_parents = defaultdict(set)
    all_instance_properties = defaultdict(lambda: {})
    class_last_line_idx = {}

    root_class_count = 0
    for cname, cdef in classes.items():
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
            resolved_pv = resolve_keys(pv, keys)
            lines.append(f"{cname} {pk} {resolved_pv}")
            all_instance_properties[cname][pk] = resolved_pv
        class_last_line_idx[cname] = len(lines)

    templates = yaml_cfg.get('templates', {})

    for tmpl_name, tmpl in templates.items():
        operation = tmpl['operation']

        def get_template_parent():
            pattern_parent = tmpl.get('pattern', {}).get('parent')
            top_parent = tmpl.get('parent')
            if pattern_parent and top_parent:
                raise ValueError(f"Template '{tmpl_name}' specifies both 'parent' and 'pattern.parent'; use only one.")
            return pattern_parent or top_parent

        if operation == 'for_each_item':
            parent = get_template_parent()
            if isinstance(parent, str):
                parent = [parent]
            for item in tmpl['input']:
                instance_name = tmpl['pattern']['name'].replace("${item}", item)
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
                for prop_key, prop_val in tmpl['pattern']['properties'].items():
                    resolved_val = resolve_keys(prop_val.replace("${item}", item), keys)
                    if is_duplicate:
                        if all_instance_properties[instance_name][prop_key] == resolved_val:
                            continue
                        else:
                            logger.warning(f"Duplicate instance name: '{instance_name}' with class '{tmpl['class']}', will attempt to add new property")
                            lines.insert(class_last_line_idx[instance_name], f"{instance_name} {prop_key} {prop_val}")
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
            prefix = tmpl.get('prefix', '')
            parent = get_template_parent()
            if isinstance(parent, str):
                parent = [parent]
            class_filter = tmpl['input']['class_name']
            subset_filter = tmpl['input'].get('if_subset', [])
            items = []
            for subset in subset_filter:
                items.extend(subset_map.get(subset, []))

            for item in items:
                instance_name = tmpl['pattern']['name'].replace("${prefix}", prefix).replace("${item}", item)
                lines.append(f"\n{instance_name} class {tmpl['class']}")
                all_classes[instance_name] = tmpl['class']
                if parent:
                    for p in parent:
                        lines.append(f"{instance_name} parent {p}")
                for prop_key, prop_val in tmpl['pattern']['properties'].items():
                    resolved_val = resolve_keys(prop_val.replace("${item}", item), keys)
                    lines.append(f"{instance_name} {prop_key} {resolved_val}")
                for subset in tmpl.get('subsets', []):
                    subset_map.setdefault(subset, []).append(instance_name)

        elif operation == 'iter.combination':
            input_sets = []
            names = []
            prefix = tmpl.get('prefix', '')
            for input_spec in tmpl['input']:
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
                    input_sets.append(items)
                elif 'values' in input_spec:
                    input_sets.append(input_spec['values'])
                else:
                    raise ValueError(f"Invalid input spec in 'iter.combination' for '{tmpl_name}'")
            parent = get_template_parent()
            for combination in itertools.product(*input_sets):
                item_dict = dict(zip(names, combination))
                instance_name = tmpl['pattern']['name'].replace("${prefix}", prefix)
                
                for k, v in item_dict.items():
                    instance_name = instance_name.replace(f"${{item:{k}}}", str(v))
                lines.append(f"\n{instance_name} class {tmpl['class']}")
                all_classes[instance_name] = tmpl['class']
                if not parent:
                    raise ValueError(f"Template '{tmpl_name}' requires a parent (either in pattern or at top level)")

                resolved_parent = parent
                if isinstance(resolved_parent, str):
                    resolved_parent = [resolved_parent]
                for p in resolved_parent:
                    for k, v in item_dict.items():
                        p = p.replace(f"${{item:{k}}}", str(v))
                    lines.append(f"{instance_name} parent {p}")

                for prop_key, prop_val in tmpl['pattern']['properties'].items():
                    val = prop_val
                    for k, v in item_dict.items():
                        val = val.replace(f"${{item:{k}}}", str(v))
                        # Find any other ${} references in the value and resolve them
                        val = resolve_keys(val, keys)
                    lines.append(f"{instance_name} {prop_key} {val}")
                for subset in tmpl.get('subsets', []):
                    subset_map.setdefault(subset, []).append(instance_name)

        else:
            raise ValueError(f"Unsupported operation '{operation}' in template '{tmpl_name}'")
    return "\n".join(lines)


# Argparse interface
def main():
    parser = argparse.ArgumentParser(description="Generate meta file from YAML config")
    parser.add_argument("-y", "--yaml", required=True, help="Path to input YAML config")
    parser.add_argument("-o", "--output", required=True, help="Path to output meta file")

    args = parser.parse_args()

    try:
        cfg = load_yaml(args.yaml)
        meta_content = generate_meta(cfg)
        with open(args.output, 'w') as f:
            f.write(meta_content)
        logger.info(f"Meta file '{args.output}' generated successfully.")
    except Exception as e:
        logger.error(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
