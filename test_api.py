# test_api.py
import requests
import os
import json
import pytest
import time # For crawl tests
from typing import List, Dict

from main import InfluencerAnalysisRequest, InfluencerPlatformContentInput, InfluencerAnalysisResponseData, InfluencerProfile, ResponseModel, EmailCreationRequest, GeneratedEmail, EmailGenerationState, InfluencerInputForWorkflow,InfluencerAnalysisRequest, ProductInputForAnalysis
from graph_state import PlatformContentData, ProductTags, InfluencerRecommendationRequest, MatchResult, MarketingWorkFlowState

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

# class TestHealthEndpoints:
#     """Tests for Health Check and Version endpoints."""

#     def test_health_check(self):
#         """Test Case 1.1: Health Check (/api/health)"""
#         url = f"{BASE_URL}/api/health"
#         response = requests.get(url, timeout=DEFAULT_TIMEOUT)
#         response_json = print_response_details(response)

#         assert response.status_code == 200
#         assert response_json is not None
#         assert response_json.get("success") is True
#         assert response_json.get("message") == "API is healthy"
#         # If your health check provides more data, add assertions for it here
#         # e.g., assert "data" in response_json and response_json["data"].get("llm_status") == "ok"

#     def test_version_check(self):
#         """Test Case 1.2: Version Check (/api/version)"""
#         url = f"{BASE_URL}/api/version"
#         response = requests.get(url, timeout=DEFAULT_TIMEOUT)
#         response_json = print_response_details(response)

#         assert response.status_code == 200
#         assert response_json is not None
#         assert response_json.get("success") is True
#         assert "API Version:" in response_json.get("message", "")
#         # If data field contains version:
#         # assert "data" in response_json and "version" in response_json["data"]


# class TestProductCrawlEndpoints:
#     """Tests for /api/products/crawl"""
#     crawl_job_id = None # To store job ID between tests

#     def test_submit_crawl_task(self):
#         """Test Case 2.1: Submit Product Crawl Task"""
#         url = f"{BASE_URL}/api/products/crawl"
#         payload = {
#             "url": "https://www.amazon.com/dp/B08N5WRWNW", # Example valid Amazon URL
#             "platform": "Amazon"
#         }
#         response = requests.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
#         response_json = print_response_details(response)

#         assert response.status_code == 200
#         assert response_json is not None
#         assert response_json.get("success") is True
#         assert "data" in response_json and isinstance(response_json["data"], dict)
#         assert "jobId" in response_json["data"]
#         TestProductCrawlEndpoints.crawl_job_id = response_json["data"]["jobId"] # Save for next test
#         assert response_json["data"].get("message") == "Crawl task submitted successfully."


#     def test_get_crawl_result_success(self):
#         """Test Case 2.2: Get Product Crawl Result (Success Scenario)"""
#         assert TestProductCrawlEndpoints.crawl_job_id is not None, "Crawl job ID not set from previous test"
#         job_id = TestProductCrawlEndpoints.crawl_job_id
#         url = f"{BASE_URL}/api/products/crawl?job_id={job_id}"

#         # Wait for the crawl task to potentially complete
#         # This is a simple polling mechanism; for robust testing, consider callbacks or longer waits
#         max_wait_time = 60  # seconds
#         start_time = time.time()
#         status = ""
#         response_json = None

#         while time.time() - start_time < max_wait_time:
#             response = requests.get(url, timeout=DEFAULT_TIMEOUT)
#             response_json = print_response_details(response)
#             assert response.status_code == 200
#             assert response_json is not None
#             assert response_json.get("success") is True
#             data = response_json.get("data", {})
#             status = data.get("status")
#             if status in ["completed", "failed"]:
#                 break
#             print(f"Job status: {status}. Waiting...")
#             time.sleep(5) # Poll every 5 seconds

#         assert status == "completed", f"Crawl job did not complete successfully. Final status: {status}. Message: {data.get('message')}"
#         assert "result" in data and isinstance(data["result"], dict)
#         assert data["result"].get("product_title") is not None # Check for some product data
#         assert data["result"].get("error") is None


#     def test_get_crawl_result_not_found(self):
#         """Test Case 2.3: Get Product Crawl Result - Job ID Not Found"""
#         job_id = "non_existent_job_id"
#         url = f"{BASE_URL}/api/products/crawl?job_id={job_id}"
#         response = requests.get(url, timeout=DEFAULT_TIMEOUT)
#         response_json = print_response_details(response) # Still print details

#         assert response.status_code == 404 # As per HTTPException in main.py
#         assert response_json is not None
#         assert "detail" in response_json and response_json["detail"] == "Job ID not found"

# class TestProductAnalysisEndpoint:
#     """Tests for /api/products/analyze"""

