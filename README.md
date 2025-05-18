# Crossborder LLM API

基于FastAPI构建的跨境大语言模型API服务

## 特性

- FastAPI框架
- 完整的OpenAPI支持
- 自定义Swagger UI和ReDoc文档
- 标准化的API响应格式

## 安装

确保您安装了Python 3.12或更高版本，然后安装依赖：

```bash
pip install -e .
```

## 运行

启动服务器：

```bash
python main.py
```

或使用uvicorn：

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API文档

启动服务后，可以通过以下地址访问API文档：

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- OpenAPI JSON: http://localhost:8000/api/openapi.json

## 项目结构


## 接口示例

- GET /api/health - 健康检查接口
- GET /api/version - 获取API版本信息


## 文件说明
.
├── graph_state.py        # LangGraph state definitions (MarketingWorkFlowState, IntentAnalysisState)
├── graph_nodes.py        # LangGraph node functions & compiled workflow_app, intent_app
├── main.py               # FastAPI app definition, routers, and endpoint logic
├── prompts.py            # All LLM prompt templates
├── product_crawl.py      # Your AmazonCrawler class and related logic
├── requirements.txt      # Project dependencies
└── .env                  # Environment variables (AZURE_API_KEY, etc.)