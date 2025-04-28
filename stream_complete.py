import os
import json
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
from dotenv import load_dotenv
import asyncio

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

def llm_process_generator(user_message):
    messages = [{"role": "system", "content": "你是一个AI助手，请根据用户的问题给出回答。"}, {"role": "user", "content": user_message}]
    
    # 发送请求
    with client.chat.completions.with_streaming_response.create(
        messages=messages,
        model=deployment_name,
        stream=True
    ) as response:
      print(response.headers.get("X-My-Header"))

      for line in response.parse():
        yield line


def main():
    user_message = "帮我写一笔篇文章说明当代年轻人为什么喜欢看小说，1000字以上"
    full_response = ""
    for line in llm_process_generator(user_message):
      if line != None:
        if len(line.choices) > 0:
          delta = line.choices[0].delta.content
          full_response += delta
          print(delta)

    print(full_response)

if __name__ == "__main__":
    main()