#     def test_product_analysis_success(self):
#         """Test Case 3.1: Product Analysis - Success Case"""
#         url = f"{BASE_URL}/api/products/analyze"
#         # This payload should align with the ProductInputForAnalysis model
#         # used by your `analyze_product_node` and the prompt.
#         # We'll use the detailed product_info structure you provided in the prompt example.
#         payload = {
#             "_id": "SPYDERPRINT_B006UACRTG_analyze", # Unique for this test
#             "product_title": "Datacolor Spyder Print - 高级数据分析和校准工具,可实现最佳打印效果,非常适合摄影师、平面设计师和印刷专业人士。",
#             "price": "US$344.00",
#             "rating": 4.5, # Example rating
#             "review_count": 150, # Example review count
#             "availability": "有现货",
#             "seller": "Datacolor Official Store",
#             "seller_url": "https://www.amazon.com/stores/Datacolor",
#             "seller_address": "Lawrenceville, NJ, USA",
#             "product_url": "https://www.amazon.com/-/zh/dp/B006UACRTG/ref=sr_1_1",
#             "asin": "B006UACRTG",
#             "image_url": "https://m.media-amazon.com/images/I/71qYqm3f0FL._AC_SX679_.jpg",
#             "features": "全功能色彩管理, 精确打印机校准, ICC配置文件创建, 软打样, 适用于多种打印机和纸张类型, SpyderProof功能, 显示器校准集成",
#             "description": "SpyderPrint 是专业人士选择管理打印输出色彩的全功能解决方案。通过选择任何打印机、墨水和纸张组合，SpyderPrint 可让您完全控制打印过程，从而生成画廊品质的打印件。只需安装软件，将色块打印到您选择的纸张上，然后使用 SpyderGuide 设备逐步完成简单流程即可校准并构建配置文件。独有的 SpyderProof 功能提供了一系列精心挑选的图像，可在编辑前来评估自定义配置文件，帮助您避免浪费纸张和墨水。",
#             "category_source": "配件和耗材 > 打印机配件 > 校准工具",
#             "brand_name": "Datacolor",
#             "listing_date": "2011-12-05"
#         }
#         # The API endpoint expects the payload directly, not nested under "product_info"
#         # unless your Pydantic model for the endpoint request body is structured that way.
#         # Assuming it expects a dictionary matching ProductInputForAnalysis.

#         response = requests.post(url, json=payload, timeout=LONG_TIMEOUT) # Analysis can take time
#         response_json = print_response_details(response)

#         assert response.status_code == 200
#         assert response_json is not None
#         assert response_json.get("success") is True
#         assert "data" in response_json and isinstance(response_json["data"], dict)
#         data_field = response_json["data"]

#         # The 'data' field should contain the 'ProductTags' structure
#         assert "FeatureTags" in data_field and isinstance(data_field["FeatureTags"], list)
#         assert "AudienceTags" in data_field and isinstance(data_field["AudienceTags"], list)
#         assert "UsageScenarioTags" in data_field and isinstance(data_field["UsageScenarioTags"], list)

#         # Check if tags are populated (LLM might return empty lists, but keys should exist)
#         assert len(data_field["FeatureTags"]) > 0, "Expected FeatureTags to be populated"
#         assert len(data_field["AudienceTags"]) > 0, "Expected AudienceTags to be populated"
#         assert len(data_field["UsageScenarioTags"]) > 0, "Expected UsageScenarioTags to be populated"



#     def test_product_analysis_input_validation_error(self):
#         """Test Case 3.2: Product Analysis - Input Validation Error"""
#         url = f"{BASE_URL}/api/products/analyze"
#         # Missing required fields like "product_title" or "features"
#         payload = {
#             "_id": "invalid_product_analyze_001",
#             "price": "19.99"
#             # "product_title" is missing
#         }
#         response = requests.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
#         response_json = print_response_details(response)

#         assert response.status_code == 422 # FastAPI's default for Pydantic validation errors
#         assert response_json is not None
#         assert "detail" in response_json
#         # Check for a message indicating missing fields (FastAPI's default is usually good)
#         assert any("product_title" in error.get("loc", []) for error in response_json.get("detail", []) if isinstance(error, dict))


# class TestMarketingWorkflowEndpoint:
#     """Tests for /api/marketing/run"""

#     def test_marketing_workflow_success_basic(self):
#         """Test Case 4.1: Marketing Workflow - Success Case (Basic)"""
#         url = f"{BASE_URL}/api/marketing/run"
#         # Using the detailed payload from your example
#         payload = {
#           "product_info": { # Corresponds to ProductInputForAnalysis
#             "productId": "SPYDERPRINT_B006UACRTG",
#             "title": "Datacolor Spyder Print - 高级数据分析和校准工具,可实现最佳打印效果,非常适合摄影师、平面设计师和印刷专业人士。",
#             "brand": "Datacolor", # Changed from HP based on description
#             "category": "配件和耗材",
#             "description": "Spyderprint 是专业人士选择管理打印输出色彩的全功能解决方案...", # Truncated for brevity
#             "price": "US$344.00", # Corrected from 34400
#             "productURL": "https://www.amazon.com/-/zh/dp/B006UACRTG/ref=sr_1_1"
#             # Add other fields from ProductInputForAnalysis if needed by prompt, e.g., description
#           },
#           "influencer_data": [ # Corresponds to List[InfluencerInputForWorkflow]
#             {
#               "influencerId": "pro_photo_print_01",
#               "influencerName": "Pixel Perfect Prints",
#               "platforms": { # Dict[str, List[InfluencerPlatformContentInput]]
#                 "youtube": [
#                   {
#                     "content_title": "Mastering Print Color: Datacolor Spyder Print Deep Dive Review",
#                     "like_count": 1850,
#                     "comment_count": 150,
#                     "publish_date": "2024-03-15T10:00:00Z",
#                     # "promo_category": "Photography Gear", # Changed to string if PlatformContentData expects str
#                     # "enhanced_tag": "ICC Profile",       # Changed to string
#                     "cover_image_url": "https://example.com/img/spyderprint_review.jpg",
#                     "content_url": "https://youtube.com/watch?v=fake12345"
#                   }
#                   # Add more content/platforms if needed for thorough testing
#                 ]
#               }
#             },
#             # Add more influencers if your test case requires it
#           ],
#           "match_threshold": 70.0
#         }
#         response = requests.post(url, json=payload, timeout=LONG_TIMEOUT * 2) # Very long timeout
#         response_json = print_response_details(response)

