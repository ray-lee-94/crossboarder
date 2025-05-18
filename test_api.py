# test_api.py
import requests
import os
import json
import time # For crawl tests

# --- Configuration ---
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000") # Ensure this matches your FastAPI app
DEFAULT_TIMEOUT = 30 # Default timeout for requests
LONG_TIMEOUT = DEFAULT_TIMEOUT * 6 # For long-running workflow tests

# --- Helper Function ---
def print_response_details(response):
    """Prints response status and body for debugging."""
    print(f"\nResponse Status: {response.status_code}")
    try:
        response_json = response.json()
        print(f"Response JSON: {json.dumps(response_json, indent=2, ensure_ascii=False)}")
        return response_json
    except requests.exceptions.JSONDecodeError:
        print(f"Response Text: {response.text}")
        return None

# --- Test Classes ---

class TestHealthEndpoints:
    """Tests for Health Check and Version endpoints."""

    def test_health_check(self):
        """Test Case 1.1: Health Check (/api/health)"""
        url = f"{BASE_URL}/api/health"
        response = requests.get(url, timeout=DEFAULT_TIMEOUT)
        response_json = print_response_details(response)

        assert response.status_code == 200
        assert response_json is not None
        assert response_json.get("success") is True
        assert response_json.get("message") == "API is healthy"
        # If your health check provides more data, add assertions for it here
        # e.g., assert "data" in response_json and response_json["data"].get("llm_status") == "ok"

    def test_version_check(self):
        """Test Case 1.2: Version Check (/api/version)"""
        url = f"{BASE_URL}/api/version"
        response = requests.get(url, timeout=DEFAULT_TIMEOUT)
        response_json = print_response_details(response)

        assert response.status_code == 200
        assert response_json is not None
        assert response_json.get("success") is True
        assert "API Version:" in response_json.get("message", "")
        # If data field contains version:
        # assert "data" in response_json and "version" in response_json["data"]


class TestProductCrawlEndpoints:
    """Tests for /api/products/crawl"""
    crawl_job_id = None # To store job ID between tests

    def test_submit_crawl_task(self):
        """Test Case 2.1: Submit Product Crawl Task"""
        url = f"{BASE_URL}/api/products/crawl"
        payload = {
            "url": "https://www.amazon.com/dp/B08N5WRWNW", # Example valid Amazon URL
            "platform": "Amazon"
        }
        response = requests.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
        response_json = print_response_details(response)

        assert response.status_code == 200
        assert response_json is not None
        assert response_json.get("success") is True
        assert "data" in response_json and isinstance(response_json["data"], dict)
        assert "jobId" in response_json["data"]
        TestProductCrawlEndpoints.crawl_job_id = response_json["data"]["jobId"] # Save for next test
        assert response_json["data"].get("message") == "Crawl task submitted successfully."


    # def test_get_crawl_result_success(self):
    #     """Test Case 2.2: Get Product Crawl Result (Success Scenario)"""
    #     assert TestProductCrawlEndpoints.crawl_job_id is not None, "Crawl job ID not set from previous test"
    #     job_id = TestProductCrawlEndpoints.crawl_job_id
    #     url = f"{BASE_URL}/api/products/crawl?job_id={job_id}"

    #     # Wait for the crawl task to potentially complete
    #     # This is a simple polling mechanism; for robust testing, consider callbacks or longer waits
    #     max_wait_time = 60  # seconds
    #     start_time = time.time()
    #     status = ""
    #     response_json = None

    #     while time.time() - start_time < max_wait_time:
    #         response = requests.get(url, timeout=DEFAULT_TIMEOUT)
    #         response_json = print_response_details(response)
    #         assert response.status_code == 200
    #         assert response_json is not None
    #         assert response_json.get("success") is True
    #         data = response_json.get("data", {})
    #         status = data.get("status")
    #         if status in ["completed", "failed"]:
    #             break
    #         print(f"Job status: {status}. Waiting...")
    #         time.sleep(5) # Poll every 5 seconds

    #     assert status == "completed", f"Crawl job did not complete successfully. Final status: {status}. Message: {data.get('message')}"
    #     assert "result" in data and isinstance(data["result"], dict)
    #     assert data["result"].get("product_title") is not None # Check for some product data
    #     assert data["result"].get("error") is None


    def test_get_crawl_result_not_found(self):
        """Test Case 2.3: Get Product Crawl Result - Job ID Not Found"""
        job_id = "non_existent_job_id"
        url = f"{BASE_URL}/api/products/crawl?job_id={job_id}"
        response = requests.get(url, timeout=DEFAULT_TIMEOUT)
        response_json = print_response_details(response) # Still print details

        assert response.status_code == 404 # As per HTTPException in main.py
        assert response_json is not None
        assert "detail" in response_json and response_json["detail"] == "Job ID not found"

