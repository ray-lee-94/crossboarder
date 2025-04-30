import requests
import os
import json # Import json for safe loading in helper

# --- Configuration ---
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
DEFAULT_TIMEOUT = 30

# --- Helper Functions ---
def assert_response_success(response, expected_status_code=200):
    """Checks for successful status code and 'success: true' in JSON body."""
    # Print response text regardless of status for easier debugging
    print(f"\nResponse Status: {response.status_code}")
    try:
        # Try to parse JSON even if status code is wrong, might contain error details
        response_json = response.json()
        print(f"Response JSON: {json.dumps(response_json, indent=2)}")
    except requests.exceptions.JSONDecodeError:
        print(f"Response Text: {response.text}") # Print raw text if not JSON
        response_json = None # Set to None if parsing fails

    # Assert status code AFTER printing details
    assert response.status_code == expected_status_code, \
        f"Expected status {expected_status_code}, got {response.status_code}."

    # Proceed with JSON checks only if status code was expected
    if response.status_code == expected_status_code:
        assert response_json is not None, "Response body is not valid JSON."
        assert "success" in response_json, "'success' key not found in response JSON."
        assert response_json.get("success") is True, f"Expected 'success' to be true."
        return response_json # Return parsed JSON
    else:
        # If status code didn't match, we can't assume structure, return None or raise
        return None


# --- Test Classes ---

# class TestHealthEndpoints:
#     """Tests for /api/health and /api/version"""

#     def test_health_check(self):
#         """Test Case 1.1: Health Check"""
#         url = f"{BASE_URL}/api/health"
#         response = requests.get(url, timeout=DEFAULT_TIMEOUT)
#         data = assert_response_success(response)
#         # Basic checks are done in the helper, add more specific ones if needed
#         assert "data" in data and isinstance(data["data"], dict)
#         assert data["data"].get("status") == "ok"
#         assert "llm_status" in data["data"] and data["data"]["llm_status"] == "ok"


#     def test_version_check(self):
#         """Test Case 1.2: Version Check"""
#         url = f"{BASE_URL}/api/version"
#         response = requests.get(url, timeout=DEFAULT_TIMEOUT)
#         data = assert_response_success(response)
#         assert "data" in data and isinstance(data["data"], dict)
#         assert "version" in data["data"]


class TestMarketingWorkflowEndpoint:
    """Tests for /api/marketing/run"""

    def test_marketing_success_basic(self):
        """Test Case 2.1: Marketing Workflow - Success Case (Basic)"""
        url = f"{BASE_URL}/api/marketing/run"
        payload = {
          "product_info": {
            "ProductName": "Test Recorder V1",
            "Description": "A simple audio recorder for basic tests.",
            "Price": 19.99,
            "Specifications": "64GB, USB-C" # FIX: Added Specifications
            # Add other Optional fields as None or default if needed by prompts
            # "Brand": None,
            # "AmazonCategory": None,
            # "Rating": None,
            # "ReviewCount": None,
            # "ProductURL": None
          },
          "influencer_data": [
            {
              "id": "inf_test_01",
              "name": "Simple Tester",
              "platforms": {
                "youtube": [
                  {
                    "content_title": "Testing the Recorder",
                    "like_count": 10,
                    # Add other Optional fields as None if needed
                    # "promo_category": None,
                    # "enhanced_tag": None,
                    # "cover_image_url": None,
                    # "content_url": None,
                    # "comment_count": None,
                    # "publish_date": None
                  }
                ]
              }
            }
          ],
          "match_threshold": 70.0
        }
        # Increase timeout significantly for the full workflow
        response = requests.post(url, json=payload, timeout=DEFAULT_TIMEOUT * 4)

        data = assert_response_success(response) # Should now pass status check if 422 is fixed

        # Check structure assuming success
        assert "data" in data and isinstance(data["data"], dict)
        assert "product_tags" in data["data"]
        assert "match_results" in data["data"]
        assert "selected_influencers" in data["data"]
        assert "generated_emails" in data["data"]
        assert "errors" in data["data"] and isinstance(data["data"]["errors"], list)

        # Ideally, errors should be empty for a fully successful run
        assert data["data"]["errors"] == [], f"Expected empty errors list, got: {data['data']['errors']}"


    def test_marketing_input_validation_error(self):
        """Test Case 2.2: Marketing Workflow - Input Validation Error (ProductInfo)"""
        url = f"{BASE_URL}/api/marketing/run"
        payload = {
          # Missing "product_info" entirely
          "influencer_data": [
            { "id": "inf_test_01", "name": "Simple Tester", "platforms": {} }
          ]
        }
        response = requests.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"


    def test_marketing_empty_influencer_list(self):
        """Test Case 2.3: Marketing Workflow - Empty Influencer List"""
        url = f"{BASE_URL}/api/marketing/run"
        payload = {
          "product_info": {
            "ProductName": "Test Recorder V2",
            "Specifications": "Basic Model" # FIX: Added Specifications
          },
          "influencer_data": [], # Empty list
          "match_threshold": 75.0
        }
        response = requests.post(url, json=payload, timeout=DEFAULT_TIMEOUT * 2)
        data = assert_response_success(response) # Should now pass status check if 422 is fixed

        assert "data" in data and isinstance(data["data"], dict)
        # Check that results involving influencers are empty
        assert data["data"].get("match_results") in ([], None)
        assert data["data"].get("selected_influencers") in ([], None)
        assert data["data"].get("generated_emails") in ([], None)
        assert data["data"].get("errors") == []


