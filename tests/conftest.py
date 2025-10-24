"""
Pytest configuration and fixtures for meta-sanity tests.
"""
import pytest
import tempfile
import os
from pathlib import Path


@pytest.fixture
def temp_output_file():
    """Create a temporary output file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.meta', delete=False) as f:
        filepath = f.name
    yield filepath
    # Cleanup
    if os.path.exists(filepath):
        os.remove(filepath)


@pytest.fixture
def basic_config():
    """Basic valid configuration for testing."""
    return {
        'config': '/path/to/config.cfg',
        'keys': {
            'base_dir': '/test/dir',
            'data_dir': '${base_dir}/data',
        },
        'classes': {
            'root_project': {
                'class': 'project',
                'parent': None,
                'properties': {
                    'name': 'test_project',
                }
            }
        }
    }


@pytest.fixture
def basic_config_with_parent():
    """Configuration with a root class and a child class."""
    return {
        'config': '/path/to/config.cfg',
        'classes': {
            'root_project': {
                'class': 'project',
                'parent': None,
                'properties': {
                    'name': 'test_project',
                }
            },
            'child_item': {
                'class': 'item',
                'parent': 'root_project',
                'properties': {
                    'item_name': 'test_item',
                }
            }
        }
    }
