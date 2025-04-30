# %%
import os
from openai import AzureOpenAI
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers.json import parse_and_check_json_markdown
from langgraph.graph import MessageGraph, END
import random


# %%

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

llm = AzureChatOpenAI(
    api_key=api_key,
    api_version=api_version,
    azure_endpoint=azure_endpoint,
    deployment_name=deployment_name
)

# %%

player_prompt_header="""
请永远记住您现在扮演{agent_role}的角色。
您的基本介绍：{agent_description}
您的性格：{agent_nature}
您的经历：{agent_experience}

目前轮到你发言，请根据上面的节目聊天内容，按照您的角色和性格，生成一条回复。回复内容必须符合您的角色和性格，不能有明显的错误,只返回你要发表的内容。
"""

role_List=["成龙","刘亦菲","沈腾","薛之谦"]

strParser=StrOutputParser()
roleDesPrompt=PromptTemplate.from_template(
    """
    用户输入：{input}
    请根据用户输入的明星，生成该明星的详细介绍。返回必须按照下面的JSON格式返回：
    {{name:str,//明星名字,
    description:str,//明星详细介绍,
    nature:str,//明星性格,
    experience:str//明星经历
    }}
    """)

roleDesChain= roleDesPrompt | llm | strParser

# %%
batchInput=[]
for role in role_List:
    batchInput.append({"input":role})

roleDesList=roleDesChain.batch(batchInput)
print(roleDesList)

# %%
roleDesListJson=[]

for roleDes in roleDesList:
    roleDesJson=parse_and_check_json_markdown(roleDes,expected_keys=["name","description","nature","experience"])
    roleDesListJson.append(roleDesJson)
print(roleDesListJson)

# %%

topic= "哪吒2为啥能大火"

player_prompt="""
这是圆桌派综艺节目，目前讨论以下主题：{topic}

本期节目嘉宾：{role_List}

节目聊天内容：
{chatList}

{roleDesc}
"""

host_prompt="""
这是圆桌派综艺节目，目前讨论以下主题：{topic}

本期节目嘉宾介绍：{roleDesList}


节目聊天内容：
{chatList}

下一位发言嘉宾是：{player}

请永远记住您现在扮演节目主持人的角色,你的名字叫喵喵。

目前轮到你发言，请根据上面的节目聊天内容进展来主持节目进行发言。如果节目尚未开始，
你需要介绍嘉宾和本次节目的开场介绍，并引导下一位嘉宾发言。如果节目已经结束，你需要总结节目内容，并引导嘉宾进行互动。回复内容必须符合主持人的角色和性格，不能有明显的错误,只返回你要发表的内容。
"""

playersPrompt=[]

for role in roleDesListJson:
    prompt=player_prompt_header.format(agent_role=role["name"],agent_description=role["description"],agent_nature=role["nature"],agent_experience=role["experience"])

    playersPrompt.append(prompt)

print(playersPrompt)

#%%
playerPromptList=[]

for item in playersPrompt:
    playerPrompt=PromptTemplate.from_template(player_prompt)
    playerPrompt=playerPrompt.partial(role_List=",".join(role_List),topic=topic,chatList="",roleDesc=item)
    playerPromptList.append(playerPrompt)

for playerPrompt in playerPromptList:
    print(playerPrompt)

# %%
playerChains=[]

for prompt in playerPromptList:
    playerChain=prompt | llm | StrOutputParser()
    playerChains.append(playerChain)

hostChain=PromptTemplate.from_template(host_prompt) | llm | StrOutputParser()

# %%
roleDesListStr=""
for roleDes in roleDesListJson:
    roleDesListStr= roleDesListStr+ roleDes["name"]+":"+roleDes["description"]+"\n"
print(roleDesListStr)

# %%
print(hostChain.invoke({"topic":topic,"roleDesList":roleDesListStr,"chatList":"节目刚开始，暂无聊天内容","player":"成龙"}))

# %%

graphBuilder=MessageGraph()

data={
    "topic":topic,
    "chatList":"节目刚开始，暂无聊天内容",
    "roleDesList":roleDesListStr,
    "plyer":"成龙",
    "isEnd": False
}

def choose(state):
    # 如果data字典中有idEnd键，则返回"end"
    if data["isEnd"]:
        return "end"
    # 如果state列表的长度大于5，则将data字典中的isEnd键的值设为True
    if len(state)>5:
        data["isEnd"]=True
    
    # 遍历role_List列表
    for index in range(len(role_List)):
        # 如果data字典中的player键的值等于role_List列表中的某个元素
        if data["player"]==role_List[index]:
            return "play"+str(index+1)
    
    return "end"

def msgParser(state):
    if not isinstance(data["chatList"],str):
        data["chatList"].append("嘉宾("+data["player"]+"):"+state[-1].content)
    
    if data["isEnd"]:
        data["player"]="节目结束，不需要下一位嘉宾发言"
    
    else:
        random_items=random.sample(role_List,k=1)
        data["player"]=random_items[0]
    return data

def playMsgParser(state):
    if isinstance(data["chatList"],str):
        data["chatList"]=["主持人（喵喵）"+state[0].content]
    else:
        data["chatList"].append("主持人（喵喵）"+state[-1].content)
    
    return {"chatList":data["chatList"],"topic":data["topic"]}

graphBuilder.add_node("hostNode",msgParser | hostChain)
graphBuilder.add_node("playNode1",playMsgParser | playerChains[0])
graphBuilder.add_node("playNode2",playMsgParser | playerChains[1])
graphBuilder.add_node("playNode3",playMsgParser | playerChains[2])
graphBuilder.add_node("playNode4",playMsgParser | playerChains[3])

graphBuilder.add_conditional_edges("hostNode",
                                   choose,{"end":END,
                                  "play1":"playNode1",
                                  "play2":"playNode2",
                                  "play3":"playNode3",
                                  "play4":"playNode4"})

graphBuilder.set_entry_point("hostNode")

graphBuilder.add_edge("playNode1", "hostNode")
graphBuilder.add_edge("playNode2", "hostNode")
graphBuilder.add_edge("playNode3", "hostNode")
graphBuilder.add_edge("playNode4", "hostNode")

graph=graphBuilder.compile()

# Image(graph.get_graph().draw_png())
# %%
graph.invoke([])

for item in data["chatList"]:
    print(item)

# %%
