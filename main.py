from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel
from graph_nodes import llm, workflow_app,intent_app
from graph_state import MarketingWorkFlowState, IntentAnalysisState

app = FastAPI(
    title="Crossborder LLM API",
    description="API服务用于跨境大语言模型",
    version="0.1.0",
    docs_url=None,  # 禁用默认的docs地址
    redoc_url=None,  # 禁用默认的redoc地址
    openapi_url="/api/openapi.json",  # 自定义OpenAPI JSON地址
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 自定义响应模型
class ResponseModel(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None



# Model for product input to analysis/matching
class ProductInput(BaseModel):
    # Include all fields expected by productPromt and potentially others
    ProductName: str
    Brand: Optional[str] = None
    AmazonCategory: Optional[str] = None
    Specifications: Optional[str] # Or Dict[str, Any]
    Description: Optional[str] = None
    Price: Optional[str] = None
    Rating: Optional[float] = None
    ReviewCount: Optional[int] = None
    ProductURL: Optional[str] = None # Useful for context
    # Add any other fields from your product DB

# Model for influencer input to analysis/matching
class InfluencerPlatformContentInput(BaseModel):
     # Matches PlatformContentData structure
    content_title: Optional[str] = None
    promo_category: Optional[List[str]] = None
    enhanced_tag: Optional[List[str]] = None
    cover_image_url: Optional[str] = None
    content_url: Optional[str] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None
    publish_date: Optional[str] = None


class InfluencerInput(BaseModel):
    id: str # Unique identifier
    name: str
    # Structure for platforms and their content
    platforms: Dict[str, List[InfluencerPlatformContentInput]] = {} # e.g., {"youtube": [content1, content2]}
    # Add other known influencer data if needed (e.g., overall follower count, main language)

# Model for the main matching/outreach endpoint request
class MarketingRequest(BaseModel):
    product_info: ProductInput # Use the detailed product model
    influencer_data: List[InfluencerInput] # List of influencers to consider
    match_threshold: Optional[float] = 75.0 # Allow overriding threshold


# Model for the email intent request (use the one you defined)
class EmailHistoryItem(BaseModel):
    sender: str
    recipient: str
    subject: str
    body: str
    timestamp: str # Consider using datetime


class EmailIntentRequest(BaseModel):
    # Expecting a list, but the prompt usually analyzes the *last* reply
    history: List[EmailHistoryItem]


# 自定义OpenAPI文档路由
@app.get("/api/docs", include_in_schema=False)
async def get_documentation():
    return get_swagger_ui_html(
        openapi_url="/api/openapi.json",
        title="Crossborder LLM API - Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
    )


@app.get("/api/redoc", include_in_schema=False)
async def get_redoc_documentation():
    return get_redoc_html(
        openapi_url="/api/openapi.json",
        title="Crossborder LLM API - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
    )


# 添加自定义OpenAPI内容
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # 添加API标签描述
    openapi_schema["tags"] = [
        {"name": "Health", "description": "健康检查接口"},
        {"name": "Marketing Workflow", "description": "营销工作流相关接口"},
        {"name": "Email Intent", "description": "邮件意图识别相关接口"},
    ]

    # 可以在这里添加更多自定义OpenAPI配置
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

@app.get("/")
async def root():
    return {"message": "Welcome to Crossborder LLM API"}

# 示例API路由
@app.get("/api/health", tags=["Health"])
async def health_check() -> ResponseModel:
    """健康检查接口"""
    # Add LLM checks here
    try:
        await llm.ainvoke("Test")
        llm_status = "ok"
    except Exception as e:
        print(f"LLM check failed: {e}")
        llm_status = "error"

    return ResponseModel(
        success=True, message="Service is running", data={"status": "ok", "llm_status": llm_status}
    )



@app.get("/api/version", tags=["Health"])
async def version() -> ResponseModel:
    """获取API版本信息"""
    return ResponseModel(
        success=True, message="Version information", data={"version": app.version}
    )


# @app.post("/api/product/crawl", tags=["Product"],response_model=ResponseModel)
# async def crawl_product(url: str, platform: str) -> ResponseModel:
#     """爬取商品信息"""
#     product_info = ProductInfo(url=url, platform=platform)
#     return ResponseModel(
#         success=True, message="Product crawled successfully", data=product_info
#     )


@app.post("/api/marketing/run",tags="Marketing Workflow", response_model=ResponseModel)
async def run_marketing_workflow(request: MarketingRequest) -> ResponseModel:
    """
    执行完整的网红营销分析、匹配和邮件生成工作流。
    输入商品信息和待分析的达人列表及其内容。
    """
    print("Received marketing workflow request.")
    # 1. Prepare Initial State
    initial_state:  MarketingWorkFlowState= {
        "product_info": request.product_info.model_dump(), # Convert Pydantic model to dict
        "influencer_data": [inf.model_dump() for inf in request.influencer_data], # Convert list of Pydantic models
        "platform_analysis": {},
        "influencer_profiles": {},
        "product_tags": None,
        "match_results": [],
        "selected_influencers": [],
        "generated_emails": [],
        "error_messages": [],
        "match_threshold": request.match_threshold
    }
    # 2. Invoke the Graph Asynchronously
    try:
        print("Invoking marketing graph...")
        final_state = await workflow_app.ainvoke(initial_state, {"recursion_limit": 30}) # Add recursion limit
        print("Marketing graph invocation finished.")

        # 3. Process Results and Errors
        errors = final_state.get("error_messages", [])
        result_data = {
            "product_tags": final_state.get("product_tags"),
            "match_results": final_state.get("match_results"),
            "selected_influencers": final_state.get("selected_influencers"),
            "generated_emails": final_state.get("generated_emails"),
            # Optionally include platform_analysis and influencer_profiles if needed
            "errors": errors,
        }

        if errors:
            print(f"Workflow completed with errors: {errors}")
            # Decide if partial success is acceptable or return failure
            return ResponseModel(
                success=False, # Or True if partial results are okay
                message=f"Workflow completed with {len(errors)} errors.",
                data=result_data
            )
        else:
            print("Workflow completed successfully.")
            return ResponseModel(
                success=True,
                message="Marketing workflow executed successfully.",
                data=result_data
            )

    except Exception as e:
        print(f"Error during marketing workflow execution: {e}")
        # Log the full traceback for debugging
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error during workflow execution: {e}")


# --- Endpoint to analyze email intent ---
@app.post("/api/email/analyze-intent", tags=["Email Intent"], response_model=ResponseModel)
async def analyze_email_intent(request: EmailIntentRequest) -> ResponseModel:
    """
    分析收到的邮件回复，判断达人的合作意向。
    通常分析历史记录中的最后一封邮件。
    """
    print("Received email intent analysis request.")
    if not request.history:
        raise HTTPException(status_code=400, detail="Email history cannot be empty.")

    # Assume we analyze the *last* email in the history as the reply
    last_email = request.history[-1]

    # 1. Prepare Initial State
    initial_state:  IntentAnalysisState= {
        "email_subject": last_email.subject,
        "email_body": last_email.body,
        "analysis_result": None,
        "error_message": None
    }

    # 2. Invoke the Graph Asynchronously
    try:
        print("Invoking intent analysis graph...")
        final_state = await intent_app.ainvoke(initial_state)
        print("Intent analysis graph invocation finished.")

        # 3. Process Results and Errors
        error = final_state.get("error_message")
        analysis_result = final_state.get("analysis_result")

        if error:
            print(f"Intent analysis failed: {error}")
            return ResponseModel(success=False, message=error, data=None)
        elif analysis_result:
            print("Intent analysis successful.")
            return ResponseModel(success=True, message="Email intent analyzed successfully.", data=analysis_result)
        else:
            # Should not happen if graph logic is correct, but handle defensively
            print("Intent analysis finished with no result and no error.")
            return ResponseModel(success=False, message="Intent analysis did not produce a result.", data=None)

    except Exception as e:
        print(f"Error during intent analysis execution: {e}")
        import traceback
        traceback.print_exc()
        # raise HTTPException(status_code=500, detail=f"Internal server error during intent analysis: {e}")


# @app.post("/api/influencer/list", tags=["Influencer"], response_model=ResponseModel)
# async def list_influencer(product_info: ProductInfo, platform: str) -> ResponseModel:
#     """推荐达人"""
#     return ResponseModel(success=True, message="Product crawled successfully", data={})


# @app.post("/api/email/intent", tags=["Email"])
# async def email_intent(history: List[Any]) -> ResponseModel:
#     """邮件意图识别"""
#     return ResponseModel(success=True, message="Product crawled successfully", data={})


def main():
    """应用入口函数"""
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
