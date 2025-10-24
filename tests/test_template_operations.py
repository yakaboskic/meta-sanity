"""
Tests for template operations (for_each_item, for_each_class, iter.combination, range).
"""
import pytest
from meta_sanity.generate_meta import generate_meta


class TestForEachItem:
    """Test for_each_item template operation."""

    def test_basic_for_each_item(self, basic_config):
        """Basic for_each_item should create instances for each item."""
        config = basic_config.copy()
        config['templates'] = {
            'samples': {
                'class': 'sample',
                'operation': 'for_each_item',
                'input': ['control', 'treatment1', 'treatment2'],
                'pattern': {
                    'name': 'sample__${item}',
                    'properties': {
                        'type': '${item}',
                    }
                },
                'parent': 'root_project'
            }
        }

        result = generate_meta(config)
        assert 'sample__control class sample' in result
        assert 'sample__treatment1 class sample' in result
        assert 'sample__treatment2 class sample' in result
        assert 'sample__control type control' in result

    def test_for_each_item_with_subsets(self, basic_config):
        """for_each_item with subsets should tag instances."""
        config = basic_config.copy()
        config['templates'] = {
            'samples': {
                'class': 'sample',
                'operation': 'for_each_item',
                'input': ['a', 'b'],
                'pattern': {
                    'name': 'sample__${item}',
                },
                'parent': 'root_project',
                'subsets': ['automated', 'high_priority']
            }
        }

        result = generate_meta(config)
        assert 'sample__a class sample' in result
        assert 'sample__b class sample' in result

    def test_for_each_item_missing_input(self, basic_config):
        """Missing input field should raise helpful error."""
        config = basic_config.copy()
        config['templates'] = {
            'samples': {
                'class': 'sample',
                'operation': 'for_each_item',
                # Missing 'input'
                'pattern': {
                    'name': 'sample__${item}',
                },
                'parent': 'root_project'
            }
        }

        with pytest.raises(ValueError, match="missing required field 'input'"):
            generate_meta(config)

    def test_for_each_item_missing_pattern(self, basic_config):
        """Missing pattern field should raise helpful error."""
        config = basic_config.copy()
        config['templates'] = {
            'samples': {
                'class': 'sample',
                'operation': 'for_each_item',
                'input': ['a', 'b'],
                # Missing 'pattern'
                'parent': 'root_project'
            }
        }

        with pytest.raises(ValueError, match="missing required field 'pattern'"):
            generate_meta(config)

    def test_for_each_item_missing_name_in_pattern(self, basic_config):
        """Missing name in pattern should raise helpful error."""
        config = basic_config.copy()
        config['templates'] = {
            'samples': {
                'class': 'sample',
                'operation': 'for_each_item',
                'input': ['a', 'b'],
                'pattern': {
                    # Missing 'name'
                    'properties': {}
                },
                'parent': 'root_project'
            }
        }

        with pytest.raises(ValueError, match="missing 'name' in 'pattern'"):
            generate_meta(config)

    def test_for_each_item_input_not_list(self, basic_config):
        """Input that's not a list should raise helpful error."""
        config = basic_config.copy()
        config['templates'] = {
            'samples': {
                'class': 'sample',
                'operation': 'for_each_item',
                'input': 'not_a_list',  # Wrong type
                'pattern': {
                    'name': 'sample__${item}',
                },
                'parent': 'root_project'
            }
        }

        with pytest.raises(ValueError, match="must be a list"):
            generate_meta(config)


