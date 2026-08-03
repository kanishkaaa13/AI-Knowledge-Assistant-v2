"""
Test script to verify user_id injection in agent tools.
This tests that the /agent/run endpoint properly passes user_id to tools
and that tools correctly extract it from RunnableConfig.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.agents.router_agent import run_agent


async def test_user_id_injection():
    """Test that user_id is properly injected and extracted by tools."""
    print("=" * 80)
    print("TEST: user_id injection in agent tools")
    print("=" * 80)
    
    # Test 1: Run agent WITH user_id (should work)
    print("\n[TEST 1] Running agent WITH user_id...")
    try:
        test_user_id = "12345678-1234-1234-1234-123456789abc"
        result = run_agent(
            user_query="find the exact term 'test' in my docs", 
            user_id=test_user_id
        )
        print(f"✓ Agent executed successfully")
        print(f"  Tools called: {result.get('tools_called', [])}")
        print(f"  Answer: {result.get('answer', '')[:200]}...")
    except ValueError as e:
        if "user_id missing" in str(e):
            print(f"✗ FAILED: {e}")
            print("  This indicates config injection is not working correctly")
        else:
            raise
    except Exception as e:
        print(f"✗ FAILED with unexpected error: {e}")
    
    # Test 2: Run agent WITHOUT user_id (should fail loudly)
    print("\n[TEST 2] Running agent WITHOUT user_id (should fail)...")
    try:
        result = run_agent(user_query="find the exact term 'test' in my docs")
        print(f"✗ FAILED: Agent should have raised ValueError but didn't")
        print(f"  This is a security issue - user_id is not required")
    except ValueError as e:
        if "user_id missing" in str(e):
            print(f"✓ PASSED: Correctly raised ValueError: {e}")
        else:
            print(f"✗ FAILED with unexpected ValueError: {e}")
    except Exception as e:
        print(f"✗ FAILED with unexpected error: {e}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_user_id_injection())
