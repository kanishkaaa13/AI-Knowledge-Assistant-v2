"""
Direct ContextVar verification test.
Tests: 1) try/finally wrapping, 2) concurrent isolation with timestamps, 3) multi-tool visibility
"""
import asyncio
import contextvars
import time
import uuid
from unittest.mock import Mock, patch

# Mock the ContextVar and dependencies
_current_user_id: contextvars.ContextVar[str | None] = contextvars.ContextVar('current_user_id', default=None)

def simulate_tool_call(tool_name: str, delay: float = 0.5) -> dict:
    """Simulate a tool call that reads from ContextVar."""
    import time
    timestamp = time.strftime('%H:%M:%S', time.localtime(time.time()))
    user_id = _current_user_id.get()
    print(f"[{tool_name}] {timestamp} ENTRY - user_id from ContextVar: {user_id}")
    time.sleep(delay)  # Simulate work
    timestamp = time.strftime('%H:%M:%S', time.localtime(time.time()))
    print(f"[{tool_name}] {timestamp} EXIT - user_id still: {_current_user_id.get()}")
    return {"tool": tool_name, "user_id": user_id}

def simulate_run_agent(user_id: str, tool_sequence: list[str], delays: list[float]) -> dict:
    """Simulate run_agent with ContextVar set/reset and try/finally."""
    import time
    request_start = time.time()
    timestamp = time.strftime('%H:%M:%S', time.localtime(request_start))
    print(f"[run_agent] {timestamp} Request START for user_id: {user_id}")
    
    token = _current_user_id.set(user_id)
    timestamp = time.strftime('%H:%M:%S', time.localtime(time.time()))
    print(f"[run_agent] {timestamp} ContextVar SET for user_id: {user_id}")
    
    try:
        results = []
        for tool_name, delay in zip(tool_sequence, delays):
            result = simulate_tool_call(tool_name, delay)
            results.append(result)
        
        return {"user_id": user_id, "tool_results": results}
    finally:
        timestamp = time.strftime('%H:%M:%S', time.localtime(time.time()))
        print(f"[run_agent] {timestamp} ContextVar RESET for user_id: {user_id}")
        _current_user_id.reset(token)
        elapsed = time.time() - request_start
        timestamp = time.strftime('%H:%M:%S', time.localtime(time.time()))
        print(f"[run_agent] {timestamp} Request END for user_id: {user_id} (elapsed: {elapsed:.3f}s)")

async def test_concurrent_isolation():
    """Test 1: Concurrent requests with detailed timestamps to prove overlap."""
    print("\n" + "="*80)
    print("TEST 1: CONCURRENT ISOLATION - Two users with overlapping tool calls")
    print("="*80 + "\n")
    
    # User 1: calls keyword_search (0.8s)
    user1_task = asyncio.to_thread(
        simulate_run_agent, 
        "user-1-uuid", 
        ["keyword_search"], 
        [0.8]
    )
    
    # User 2: calls keyword_search (0.8s) - started 0.1s after User 1
    await asyncio.sleep(0.1)
    user2_task = asyncio.to_thread(
        simulate_run_agent,
        "user-2-uuid", 
        ["keyword_search"], 
        [0.8]
    )
    
    start_time = time.time()
    results = await asyncio.gather(user1_task, user2_task)
    total_elapsed = time.time() - start_time
    
    print("\n" + "="*80)
    print("TEST 1 RESULTS")
    print("="*80)
    
    for result in results:
        print(f"\nUser ID: {result['user_id']}")
        for tool_result in result['tool_results']:
            print(f"  Tool: {tool_result['tool']}, Read user_id: {tool_result['user_id']}")
    
    print(f"\nTotal elapsed: {total_elapsed:.3f}s")
    
    # Verify isolation
    user1_id = results[0]['tool_results'][0]['user_id']
    user2_id = results[1]['tool_results'][0]['user_id']
    
    if user1_id == "user-1-uuid" and user2_id == "user-2-uuid" and user1_id != user2_id:
        print("\n✓ TEST 1 PASSED: ContextVar isolation confirmed - each tool read correct user_id")
    else:
        print(f"\n✗ TEST 1 FAILED: user1_id={user1_id}, user2_id={user2_id}")
    
    return results

def test_try_finally():
    """Test 2: Verify ContextVar.reset() is called even on exception."""
    print("\n" + "="*80)
    print("TEST 2: TRY/FINALLY WRAPPING - Exception handling")
    print("="*80 + "\n")
    
    def failing_agent(user_id: str):
        import time
        timestamp = time.strftime('%H:%M:%S', time.localtime(time.time()))
        print(f"[failing_agent] {timestamp} Request START for user_id: {user_id}")
        
        token = _current_user_id.set(user_id)
        timestamp = time.strftime('%H:%M:%S', time.localtime(time.time()))
        print(f"[failing_agent] {timestamp} ContextVar SET for user_id: {user_id}")
        
        try:
            # Simulate work then raise exception
            time.sleep(0.2)
            timestamp = time.strftime('%H:%M:%S', time.localtime(time.time()))
            print(f"[failing_agent] {timestamp} About to raise exception")
            raise ValueError("Simulated agent failure")
        finally:
            timestamp = time.strftime('%H:%M:%S', time.localtime(time.time()))
            print(f"[failing_agent] {timestamp} ContextVar RESET for user_id: {user_id}")
            _current_user_id.reset(token)
            timestamp = time.strftime('%H:%M:%S', time.localtime(time.time()))
            print(f"[failing_agent] {timestamp} Request END (after reset)")
    
    try:
        failing_agent("test-user-uuid")
    except ValueError:
        pass
    
    # Verify ContextVar was reset
    final_value = _current_user_id.get(None)
    if final_value is None:
        print("\n✓ TEST 2 PASSED: ContextVar.reset() called in finally block - value is None after exception")
    else:
        print(f"\n✗ TEST 2 FAILED: ContextVar not reset, value is: {final_value}")

def test_multi_tool_visibility():
    """Test 3: ContextVar visibility across multiple tool calls in same request."""
    print("\n" + "="*80)
    print("TEST 3: MULTI-TOOL VISIBILITY - Same user, sequential tools")
    print("="*80 + "\n")
    
    # Single user calling two tools in sequence
    result = simulate_run_agent(
        "multi-tool-user-uuid",
        ["search_documents", "quiz_generator"],
        [0.3, 0.3]
    )
    
    print("\n" + "="*80)
    print("TEST 3 RESULTS")
    print("="*80)
    
    tool1_user_id = result['tool_results'][0]['user_id']
    tool2_user_id = result['tool_results'][1]['user_id']
    
    print(f"\nTool 1 (search_documents) read user_id: {tool1_user_id}")
    print(f"Tool 2 (quiz_generator) read user_id: {tool2_user_id}")
    
    if tool1_user_id == "multi-tool-user-uuid" and tool2_user_id == "multi-tool-user-uuid":
        print("\n✓ TEST 3 PASSED: ContextVar visible across all tool calls in same request")
    else:
        print(f"\n✗ TEST 3 FAILED: Expected 'multi-tool-user-uuid' for both, got {tool1_user_id} and {tool2_user_id}")

async def main():
    """Run all three verification tests."""
    print("\n" + "="*80)
    print("CONTEXTVAR VERIFICATION TEST SUITE")
    print("="*80)
    
    # Test 1: Concurrent isolation
    await test_concurrent_isolation()
    
    # Test 2: Try/finally wrapping
    test_try_finally()
    
    # Test 3: Multi-tool visibility
    test_multi_tool_visibility()
    
    print("\n" + "="*80)
    print("ALL TESTS COMPLETED")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())
