"""
Tests for type handling in meta-sanity.
These tests ensure that different YAML value types (numbers, strings, booleans, etc.)
are handled correctly throughout the generation process.
"""
import pytest
from meta_sanity.generate_meta import (
    generate_meta,
    normalize_value,
    process_template_expr,
)


class TestNormalizeValue:
    """Test the normalize_value function."""

    def test_normalize_string(self):
        """Strings should pass through unchanged."""
        assert normalize_value("hello") == "hello"
        assert normalize_value("123") == "123"
        assert normalize_value("true") == "true"

    def test_normalize_integer(self):
        """Integers should convert to strings."""
        assert normalize_value(42) == "42"
        assert normalize_value(0) == "0"
        assert normalize_value(-5) == "-5"

    def test_normalize_float(self):
        """Floats should convert to strings, ints when whole numbers."""
        assert normalize_value(3.14) == "3.14"
        assert normalize_value(5.0) == "5"
        assert normalize_value(0.0) == "0"

    def test_normalize_boolean(self):
        """Booleans should convert to 'true' or 'false'."""
        assert normalize_value(True) == "true"
        assert normalize_value(False) == "false"

    def test_normalize_none(self):
        """None should convert to 'null'."""
        assert normalize_value(None) == "null"


class TestProcessTemplateExpr:
    """Test the process_template_expr function."""

    def test_simple_string_substitution(self):
        """Simple ${item} replacement with string."""
        result = process_template_expr("sample__${item}", "test")
        assert result == "sample__test"

    def test_number_substitution(self):
        """${item} replacement with numbers."""
        result = process_template_expr("sample__${item}", 42)
        assert result == "sample__42"

        result = process_template_expr("sample__${item}", 3.14)
        assert result == "sample__3.14"

    def test_boolean_substitution(self):
        """${item} replacement with booleans."""
        result = process_template_expr("flag__${item}", True)
        assert result == "flag__true"

        result = process_template_expr("flag__${item}", False)
        assert result == "flag__false"

    def test_expression_evaluation(self):
        """Test Python expression evaluation."""
        result = process_template_expr("sample__${int(item) * 2}", "5")
        assert result == "sample__10"

        result = process_template_expr("sample__${item.upper()}", "test")
        assert result == "sample__TEST"

    def test_invalid_template_type(self):
        """Non-string templates should raise an error."""
        with pytest.raises(ValueError, match="Template must be a string"):
            process_template_expr(123, "test")

    def test_unclosed_expression(self):
        """Unclosed ${item expression should raise an error."""
        with pytest.raises(ValueError, match="Unclosed"):
            process_template_expr("sample__${item", "test")

    def test_invalid_expression(self):
        """Invalid Python expression should raise an error."""
        with pytest.raises(ValueError, match="Failed to evaluate"):
            process_template_expr("sample__${item.nonexistent_method()}", "test")


