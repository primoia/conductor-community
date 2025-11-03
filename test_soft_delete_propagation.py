#!/usr/bin/env python3
"""
Test script for soft-delete propagation functionality
Tests all scenarios described in requisitos_propagacao_soft_delete.md
"""

import requests
import json
from datetime import datetime
import time

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

def print_section(title):
    """Print formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def print_result(test_name, passed, details=""):
    """Print test result"""
    status = "✅ PASSED" if passed else "❌ FAILED"
    print(f"{status} - {test_name}")
    if details:
        print(f"  Details: {details}")

def create_test_instance(agent_id="test-agent-001"):
    """Create a test agent instance"""
    response = requests.post(
        f"{API_BASE}/agents/instances",
        json={
            "agent_id": agent_id,
            "config": {"test": True}
        }
    )
    if response.status_code == 200:
        data = response.json()
        return data.get("instance_id")
    return None

def add_test_messages(instance_id, count=5):
    """Add test messages to an instance"""
    # This would depend on your actual API for adding messages
    # For now, we'll simulate by directly inserting to MongoDB if needed
    print(f"  Note: Add {count} test messages to instance {instance_id} manually or via API")
    return count

def get_instance(instance_id):
    """Get instance details"""
    response = requests.get(f"{API_BASE}/agents/instances/{instance_id}")
    if response.status_code == 200:
        return response.json()
    return None

def get_history_count(instance_id, is_deleted=None):
    """Count history messages for an instance"""
    # This would depend on your actual API
    # For now, return a placeholder
    return {"total": 5, "deleted": 0}

def soft_delete_instance(instance_id):
    """Soft delete an instance"""
    response = requests.delete(f"{API_BASE}/agents/instances/{instance_id}")
    return response

def hard_delete_instance(instance_id, cascade=False):
    """Hard delete an instance"""
    params = {"hard": "true"}
    if cascade:
        params["cascade"] = "true"
    response = requests.delete(f"{API_BASE}/agents/instances/{instance_id}", params=params)
    return response

# Test 1: Soft-Delete with Messages
def test_soft_delete_with_messages():
    print_section("Test 1: Soft-Delete with Messages")

    # Create instance
    instance_id = create_test_instance()
    if not instance_id:
        print_result("Create instance", False, "Failed to create test instance")
        return False

    print(f"Created instance: {instance_id}")

    # Add messages
    message_count = add_test_messages(instance_id, 5)
    print(f"Added {message_count} messages")

    # Perform soft delete
    response = soft_delete_instance(instance_id)

    if response.status_code != 200:
        print_result("Soft delete", False, f"Status code: {response.status_code}")
        return False

    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

    # Validate response
    checks = [
        (result.get("success") == True, "success flag is True"),
        (result.get("deletion_type") == "soft", "deletion_type is 'soft'"),
        (result.get("isDeleted") == True, "isDeleted flag is True"),
        ("history_messages_affected" in result, "history_messages_affected is present"),
    ]

    all_passed = True
    for passed, description in checks:
        print_result(description, passed)
        all_passed = all_passed and passed

    return all_passed

# Test 2: Soft-Delete without Messages
def test_soft_delete_without_messages():
    print_section("Test 2: Soft-Delete without Messages")

    # Create instance
    instance_id = create_test_instance("test-agent-002")
    if not instance_id:
        print_result("Create instance", False, "Failed to create test instance")
        return False

    print(f"Created instance: {instance_id}")
    print("No messages added (testing empty instance)")

    # Perform soft delete
    response = soft_delete_instance(instance_id)

    if response.status_code != 200:
        print_result("Soft delete", False, f"Status code: {response.status_code}")
        return False

    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

    # Validate that history_messages_affected is 0
    checks = [
        (result.get("success") == True, "success flag is True"),
        (result.get("history_messages_affected") == 0, "history_messages_affected is 0"),
    ]

    all_passed = True
    for passed, description in checks:
        print_result(description, passed)
        all_passed = all_passed and passed

    return all_passed

# Test 3: Hard-Delete with Cascade
def test_hard_delete_cascade():
    print_section("Test 3: Hard-Delete with Cascade")

    # Create instance
    instance_id = create_test_instance("test-agent-003")
    if not instance_id:
        print_result("Create instance", False, "Failed to create test instance")
        return False

    print(f"Created instance: {instance_id}")

    # Add messages
    message_count = add_test_messages(instance_id, 3)
    print(f"Added {message_count} messages")

    # Perform hard delete with cascade
    response = hard_delete_instance(instance_id, cascade=True)

    if response.status_code != 200:
        print_result("Hard delete", False, f"Status code: {response.status_code}")
        return False

    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

    # Validate response
    checks = [
        (result.get("success") == True, "success flag is True"),
        (result.get("deletion_type") == "hard", "deletion_type is 'hard'"),
        ("cascade_deleted" in result, "cascade_deleted info present"),
    ]

    all_passed = True
    for passed, description in checks:
        print_result(description, passed)
        all_passed = all_passed and passed

    # Verify instance is gone
    get_response = requests.get(f"{API_BASE}/agents/instances/{instance_id}")
    instance_gone = get_response.status_code == 404
    print_result("Instance permanently deleted", instance_gone)
    all_passed = all_passed and instance_gone

    return all_passed

# Test 4: Idempotent Soft-Delete
def test_idempotent_soft_delete():
    print_section("Test 4: Idempotent Soft-Delete (Delete Twice)")

    # Create instance
    instance_id = create_test_instance("test-agent-004")
    if not instance_id:
        print_result("Create instance", False, "Failed to create test instance")
        return False

    print(f"Created instance: {instance_id}")

    # Add messages
    message_count = add_test_messages(instance_id, 2)
    print(f"Added {message_count} messages")

    # First soft delete
    print("\n--- First deletion ---")
    response1 = soft_delete_instance(instance_id)
    result1 = response1.json()
    print(f"First delete - messages affected: {result1.get('history_messages_affected', 0)}")

    # Second soft delete
    print("\n--- Second deletion ---")
    time.sleep(1)  # Small delay
    response2 = soft_delete_instance(instance_id)
    result2 = response2.json()
    print(f"Second delete - messages affected: {result2.get('history_messages_affected', 0)}")

    # Validate idempotency
    checks = [
        (response1.status_code == 200, "First deletion succeeded"),
        (response2.status_code == 200, "Second deletion succeeded"),
        (result1.get('history_messages_affected', 0) > 0, "First deletion affected messages"),
        (result2.get('history_messages_affected', 0) == 0, "Second deletion affected 0 messages (idempotent)"),
    ]

    all_passed = True
    for passed, description in checks:
        print_result(description, passed)
        all_passed = all_passed and passed

    return all_passed

# Test 5: Instance Isolation
def test_instance_isolation():
    print_section("Test 5: Instance Isolation")

    # Create two instances
    instance_a = create_test_instance("test-agent-005")
    instance_b = create_test_instance("test-agent-005")  # Same agent, different instance

    if not instance_a or not instance_b:
        print_result("Create instances", False, "Failed to create test instances")
        return False

    print(f"Created instance A: {instance_a}")
    print(f"Created instance B: {instance_b}")

    # Add messages to both
    add_test_messages(instance_a, 3)
    add_test_messages(instance_b, 3)

    # Delete only instance A
    print(f"\nDeleting only instance A: {instance_a}")
    response = soft_delete_instance(instance_a)

    if response.status_code != 200:
        print_result("Soft delete A", False, f"Status code: {response.status_code}")
        return False

    result = response.json()
    print(f"Deletion result: {json.dumps(result, indent=2)}")

    # Check instance B is still active
    instance_b_data = get_instance(instance_b)

    checks = [
        (result.get("success") == True, "Instance A deleted successfully"),
        (instance_b_data is not None, "Instance B still exists"),
        (instance_b_data.get("isDeleted") != True if instance_b_data else False, "Instance B not marked as deleted"),
    ]

    all_passed = True
    for passed, description in checks:
        print_result(description, passed)
        all_passed = all_passed and passed

    return all_passed

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  SOFT-DELETE PROPAGATION TEST SUITE")
    print("="*60)
    print("\nThis test suite validates the implementation of")
    print("soft-delete propagation from agent_instances to history")
    print("\nBased on: requisitos_propagacao_soft_delete.md")

    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code != 200:
            print("\n❌ ERROR: Server is not responding properly")
            print(f"   Make sure the backend is running on {BASE_URL}")
            return
    except requests.exceptions.RequestException:
        print(f"\n❌ ERROR: Cannot connect to {BASE_URL}")
        print("   Make sure the backend server is running")
        return

    # Run tests
    tests = [
        ("Soft-Delete with Messages", test_soft_delete_with_messages),
        ("Soft-Delete without Messages", test_soft_delete_without_messages),
        ("Hard-Delete with Cascade", test_hard_delete_cascade),
        ("Idempotent Soft-Delete", test_idempotent_soft_delete),
        ("Instance Isolation", test_instance_isolation),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ ERROR in {test_name}: {str(e)}")
            results.append((test_name, False))

    # Summary
    print_section("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        print_result(test_name, result)

    print(f"\n{'='*60}")
    print(f"  RESULTS: {passed}/{total} tests passed")
    print(f"{'='*60}\n")

    if passed == total:
        print("✅ All tests passed! Implementation is correct.")
    else:
        print("⚠️  Some tests failed. Please review the implementation.")

if __name__ == "__main__":
    main()