#         assert response.status_code == 200
#         assert response_json is not None
#         assert response_json.get("success") is True
#         assert "data" in response_json and isinstance(response_json["data"], dict)
#         data_field = response_json["data"]

#         assert "product_tags" in data_field and (data_field["product_tags"] is None or isinstance(data_field["product_tags"], dict))
#         assert "influencer_profiles" in data_field # Further checks depend on graph output
#         assert "match_results" in data_field
#         assert "selected_influencers" in data_field
#         assert "generated_emails" in data_field
#         assert "workflow_errors" in data_field and isinstance(data_field["workflow_errors"], list)

#         # For a fully successful run, workflow_errors should ideally be empty or contain only minor warnings.
#         # Depending on the robustness of your LLM calls and parsing.
#         if data_field.get("workflow_errors"):
#             print(f"Workflow reported errors/warnings: {data_field['workflow_errors']}")
#         # assert not data_field.get("workflow_errors"), f"Expected empty workflow_errors, got: {data_field.get('workflow_errors')}"


#     def test_marketing_workflow_input_validation_error(self):
#         """Test Case 4.2: Marketing Workflow - Input Validation Error"""
#         url = f"{BASE_URL}/api/marketing/run"
#         payload = {
#           # Missing "product_info" which is required by MarketingWorkflowRequest
#           "influencer_data": [
#             { "influencerId": "inf_test_01", "influencerName": "Simple Tester", "platforms": {} }
#           ]
#         }
#         response = requests.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
#         response_json = print_response_details(response)

#         assert response.status_code == 422
#         assert response_json is not None
#         assert "detail" in response_json


#     def test_marketing_workflow_empty_influencer_list(self):
#         """Test Case 4.3: Marketing Workflow - Empty Influencer List"""
#         url = f"{BASE_URL}/api/marketing/run"
#         payload = {
#           "product_info": {
#             "productId": "TEST_PROD_002",
#             "title": "Test Product for Empty Influencer List",
#             "description": "A product to test with no influencers."
#           },
#           "influencer_data": [], # Empty list
#           "match_threshold": 75.0
#         }
#         response = requests.post(url, json=payload, timeout=LONG_TIMEOUT)
#         response_json = print_response_details(response)

#         assert response.status_code == 200
#         assert response_json is not None
#         assert response_json.get("success") is True
#         assert "data" in response_json and isinstance(response_json["data"], dict)
#         data_field = response_json["data"]

#         # With an empty influencer list, downstream results should be empty or reflect this
#         assert data_field.get("influencer_profiles") == {} or data_field.get("influencer_profiles") is None
#         assert data_field.get("match_results") == [] or data_field.get("match_results") is None
#         assert data_field.get("selected_influencers") == [] or data_field.get("selected_influencers") is None
#         assert data_field.get("generated_emails") == [] or data_field.get("generated_emails") is None
        
#         # Check for specific error messages if your graph is designed to produce them
#         # e.g., if "Cannot match: Influencer profiles missing." is added to workflow_errors
#         # workflow_errors = data_field.get("workflow_errors", [])
#         # assert any("Cannot match" in err for err in workflow_errors)


# class TestEmailIntentEndpoint:
#     """Tests for /api/outreachs/intent"""

#     def test_email_intent_success(self):
#         """Test Case 5.1: Email Intent - Success Case"""
#         url = f"{BASE_URL}/api/outreachs/intent" # Corrected endpoint
#         payload = { # Corresponds to EmailIntentRequest in main.py
#           "email_subject": "Re: Collaboration Invite",
#           "email_body": "Hey there! Thanks for reaching out. Yes, I'm interested. What are the next steps and payment details?"
#         }
#         response = requests.post(url, json=payload, timeout=LONG_TIMEOUT)
#         response_json = print_response_details(response)

#         assert response.status_code == 200
#         assert response_json is not None
#         assert response_json.get("success") is True
#         assert "data" in response_json and isinstance(response_json["data"], dict)
#         data_field = response_json["data"]

#         assert "cooperation_intent" in data_field
#         assert "key_points" in data_field and isinstance(data_field["key_points"], list)
#         assert "suggested_next_step" in data_field
#         assert "sentiment" in data_field
#         assert "is_urgent" in data_field and isinstance(data_field["is_urgent"], bool)
#         assert "notification_summary" in data_field

#     def test_email_intent_empty_body(self):
#         """Test Case 5.2: Email Intent - Empty Body"""
#         url = f"{BASE_URL}/api/outreachs/intent"
#         payload = {
#             "email_subject": "Test",
#             "email_body": "" # Empty body
#         }
#         response = requests.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
#         response_json = print_response_details(response) # Make sure this returns the parsed JSON

#         assert response.status_code == 200# The API call itself is successful
#         assert response_json.get("detail") == "Email intent analysis failed: Email body is empty."

#     def test_email_intent_validation_error_missing_field(self):
#         """Test Case 5.3: Email Intent - Input Validation Error (Missing body)"""
#         url = f"{BASE_URL}/api/outreachs/intent"
#         payload = {
#           "email_subject": "Subject Only"
#           # Missing "email_body" which is required
#         }
#         response = requests.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
#         response_json = print_response_details(response)

#         assert response.status_code == 422 # FastAPI validation error
#         assert response_json is not None
#         assert "detail" in response_json


