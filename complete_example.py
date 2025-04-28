# %%
import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

# 设置 Azure OpenAI 服务凭据
api_key = os.getenv("AZURE_API_KEY")
api_version = os.getenv("AZURE_API_VERSION")
azure_endpoint = os.getenv("AZURE_API_BASE")
deployment_name = os.getenv("AZURE_COMPLETION_DEPLOYMENT")

# 初始化 Azure OpenAI 客户端
client = AzureOpenAI(
    api_key=api_key,
    api_version=api_version,
    azure_endpoint=azure_endpoint
)


def llm_process_generator():
    messages = [{"role": "system", "content": "你是一个智能AI助手，请根据用户的问题给出回答。"}, {"role": "user", "content": "你好"}]
    
    # 发送请求
    response = client.chat.completions.create(
        messages=messages,
        model=deployment_name,
        stream=False
    )
    return response.choices[0].message.content
# %%

from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="You are a helpful assistant")

result = Runner.run_sync(agent, "Write a haiku about recursion in programming.")
print(result.final_output)


# %%

def main():
    full_response = llm_process_generator()
    print(full_response)

if __name__ == "__main__":
    main()