class TestTemplateWithNumericValues:
    """Test templates with numeric input values."""

    def test_for_each_item_with_numbers(self, basic_config):
        """for_each_item should handle numeric values in input."""
        config = basic_config.copy()
        config['templates'] = {
            'test_samples': {
                'class': 'sample',
                'operation': 'for_each_item',
                'input': [1, 2, 3],  # Numeric values
                'pattern': {
                    'name': 'sample__${item}',
                    'properties': {
                        'sample_id': '${item}',
                        'count': '${int(item) * 2}',
                    }
                },
                'parent': 'root_project'
            }
        }

        result = generate_meta(config)
        assert 'sample__1 class sample' in result
        assert 'sample__1 sample_id 1' in result
        assert 'sample__1 count 2' in result
        assert 'sample__2 class sample' in result
        assert 'sample__2 count 4' in result

    def test_for_each_item_with_floats(self, basic_config):
        """for_each_item should handle float values."""
        config = basic_config.copy()
        config['templates'] = {
            'test_samples': {
                'class': 'sample',
                'operation': 'for_each_item',
                'input': [1.5, 2.0, 3.14],
                'pattern': {
                    'name': 'sample__${item}',
                    'properties': {
                        'value': '${item}',
                    }
                },
                'parent': 'root_project'
            }
        }

        result = generate_meta(config)
        assert 'sample__1.5 class sample' in result
        assert 'sample__1.5 value 1.5' in result
        assert 'sample__2 class sample' in result  # 2.0 becomes 2
        assert 'sample__2 value 2' in result

    def test_for_each_item_with_booleans(self, basic_config):
        """for_each_item should handle boolean values."""
        config = basic_config.copy()
        config['templates'] = {
            'test_flags': {
                'class': 'flag',
                'operation': 'for_each_item',
                'input': [True, False],
                'pattern': {
                    'name': 'flag__${item}',
                    'properties': {
                        'enabled': '${item}',
                    }
                },
                'parent': 'root_project'
            }
        }

        result = generate_meta(config)
        assert 'flag__true class flag' in result
        assert 'flag__true enabled true' in result
        assert 'flag__false class flag' in result
        assert 'flag__false enabled false' in result

    def test_properties_with_numeric_values(self, basic_config):
        """Properties can have numeric values directly."""
        config = basic_config.copy()
        config['classes']['root_project']['properties'] = {
            'name': 'test_project',
            'count': 42,
            'ratio': 3.14,
            'enabled': True,
        }

        result = generate_meta(config)
        assert 'root_project count 42' in result
        assert 'root_project ratio 3.14' in result
        assert 'root_project enabled true' in result

    def test_mixed_types_in_template_properties(self, basic_config):
        """Template properties can mix strings and variable expressions."""
        config = basic_config.copy()
        config['templates'] = {
            'test_samples': {
                'class': 'sample',
                'operation': 'for_each_item',
                'input': [1, 2],
                'pattern': {
                    'name': 'sample__${item}',
                    'properties': {
                        'id': '${item}',  # Will be numeric
                        'name': 'sample_${item}',  # String interpolation
                        'active': True,  # Direct boolean
                        'threshold': 100,  # Direct number
                    }
                },
                'parent': 'root_project'
            }
        }

        result = generate_meta(config)
        assert 'sample__1 id 1' in result
        assert 'sample__1 name sample_1' in result
        assert 'sample__1 active true' in result
        assert 'sample__1 threshold 100' in result


class TestRangeWithTypes:
    """Test range operation with different numeric types."""

    def test_range_integer_values(self, basic_config):
        """Range with integer start/end/inc."""
        config = basic_config.copy()
        config['templates'] = {
            'numbered_samples': {
                'class': 'sample',
                'operation': 'range',
                'input': {
                    'start': 1,
                    'end': 3,
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
        assert 'sample__1 id 1' in result

    def test_range_float_values(self, basic_config):
        """Range with float start/end/inc."""
        config = basic_config.copy()
        config['templates'] = {
            'float_samples': {
                'class': 'sample',
                'operation': 'range',
                'input': {
                    'start': 0.5,
                    'end': 1.5,
                    'inc': 0.5,
                },
                'pattern': {
                    'name': 'sample__${item}',
                    'properties': {
                        'value': '${item}',
                    }
                },
                'parent': 'root_project'
            }
        }

        result = generate_meta(config)
        assert 'sample__0.5 class sample' in result
        assert 'sample__1 class sample' in result  # 1.0 becomes 1
        assert 'sample__1.5 class sample' in result

    def test_range_with_string_numbers(self, basic_config):
        """Range should handle string numbers in YAML."""
        config = basic_config.copy()
        config['templates'] = {
            'string_range': {
                'class': 'sample',
                'operation': 'range',
                'input': {
                    'start': "1",
                    'end': "3",
                    'inc': "1",
                },
                'pattern': {
                    'name': 'sample__${item}',
                },
                'parent': 'root_project'
            }
        }

        result = generate_meta(config)
        assert 'sample__1 class sample' in result
        assert 'sample__2 class sample' in result
        assert 'sample__3 class sample' in result