class TestAnalyzeInfluencerDetailsEndpoint:

    def test_analyze_influencer_details_success_single_influencer(self,):
        """Test successful analysis for a single influencer with content."""

        url = f"{BASE_URL}/api/influencers/analyze"
        payload =InfluencerAnalysisRequest(influencer_data=[InfluencerInputForWorkflow(
                    influencerId="inf_test_001",
                    influencerName="TechExplorer",
                    platforms={
                        "youtube": [
                              InfluencerPlatformContentInput(
                                content_title="Reviewing the new SuperPhone X!", 
                                like_count=1200, 
                                comment_count=150, 
                                publish_date="2023-11-01", 
                                promo_category="Smartphones",
                                cover_image_url="http://example.com/image1.jpg" # Test HttpUrl serialization
                            ),
                            InfluencerPlatformContentInput(
                                content_title="My Top 5 Productivity Apps", 
                                like_count=800, 
                                comment_count=90, 
                                publish_date="2023-10-15",
                                enhanced_tag="productivity, apps"
                            )
                        ],
                        "tiktok": [
                             InfluencerPlatformContentInput(
                                content_title="Quick look: SuperPhone X camera", 
                                like_count=5000, 
                                comment_count=250, 
                                publish_date="2023-11-02"
                            )
                        ]
                    }
        )]).model_dump(mode="json") # Ensures HttpUrl becomes string
        
        response = requests.post(url, json=payload, timeout=LONG_TIMEOUT*2)
        response_json = print_response_details(response)

        assert response.status_code == 200
        assert response_json["success"] is True
        assert response_json.get("message") == "Influencer analysis completed."
        assert "data" in response_json and response_json["data"] is not None
        
        # Validate the structure of the data field using the specific response data model
        response_data_obj = InfluencerAnalysisResponseData(**response_json["data"])
        assert response_data_obj.influencer_profiles is not None
        assert isinstance(response_data_obj.influencer_profiles, dict)
        assert response_data_obj.influencer_details is not None
        assert isinstance(response_data_obj.influencer_details, dict)
        assert "inf_test_001" in response_data_obj.influencer_profiles
        assert "inf_test_001" in response_data_obj.influencer_details
        profile = response_data_obj.influencer_profiles["inf_test_001"]
        assert len(profile.coreContentDirection) > 0, "Expected LLM to derive core content direction"
        assert profile.overallPersonaAndStyle is not None, "Expected LLM to derive persona/style"
        # Add more assertions based on expected LLM output for the given content

    # def test_analyze_influencer_details_multiple_influencers(self,):
    #     """Test successful analysis for multiple influencers."""
    #     url = f"{BASE_URL}/api/influencers/analyze-details"
    #     payload = InfluencerAnalysisRequest(
    #         influencers_input_data=[
    #             InfluencerPlatformContentInput(
    #                 influencerId="inf_multi_A", influencerName="AlphaVlogger",
    #                 platforms={"youtube": [ PlatformContentData(content_title="Alpha's Day")]}
    #             ),
    #             InfluencerPlatformContentInput(
    #                 influencerId="inf_multi_B", influencerName="BetaGamer",
    #                 platforms={"twitch": [PlatformContentData(content_title="Beta's Game Stream")]}
    #             )
    #         ]
    #     ).model_dump(mode="json")

    #     response = requests.post(url, json=payload, timeout=LONG_TIMEOUT)
    #     response_json = print_response_details(response)

    #     assert response.status_code == 200
    #     assert response_json["success"] is True
    #     assert "data" in response_json and response_json["data"] is not None
    #     response_data_obj = InfluencerAnalysisResponseData(**response_json["data"])
    #     assert response_data_obj.influencer_profiles is not None
    #     assert len(response_data_obj.influencer_profiles) == 2
    #     assert "inf_multi_A" in response_data_obj.influencer_profiles
    #     assert "inf_multi_B" in response_data_obj.influencer_profiles
    #     assert response_data_obj.influencer_profiles["inf_multi_A"].coreContentDirection is not None
    #     assert response_data_obj.influencer_profiles["inf_multi_B"].coreContentDirection is not None

    # def test_analyze_influencer_details_no_platform_content(self):
    #     """Test analysis for an influencer with no platform content provided."""
    #     url = f"{BASE_URL}/api/influencers/analyze-details"
    #     payload = InfluencerAnalysisRequest(
    #         influencers_input_data=[
    #             InfluencerPlatformContentInput(
    #                 influencerId="inf_no_content_002",
    #                 influencerName="SilentCreator",
    #                 platforms={} # Empty platforms dict
    #             )
    #         ]
    #     ).model_dump(mode="json")

    #     response = requests.post(url, json=payload, timeout=LONG_TIMEOUT) # LLM might still run
    #     response_json = print_response_details(response)

    #     assert response.status_code == 200
    #     assert response_json["success"] is True # The process itself might complete
    #     assert "data" in response_json and response_json["data"] is not None
    #     response_data_obj = InfluencerAnalysisResponseData(**response_json["data"])
    #     assert response_data_obj.influencer_profiles is not None
    #     assert "inf_no_content_002" in response_data_obj.influencer_profiles
    #     profile = response_data_obj.influencer_profiles["inf_no_content_002"]
    #     # Expect "无法判断" or empty lists for fields derived from content
    #     assert not profile.coreContentDirection or \
    #            any("无法判断" in item.lower() for item in profile.coreContentDirection) # Be flexible with LLM
    #     assert profile.overallPersonaAndStyle is None or "无法判断" in profile.overallPersonaAndStyle.lower()
    #     # The API returns the profile object even if it's mostly "unable to determine"

    # def test_analyze_influencer_details_empty_input_list(self):
    #     """Test analysis with an empty list of influencers."""
    #     url = f"{BASE_URL}/api/influencers/analyze-details"
    #     payload = InfluencerAnalysisRequest(
    #         influencers_input_data=[] # Empty list
    #     ).model_dump(mode="json")

    #     response = requests.post(url, json=payload, timeout=LONG_TIMEOUT) # Should be fast
    #     response_json = print_response_details(response)

    #     assert response.status_code == 200
    #     assert response_json["success"] is True
    #     assert response_json.get("message") == "Influencer analysis completed."
    #     assert "data" in response_json and response_json["data"] is not None
    #     response_data_obj = InfluencerAnalysisResponseData(**response_json["data"])
    #     assert response_data_obj.influencer_profiles is not None
    #     assert len(response_data_obj.influencer_profiles) == 0 # No profiles generated

    # def test_analyze_influencer_details_input_validation_error(self):
    #     """Test with malformed input (e.g., missing 'influencers_input_data')."""
    #     url = f"{BASE_URL}/api/influencers/analyze-details"
    #     payload = {
    #         "some_other_key": "some_value" 
    #         # influencers_input_data is missing
    #     }
    #     response = requests.post(url, json=payload, timeout=LONG_TIMEOUT)
    #     response_json = print_response_details(response)

    #     assert response.status_code == 422 # Pydantic validation error
    #     assert response_json["detail"][0]["msg"] == "Field required" # Or similar Pydantic message
    #     assert response_json["detail"][0]["loc"] == ["body", "influencers_input_data"]

    # def test_analyze_influencer_details_partial_error_in_graph(self):
    #     """
    #     Test scenario where one influencer analysis succeeds and another fails within the graph.
    #     This depends on how your graph collects and reports errors.
    #     The current API endpoint returns success=False if ANY errors are present in error_messages.
    #     """
    #     url = f"{BASE_URL}/api/influencers/analyze-details"
    #     # To simulate an error, one might have invalid content data that causes an LLM issue for one influencer
    #     # but not the other. This is hard to reliably mock without deeper graph instrumentation.
    #     # For now, let's assume if the graph returns any error_messages, success becomes False.
        
    #     # This test is more conceptual for this API structure.
    #     # If you had a way to inject an error for one influencer in the mock LLM, this would be more concrete.
    #     # Let's test the API's behavior if the graph returns errors.
    #     # We can't directly make the graph fail partially via API input here easily.
    #     # So, this test case is more about verifying the API's error reporting logic if the graph *were* to produce partial errors.
    #     # The current endpoint logic: `success=True if not errors else False`
        
    #     # Simulating a case where the graph might populate `errors` but still produce some profiles.
    #     # This would require mocking the `influencer_app.invoke` call.
    #     # For an integration test, we expect the LLM to work or fail fully for each item based on input quality.
    #     # Let's assume the LLM fails for one influencer due to bad (e.g., too long, nonsensical) content.
    #     payload = InfluencerAnalysisRequest(
    #         influencers_input_data=[
    #             InfluencerPlatformContentInput(
    #                 influencerId="inf_good_003", influencerName="GoodInfluencer",
    #                 platforms={"youtube": [PlatformContentData(content_title="Valid short content")]}
    #             ),
    #             InfluencerPlatformContentInput(
    #                 influencerId="inf_bad_content_004", influencerName="BadContentInfluencer",
    #                 # Assume this content is so bad/long it makes the LLM error out for this item only.
    #                 # This is hard to guarantee without mocking the LLM.
    #                 platforms={"youtube": [PlatformContentData(content_title="Extremely long gibberish..." * 10000)]}
    #             )
    #         ]
    #     ).model_dump(mode="json")

    #     response = requests.post(url, json=payload, timeout=LONG_TIMEOUT* 2) # Longer timeout for potentially slow error
    #     response_json = print_response_details(response)

    #     assert response.status_code == 200 # API call itself is fine
    #     # If the graph node adds to `error_messages` for inf_bad_content_004
    #     if response_json["errors"]:
    #         assert response_json["success"] is False
    #         assert "Influencer analysis completed with some errors." in response_json["message"]
    #         assert len(response_json["errors"]) > 0
    #     else:
    #         # If LLM somehow processes both without error (unlikely with truly bad input)
    #         assert response_json["success"] is True

    #     assert "data" in response_json and response_json["data"] is not None
    #     response_data_obj = InfluencerAnalysisResponseData(**response_json["data"])
    #     assert response_data_obj.influencer_profiles is not None
        
    #     # We expect a profile for the good one, maybe not for the bad one, or a minimal one.
    #     assert "inf_good_003" in response_data_obj.influencer_profiles
    #     if "inf_bad_content_004" in response_data_obj.influencer_profiles:
    #         # It might still create a profile entry even if analysis had issues for that specific one.
    #         pass 
    #         # print("Profile for 'inf_bad_content_004' was created despite potentially bad input.")


