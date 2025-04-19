import json
import requests
from typing import Dict, Optional

class DifyAgent:
    def __init__(self, api_key: str, base_url: str = "http://127.0.0.1/v1"):
        self.api_key = api_key
        self.base_url = base_url

    def send_message(self, query: str, user: str = "default_user", conversation_id: Optional[str] = None) -> Dict[str, str]:
        """
        发送消息到Dify并获取最终响应文本
        :param query: 要发送的文本消息
        :param user: 用户标识符
        :param conversation_id: 会话ID，可选
        :return: 包含完整响应文本和会话ID的字典
        """
        url = f"{self.base_url}/chat-messages"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "inputs": {},
            "query": query,
            "response_mode": "streaming",
            "conversation_id": conversation_id or "",
            "user": user
        }

        response = requests.post(url, headers=headers, json=payload, stream=True)
        response.raise_for_status()

        full_text = ""
        last_conversation_id = conversation_id
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith("data:"):
                    try:
                        data = json.loads(decoded_line[5:])
                        if data.get("event") == "agent_message":
                            full_text += data.get("answer", "")
                            last_conversation_id = data.get("conversation_id", last_conversation_id)
                    except json.JSONDecodeError:
                        continue

        return {
            "text": full_text,
            "conversation_id": last_conversation_id
        }

if __name__ == '__main__':
    agent = DifyAgent(api_key="app-oQB8qNjDDbaeXqYd4Ty9YN5U")
    result = agent.send_message("这些功能里，哪个不需要传参？", conversation_id="1bfb653f-bfc5-42b2-8463-97c7903f19a3")
    print("Response:", result["text"])
    print("Conversation ID:", result["conversation_id"])