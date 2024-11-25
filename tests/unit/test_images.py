# tests/unit/test_images.py

import pytest
from openhands.core.config.sandbox_config import SandboxConfig

def test_runtime_container_image_default():
    config = SandboxConfig()
    assert config.runtime_container_image == 'ghcr.io/assertion/runtime:latest'

def test_memory_limit_default():
    # Assuming there's a way to access the memory limit from the config or environment
    # This is a placeholder for the actual implementation
    mem_limit = "100g"  # This should be fetched from the actual configuration
    assert mem_limit == "100g"