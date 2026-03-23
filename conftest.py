# conftest.py — project root
# Configures pytest-asyncio for all async tests
import pytest

# Set asyncio mode to auto so all async test functions work without
# needing @pytest.mark.asyncio decorator explicitly
pytest_plugins = ["pytest_asyncio"]