# class TestRecommendInfluencersEndpoint:
#     """Tests for /api/influencers/recommend"""

#     # Using fixtures for sample data can make tests cleaner
#     @pytest.fixture
#     def tech_product_tags(self) -> ProductTags:
#         return ProductTags(
#         FeatureTags=["High Performance", "AI-Powered"], # Product's own features
#         AudienceTags=["Professionals", "Early Adopters"], # Product's direct audience
#         UsageScenarioTags=["Work", "Productivity"], # Product's usage
#         coreContentDirection=["Tech Reviews", "Gadget Unboxing", "Software Tutorials"], # Ideal Influencer
#         overallPersonaAndStyle="Informative", # Ideal Influencer
#         mainAudience="Tech Enthusiasts" # Ideal Influencer
#     )

#     @pytest.fixture
#     def product_info(self)-> ProductInputForAnalysis:
#         return   ProductInputForAnalysis( _id="SPYDERPRINT_B006UACRTG_analyze", # Unique for this test
#             product_title= "Datacolor Spyder Print - 高级数据分析和校准工具,可实现最佳打印效果,非常适合摄影师、平面设计师和印刷专业人士。",
#             price= "US$344.00",
#             rating= 4.5, # Example rating
#             review_count= 150, # Example review count
#             availability= "有现货",
#             seller= "Datacolor Official Store",
#             seller_url= "https://www.amazon.com/stores/Datacolor",
#             seller_address= "Lawrenceville, NJ, USA",
#             product_url= "https://www.amazon.com/-/zh/dp/B006UACRTG/ref=sr_1_1",
#             asin= "B006UACRTG",
#             image_url= "https://m.media-amazon.com/images/I/71qYqm3f0FL._AC_SX679_.jpg",
#             features= "全功能色彩管理, 精确打印机校准, ICC配置文件创建, 软打样, 适用于多种打印机和纸张类型, SpyderProof功能, 显示器校准集成",
#             description= "SpyderPrint 是专业人士选择管理打印输出色彩的全功能解决方案。通过选择任何打印机、墨水和纸张组合，SpyderPrint 可让您完全控制打印过程，从而生成画廊品质的打印件。只需安装软件，将色块打印到您选择的纸张上，然后使用 SpyderGuide 设备逐步完成简单流程即可校准并构建配置文件。独有的 SpyderProof 功能提供了一系列精心挑选的图像，可在编辑前来评估自定义配置文件，帮助您避免浪费纸张和墨水。",
#             category_source= "配件和耗材 > 打印机配件 > 校准工具",
#             brand_name= "Datacolor",
#             listing_date= "2011-12-05").model_dump(mode="json")


