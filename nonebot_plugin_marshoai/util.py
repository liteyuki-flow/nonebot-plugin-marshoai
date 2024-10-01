import base64
import mimetypes
import os
import json
import httpx
from datetime import datetime
from zhDateTime import DateTime
from azure.ai.inference.models import SystemMessage
from .config import config
async def get_image_b64(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code == 200:
            # 获取图片数据
            image_data = response.content
            content_type = response.headers.get('Content-Type')
            if not content_type:
                content_type = mimetypes.guess_type(url)[0]
            image_format = content_type.split('/')[1] if content_type else 'jpeg'
            base64_image = base64.b64encode(image_data).decode('utf-8')
            data_url = f"data:{content_type};base64,{base64_image}"
            return data_url
        else:
            return None
        
def get_praises():
    filename = "praises.json"
    if not os.path.exists("praises.json"):
        init_data = {
            "like": [
                    {"name":"Asankilp","advantages":"赋予了Marsho猫娘人格，使用vim与vscode为Marsho写了许多代码，使Marsho更加可爱"}
                ]
            }
        with open(filename,"w",encoding="utf-8") as f:
            json.dump(init_data,f,ensure_ascii=False,indent=4)
    with open(filename,"r",encoding="utf-8") as f:
        data = json.load(f)
    return data

def build_praises():
    praises = get_praises()
    result = ["你喜欢以下几个人物，他们有各自的优点："]
    for item in praises["like"]:
        result.append(f"名字：{item['name']}，优点：{item['advantages']}")
    return "\n".join(result)

def get_prompt():
    prompts = ""
    prompts += config.marshoai_additional_prompt
    if config.marshoai_enable_praises:
        praises_prompt = build_praises()
        prompts += praises_prompt
    if config.marshoai_enable_time_prompt:
        current_time = datetime.now().strftime('%Y.%m.%d %H:%M:%S')
        current_lunar_date = DateTime.now().to_lunar().date_hanzify()[5:] #库更新之前使用切片
        time_prompt = f"现在的时间是{current_time}，农历{current_lunar_date}。"
        prompts += time_prompt
    marsho_prompt = config.marshoai_prompt
    spell = SystemMessage(content=marsho_prompt+prompts)
    return spell

def suggest_solution(errinfo: str):
    suggestion = ""
    if "content_filter" in errinfo:
        suggestion = "消息已被内容过滤器过滤。请调整聊天内容后重试。"
    elif "RateLimitReached" in errinfo:
        suggestion = "模型达到调用速率限制。请稍等一段时间或联系Bot管理员。"
    elif "tokens_limit_reached" in errinfo:
        suggestion = "请求token达到上限。请重置上下文。"
    elif "unauthorized" in errinfo:
        suggestion = "Azure凭据无效。请联系Bot管理员。"
    if suggestion != "":
        return "\n"+suggestion
    else:
        return suggestion