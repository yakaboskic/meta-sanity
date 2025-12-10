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


class TestClassSubsets:
    """Test subset support for basic class definitions."""

    def test_basic_class_with_subsets(self):
        """Basic classes can have subsets defined."""
        config = {
            'config': '/path/to/config.cfg',
            'classes': {
                'root': {
                    'class': 'project',
                    'parent': None,
                    'subsets': ['core', 'infrastructure']
                }
            }
        }

        # Should generate without error
        result = generate_meta(config)
        assert 'root class project' in result

    def test_class_subsets_used_in_for_each_class_filter(self):
        """Class subsets can be filtered in for_each_class templates."""
        config = {
            'config': '/path/to/config.cfg',
            'classes': {
                'root': {
                    'class': 'project',
                    'parent': None,
                },
                'gwas_data': {
                    'class': 'genetic_data',
                    'parent': 'root',
                    'properties': {
                        'source': 'gwas',
                    },
                    'subsets': ['gwas']
                },
                'bottomline_data': {
                    'class': 'genetic_data',
                    'parent': 'root',
                    'properties': {
                        'source': 'bottomline',
                    },
                    'subsets': ['bottomline']
                },
                'other_data': {
                    'class': 'genetic_data',
                    'parent': 'root',
                    'properties': {
                        'source': 'other',
                    },
                    # No subsets
                }
            },
            'templates': {
                'gwas_analyses': {
                    'class': 'analysis',
                    'operation': 'for_each_class',
                    'input': {
                        'class_name': 'genetic_data',
                        'if_subset': ['gwas']
                    },
                    'pattern': {
                        'name': 'analysis__${item}',
                        'properties': {
                            'target': '${item}',
                        }
                    },
                    'parent': 'root'
                }
            }
        }

        result = generate_meta(config)
        # Should only include gwas_data since it has the 'gwas' subset
        assert 'analysis__gwas_data class analysis' in result
        assert 'analysis__bottomline_data class analysis' not in result
        assert 'analysis__other_data class analysis' not in result

    def test_class_subsets_used_in_iter_combination_filter(self):
        """Class subsets can be filtered in iter.combination templates."""
        config = {
            'config': '/path/to/config.cfg',
            'classes': {
                'root': {
                    'class': 'project',
                    'parent': None,
                },
                'sample_a': {
                    'class': 'sample',
                    'parent': 'root',
                    'subsets': ['batch1']
                },
                'sample_b': {
                    'class': 'sample',
                    'parent': 'root',
                    'subsets': ['batch1']
                },
                'sample_c': {
                    'class': 'sample',
                    'parent': 'root',
                    'subsets': ['batch2']
                }
            },
            'templates': {
                'experiments': {
                    'class': 'experiment',
                    'operation': 'iter.combination',
                    'input': [
                        {
                            'name': 'sample',
                            'class_name': 'sample',
                            'if_subset': ['batch1']
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
                        }
                    },
                    'parent': 'root'
                }
            }
        }

        result = generate_meta(config)
        # Should only include samples from batch1 subset
        assert 'exp__sample_a__4c class experiment' in result
        assert 'exp__sample_a__22c class experiment' in result
        assert 'exp__sample_b__4c class experiment' in result
        assert 'exp__sample_b__22c class experiment' in result
        # sample_c is in batch2, not batch1
        assert 'exp__sample_c__4c class experiment' not in result
        assert 'exp__sample_c__22c class experiment' not in result

    def test_class_subsets_combined_with_template_subsets(self):
        """Class subsets work together with template-generated subsets."""
        config = {
            'config': '/path/to/config.cfg',
            'classes': {
                'root': {
                    'class': 'project',
                    'parent': None,
                },
                'static_sample': {
                    'class': 'sample',
                    'parent': 'root',
                    'subsets': ['automated']
                }
            },
            'templates': {
                'dynamic_samples': {
                    'class': 'sample',
                    'operation': 'for_each_item',
                    'input': ['dynamic1', 'dynamic2'],
                    'pattern': {
                        'name': 'sample__${item}',
                    },
                    'parent': 'root',
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
                    'parent': 'root'
                }
            }
        }

        result = generate_meta(config)
        # Should include both static and dynamic samples with 'automated' subset
        assert 'analysis__static_sample class analysis' in result
        assert 'analysis__sample__dynamic1 class analysis' in result
        assert 'analysis__sample__dynamic2 class analysis' in result

    def test_multiple_class_subsets(self):
        """Classes can belong to multiple subsets."""
        config = {
            'config': '/path/to/config.cfg',
            'classes': {
                'root': {
                    'class': 'project',
                    'parent': None,
                },
                'multi_subset_data': {
                    'class': 'data',
                    'parent': 'root',
                    'subsets': ['gwas', 'published', 'validated']
                }
            },
            'templates': {
                'gwas_analysis': {
                    'class': 'analysis',
                    'operation': 'for_each_class',
                    'input': {
                        'class_name': 'data',
                        'if_subset': ['gwas']
                    },
                    'pattern': {
                        'name': 'gwas_analysis__${item}',
                        'properties': {}
                    },
                    'parent': 'root'
                },
                'published_analysis': {
                    'class': 'analysis',
                    'operation': 'for_each_class',
                    'input': {
                        'class_name': 'data',
                        'if_subset': ['published']
                    },
                    'pattern': {
                        'name': 'published_analysis__${item}',
                        'properties': {}
                    },
                    'parent': 'root'
                }
            }
        }

        result = generate_meta(config)
        # multi_subset_data should appear in both analyses
        assert 'gwas_analysis__multi_subset_data class analysis' in result
        assert 'published_analysis__multi_subset_data class analysis' in result
