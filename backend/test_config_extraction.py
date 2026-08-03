"""
Simple test to verify config extraction logic without full agent infrastructure.
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from langchain_core.runnables import RunnableConfig


def test_config_extraction():
    """Test that config extraction logic works correctly."""
    print("=" * 80)
    print("TEST: RunnableConfig extraction logic")
    print("=" * 80)
    
    # Test 1: Valid config with user_id
    print("\n[TEST 1] Valid config with user_id...")
    config = RunnableConfig(configurable={"user_id": "12345678-1234-1234-1234-123456789abc"})
    
    try:
        if not config or "configurable" not in config:
            raise ValueError("user_id missing from agent config - config not properly passed")
        user_id = config["configurable"].get("user_id")
        if not user_id:
            raise ValueError("user_id missing from agent config - user_id not set in configurable")
        print(f"✓ PASSED: Extracted user_id = {user_id}")
    except Exception as e:
        print(f"✗ FAILED: {e}")
    
    # Test 2: Config without configurable key
    print("\n[TEST 2] Config without configurable key (should fail)...")
    config = RunnableConfig()
    
    try:
        if not config or "configurable" not in config:
            raise ValueError("user_id missing from agent config - config not properly passed")
        user_id = config["configurable"].get("user_id")
        print(f"✗ FAILED: Should have raised ValueError")
    except ValueError as e:
        if "config not properly passed" in str(e):
            print(f"✓ PASSED: Correctly raised ValueError: {e}")
        else:
            print(f"✗ FAILED with unexpected ValueError: {e}")
    
    # Test 3: Config with empty user_id
    print("\n[TEST 3] Config with empty user_id (should fail)...")
    config = RunnableConfig(configurable={"user_id": None})
    
    try:
        if not config or "configurable" not in config:
            raise ValueError("user_id missing from agent config - config not properly passed")
        user_id = config["configurable"].get("user_id")
        if not user_id:
            raise ValueError("user_id missing from agent config - user_id not set in configurable")
        print(f"✗ FAILED: Should have raised ValueError")
    except ValueError as e:
        if "user_id not set in configurable" in str(e):
            print(f"✓ PASSED: Correctly raised ValueError: {e}")
        else:
            print(f"✗ FAILED with unexpected ValueError: {e}")
    
    # Test 4: Config with missing user_id key
    print("\n[TEST 4] Config with missing user_id key (should fail)...")
    config = RunnableConfig(configurable={})
    
    try:
        if not config or "configurable" not in config:
            raise ValueError("user_id missing from agent config - config not properly passed")
        user_id = config["configurable"].get("user_id")
        if not user_id:
            raise ValueError("user_id missing from agent config - user_id not set in configurable")
        print(f"✗ FAILED: Should have raised ValueError")
    except ValueError as e:
        if "user_id not set in configurable" in str(e):
            print(f"✓ PASSED: Correctly raised ValueError: {e}")
        else:
            print(f"✗ FAILED with unexpected ValueError: {e}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_config_extraction()