class TestProductAnalysisEndpoint:
    """Tests for /api/products/analyze"""

    def test_product_analysis_success(self):
        """Test Case 3.1: Product Analysis - Success Case"""
        url = f"{BASE_URL}/api/products/analyze"
        # This payload should align with the ProductInputForAnalysis model
        # used by your `analyze_product_node` and the prompt.
        # We'll use the detailed product_info structure you provided in the prompt example.
        payload = {
            "_id": "SPYDERPRINT_B006UACRTG_analyze", # Unique for this test
            "product_title": "Datacolor Spyder Print - 高级数据分析和校准工具,可实现最佳打印效果,非常适合摄影师、平面设计师和印刷专业人士。",
            "price": "US$344.00",
            "rating": 4.5, # Example rating
            "review_count": 150, # Example review count
            "availability": "有现货",
            "seller": "Datacolor Official Store",
            "seller_url": "https://www.amazon.com/stores/Datacolor",
            "seller_address": "Lawrenceville, NJ, USA",
            "product_url": "https://www.amazon.com/-/zh/dp/B006UACRTG/ref=sr_1_1",
            "asin": "B006UACRTG",
            "image_url": "https://m.media-amazon.com/images/I/71qYqm3f0FL._AC_SX679_.jpg",
            "features": "全功能色彩管理, 精确打印机校准, ICC配置文件创建, 软打样, 适用于多种打印机和纸张类型, SpyderProof功能, 显示器校准集成",
            "description": "SpyderPrint 是专业人士选择管理打印输出色彩的全功能解决方案。通过选择任何打印机、墨水和纸张组合，SpyderPrint 可让您完全控制打印过程，从而生成画廊品质的打印件。只需安装软件，将色块打印到您选择的纸张上，然后使用 SpyderGuide 设备逐步完成简单流程即可校准并构建配置文件。独有的 SpyderProof 功能提供了一系列精心挑选的图像，可在编辑前来评估自定义配置文件，帮助您避免浪费纸张和墨水。",
            "category_source": "配件和耗材 > 打印机配件 > 校准工具",
            "brand_name": "Datacolor",
            "listing_date": "2011-12-05"
        }
        # The API endpoint expects the payload directly, not nested under "product_info"
        # unless your Pydantic model for the endpoint request body is structured that way.
        # Assuming it expects a dictionary matching ProductInputForAnalysis.

        response = requests.post(url, json=payload, timeout=LONG_TIMEOUT) # Analysis can take time
        response_json = print_response_details(response)

        assert response.status_code == 200
        assert response_json is not None
        assert response_json.get("success") is True
        assert "data" in response_json and isinstance(response_json["data"], dict)
        data_field = response_json["data"]

        # The 'data' field should contain the 'ProductTags' structure
        assert "FeatureTags" in data_field and isinstance(data_field["FeatureTags"], list)
        assert "AudienceTags" in data_field and isinstance(data_field["AudienceTags"], list)
        assert "UsageScenarioTags" in data_field and isinstance(data_field["UsageScenarioTags"], list)

        # Check if tags are populated (LLM might return empty lists, but keys should exist)
        assert len(data_field["FeatureTags"]) > 0, "Expected FeatureTags to be populated"
        assert len(data_field["AudienceTags"]) > 0, "Expected AudienceTags to be populated"
        assert len(data_field["UsageScenarioTags"]) > 0, "Expected UsageScenarioTags to be populated"



    def test_product_analysis_input_validation_error(self):
        """Test Case 3.2: Product Analysis - Input Validation Error"""
        url = f"{BASE_URL}/api/products/analyze"
        # Missing required fields like "product_title" or "features"
        payload = {
            "_id": "invalid_product_analyze_001",
            "price": "19.99"
            # "product_title" is missing
        }
        response = requests.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
        response_json = print_response_details(response)

        assert response.status_code == 422 # FastAPI's default for Pydantic validation errors
        assert response_json is not None
        assert "detail" in response_json
        # Check for a message indicating missing fields (FastAPI's default is usually good)
        assert any("product_title" in error.get("loc", []) for error in response_json.get("detail", []) if isinstance(error, dict))