#     @pytest.fixture
#     def sample_influencer_profiles_for_reco(self) -> Dict[str, InfluencerProfile]:
#     # Ensure these profiles have ALL required fields for InfluencerProfile
#         return {
#             "inf_tech_A": InfluencerProfile(
#                 influencerId="inf_tech_A", influencerName="AnnaTheAnalyzer",
#                 coreContentDirection=["Tech Reviews", "Software Deep Dives", "AI Ethics"],
#                 overallPersonaAndStyle="Analytical and Detailed",
#                 mainAudience="Developers, IT Pros, Academics",
#                 commercialDegree="中度商业化", crossPlatformConsist="高度一致",
#                 potentialBrandType=["Software", "Cloud Services", "AI Tools"],
#                 influencerEval="Highly respected, niche audience", goodsCarryRating="中"
#             ),
#             "inf_lifestyle_B": InfluencerProfile(
#                 influencerId="inf_lifestyle_B", influencerName="BennyVlogs",
#                 coreContentDirection=["Lifestyle", "Travel Vlogs", "Food Challenges"],
#                 overallPersonaAndStyle="Casual and Fun",
#                 mainAudience="General Audience (18-30), Travel Fans",
#                 commercialDegree="高度商业化", crossPlatformConsist="平台差异化明显",
#                 potentialBrandType=["Fashion", "Travel Gear", "Consumer Goods"],
#                 influencerEval="Broad appeal, high engagement", goodsCarryRating="高"
#             ),
#             "inf_tech_C": InfluencerProfile(
#                 influencerId="inf_tech_C", influencerName="ChrisGadgets",
#                 coreContentDirection=["Gadget Unboxing", "Quick Tech Tips", "Gaming Gear Reviews"],
#                 overallPersonaAndStyle="Enthusiastic and Quick Paced",
#                 mainAudience="Gamers, Gadget Lovers, Tech Hobbyists",
#                 commercialDegree="频繁推广", crossPlatformConsist="基本一致",
#                 potentialBrandType=["Gaming Peripherals", "Smart Home", "Consumer Electronics"],
#                 influencerEval="Very popular, trendy content", goodsCarryRating="高"
#             )
#         }


#     def test_recommend_influencers_success(
#         self,product_info, tech_product_tags, sample_influencer_profiles_for_reco
#     ):
#         """Test Case 6.1: Successful influencer recommendation with matches."""
#         url = f"{BASE_URL}/api/influencers/recommend"
        
#         request_payload_model = InfluencerRecommendationRequest(
#             product_info=product_info,
#             product_tags=tech_product_tags,
#             influencer_profiles_input=sample_influencer_profiles_for_reco,
#             match_threshold=65.0 # Expecting Anna and Chris
#         )
#         payload = request_payload_model.model_dump(mode="json")

#         response = requests.post(url, json=payload, timeout=LONG_TIMEOUT)
#         response_json = print_response_details(response)

#         assert response.status_code == 200
#         api_response = ResponseModel(**response_json)
#         assert api_response.success is True
        
#     def test_recommend_influencers_no_matches(
#         self,  sample_influencer_profiles_for_reco
#     ):
#         """Test Case 6.2: Recommendation when no influencers meet the criteria."""
#         url = f"{BASE_URL}/api/influencers/recommend"
        
#         # Product tags for a very niche, non-tech product
#         niche_product_tags = ProductTags(
#             coreContentDirection=["Antique Doll Collecting", "Historical Crafts"],
#             overallPersonaAndStyle=["Academic", "Nostalgic"],
#             mainAudience=["Collectors (50+)", "History Buffs"]
#         )
#         request_payload_model = InfluencerRecommendationRequest(
#             product_tags=niche_product_tags,
#             influencer_profiles_input=sample_influencer_profiles_for_reco, # Using tech influencers
#             match_threshold=50.0
#         )
#         payload = request_payload_model.model_dump(mode="json")

