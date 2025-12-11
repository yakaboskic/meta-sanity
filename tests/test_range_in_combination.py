"""
Tests for range expansion in iter.combination operation.
"""
import pytest
from meta_sanity.generate_meta import generate_meta


class TestRangeInCombination:
    """Test range expansion within iter.combination."""

    def test_basic_range_in_combination(self, basic_config):
        """Range expansion in combination should work."""
        config = basic_config.copy()
        config['templates'] = {
            'experiments': {
                'class': 'experiment',
                'operation': 'iter.combination',
                'input': [
                    {
                        'name': 'temp',
                        'values': ['4c', '22c']
                    },
                    {
                        'name': 'time',
                        'operation': 'range',
                        'start': 1,
                        'end': 3,
                        'inc': 1,
                    }
                ],
                'pattern': {
                    'name': 'exp__${item:temp}__t${item:time}',
                    'properties': {
                        'temperature': '${item:temp}',
                        'timepoint': '${item:time}',
                    }
                },
                'parent': 'root_project'
            }
        }

        result = generate_meta(config)
        # Should have 2 temps × 3 times = 6 combinations
        assert 'exp__4c__t1 class experiment' in result
        assert 'exp__4c__t2 class experiment' in result
        assert 'exp__4c__t3 class experiment' in result
        assert 'exp__22c__t1 class experiment' in result
        assert 'exp__22c__t2 class experiment' in result
        assert 'exp__22c__t3 class experiment' in result

        # Check properties
        assert 'exp__4c__t1 temperature 4c' in result
        assert 'exp__4c__t1 timepoint 1' in result

    def test_float_range_in_combination(self, basic_config):
        """Float range in combination should work."""
        config = basic_config.copy()
        config['templates'] = {
            'experiments': {
                'class': 'experiment',
                'operation': 'iter.combination',
                'input': [
                    {
                        'name': 'concentration',
                        'operation': 'range',
                        'start': 0.5,
                        'end': 1.5,
                        'inc': 0.5,
                    },
                    {
                        'name': 'replicate',
                        'values': ['A', 'B']
                    }
                ],
                'pattern': {
                    'name': 'exp__c${item:concentration}__${item:replicate}',
                    'properties': {
                        'conc': '${item:concentration}',
                        'rep': '${item:replicate}',
                    }
                },
                'parent': 'root_project'
            }
        }

        result = generate_meta(config)
        # Should have 3 concentrations × 2 replicates = 6 combinations
        assert 'exp__c0.5__A class experiment' in result
        assert 'exp__c1__A class experiment' in result  # 1.0 becomes 1
        assert 'exp__c1.5__A class experiment' in result
        assert 'exp__c0.5__B class experiment' in result

    def test_multiple_ranges_in_combination(self, basic_config):
        """Multiple range expansions in combination."""
        config = basic_config.copy()
        config['templates'] = {
            'experiments': {
                'class': 'experiment',
                'operation': 'iter.combination',
                'input': [
                    {
                        'name': 'x',
                        'operation': 'range',
                        'start': 1,
                        'end': 2,
                        'inc': 1,
                    },
                    {
                        'name': 'y',
                        'operation': 'range',
                        'start': 10,
                        'end': 20,
                        'inc': 10,
                    }
                ],
                'pattern': {
                    'name': 'exp__x${item:x}_y${item:y}',
                },
                'parent': 'root_project'
            }
        }

        result = generate_meta(config)
        # Should have 2 × 2 = 4 combinations
        assert 'exp__x1_y10 class experiment' in result
        assert 'exp__x1_y20 class experiment' in result
        assert 'exp__x2_y10 class experiment' in result
        assert 'exp__x2_y20 class experiment' in result

    def test_range_with_class_and_values(self, basic_config):
        """Mix range with class_name and values."""
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
                        'values': ['4c', '37c']
                    },
                    {
                        'name': 'time',
                        'operation': 'range',
                        'start': 1,
                        'end': 2,
                        'inc': 1,
                    }
                ],
                'pattern': {
                    'name': 'exp__${item:sample}__${item:temp}__t${item:time}',
                    'properties': {
                        'sample_id': '${item:sample}',
                        'temperature': '${item:temp}',
                        'timepoint': '${item:time}',
                    }
                },
                'parent': 'root_project'
            }
        }

        result = generate_meta(config)
        # Should have 2 samples × 2 temps × 2 times = 8 combinations
        assert 'exp__sample__s1__4c__t1 class experiment' in result
        assert 'exp__sample__s1__4c__t2 class experiment' in result
        assert 'exp__sample__s1__37c__t1 class experiment' in result
        assert 'exp__sample__s1__37c__t2 class experiment' in result
        assert 'exp__sample__s2__4c__t1 class experiment' in result
        assert 'exp__sample__s2__4c__t2 class experiment' in result
        assert 'exp__sample__s2__37c__t1 class experiment' in result
        assert 'exp__sample__s2__37c__t2 class experiment' in result

    def test_range_missing_start(self, basic_config):
        """Range in combination missing start should raise error."""
        config = basic_config.copy()
        config['templates'] = {
            'experiments': {
                'class': 'experiment',
                'operation': 'iter.combination',
                'input': [
                    {
                        'name': 'time',
                        'operation': 'range',
                        # Missing 'start'
                        'end': 3,
                        'inc': 1,
                    }
                ],
                'pattern': {
                    'name': 'exp__t${item:time}',
                },
                'parent': 'root_project'
            }
        }

        with pytest.raises(ValueError, match="missing 'start' field"):
            generate_meta(config)

    def test_range_zero_increment(self, basic_config):
        """Range in combination with zero increment should raise error."""
        config = basic_config.copy()
        config['templates'] = {
            'experiments': {
                'class': 'experiment',
                'operation': 'iter.combination',
                'input': [
                    {
                        'name': 'time',
                        'operation': 'range',
                        'start': 1,
                        'end': 3,
                        'inc': 0,  # Invalid
                    }
                ],
                'pattern': {
                    'name': 'exp__t${item:time}',
                },
                'parent': 'root_project'
            }
        }

        with pytest.raises(ValueError, match="inc.*0.*infinite loop"):
            generate_meta(config)

    def test_range_invalid_direction(self, basic_config):
        """Range in combination with invalid direction should raise error."""
        config = basic_config.copy()
        config['templates'] = {
            'experiments': {
                'class': 'experiment',
                'operation': 'iter.combination',
                'input': [
                    {
                        'name': 'time',
                        'operation': 'range',
                        'start': 10,
                        'end': 1,
                        'inc': 1,  # Should be negative
                    }
                ],
                'pattern': {
                    'name': 'exp__t${item:time}',
                },
                'parent': 'root_project'
            }
        }

        with pytest.raises(ValueError, match="positive 'inc' but 'start'.*> 'end'"):
            generate_meta(config)

    def test_range_invalid_numeric_value(self, basic_config):
        """Range in combination with non-numeric value should raise error."""
        config = basic_config.copy()
        config['templates'] = {
            'experiments': {
                'class': 'experiment',
                'operation': 'iter.combination',
                'input': [
                    {
                        'name': 'time',
                        'operation': 'range',
                        'start': 'not_a_number',
                        'end': 3,
                        'inc': 1,
                    }
                ],
                'pattern': {
                    'name': 'exp__t${item:time}',
                },
                'parent': 'root_project'
            }
        }

        with pytest.raises(ValueError, match="invalid numeric values"):
            generate_meta(config)

    def test_descending_range_in_combination(self, basic_config):
        """Descending range in combination should work."""
        config = basic_config.copy()
        config['templates'] = {
            'experiments': {
                'class': 'experiment',
                'operation': 'iter.combination',
                'input': [
                    {
                        'name': 'temp',
                        'values': ['hot']
                    },
                    {
                        'name': 'time',
                        'operation': 'range',
                        'start': 5,
                        'end': 1,
                        'inc': -2,
                    }
                ],
                'pattern': {
                    'name': 'exp__${item:temp}__t${item:time}',
                },
                'parent': 'root_project'
            }
        }

        result = generate_meta(config)
        assert 'exp__hot__t5 class experiment' in result
        assert 'exp__hot__t3 class experiment' in result
        assert 'exp__hot__t1 class experiment' in result