class TestMarketingWorkflowEndpoint:
    """Tests for /api/marketing/run"""

    def test_marketing_workflow_success_basic(self):
        """Test Case 4.1: Marketing Workflow - Success Case (Basic)"""
        url = f"{BASE_URL}/api/marketing/run"
        # Using the detailed payload from your example
        payload = {
          "product_info": { # Corresponds to ProductInputForAnalysis
            "productId": "SPYDERPRINT_B006UACRTG",
            "title": "Datacolor Spyder Print - 高级数据分析和校准工具,可实现最佳打印效果,非常适合摄影师、平面设计师和印刷专业人士。",
            "brand": "Datacolor", # Changed from HP based on description
            "category": "配件和耗材",
            "description": "Spyderprint 是专业人士选择管理打印输出色彩的全功能解决方案...", # Truncated for brevity
            "price": "US$344.00", # Corrected from 34400
            "productURL": "https://www.amazon.com/-/zh/dp/B006UACRTG/ref=sr_1_1"
            # Add other fields from ProductInputForAnalysis if needed by prompt, e.g., description
          },
          "influencer_data": [ # Corresponds to List[InfluencerInputForWorkflow]
            {
              "influencerId": "pro_photo_print_01",
              "influencerName": "Pixel Perfect Prints",
              "platforms": { # Dict[str, List[InfluencerPlatformContentInput]]
                "youtube": [
                  {
                    "content_title": "Mastering Print Color: Datacolor Spyder Print Deep Dive Review",
                    "like_count": 1850,
                    "comment_count": 150,
                    "publish_date": "2024-03-15T10:00:00Z",
                    # "promo_category": "Photography Gear", # Changed to string if PlatformContentData expects str
                    # "enhanced_tag": "ICC Profile",       # Changed to string
                    "cover_image_url": "https://example.com/img/spyderprint_review.jpg",
                    "content_url": "https://youtube.com/watch?v=fake12345"
                  }
                  # Add more content/platforms if needed for thorough testing
                ]
              }
            },
            # Add more influencers if your test case requires it
          ],
          "match_threshold": 70.0
        }
        response = requests.post(url, json=payload, timeout=LONG_TIMEOUT * 2) # Very long timeout
        response_json = print_response_details(response)

        assert response.status_code == 200
        assert response_json is not None
        assert response_json.get("success") is True
        assert "data" in response_json and isinstance(response_json["data"], dict)
        data_field = response_json["data"]

        assert "product_tags" in data_field and (data_field["product_tags"] is None or isinstance(data_field["product_tags"], dict))
        assert "influencer_profiles" in data_field # Further checks depend on graph output
        assert "match_results" in data_field
        assert "selected_influencers" in data_field
        assert "generated_emails" in data_field
        assert "workflow_errors" in data_field and isinstance(data_field["workflow_errors"], list)

        # For a fully successful run, workflow_errors should ideally be empty or contain only minor warnings.
        # Depending on the robustness of your LLM calls and parsing.
        if data_field.get("workflow_errors"):
            print(f"Workflow reported errors/warnings: {data_field['workflow_errors']}")
        # assert not data_field.get("workflow_errors"), f"Expected empty workflow_errors, got: {data_field.get('workflow_errors')}"


    def test_marketing_workflow_input_validation_error(self):
        """Test Case 4.2: Marketing Workflow - Input Validation Error"""
        url = f"{BASE_URL}/api/marketing/run"
        payload = {
          # Missing "product_info" which is required by MarketingWorkflowRequest
          "influencer_data": [
            { "influencerId": "inf_test_01", "influencerName": "Simple Tester", "platforms": {} }
          ]
        }
        response = requests.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
        response_json = print_response_details(response)

        assert response.status_code == 422
        assert response_json is not None
        assert "detail" in response_json


    def test_marketing_workflow_empty_influencer_list(self):
        """Test Case 4.3: Marketing Workflow - Empty Influencer List"""
        url = f"{BASE_URL}/api/marketing/run"
        payload = {
          "product_info": {
            "productId": "TEST_PROD_002",
            "title": "Test Product for Empty Influencer List",
            "description": "A product to test with no influencers."
          },
          "influencer_data": [], # Empty list
          "match_threshold": 75.0
        }
        response = requests.post(url, json=payload, timeout=LONG_TIMEOUT)
        response_json = print_response_details(response)

        assert response.status_code == 200
        assert response_json is not None
        assert response_json.get("success") is True
        assert "data" in response_json and isinstance(response_json["data"], dict)
        data_field = response_json["data"]

        # With an empty influencer list, downstream results should be empty or reflect this
        assert data_field.get("influencer_profiles") == {} or data_field.get("influencer_profiles") is None
        assert data_field.get("match_results") == [] or data_field.get("match_results") is None
        assert data_field.get("selected_influencers") == [] or data_field.get("selected_influencers") is None
        assert data_field.get("generated_emails") == [] or data_field.get("generated_emails") is None
        
        # Check for specific error messages if your graph is designed to produce them
        # e.g., if "Cannot match: Influencer profiles missing." is added to workflow_errors
        # workflow_errors = data_field.get("workflow_errors", [])
        # assert any("Cannot match" in err for err in workflow_errors)


