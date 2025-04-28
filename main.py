from fastapi import FastAPI, Depends, HTTPException
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

app = FastAPI(
    title="Crossborder LLM API",
    description="API服务用于跨境大语言模型",
    version="0.1.0",
    docs_url=None,  # 禁用默认的docs地址
    redoc_url=None,  # 禁用默认的redoc地址
    openapi_url="/api/openapi.json"  # 自定义OpenAPI JSON地址
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

class ProductInfo(BaseModel):
    url: str
    name: str
    price: float
    features: List[str]
    target: str

# 自定义OpenAPI文档路由
@app.get("/api/docs", include_in_schema=False)
async def get_documentation():
    return get_swagger_ui_html(
        openapi_url="/api/openapi.json",
        title="Crossborder LLM API - Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css"
    )

@app.get("/api/redoc", include_in_schema=False)
async def get_redoc_documentation():
    return get_redoc_html(
        openapi_url="/api/openapi.json",
        title="Crossborder LLM API - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js"
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
        {
            "name": "Health",
            "description": "健康检查接口"
        },
        {
            "name": "LLM",
            "description": "大语言模型相关接口"
        }
    ]
    
    # 可以在这里添加更多自定义OpenAPI配置
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# 示例API路由
@app.get("/api/health", tags=["Health"])
async def health_check() -> ResponseModel:
    """健康检查接口"""
    return ResponseModel(success=True, message="Service is running", data={"status": "ok"})

@app.get("/api/version", tags=["Health"])
async def version() -> ResponseModel:
    """获取API版本信息"""
    return ResponseModel(
        success=True, 
        message="Version information", 
        data={"version": app.version}
    )


@app.post("/api/product/crawl", tags=["Product"])
async def crawl_product(url: str, platform: str) -> ResponseModel:
    """爬取商品信息"""
    product_info = ProductInfo(url=url, platform=platform)
    return ResponseModel(success=True, message="Product crawled successfully", data=product_info)


@app.post("/api/influencer/list", tags=["Influencer"])
async def list_influencer(product_info: ProductInfo, platform: str) -> ResponseModel:
    """推荐达人"""
    return ResponseModel(success=True, message="Product crawled successfully", data={})
                                                                                     
                                                                                    
@app.post("/api/email/intent", tags=["Email"])
async def email_intent(history: List[any]) -> ResponseModel:
    """邮件意图识别"""
    return ResponseModel(success=True, message="Product crawled successfully", data={})

def main():
    """应用入口函数"""
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
