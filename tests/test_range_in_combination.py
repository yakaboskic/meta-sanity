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