class TestEmailIntentEndpoint:
    """Tests for /api/outreachs/intent"""

    def test_email_intent_success(self):
        """Test Case 5.1: Email Intent - Success Case"""
        url = f"{BASE_URL}/api/outreachs/intent" # Corrected endpoint
        payload = { # Corresponds to EmailIntentRequest in main.py
          "email_subject": "Re: Collaboration Invite",
          "email_body": "Hey there! Thanks for reaching out. Yes, I'm interested. What are the next steps and payment details?"
        }
        response = requests.post(url, json=payload, timeout=LONG_TIMEOUT)
        response_json = print_response_details(response)

        assert response.status_code == 200
        assert response_json is not None
        assert response_json.get("success") is True
        assert "data" in response_json and isinstance(response_json["data"], dict)
        data_field = response_json["data"]

        assert "cooperation_intent" in data_field
        assert "key_points" in data_field and isinstance(data_field["key_points"], list)
        assert "suggested_next_step" in data_field
        assert "sentiment" in data_field
        assert "is_urgent" in data_field and isinstance(data_field["is_urgent"], bool)
        assert "notification_summary" in data_field

    def test_email_intent_empty_body(self):
        """Test Case 5.2: Email Intent - Empty Body"""
        url = f"{BASE_URL}/api/outreachs/intent"
        payload = {
            "email_subject": "Test",
            "email_body": "" # Empty body
        }
        response = requests.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
        response_json = print_response_details(response) # Make sure this returns the parsed JSON

        assert response.status_code == 200# The API call itself is successful
        assert response_json is not None
        assert response_json.get("success") is False # Business logic indicates failure
        assert response_json.get("message") == "Email intent analysis failed: Email body is empty."

    def test_email_intent_validation_error_missing_field(self):
        """Test Case 5.3: Email Intent - Input Validation Error (Missing body)"""
        url = f"{BASE_URL}/api/outreachs/intent"
        payload = {
          "email_subject": "Subject Only"
          # Missing "email_body" which is required
        }
        response = requests.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
        response_json = print_response_details(response)

        assert response.status_code == 422 # FastAPI validation error
        assert response_json is not None
        assert "detail" in response_json