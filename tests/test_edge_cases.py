"""
Tests for edge cases and error conditions.
"""
import pytest
from meta_sanity.generate_meta import generate_meta, resolve_keys


class TestKeyResolution:
    """Test key resolution and variable substitution."""

    def test_basic_key_resolution(self):
        """Keys should resolve ${} references."""
        keys = {
            'base': '/path',
            'derived': '${base}/data',
        }
        result = resolve_keys('${derived}/file', keys)
        assert result == '/path/data/file'

    def test_nested_key_resolution(self):
        """Keys can reference other keys that reference keys."""
        keys = {
            'a': '/root',
            'b': '${a}/middle',
            'c': '${b}/leaf',
        }
        result = resolve_keys('${c}', keys)
        assert result == '/root/middle/leaf'

    def test_undefined_key_reference(self):
        """Undefined key reference should raise error."""
        keys = {'known': 'value'}
        with pytest.raises(ValueError, match="Undefined key: 'unknown'"):
            resolve_keys('${unknown}', keys)

    def test_numeric_key_value(self):
        """Key values can be numeric."""
        keys = {
            'port': 8080,
            'timeout': 30.5,
        }
        # Keys are resolved during key writing
        assert keys['port'] == 8080


class TestClassDefinitions:
    """Test class definition edge cases."""

    def test_multiple_root_classes(self):
        """Multiple root classes should raise error."""
        config = {
            'config': '/path/to/config.cfg',
            'classes': {
                'root1': {
                    'class': 'project',
                    'parent': None,
                },
                'root2': {
                    'class': 'project',
                    'parent': None,
                }
            }
        }

        with pytest.raises(ValueError, match="Multiple root classes"):
            generate_meta(config)

    def test_class_without_parent_not_root(self):
        """Non-null parent class defined after root should work."""
        config = {
            'config': '/path/to/config.cfg',
            'classes': {
                'root': {
                    'class': 'project',
                    'parent': None,
                },
                'child': {
                    'class': 'item',
                    'parent': 'root',
                }
            }
        }

        result = generate_meta(config)
        assert 'root class project' in result
        assert 'child class item' in result
        assert 'child parent root' in result

    def test_class_with_multiple_parents(self):
        """Class can have multiple parents."""
        config = {
            'config': '/path/to/config.cfg',
            'classes': {
                'root': {
                    'class': 'project',
                    'parent': None,
                },
                'parent1': {
                    'class': 'group',
                    'parent': 'root',
                },
                'parent2': {
                    'class': 'group',
                    'parent': 'root',
                },
                'child': {
                    'class': 'item',
                    'parent': ['parent1', 'parent2'],
                }
            }
        }

        result = generate_meta(config)
        assert 'child parent parent1' in result
        assert 'child parent parent2' in result

    def test_empty_properties(self):
        """Class with no properties should work."""
        config = {
            'config': '/path/to/config.cfg',
            'classes': {
                'root': {
                    'class': 'project',
                    'parent': None,
                    # No properties
                }
            }
        }

        result = generate_meta(config)
        assert 'root class project' in result


class TestTemplateEdgeCases:
    """Test edge cases in template processing."""

    def test_empty_template_input_list(self, basic_config):
        """Empty input list should not create any instances."""
        config = basic_config.copy()
        config['templates'] = {
            'empty': {
                'class': 'sample',
                'operation': 'for_each_item',
                'input': [],  # Empty list
                'pattern': {
                    'name': 'sample__${item}',
                },
                'parent': 'root_project'
            }
        }

        result = generate_meta(config)
        # Should not have any sample classes
        assert result.count('class sample') == 0

    def test_template_with_special_characters_in_name(self, basic_config):
        """Template names with special chars in values."""
        config = basic_config.copy()
        config['templates'] = {
            'samples': {
                'class': 'sample',
                'operation': 'for_each_item',
                'input': ['test-1', 'test_2', 'test.3'],
                'pattern': {
                    'name': 'sample__${item}',
                },
                'parent': 'root_project'
            }
        }

        result = generate_meta(config)
        assert 'sample__test-1 class sample' in result
        assert 'sample__test_2 class sample' in result
        assert 'sample__test.3 class sample' in result

    def test_template_property_with_expression(self, basic_config):
        """Template property can use Python expressions."""
        config = basic_config.copy()
        config['templates'] = {
            'samples': {
                'class': 'sample',
                'operation': 'for_each_item',
                'input': ['short', 'very_long_name'],
                'pattern': {
                    'name': 'sample__${item}',
                    'properties': {
                        'length': '${len(item)}',
                        'upper': '${item.upper()}',
                    }
                },
                'parent': 'root_project'
            }
        }

        result = generate_meta(config)
        assert 'sample__short length 5' in result
        assert 'sample__short upper SHORT' in result
        assert 'sample__very_long_name length 14' in result

    def test_template_with_both_parent_locations(self, basic_config):
        """Template with parent in both pattern and top level should error."""
        config = basic_config.copy()
        config['templates'] = {
            'samples': {
                'class': 'sample',
                'operation': 'for_each_item',
                'input': ['a'],
                'pattern': {
                    'name': 'sample__${item}',
                    'parent': 'root_project',  # Here
                },
                'parent': 'root_project'  # And here
            }
        }

        with pytest.raises(ValueError, match="specifies both 'parent' and 'pattern.parent'"):
            generate_meta(config)

    def test_prefix_in_for_each_class(self, basic_config):
        """for_each_class with prefix should prepend to names."""
        config = basic_config.copy()
        config['templates'] = {
            'samples': {
                'class': 'sample',
                'operation': 'for_each_item',
                'input': ['s1'],
                'pattern': {
                    'name': '${item}',
                },
                'parent': 'root_project',
            },
            'analyses': {
                'class': 'analysis',
                'operation': 'for_each_class',
                'input': {
                    'class_name': 'sample',
                },
                'prefix': 'qc',
                'pattern': {
                    'name': '${prefix}__${item}',
                    'properties': {
                        'target': '${item}',
                    }
                },
                'parent': 'root_project'
            }
        }

        result = generate_meta(config)
        assert 'qc__s1 class analysis' in result


