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
            "ProductName": "Datacolor Spyder Print - 高级数据分析和校准工具,可实现最佳打印效果,非常适合摄影师、平面设计师和印刷专业人士。",
            "Brand": "HP",
            "AmazonCategory": "配件和耗材",
            "Specifications": ": 条形阅读分光色度计可在几分钟内创建自定义配置文件,彩色和黑白目标易于读取。 包括改进的 SpyderGuide 以方便轻松准确地创建配置文件 | {1 } {1 } {1 } {1 } {1 } {1 } {1 } {1 } {1 } { 1 } { 1 }\ | 独特的SpyderProof功能为您提供一系列精心挑选的图像,从摄影师的角度评估细节。 Profile Softproof 可用于每个独特的打印机配置文件。 | 数据彩色Spyder Print是摄影师和设计师的领先校准和分析工具,让您完全掌控打印输出,实现画廊品质的打印效果。 | Datacolor 和 Adobe 携手合作,为您的摄影工作流程提供完整的包。 购买 Spyder 即可获得免费的 Adobe Creative Cloud Photography计划 - 90 天试用。 Spyder 激活后将发送兑换代码。",
            "Description": """内容简介
                            Spyderprint 是专业人士选择管理打印输出色彩的全功能解决方案。 通过在软件中选择打印机、墨水和介质的任意组合,Spyderprint 提供了各种工具,让您突破高级喷墨打印机的极限,创造彩色和黑白相间的画廊级打印质量。 Spyderprint 让您完全控制打印机输出,并能够根据 ICC 标准创建任意数量的自定义配置文件。 只需安装软件,使用打印机打印您选择的目标,然后使用 SpyderGuide 设备帮助您完成校准和构建配置文件的简单过程。 包括 Spyderprint 分光色度计和底座,SpyderGuide, 6? USB 数据线,Spyderprint 软件 CD,快速入门指南(10 种语言),免费在线支持。
                            From the Manufacturer
                            SpyderPRINT lets you effectively manage color in your print output. By selecting any combination of printer, ink, and media in the software, you can control your printer output to create gallery-quality prints in color or black and white. SpyderPRINT includes software and a SpyderGuide device and is designed for professional photographers, fine art printers, production professionals, and anyone who wants accurate print-to-screen matching.
                            SpyderPRINT
                            AT A GLANCE:
                            Effectively manage color in your print output
                            Spectrocolorimeter creates custom profiles in minutes
                            Gives you true-to-life reproduction of image files
                            SpyderProof images provide soft-proofing tool
                            Make adjustments to entire profile in image editor
                            One-year warranty
                            Spectrocolorimeter creates custom color profiles in minutes. View larger.
                            Software creates RGB ICC profiles for consistent, accurate prints. View larger.
                            Easily Calibrate Printer and Display
                            With SpyderPRINT you can have full control of your printer output by creating any number of custom profiles to ICC standards*. Simply install the software, print your choice of targets with your printer, and use the SpyderGuide device to calibrate and build a profile.
                            After calibration, images can be viewed and edited with confidence. You will see less waste in your printed output and fewer unused prints. Images can be reliably assessed and adjusted, giving you true-to-life reproduction.
                            Custom Profiles in Minutes
                            Working with profiling speed and accuracy, SpyderPRINT's spectrocolorimeter gives you custom profiles with EZ targets for color and black and white.
                            The SpyderProof function gives you a series of images to review so you can evaluate each detail from a photographer's point of view and compare it with your own images. This feature serves as a soft-proofing tool for each printer profile you create.
                            Software Includes Extensive Editing Functions
                            The color and black-and-white tinting curves in the image editor software allow you to apply adjustments to a profile rather than to each individual image. The extended grays target adds precision gray and near gray data to profiles, enhancing the quality of tinted and black-and-white prints.
                            Flexible target options and high-patch profiling targets allow you to produce gallery quality prints in color or black and white. Select preset profile settings to produce profiles with specific combinations of highlight and shadow tint, detail, and neutrality settings.
                            System Requirements and Warranty Information
                            SpyderPRINT is compatible with Windows XP (32/64), Vista (32/64), and 7 (32/64) operating systems as well as Mac OS X 10.4 or higher. To use this device, you need a powered USB port, a color monitor resolution of at least 1,024 by 768 pixels, a 16-bit video card, 128 MB RAM, and 100 MB free hard disk space.
                            SpyderPRINT comes with a one-year hardware warranty and free online support.
                            * SpyderPRINT builds RGB ICC profiles. Please check with the manufacturer of your laser printer or the developer of your RIP software to determine if your laser printer or RIP is compatible with RGB ICC profiles.
                            What's in the Box
                            SpyderPRINT spectrocolorimeter and base, SpyderGuide, 6-foot USB cable, SpyderPRINT software CD, and quick-start guide.
                            Other Products by DataColor:
                            Light balance reference tool.
                            Complete color management.
                            At-home lens calibration.
                            Color correction for HDTV.
                            Color color standard tool.  来自品牌
                            A Foundation of Trust
                            We help others achieve their goals by eliminating roadblocks and facilitating processes critical to color management. In turn, the world’s leading brands, manufacturers and creative professionals, (Audi, Hugo Boss, Walmart, Ace Hardware, and more) trust us to deliver innovative color management solutions for their needs."
                            """,
            "Price": "US$34400",
            "Rating": 2.9,
            "ReviewCount": 35,
            "ProductURL": "https://www.amazon.com/-/zh/dp/B006UACRTG/ref=sr_1_1"
          },
          "influencer_data": [
            {
              "influencerId": "pro_photo_print_01",
              "influencerName": "Pixel Perfect Prints",
              "platforms": {
                "youtube": [
                  {
                    "content_title": "Mastering Print Color: Datacolor Spyder Print Deep Dive Review",
                    "like_count": 1850,
                    "comment_count": 150,
                    "publish_date": "2024-03-15T10:00:00Z",
                    "promo_category": ["Photography Gear", "Printing Supplies", "Color Management"],
                    "enhanced_tag": ["ICC Profile", "Spectrocolorimeter", "Fine Art Printing", "Tutorial", "Review", "Datacolor", "SpyderPrint"],
                    "cover_image_url": "https://example.com/img/spyderprint_review.jpg",
                    "content_url": "https://youtube.com/watch?v=fake12345"
                  },
                  {
                    "content_title": "My Essential Print Workflow Tools for Gallery Quality (2024)",
                    "like_count": 2100,
                    "comment_count": 180,
                    "publish_date": "2024-02-20T11:30:00Z",
                    "promo_category": ["Photography Gear", "Software", "Printing"],
                    "enhanced_tag": ["Workflow", "Printing", "Color Accuracy", "Photoshop", "Lightroom", "Epson Printer"],
                    "cover_image_url": "https://example.com/img/print_workflow.jpg",
                    "content_url": "https://youtube.com/watch?v=fake67890"
                  }
                ],
                "instagram": [
                  {
                    "content_title": "Side-by-side print comparison before and after calibration with Spyder Print. The difference is HUGE! #coloraccuracy #fineartprint #datacolor #photographytips",
                    "like_count": 950,
                    "comment_count": 60,
                    "publish_date": "2024-03-18T15:00:00Z",
                    "promo_category": ["Photography Gear"],
                    "enhanced_tag": ["Color Management", "Printing", "Comparison", "Tips"]
                  }
                ]
              }
            },
            {
              "influencerId": "design_creative_02",
              "influencerName": "Design & Flow Studio",
              "platforms": {
                "youtube": [
                  {
                    "content_title": "Setting Up Your Workspace for Perfect Print Design - Color Matters!",
                    "like_count": 3500,
                    "comment_count": 280,
                    "publish_date": "2024-04-01T09:00:00Z",
                    "promo_category": ["Graphic Design", "Creative Tools", "Monitors"],
                    "enhanced_tag": ["Workspace Setup", "Color Management", "Print Design", "Adobe Illustrator", "Monitor Calibration"],
                    "cover_image_url": "https://example.com/img/design_workspace.jpg", 
                    "content_url": "https://youtube.com/watch?v=fakeabcde"
                  },
                  {
                    "content_title": "Top 5 Tech Gadgets Every Designer Needs in 2024",
                    "like_count": 5200,
                    "comment_count": 410,
                    "publish_date": "2024-03-10T14:00:00Z",
                    "promo_category": ["Tech Gadgets", "Creative Tools", "Productivity"],
                    "enhanced_tag": ["Review", "Designer Tools", "Tablet", "Monitor", "Software", "Keyboard"],
                    "cover_image_url": "https://example.com/img/designer_gadgets.jpg",
                    "content_url": "https://youtube.com/watch?v=fakefghij"
                  }
                ],
                "tiktok": [ 
                  {
                    "content_title": "Quick tip: Why your screen colour doesn't match your print! #graphicdesign #printdesign #colortheory #designtips",
                    "like_count": 15000,
                    "comment_count": 500,
                    "publish_date": "2024-04-05T18:00:00Z",
                    "promo_category": ["Graphic Design"],
                    "enhanced_tag": ["Design Education", "Tips", "Color Management"]
                  }
                ]
              }
            },{
              "influencerId": "gen_tech_review_03",
              "influencerName": "Tech Tomorrow",
              "platforms": {
                "youtube": [
                  {
                    "content_title": "Is the NEW MegaPixel Camera Worth It? Full Review!",
                    "like_count": 25000,
                    "comment_count": 1500,
                    "publish_date": "2024-04-10T12:00:00Z",
                    "promo_category": ["Cameras", "Tech Gadgets", "Photography"],
                    "enhanced_tag": ["Camera Review", "Mirrorless", "4K Video", "Unboxing", "Tech Review"],
                    "cover_image_url": "https://example.com/img/new_camera.jpg",
                    "content_url": "https://youtube.com/watch?v=fakeklmno"
                  },
                  {
                    "content_title": "Building the Ultimate Budget Gaming PC - Part 1",
                    "like_count": 35000,
                    "comment_count": 2800,
                    "publish_date": "2024-03-25T16:00:00Z",
                    "promo_category": ["PC Hardware", "Gaming"],
                    "enhanced_tag": ["PC Build", "Gaming PC", "Budget Build", "CPU", "GPU", "Tutorial"],
                    "cover_image_url": "https://example.com/img/gaming_pc.jpg",
                    "content_url": "https://youtube.com/watch?v=fakepqrst"
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