#         response = requests.post(url, json=payload, timeout=LONG_TIMEOUT)
#         response_json = print_response_details(response)

#         assert response.status_code == 200
#         api_response = ResponseModel(**response_json)
#         assert api_response.success is True # Process completes, even with no matches
#         assert api_response.data is not None
#         recommendation_data =MarketingWorkFlowState(**api_response.data)
#         assert recommendation_data.selected_influencers is not None
#         assert len(recommendation_data.selected_influencers) == 0

#     def test_recommend_influencers_empty_profiles_input(
#         self,  tech_product_tags
#     ):
#         """Test Case 6.3: Recommendation with empty influencer_profiles_input."""
#         url = f"{BASE_URL}/api/influencers/recommend"
#         request_payload_model = InfluencerRecommendationRequest(
#             product_tags=tech_product_tags,
#             influencer_profiles_input={}, # Empty
#             match_threshold=70.0
#         )
#         payload = request_payload_model.model_dump(mode="json")

#         response = requests.post(url, json=payload, timeout=LONG_TIMEOUT)
#         response_json = print_response_details(response)

#         assert response.status_code == 200
#         api_response = ResponseModel(**response_json)
#         assert api_response.success is True # Process completes
#         assert api_response.data is not None
#         recommendation_data =MarketingWorkFlowState(**api_response.data)
#         assert recommendation_data.selected_influencers is not None
#         assert len(recommendation_data.selected_influencers) == 0

#     def test_recommend_influencers_validation_error(self):
#         """Test Case 6.4: Input validation error (e.g., missing product_tags)."""
#         url = f"{BASE_URL}/api/influencers/recommend"
#         payload = {
#             # "product_tags": "is missing",
#             "influencer_profiles_input": {},
#             "match_threshold": 70.0
#         }
#         response = requests.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
#         response_json = print_response_details(response)
        
#         assert response.status_code == 422
#         assert "detail" in response_json and response_json["detail"][0]["loc"] == ["body", "product_tags"]


# class TestCreateOutreachEmailsEndpoint:
#     """Tests for /api/outreachs/create"""

#     @pytest.fixture
#     def sample_selected_influencers(self) -> List[MatchResult]:
#         return [
#             MatchResult(influencerId="inf_tech_A", influencerName="AnnaTheAnalyzer", match_score="85%", match_rationale="Strong content alignment."),
#             MatchResult(influencerId="inf_tech_C", influencerName="ChrisGadgets", match_score="78%", match_rationale="Good audience fit and style.")
#         ]

#     @pytest.fixture
#     def product_info(self)-> ProductInputForAnalysis:
#         return   ProductInputForAnalysis( _id="SPYDERPRINT_B006UACRTG_analyze", # Unique for this test
#             product_title= "Datacolor Spyder Print - 高级数据分析和校准工具,可实现最佳打印效果,非常适合摄影师、平面设计师和印刷专业人士。",
#             price= "US$344.00",
#             rating= 4.5, # Example rating
#             review_count= 150, # Example review count
#             availability= "有现货",
#             seller= "Datacolor Official Store",
#             seller_url= "https://www.amazon.com/stores/Datacolor",
#             seller_address= "Lawrenceville, NJ, USA",
#             product_url= "https://www.amazon.com/-/zh/dp/B006UACRTG/ref=sr_1_1",
#             asin= "B006UACRTG",
#             image_url= "https://m.media-amazon.com/images/I/71qYqm3f0FL._AC_SX679_.jpg",
#             features= "全功能色彩管理, 精确打印机校准, ICC配置文件创建, 软打样, 适用于多种打印机和纸张类型, SpyderProof功能, 显示器校准集成",
#             description= "SpyderPrint 是专业人士选择管理打印输出色彩的全功能解决方案。通过选择任何打印机、墨水和纸张组合，SpyderPrint 可让您完全控制打印过程，从而生成画廊品质的打印件。只需安装软件，将色块打印到您选择的纸张上，然后使用 SpyderGuide 设备逐步完成简单流程即可校准并构建配置文件。独有的 SpyderProof 功能提供了一系列精心挑选的图像，可在编辑前来评估自定义配置文件，帮助您避免浪费纸张和墨水。",
#             category_source= "配件和耗材 > 打印机配件 > 校准工具",
#             brand_name= "Datacolor",
#             listing_date= "2011-12-05").model_dump(mode="json")
    
    
    
#     @pytest.fixture
#     def tech_product_tags(self) -> ProductTags:
#         return ProductTags(
#         FeatureTags=["High Performance", "AI-Powered"], # Product's own features
#         AudienceTags=["Professionals", "Early Adopters"], # Product's direct audience
#         UsageScenarioTags=["Work", "Productivity"], # Product's usage
#         coreContentDirection=["Tech Reviews", "Gadget Unboxing", "Software Tutorials"], # Ideal Influencer
#         overallPersonaAndStyle="Informative", # Ideal Influencer
#         mainAudience="Tech Enthusiasts" # Ideal Influencer
#     )


    
#     @pytest.fixture
#     def sample_influencer_profiles_for_email(self) -> Dict[str, InfluencerProfile]:
#         # Ensure InfluencerProfile is imported from graph_state
#         # from graph_state import InfluencerProfile # (if not already at top)
#         return {
#             "inf_tech_A": InfluencerProfile(
#                 influencerId="inf_tech_A",
#                 influencerName="AnnaTheAnalyzer",
#                 coreContentDirection=["AI Tools", "Software Reviews", "Productivity Hacks"],
#                 overallPersonaAndStyle="Insightful and Expert",
#                 mainAudience="Tech Professionals, Software Users",
#                 # --- ADD THESE MISSING FIELDS ---
#                 commercialDegree="中度商业化",
#                 crossPlatformConsist="高度一致",
#                 potentialBrandType=["Software", "Tech Gadgets"],
#                 influencerEval="High quality content, niche expert",
#                 goodsCarryRating="中"
#                 # --- END ADDITION ---
#             ),
#             "inf_tech_C": InfluencerProfile(
#                 influencerId="inf_tech_C",
#                 influencerName="ChrisGadgets",
#                 coreContentDirection=["Gadget Unboxings", "Tech News", "AI Gadgets"],
#                 overallPersonaAndStyle="Enthusiastic and Engaging",
#                 mainAudience="Gadget Lovers, General Tech Consumers",
#                 # --- ADD THESE MISSING FIELDS ---
#                 commercialDegree="高度商业化",
#                 crossPlatformConsist="基本一致",
#                 potentialBrandType=["Consumer Electronics", "Smart Home"],
#                 influencerEval="Popular and trendy",
#                 goodsCarryRating="高"
#                 # --- END ADDITION ---
#             )
#         }