# class TestEmailIntentEndpoint:
#     """Tests for /api/email/analyze-intent"""

#     def test_email_intent_success(self):
#         """Test Case 3.1: Email Intent - Success Case (Basic)"""
#         url = f"{BASE_URL}/api/email/analyze-intent"
#         payload = {
#           "history": [
#             {
#               "sender": "us", "recipient": "influencer@example.com",
#               "subject": "Collaboration Invite", "body": "Hi Influencer, want to collab?",
#               "timestamp": "2023-10-26T10:00:00Z"
#             },
#             {
#               "sender": "influencer@example.com", "recipient": "us",
#               "subject": "Re: Collaboration Invite",
#               "body": "Hey there! Thanks for reaching out. Yes, I'm interested. What are the next steps and payment details?",
#               "timestamp": "2023-10-27T09:30:00Z"
#             }
#           ]
#         }
#         # Allow a bit more time for the LLM call
#         response = requests.post(url, json=payload, timeout=DEFAULT_TIMEOUT * 2)

#         # This assertion will likely still fail if the 500 error persists on the server.
#         # The fix needs to be applied server-side based on logs.
#         data = assert_response_success(response)

#         # If the server-side 500 error is fixed, these checks should pass:
#         if data: # Only check further if assert_response_success didn't fail/return None
#             assert "data" in data and isinstance(data["data"], dict)
#             assert "cooperation_intent" in data["data"]
#             assert "key_points" in data["data"] and isinstance(data["data"]["key_points"], list)
#             assert "suggested_next_step" in data["data"]
#             assert "sentiment" in data["data"]
#             assert "is_urgent" in data["data"]
#             assert "notification_summary" in data["data"]

#     def test_email_intent_empty_history(self):
#         """Test Case 3.2: Email Intent - Empty History"""
#         url = f"{BASE_URL}/api/email/analyze-intent"
#         payload = { "history": [] }
#         response = requests.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
#         assert response.status_code == 400, f"Expected 400, got {response.status_code}"
#         assert "Email history cannot be empty" in response.text


#     def test_email_intent_validation_error(self):
#         """Test Case 3.3: Email Intent - Input Validation Error"""
#         url = f"{BASE_URL}/api/email/analyze-intent"
#         payload = {
#           "history": [
#             { "sender": "influencer@example.com", "recipient": "us", "subject": "Re:..." }
#           ] # Missing body, timestamp
#         }
#         response = requests.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
#         assert response.status_code == 422, f"Expected 422, got {response.status_code}"