class TestCombinationExpressions:
    """Test expression evaluation in iter.combination patterns."""

    def test_round_expression_in_name(self, basic_config):
        """round() expression with named item should work in pattern name."""
        config = basic_config.copy()
        config['templates'] = {
            'experiments': {
                'class': 'experiment',
                'operation': 'iter.combination',
                'input': [
                    {
                        'name': 'fraction',
                        'values': [0.123, 0.456, 0.789]
                    }
                ],
                'pattern': {
                    'name': 'exp__${round(item:fraction, 2)}',
                    'properties': {
                        'fraction': '${item:fraction}',
                    }
                },
                'parent': 'root_project'
            }
        }

        result = generate_meta(config)
        assert 'exp__0.12 class experiment' in result
        assert 'exp__0.46 class experiment' in result
        assert 'exp__0.79 class experiment' in result

    def test_math_expression_in_properties(self, basic_config):
        """Math expressions with named items should work in properties."""
        config = basic_config.copy()
        config['templates'] = {
            'experiments': {
                'class': 'experiment',
                'operation': 'iter.combination',
                'input': [
                    {
                        'name': 'percentage',
                        'values': [10, 50, 100]
                    }
                ],
                'pattern': {
                    'name': 'exp__${item:percentage}pct',
                    'properties': {
                        'fraction': '${item:percentage / 100}',
                        'doubled': '${item:percentage * 2}',
                    }
                },
                'parent': 'root_project'
            }
        }

        result = generate_meta(config)
        assert 'exp__10pct fraction 0.1' in result
        assert 'exp__50pct fraction 0.5' in result
        assert 'exp__100pct fraction 1' in result
        assert 'exp__10pct doubled 20' in result
        assert 'exp__50pct doubled 100' in result

    def test_multiple_named_items_in_expression(self, basic_config):
        """Multiple named items in a single expression should work."""
        config = basic_config.copy()
        config['templates'] = {
            'experiments': {
                'class': 'experiment',
                'operation': 'iter.combination',
                'input': [
                    {
                        'name': 'x',
                        'values': [10, 20]
                    },
                    {
                        'name': 'y',
                        'values': [2, 5]
                    }
                ],
                'pattern': {
                    'name': 'exp__x${item:x}_y${item:y}',
                    'properties': {
                        'sum': '${item:x + item:y}',
                        'product': '${item:x * item:y}',
                    }
                },
                'parent': 'root_project'
            }
        }

        result = generate_meta(config)
        # x=10, y=2: sum=12, product=20
        assert 'exp__x10_y2 sum 12' in result
        assert 'exp__x10_y2 product 20' in result
        # x=10, y=5: sum=15, product=50
        assert 'exp__x10_y5 sum 15' in result
        assert 'exp__x10_y5 product 50' in result
        # x=20, y=2: sum=22, product=40
        assert 'exp__x20_y2 sum 22' in result
        assert 'exp__x20_y2 product 40' in result

    def test_complex_expression_with_round_and_math(self, basic_config):
        """Complex expression combining round and math operations."""
        config = basic_config.copy()
        config['templates'] = {
            'model_downsample': {
                'class': 'model_data',
                'operation': 'iter.combination',
                'input': [
                    {
                        'name': 'downsample_fraction',
                        'operation': 'range',
                        'start': 0.1,
                        'end': 0.3,
                        'inc': 0.1,
                    },
                    {
                        'name': 'strategy',
                        'values': ['geneset', 'gene']
                    }
                ],
                'pattern': {
                    'name': 'model__${round(item:downsample_fraction, 2)}__${item:strategy}',
                    'properties': {
                        'downsample_strategy': '${item:strategy}',
                        'downsample_fraction': '${item:downsample_fraction / 100}',
                    }
                },
                'parent': 'root_project'
            }
        }

        result = generate_meta(config)
        # Check names are rounded
        assert 'model__0.1__geneset class model_data' in result
        assert 'model__0.2__gene class model_data' in result
        # Check fraction divided by 100
        assert 'model__0.1__geneset downsample_fraction 0.001' in result
        assert 'model__0.2__geneset downsample_fraction 0.002' in result

    def test_expression_in_parent(self, basic_config):
        """Expression in parent reference should work."""
        config = basic_config.copy()
        config['classes'] = {
            'root_project': {
                'class': 'project',
                'parent': None,
            },
            'model_a': {
                'class': 'model',
                'parent': 'root_project',
            },
            'model_b': {
                'class': 'model',
                'parent': 'root_project',
            }
        }
        config['templates'] = {
            'experiments': {
                'class': 'experiment',
                'operation': 'iter.combination',
                'input': [
                    {
                        'name': 'model',
                        'class_name': 'model'
                    },
                    {
                        'name': 'replicate',
                        'values': [1, 2]
                    }
                ],
                'pattern': {
                    'name': 'exp__${item:model}__rep${item:replicate}',
                    'parent': '${item:model}',
                    'properties': {
                        'rep_id': '${item:replicate}',
                    }
                }
            }
        }

        result = generate_meta(config)
        assert 'exp__model_a__rep1 parent model_a' in result
        assert 'exp__model_a__rep2 parent model_a' in result
        assert 'exp__model_b__rep1 parent model_b' in result
        assert 'exp__model_b__rep2 parent model_b' in result

    def test_string_methods_in_expression(self, basic_config):
        """String methods should work in expressions."""
        config = basic_config.copy()
        config['templates'] = {
            'experiments': {
                'class': 'experiment',
                'operation': 'iter.combination',
                'input': [
                    {
                        'name': 'name',
                        'values': ['hello', 'world']
                    }
                ],
                'pattern': {
                    'name': 'exp__${item:name}',
                    'properties': {
                        'upper': '${str(item:name).upper()}',
                        'length': '${len(str(item:name))}',
                    }
                },
                'parent': 'root_project'
            }
        }

        result = generate_meta(config)
        assert 'exp__hello upper HELLO' in result
        assert 'exp__hello length 5' in result
        assert 'exp__world upper WORLD' in result
        assert 'exp__world length 5' in result

    def test_invalid_expression_raises_error(self, basic_config):
        """Invalid expression should raise helpful error."""
        config = basic_config.copy()
        config['templates'] = {
            'experiments': {
                'class': 'experiment',
                'operation': 'iter.combination',
                'input': [
                    {
                        'name': 'val',
                        'values': [1, 2]
                    }
                ],
                'pattern': {
                    'name': 'exp__${item:val.nonexistent()}',
                },
                'parent': 'root_project'
            }
        }

        with pytest.raises(ValueError, match="Failed to evaluate expression"):
            generate_meta(config)

    def test_unknown_item_reference_raises_error(self, basic_config):
        """Unknown item reference should raise helpful error."""
        config = basic_config.copy()
        config['templates'] = {
            'experiments': {
                'class': 'experiment',
                'operation': 'iter.combination',
                'input': [
                    {
                        'name': 'val',
                        'values': [1, 2]
                    }
                ],
                'pattern': {
                    'name': 'exp__${item:unknown}',
                },
                'parent': 'root_project'
            }
        }

        with pytest.raises(ValueError, match="Unknown item reference 'item:unknown'"):
            generate_meta(config)
