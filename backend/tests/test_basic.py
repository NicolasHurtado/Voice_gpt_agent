"""
Basic tests to verify the test setup is working.
"""

import pytest


def test_basic_math():
    """Test that basic math works."""
    assert 2 + 2 == 4


def test_basic_string():
    """Test that string operations work."""
    assert "hello" + " world" == "hello world"


@pytest.mark.asyncio
async def test_async_basic():
    """Test that async tests work."""
    async def async_add(a, b):
        return a + b
    
    result = await async_add(2, 3)
    assert result == 5


class TestBasicClass:
    """Test class for basic functionality."""
    
    def test_class_method(self):
        """Test that class methods work."""
        assert True
    
    @pytest.mark.asyncio
    async def test_async_class_method(self):
        """Test that async class methods work."""
        async def async_multiply(a, b):
            return a * b
        
        result = await async_multiply(3, 4)
        assert result == 12
