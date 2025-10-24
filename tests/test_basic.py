"""
Basic tests for core functionality.
"""
import pytest
from meta_sanity.generate_meta import generate_meta


class TestBasicGeneration:
    """Test basic meta file generation."""

    def test_minimal_config(self):
        """Minimal valid configuration should generate."""
        config = {
            'config': '/path/to/config.cfg',
            'classes': {
                'root': {
                    'class': 'project',
                    'parent': None,
                }
            }
        }

        result = generate_meta(config)
        assert '!config /path/to/config.cfg' in result
        assert 'root class project' in result

    def test_with_keys(self):
        """Configuration with keys should write them."""
        config = {
            'config': '/path/to/config.cfg',
            'keys': {
                'base_dir': '/test',
                'data_dir': '/test/data',
            },
            'classes': {
                'root': {
                    'class': 'project',
                    'parent': None,
                }
            }
        }

        result = generate_meta(config)
        assert '!key base_dir /test' in result
        assert '!key data_dir /test/data' in result

    def test_with_properties(self):
        """Classes with properties should write them."""
        config = {
            'config': '/path/to/config.cfg',
            'classes': {
                'root': {
                    'class': 'project',
                    'parent': None,
                    'properties': {
                        'name': 'test_project',
                        'version': '1.0',
                    }
                }
            }
        }

        result = generate_meta(config)
        assert 'root name test_project' in result
        assert 'root version 1.0' in result

    def test_parent_child_relationship(self):
        """Parent-child relationships should be preserved."""
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
        assert 'child parent root' in result

    def test_generation_order(self):
        """Elements should appear in the correct order."""
        config = {
            'config': '/path/to/config.cfg',
            'keys': {
                'key1': 'value1',
            },
            'classes': {
                'root': {
                    'class': 'project',
                    'parent': None,
                }
            }
        }

        result = generate_meta(config)
        lines = result.split('\n')

        # Config should be first
        assert lines[0].startswith('!config')

        # Keys should come before classes
        key_line = next(i for i, line in enumerate(lines) if '!key' in line)
        class_line = next(i for i, line in enumerate(lines) if 'class project' in line)
        assert key_line < class_line

    def test_empty_templates_section(self, basic_config):
        """Empty templates section should work."""
        config = basic_config.copy()
        config['templates'] = {}

        result = generate_meta(config)
        assert 'root_project class project' in result


class TestErrorMessages:
    """Test that error messages are helpful."""

    def test_missing_config_field(self):
        """Missing config field should raise error."""
        config = {
            # Missing 'config'
            'classes': {
                'root': {
                    'class': 'project',
                    'parent': None,
                }
            }
        }

        with pytest.raises(KeyError, match="config"):
            generate_meta(config)

    def test_template_error_includes_template_name(self, basic_config):
        """Template errors should include the template name."""
        config = basic_config.copy()
        config['templates'] = {
            'my_template': {
                'class': 'sample',
                'operation': 'for_each_item',
                'input': ['a'],
                'pattern': {
                    'name': 'sample__${item.bad_method()}',  # Will error
                },
                'parent': 'root_project'
            }
        }

        with pytest.raises(ValueError, match="my_template"):
            generate_meta(config)

    def test_property_error_includes_context(self, basic_config):
        """Property processing errors should include context."""
        config = basic_config.copy()
        config['templates'] = {
            'samples': {
                'class': 'sample',
                'operation': 'for_each_item',
                'input': ['test'],
                'pattern': {
                    'name': 'sample__${item}',
                    'properties': {
                        'bad_prop': '${item.nonexistent()}',
                    }
                },
                'parent': 'root_project'
            }
        }

        with pytest.raises(ValueError, match="bad_prop"):
            generate_meta(config)


class TestConfigValidation:
    """Test configuration validation."""

    def test_pattern_must_be_dict(self, basic_config):
        """Pattern field must be a dictionary."""
        config = basic_config.copy()
        config['templates'] = {
            'test': {
                'class': 'sample',
                'operation': 'for_each_item',
                'input': ['a'],
                'pattern': 'not_a_dict',  # Wrong type
                'parent': 'root_project'
            }
        }

        with pytest.raises(ValueError, match="must be a dictionary"):
            generate_meta(config)

    def test_input_type_validation_for_each_class(self, basic_config):
        """for_each_class input must be dict."""
        config = basic_config.copy()
        config['templates'] = {
            'test': {
                'class': 'analysis',
                'operation': 'for_each_class',
                'input': ['not', 'a', 'dict'],  # Wrong type
                'pattern': {
                    'name': 'analysis__${item}',
                    'properties': {}
                },
                'parent': 'root_project'
            }
        }

        with pytest.raises(ValueError, match="requires 'input' to be a dictionary"):
            generate_meta(config)

    def test_input_type_validation_range(self, basic_config):
        """range input must be dict."""
        config = basic_config.copy()
        config['templates'] = {
            'test': {
                'class': 'sample',
                'operation': 'range',
                'input': [1, 2, 3],  # Wrong type
                'pattern': {
                    'name': 'sample__${item}',
                },
                'parent': 'root_project'
            }
        }

        with pytest.raises(ValueError, match="requires 'input' to be a dictionary"):
            generate_meta(config)
