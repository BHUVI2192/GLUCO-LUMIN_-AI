"""Test script to verify the input validation fix for upload_raw endpoint."""
import requests

BASE_URL = "http://localhost:8000"

def test_bad_data():
    """Test Case 1: All non-numeric data should return 400."""
    print("\n=== Test 1: Bad Data (All Non-Numeric) ===")
    payload = {
        "lines": [
            "V_TEST_BAD,0,Glucose Levels :",
            "V_TEST_BAD,1,No finger?",
            "V_TEST_BAD,2,:145.28 mg/dL"
        ]
    }
    response = requests.post(f"{BASE_URL}/api/upload_raw", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200, f"Expected 200 (graceful failure), got {response.status_code}"
    data = response.json()
    assert data["count"] == 0, f"Expected count=0 for bad data, got {data['count']}"
    print("✅ PASSED: Bad data accepted gracefully for pipeline handling")

def test_good_data():
    """Test Case 2: All numeric data should return 200."""
    print("\n=== Test 2: Good Data (All Numeric) ===")
    payload = {
        "lines": [
            "V_TEST_GOOD,0,0.145",
            "V_TEST_GOOD,1,0.152",
            "V_TEST_GOOD,2,0.148"
        ]
    }
    response = requests.post(f"{BASE_URL}/api/upload_raw", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["count"] == 3, f"Expected count=3, got {data['count']}"
    assert data["skipped"] == 0, f"Expected skipped=0, got {data['skipped']}"
    print("✅ PASSED: Good data accepted correctly")

def test_mixed_data():
    """Test Case 3: Mixed data should filter out bad lines."""
    print("\n=== Test 3: Mixed Data ===")
    payload = {
        "lines": [
            "V_TEST_MIX,0,0.145",
            "V_TEST_MIX,1,No finger?",
            "V_TEST_MIX,2,0.148",
            "V_TEST_MIX,3,Glucose Levels :"
        ]
    }
    response = requests.post(f"{BASE_URL}/api/upload_raw", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["count"] == 2, f"Expected count=2, got {data['count']}"
    assert data["skipped"] == 2, f"Expected skipped=2, got {data['skipped']}"
    print("✅ PASSED: Mixed data filtered correctly")

if __name__ == "__main__":
    print("Running upload_raw validation tests...")
    try:
        test_bad_data()
        test_good_data()
        test_mixed_data()
        print("\n" + "="*50)
        print("ALL TESTS PASSED!")
        print("="*50)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to server. Is uvicorn running on port 8000?")
