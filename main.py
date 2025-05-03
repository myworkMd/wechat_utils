import configparser
from robot import WeChatWork, Message
from agent.agent import DifyAgent
import agent.sql as agent_sql
import api


def load_config():
    config = configparser.ConfigParser()
    if not config.read('config.ini'):
        raise FileNotFoundError("找不到配置文件 config.ini")

    # 读取 database 配置
    wechat_config = {
        "robot_name": config.get('wechat', 'robot_name')
    }

    agent_config = {
        "api_key": config.get("agent", 'api_key')
    }

    return {"wechat": wechat_config, "agent": agent_config}


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    config = load_config()
    WeChatWork.init(config["wechat"]["robot_name"])
    dify_agent = DifyAgent(config["agent"]["api_key"])
    conn = agent_sql.init_db()
    user_map = agent_sql.load_users_to_map(conn)
    while True:
        WeChatWork.cancelUpdate()
        we = WeChatWork.hw.TextControl(searchDepth=4)
        if not we.Exists():
            continue
        try:
            message_num = we.Name
            if message_num:
                user_name = WeChatWork.find_msg_master(we.GetParentControl())
                message = WeChatWork.get_message(user_name, int(message_num))
                hw_message = Message.HwMessage(hw_name=user_name,type=WeChatWork.get_chat_type(), message=message)
                message_json = WeChatWork.list_message2json([hw_message])
                print(message_json)
                if user_name in user_map:
                    result = dify_agent.send_message(query=message_json,conversation_id=user_map[user_name])
                    print(result["text"])
                else:
                    result = dify_agent.send_message(query=message_json)
                    agent_sql.handle_new_user(conn,user_map,user_name,result["conversation_id"])
                    print(result["text"])
        except Exception as e:
            print(e)