class TestForEachClass:
    """Test for_each_class template operation."""

    def test_basic_for_each_class(self, basic_config):
        """for_each_class should create instances based on existing classes."""
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
                'subsets': ['automated']
            },
            'analyses': {
                'class': 'analysis',
                'operation': 'for_each_class',
                'input': {
                    'class_name': 'sample',
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
        assert 'analysis__sample__s1 class analysis' in result
        assert 'analysis__sample__s2 class analysis' in result
        assert 'analysis__sample__s1 target sample__s1' in result

    def test_for_each_class_with_subset_filter(self, basic_config):
        """for_each_class with subset filter should only process matching classes."""
        config = basic_config.copy()
        config['templates'] = {
            'samples': {
                'class': 'sample',
                'operation': 'for_each_item',
                'input': ['s1', 's2', 's3'],
                'pattern': {
                    'name': 'sample__${item}',
                },
                'parent': 'root_project',
                'subsets': ['automated']
            },
            'analyses': {
                'class': 'analysis',
                'operation': 'for_each_class',
                'input': {
                    'class_name': 'sample',
                    'if_subset': ['automated']
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
        assert 'analysis__sample__s1 class analysis' in result
        assert 'analysis__sample__s2 class analysis' in result

    def test_for_each_class_missing_class_name(self, basic_config):
        """Missing class_name in input should raise error."""
        config = basic_config.copy()
        config['templates'] = {
            'analyses': {
                'class': 'analysis',
                'operation': 'for_each_class',
                'input': {
                    # Missing 'class_name'
                },
                'pattern': {
                    'name': 'analysis__${item}',
                    'properties': {}
                },
                'parent': 'root_project'
            }
        }

        with pytest.raises(ValueError, match="missing 'class_name' in 'input'"):
            generate_meta(config)

    def test_for_each_class_no_matching_classes(self, basic_config):
        """for_each_class with no matching classes should warn."""
        config = basic_config.copy()
        config['templates'] = {
            'analyses': {
                'class': 'analysis',
                'operation': 'for_each_class',
                'input': {
                    'class_name': 'nonexistent',
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

        # Should generate without error but with warning
        result = generate_meta(config)
        assert 'analysis' not in result or result.count('class analysis') == 0


class TestIterCombination:
    """Test iter.combination template operation."""

    def test_basic_iter_combination(self, basic_config):
        """iter.combination should create all combinations."""
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
                'subsets': ['test']
            },
            'experiments': {
                'class': 'experiment',
                'operation': 'iter.combination',
                'input': [
                    {
                        'name': 'sample',
                        'class_name': 'sample',
                        'if_subset': ['test']
                    },
                    {
                        'name': 'temp',
                        'values': ['4c', '22c']
                    }
                ],
                'pattern': {
                    'name': 'exp__${item:sample}__${item:temp}',
                    'properties': {
                        'sample_id': '${item:sample}',
                        'temperature': '${item:temp}',
                    }
                },
                'parent': 'root_project'
            }
        }

        result = generate_meta(config)
        assert 'exp__sample__s1__4c class experiment' in result
        assert 'exp__sample__s1__22c class experiment' in result
        assert 'exp__sample__s2__4c class experiment' in result
        assert 'exp__sample__s2__22c class experiment' in result

    def test_iter_combination_missing_name_in_input(self, basic_config):
        """iter.combination input spec without 'name' should raise error."""
        config = basic_config.copy()
        config['templates'] = {
            'experiments': {
                'class': 'experiment',
                'operation': 'iter.combination',
                'input': [
                    {
                        # Missing 'name'
                        'values': ['a', 'b']
                    }
                ],
                'pattern': {
                    'name': 'exp__${item}',
                },
                'parent': 'root_project'
            }
        }

        with pytest.raises(ValueError, match="missing 'name' field"):
            generate_meta(config)

    def test_iter_combination_empty_input(self, basic_config):
        """iter.combination with empty input list should raise error."""
        config = basic_config.copy()
        config['templates'] = {
            'experiments': {
                'class': 'experiment',
                'operation': 'iter.combination',
                'input': [],  # Empty
                'pattern': {
                    'name': 'exp__${item}',
                },
                'parent': 'root_project'
            }
        }

        with pytest.raises(ValueError, match="empty 'input' list"):
            generate_meta(config)


class TestRange:
    """Test range template operation."""

    def test_basic_range(self, basic_config):
        """Basic range operation."""
        config = basic_config.copy()
        config['templates'] = {
            'samples': {
                'class': 'sample',
                'operation': 'range',
                'input': {
                    'start': 1,
                    'end': 5,
                    'inc': 1,
                },
                'pattern': {
                    'name': 'sample__${item}',
                    'properties': {
                        'id': '${item}',
                    }
                },
                'parent': 'root_project'
            }
        }

        result = generate_meta(config)
        assert 'sample__1 class sample' in result
        assert 'sample__2 class sample' in result
        assert 'sample__3 class sample' in result
        assert 'sample__4 class sample' in result
        assert 'sample__5 class sample' in result

    def test_range_descending(self, basic_config):
        """Range with negative increment."""
        config = basic_config.copy()
        config['templates'] = {
            'samples': {
                'class': 'sample',
                'operation': 'range',
                'input': {
                    'start': 5,
                    'end': 1,
                    'inc': -1,
                },
                'pattern': {
                    'name': 'sample__${item}',
                },
                'parent': 'root_project'
            }
        }

        result = generate_meta(config)
        assert 'sample__5 class sample' in result
        assert 'sample__4 class sample' in result
        assert 'sample__1 class sample' in result

    def test_range_missing_start(self, basic_config):
        """Range missing 'start' should raise error."""
        config = basic_config.copy()
        config['templates'] = {
            'samples': {
                'class': 'sample',
                'operation': 'range',
                'input': {
                    # Missing 'start'
                    'end': 5,
                    'inc': 1,
                },
                'pattern': {
                    'name': 'sample__${item}',
                },
                'parent': 'root_project'
            }
        }

        with pytest.raises(ValueError, match="missing 'start' in 'input'"):
            generate_meta(config)

    def test_range_zero_increment(self, basic_config):
        """Range with zero increment should raise error."""
        config = basic_config.copy()
        config['templates'] = {
            'samples': {
                'class': 'sample',
                'operation': 'range',
                'input': {
                    'start': 1,
                    'end': 5,
                    'inc': 0,  # Invalid
                },
                'pattern': {
                    'name': 'sample__${item}',
                },
                'parent': 'root_project'
            }
        }

        with pytest.raises(ValueError, match="inc.*0.*infinite loop"):
            generate_meta(config)

    def test_range_invalid_direction(self, basic_config):
        """Range with positive inc but start > end should raise error."""
        config = basic_config.copy()
        config['templates'] = {
            'samples': {
                'class': 'sample',
                'operation': 'range',
                'input': {
                    'start': 10,
                    'end': 1,
                    'inc': 1,  # Should be negative
                },
                'pattern': {
                    'name': 'sample__${item}',
                },
                'parent': 'root_project'
            }
        }

        with pytest.raises(ValueError, match="positive 'inc' but 'start'.*> 'end'"):
            generate_meta(config)

    def test_range_invalid_numeric_value(self, basic_config):
        """Range with non-numeric value should raise error."""
        config = basic_config.copy()
        config['templates'] = {
            'samples': {
                'class': 'sample',
                'operation': 'range',
                'input': {
                    'start': 'not_a_number',
                    'end': 5,
                    'inc': 1,
                },
                'pattern': {
                    'name': 'sample__${item}',
                },
                'parent': 'root_project'
            }
        }

        with pytest.raises(ValueError, match="invalid numeric values"):
            generate_meta(config)
