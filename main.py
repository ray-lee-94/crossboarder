import time
import uuid
import traceback # For detailed error logging if needed
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, HttpUrl, Field

# Project-specific imports
from graph_nodes import workflow_app, intent_app # Compiled LangGraph apps
from graph_state import MarketingWorkFlowState, IntentAnalysisState, PlatformContentData, GeneratedEmail, ProductTags # LangGraph states
from product_crawl import run_crawl_task, jobs as crawl_jobs # Crawler task and job store




# --- API Request/Response Pydantic Models ---

# General Response Model
class ResponseModel(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None


# --- Product Crawl API Models ---
class CrawlRequest(BaseModel):
    url: HttpUrl
    platform: str = Field(default="Amazon", description="Platform to crawl, e.g., Amazon, TikTokShop")

class CrawlJobSubmitResponse(BaseModel):
    jobId: str
    message: str = "Crawl task submitted successfully."
    
class ProductDataResponse(BaseModel): # For crawl result
    platform: Optional[str] = None
    product_url: Optional[str] = None
    product_title: Optional[str] = None
    asin: Optional[str] = None
    price: Optional[str] = None
    rating: Optional[str] = None
    review_count: Optional[str] = None
    monthly_sales: Optional[str] = None
    availability: Optional[str] = None
    seller: Optional[str] = None
    seller_url: Optional[str] = None
    seller_address: Optional[str] = None
    image_url: Optional[str] = None
    features: Optional[str] = None # Semicolon-separated string or list
    description: Optional[str] = None
    brand_name: Optional[str] = None
    listing_date: Optional[str] = None
    bsr_rank_full_text: Optional[str] = None
    bsr_top_category_rank: Optional[str] = None
    error: Optional[str] = None

class CrawlJobStatusResponse(BaseModel):
    jobId: str
    status: str # e.g., "submitted", "running", "completed", "failed"
    message: Optional[str] = None
    submitted_at: Optional[float] = None
    updated_at: Optional[float] = None
    result: Optional[ProductDataResponse] = None

# --- Product Analysis API Models (Standalone) ---
class ProductInputForAnalysis(BaseModel): # Your FastAPI input model
    _id: str
    product_title: str
    price: str
    rating: Optional[float] = None
    review_count: Optional[int] = None
    availability: Optional[str] = None
    seller: Optional[str] = None
    seller_url: Optional[str] = None
    seller_address: Optional[str] = None
    product_url: Optional[str] = None
    asin: Optional[str] = None
    image_url: Optional[str] = None
    features: Optional[str] = None
    description: Optional[str] = None
    category_source: Optional[str] = None
    brand_name: Optional[str] = None
    listing_date: Optional[str] = None


class ProductAnalysisOutput(BaseModel):
    # This model should directly reflect the structure of ProductTags from graph_state.py
    # as product_tags in MarketingWorkFlowState is of type ProductTags.
    FeatureTags: List[str]
    AudienceTags: List[str]
    UsageScenarioTags: List[str]
    CoreContentDirection: Optional[List[str]] = None
    OverallPersonaAndStyle: Optional[List[str]] = None
    MainAudience: Optional[List[str]] = None  


# --- Influencer Input Model for Marketing Workflow ---
class InfluencerPlatformContentInput(BaseModel):
    # Matches PlatformContentData in graph_state.py
    content_title: Optional[str] = None
    promo_category: Optional[str] = None
    enhanced_tag: Optional[str] = None
    cover_image_url: Optional[str] = None
    content_url: Optional[str] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None
    publish_date: Optional[str] = None

class InfluencerInputForWorkflow(BaseModel):
    influencerId: str
    influencerName: str
    platforms: Dict[str, List[InfluencerPlatformContentInput]] = Field(default_factory=dict, description="Platform name to list of content data")


# --- Full Marketing Workflow API Models ---
class MarketingWorkflowRequest(BaseModel):
    product_info: ProductInputForAnalysis # Using the same detailed product input as for standalone analysis
    influencer_data: List[InfluencerInputForWorkflow]
    match_threshold: Optional[float] = Field(default=75.0, ge=0, le=100, description="Match score threshold (0-100)")
    
    
class MarketingWorkflowOutputData(BaseModel):
    # Expose relevant parts of the final MarketingWorkFlowState
    product_tags: Optional[ProductTags] = None # From graph_state.ProductTags
    # platform_analysis: Optional[Dict[str, Dict[str, Any]]] = None # Can be very verbose
    influencer_profiles: Optional[Dict[str, Any]] = None # Dict[influencerId, InfluencerProfile dict]
    match_results: Optional[List[Dict[str,Any]]] = None # List of MatchResult dicts
    selected_influencers: Optional[List[Dict[str,Any]]] = None # List of MatchResult dicts
    generated_emails: Optional[List[GeneratedEmail]] = None # From graph_state.GeneratedEmail
    workflow_errors: Optional[List[str]] = None

# --- Email Intent Analysis API Models ---
class EmailHistoryItem(BaseModel):
    sender: str
    recipient: str
    subject: str
    body: str
    timestamp: str # Consider using datetime for proper sorting/filtering if needed
    
class EmailIntentRequest(BaseModel):
    # The prompt analyzes the most recent email, usually a reply.
    # If full history is passed, the API or prompt needs to select the relevant part.
    # For simplicity, let's assume the API expects the specific email to analyze.
    email_subject: Optional[str] = None
    email_body: str

class EmailIntentOutput(BaseModel):
    # This should match the structure returned by email_intent_Prompt
    cooperation_intent: str
    key_points: List[str]
    suggested_next_step: str
    sentiment: str
    is_urgent: bool
    notification_summary: str
    # Add any other fields your email_intent_Prompt returns

app = FastAPI(
    title="Crossborder LLM API",
    description="API服务用于跨境大语言模型",
    version="0.1.1",
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


# --- Custom OpenAPI Docs ---
@app.get("/api/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
    )


@app.get("/api/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
    )




# --- API Routers ---
health_router = APIRouter(tags=["Health"])
product_crawl_router = APIRouter(prefix="/api/products/crawl", tags=["Product Crawl"])
product_analysis_router = APIRouter(prefix="/api/products", tags=["Product Analysis"]) # For standalone analysis
marketing_workflow_router = APIRouter(prefix="/api/marketing", tags=["Marketing Workflow"])
email_intent_router = APIRouter(prefix="/api/outreachs/intent", tags=["Email Intent"])


# --- Health Check Endpoints ---
@health_router.get("/api/health", response_model=ResponseModel)
async def health_check():
    return ResponseModel(success=True, message="API is healthy")


@health_router.get("/api/version", response_model=ResponseModel)
async def version():
    return ResponseModel(success=True, message=f"API Version: {app.version}")



# --- Product Crawl Endpoints ---
@product_crawl_router.post("", response_model=ResponseModel) # POST to /api/products/crawl
async def submit_crawl_product_task(
    request: CrawlRequest, background_tasks: BackgroundTasks
):
    job_id = str(uuid.uuid4())
    crawl_jobs[job_id] = {
        "status": "submitted",
        "product_url": str(request.url),
        "platform": request.platform,
        "submitted_at": time.time(),
        "updated_at": time.time(),
        "result": None,
        "message": "Task submitted for crawling."
    }
    background_tasks.add_task(run_crawl_task, job_id, str(request.url), request.platform)
    return ResponseModel(
        success=True,
        message="Crawl task submitted successfully.",
        data=CrawlJobSubmitResponse(jobId=job_id)
    )

@product_crawl_router.get("", response_model=ResponseModel) # GET to /api/products/crawl
async def get_crawl_product_result(job_id: str = Query(..., description="The ID of the crawl job")):
    job_info = crawl_jobs.get(job_id)
    if not job_info:
        raise HTTPException(status_code=404, detail="Job ID not found")
    
    # Ensure result is parsed into ProductDataResponse if completed successfully
    result_data = job_info.get("result")
    parsed_result = None
    if job_info["status"] == "completed" and result_data and isinstance(result_data, dict):
        try:
            parsed_result = ProductDataResponse(**result_data)
        except Exception as e:
            # If parsing fails, keep raw dict and log error, or adjust ProductDataResponse
            print(f"Error parsing crawl result for job {job_id}: {e}. Result: {result_data}")
            # Potentially set an error message in job_info
            parsed_result = result_data # Send raw if parsing fails for now
            job_info["message"] = job_info.get("message","") + f" | Result parsing error: {e}"


    return ResponseModel(
        success=True,
        message=f"Status for job ID: {job_id}",
        data=CrawlJobStatusResponse(
            jobId=job_id,
            status=job_info["status"],
            message=job_info.get("message"),
            submitted_at=job_info.get("submitted_at"),
            updated_at=job_info.get("updated_at"),
            result=parsed_result if parsed_result else result_data # Send parsed or raw
        )
    )

# --- Product Analysis Endpoint (Standalone - using LangGraph) ---
@product_analysis_router.post("/analyze", response_model=ResponseModel)
async def analyze_product_standalone(request_data: ProductInputForAnalysis):
    """
    Analyzes product information using the `analyze_product_node` from the LangGraph workflow.
    This provides the raw tag output.
    """
    initial_state_dict = {
        "product_info": request_data.model_dump(),
        "influencer_data": [], # Not needed for this specific task if graph handles it
        "error_messages": [],
    }
    try:
        # We need to ensure workflow_app can run just the product analysis part
        # or that invoking it with this state leads to product_tags being populated.
        # This might involve configuring the graph invocation or using a specific entry point if available.
        # For simplicity, if 'analyze_product_node' is the first, this should work.
        final_state_dict = workflow_app.invoke(initial_state_dict)
        
        if final_state_dict.get("error_messages") and any("Product analysis" in msg for msg in final_state_dict["error_messages"]):
            raise HTTPException(status_code=500, detail=f"Product analysis failed: {'; '.join(final_state_dict['error_messages'])}")

        product_tags_output = final_state_dict.get("product_tags")
        if not product_tags_output or not isinstance(product_tags_output, dict):
            # Try to access via Pydantic model if final_state_dict is a MarketingWorkFlowState model_dump
            if isinstance(final_state_dict, dict) and 'product_tags' in final_state_dict and isinstance(final_state_dict['product_tags'], dict):
                 product_tags_output = final_state_dict['product_tags']
            else:
                raise HTTPException(status_code=500, detail="Product analysis via LangGraph did not return valid tags.")

        # product_tags_output is expected to be a dict matching ProductTags model
        return ResponseModel(
            success=True,
            message="Product analysis successful.",
            data=ProductAnalysisOutput(**product_tags_output) # Directly use dict if keys match
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"API Error during standalone product analysis: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error during product analysis: {str(e)}")


# --- Full Marketing Workflow Endpoint ---
@marketing_workflow_router.post("/run", response_model=ResponseModel)
async def run_marketing_workflow(request_data: MarketingWorkflowRequest):
    """
    Runs the full marketing workflow: product analysis, influencer platform analysis,
    profile generation, matching, filtering, and email generation.
    """
    # Convert Pydantic models from request to simple dicts for LangGraph state
    product_info_dict = request_data.product_info.model_dump()
    
    influencer_data_list_for_state = []
    for inf_input in request_data.influencer_data:
        platforms_dict_for_state = {}
        for platform_name, content_list in inf_input.platforms.items():
            platforms_dict_for_state[platform_name] = [content.model_dump() for content in content_list]
        
        influencer_data_list_for_state.append({
            "influencerId": inf_input.influencerId,
            "influencerName": inf_input.influencerName,
            "platforms": platforms_dict_for_state
        })

    initial_state_dict = {
        "product_info": product_info_dict,
        "influencer_data": influencer_data_list_for_state,
        "match_threshold": request_data.match_threshold,
        "error_messages": [],
    }

    try:
        final_state_dict = workflow_app.invoke(initial_state_dict)
        
        # Prepare output data, converting Pydantic models in state back to dicts if needed
        output_data = MarketingWorkflowOutputData(
            product_tags=final_state_dict.get("product_tags"), # Already a dict or Pydantic model
            influencer_profiles=final_state_dict.get("influencer_profiles"),
            match_results=final_state_dict.get("match_results"),
            selected_influencers=final_state_dict.get("selected_influencers"),
            generated_emails=final_state_dict.get("generated_emails"),
            workflow_errors=final_state_dict.get("error_messages")
        )
        
        return ResponseModel(
            success=True,
            message="Marketing workflow executed.",
            data=output_data
        )
    except Exception as e:
        print(f"API Error during marketing workflow: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error executing marketing workflow: {str(e)}")


# --- Email Intent Analysis Endpoint ---
@email_intent_router.post("", response_model=ResponseModel)
async def analyze_email_intent(request_data: EmailIntentRequest):
    """
    Analyzes the intent of an email reply.
    """
    initial_state_dict = {
        "email_subject": request_data.email_subject,
        "email_body": request_data.email_body,
        "error_message": None,
    }
    try:
        final_state_dict = intent_app.invoke(initial_state_dict)

        if final_state_dict.get("error_message"):
            raise HTTPException(status_code=200, detail=f"Email intent analysis failed: {final_state_dict['error_message']}")

        analysis_result = final_state_dict.get("analysis_result")
        if not analysis_result or not isinstance(analysis_result, dict):
            raise HTTPException(status_code=500, detail="Email intent analysis returned invalid format.")

        return ResponseModel(
            success=True,
            message="Email intent analysis successful.",
            data=EmailIntentOutput(**analysis_result) # Expects analysis_result to match EmailIntentOutput
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"API Error during email intent analysis: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error during email intent analysis: {str(e)}")

# --- Include Routers ---
app.include_router(health_router)
app.include_router(product_crawl_router)
app.include_router(product_analysis_router)
app.include_router(marketing_workflow_router)
app.include_router(email_intent_router)


# --- Root Endpoint ---
@app.get("/", response_model=ResponseModel, tags=["default"])
async def root():
    return ResponseModel(success=True, message="Welcome to Crossborder LLM API")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