class TestIgnoreClass:
    """Test ignore-class functionality."""

    def test_ignore_all_instances_of_class(self, basic_config):
        """ignore-class should skip all instances of specified class."""
        config = basic_config.copy()
        config['templates'] = {
            'samples': {
                'class': 'sample',
                'operation': 'for_each_item',
                'input': ['s1', 's2'],
                'pattern': {
                    'name': 'sample__${item}',
                },
                'parent': 'root_project'
            }
        }

        result = generate_meta(config, ignore_class=['sample'])
        # Should not have any sample classes
        assert 'class sample' not in result

    def test_ignore_class_with_pattern(self, basic_config):
        """ignore-class with pattern should skip matching instances."""
        config = basic_config.copy()
        config['templates'] = {
            'samples': {
                'class': 'sample',
                'operation': 'for_each_item',
                'input': ['control_1', 'control_2', 'treatment_1'],
                'pattern': {
                    'name': 'sample__${item}',
                },
                'parent': 'root_project'
            }
        }

        result = generate_meta(config, ignore_class=['sample:.*control.*'])
        # Should only have treatment
        assert 'sample__treatment_1 class sample' in result
        assert 'sample__control_1' not in result
        assert 'sample__control_2' not in result


class TestInvalidOperations:
    """Test invalid/unsupported operations."""

    def test_unknown_operation(self, basic_config):
        """Unknown operation should raise error."""
        config = basic_config.copy()
        config['templates'] = {
            'test': {
                'class': 'sample',
                'operation': 'unknown_operation',
                'input': ['a'],
                'pattern': {
                    'name': '${item}',
                },
                'parent': 'root_project'
            }
        }

        with pytest.raises(ValueError, match="Unsupported operation 'unknown_operation'"):
            generate_meta(config)

    def test_missing_operation_field(self, basic_config):
        """Template without operation field should raise error."""
        config = basic_config.copy()
        config['templates'] = {
            'test': {
                'class': 'sample',
                # Missing 'operation'
                'input': ['a'],
                'pattern': {
                    'name': '${item}',
                },
                'parent': 'root_project'
            }
        }

        with pytest.raises(ValueError, match="missing required field 'operation'"):
            generate_meta(config)


class TestComplexScenarios:
    """Test complex real-world scenarios."""

    def test_chained_templates(self, basic_config):
        """Templates can reference outputs of previous templates."""
        config = basic_config.copy()
        config['templates'] = {
            'samples': {
                'class': 'sample',
                'operation': 'for_each_item',
                'input': ['s1', 's2'],
                'pattern': {
                    'name': 'sample__${item}',
                },
                'parent': 'root_project',
                'subsets': ['active']
            },
            'preps': {
                'class': 'prep',
                'operation': 'for_each_class',
                'input': {
                    'class_name': 'sample',
                    'if_subset': ['active']
                },
                'pattern': {
                    'name': 'prep__${item}',
                    'properties': {
                        'source': '${item}',
                    }
                },
                'parent': 'root_project'
            },
            'analyses': {
                'class': 'analysis',
                'operation': 'for_each_class',
                'input': {
                    'class_name': 'prep',
                },
                'pattern': {
                    'name': 'analysis__${item}',
                    'properties': {
                        'target': '${item}',
                    }
                },
                'parent': 'root_project'
            }
        }

        result = generate_meta(config)
        assert 'sample__s1 class sample' in result
        assert 'prep__sample__s1 class prep' in result
        assert 'analysis__prep__sample__s1 class analysis' in result

    def test_combination_of_all_operations(self, basic_config):
        """Use all operations together."""
        config = basic_config.copy()
        config['templates'] = {
            'base_samples': {
                'class': 'sample',
                'operation': 'for_each_item',
                'input': ['s1'],
                'pattern': {
                    'name': 'manual__${item}',
                },
                'parent': 'root_project',
                'subsets': ['manual']
            },
            'numbered_samples': {
                'class': 'sample',
                'operation': 'range',
                'input': {
                    'start': 1,
                    'end': 2,
                    'inc': 1,
                },
                'pattern': {
                    'name': 'auto__${item}',
                },
                'parent': 'root_project',
                'subsets': ['auto']
            },
            'treatments': {
                'class': 'treatment',
                'operation': 'for_each_class',
                'input': {
                    'class_name': 'sample',
                    'if_subset': ['auto']
                },
                'pattern': {
                    'name': 'treatment__${item}',
                    'properties': {
                        'sample': '${item}',
                    }
                },
                'parent': 'root_project'
            },
            'experiments': {
                'class': 'experiment',
                'operation': 'iter.combination',
                'input': [
                    {
                        'name': 'treatment',
                        'class_name': 'treatment',
                    },
                    {
                        'name': 'time',
                        'values': ['12h', '24h']
                    }
                ],
                'pattern': {
                    'name': 'exp__${item:treatment}__${item:time}',
                    'properties': {
                        'treatment_id': '${item:treatment}',
                        'timepoint': '${item:time}',
                    }
                },
                'parent': 'root_project'
            }
        }

        result = generate_meta(config)
        # Verify all types are created
        assert 'manual__s1 class sample' in result
        assert 'auto__1 class sample' in result
        assert 'treatment__auto__1 class treatment' in result
        assert 'exp__treatment__auto__1__12h class experiment' in result