#     def test_create_emails_success(
#         self, sample_selected_influencers, 
#         product_info,tech_product_tags, 
#         sample_influencer_profiles_for_email
#     ):
#         """Test Case 7.1: Successful email generation."""
#         url = f"{BASE_URL}/api/outreachs/create"
#         request_payload_model = EmailCreationRequest(
#             selected_influencers=sample_selected_influencers,
#             product_info=product_info,
#             product_tags=tech_product_tags,
#             influencer_profiles=sample_influencer_profiles_for_email
#         )
#         payload = request_payload_model.model_dump(mode="json") # Ensures HttpUrl is string

#         response = requests.post(url, json=payload, timeout=LONG_TIMEOUT)
#         response_json = print_response_details(response)

#         assert response.status_code == 200
#         api_response = ResponseModel(**response_json)
#         assert api_response.success is True
#         assert api_response.data is not None
        

#     def test_create_emails_no_selected_influencers(
#         self, sample_product_info_for_email, 
#         sample_product_tags_for_email, sample_influencer_profiles_for_email
#     ):
#         """Test Case 7.2: Email creation with no selected influencers."""
#         url = f"{BASE_URL}/api/outreachs/create"
#         request_payload_model = EmailCreationRequest(
#             selected_influencers=[], # Empty list
#             product_info=sample_product_info_for_email,
#             product_tags=sample_product_tags_for_email,
#             influencer_profiles=sample_influencer_profiles_for_email # Can be empty or not, shouldn't matter
#         )
#         payload = request_payload_model.model_dump(mode="json")

#         response = requests.post(url, json=payload, timeout=DEFAULT_TIMEOUT) # Should be fast
#         response_json = print_response_details(response)

#         assert response.status_code == 200
#         api_response = ResponseModel(**response_json)
#         assert api_response.success is True # Process completes, just no emails
#         assert api_response.data is not None
#         email_data =GeneratedEmail(**api_response.data)
#         assert email_data.generated_emails is not None
#         assert len(email_data.generated_emails) == 0

#     def test_create_emails_profile_missing_for_selected_influencer(
#         self, sample_selected_influencers,
#         sample_product_info_for_email, sample_product_tags_for_email
#         # sample_influencer_profiles_for_email # Intentionally not passing all profiles
#     ):
#         """Test Case 7.3: Email creation when a selected influencer's profile is missing."""
#         url = f"{BASE_URL}/api/outreachs/create"
        
#         # Only provide profile for one of the selected influencers
#         limited_profiles = {
#             "inf_tech_A": InfluencerProfile(
#                 influencerId="inf_tech_A", influencerName="AnnaTheAnalyzer",
#                 coreContentDirection=["AI Tools"], overallPersonaAndStyle="Expert", mainAudience="Tech Pros"
#             )
#             # Profile for "inf_tech_C" is missing
#         }
        
#         request_payload_model = EmailCreationRequest(
#             selected_influencers=sample_selected_influencers, # Contains inf_tech_A and inf_tech_C
#             product_info=sample_product_info_for_email,
#             product_tags=sample_product_tags_for_email,
#             influencer_profiles=limited_profiles 
#         )
#         payload = request_payload_model.model_dump(mode="json")

#         response = requests.post(url, json=payload, timeout=LONG_TIMEOUT)
#         response_json = print_response_details(response)

#         assert response.status_code == 200
#         api_response = ResponseModel(**response_json)
#         # API returns success=False if there are errors during generation
#         assert api_response.success is False 
#         assert "Email generation completed with some errors." in api_response.message
#         assert api_response.errors is not None
#         assert any("Profile missing for selected influencer inf_tech_C" in error for error in api_response.errors)
        
#         assert api_response.data is not None
#         email_data =EmailGenerationState(**api_response.data)
#         assert email_data.generated_emails is not None
#         assert len(email_data.generated_emails) == 1 # Only for inf_tech_A
#         assert email_data.generated_emails[0].influencerId == "inf_tech_A"

#     def test_create_emails_validation_error(self,):
#         """Test Case 7.4: Input validation error (e.g., missing selected_influencers)."""
#         url = f"{BASE_URL}/api/outreachs/create"
#         payload = {
#             # "selected_influencers": "is missing",
#             "product_info": ProductTags(ProductName="Test").model_dump(mode="json"),
#             "influencer_profiles": {}
#         }
#         response = requests.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
#         response_json = print_response_details(response)

#         assert response.status_code == 422
#         assert "detail" in response_json and response_json["detail"][0]["loc"] == ["body", "selected_influencers"]