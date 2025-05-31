# 简介
本项目提供一系列操作个人微信基础方法。并开放api，可接入dify等工具让AI根据聊天场景调用本项目提供的api来操控微信。<br/>
相比于其它AI微信机器人，本项目最大特点是可以基于此个性化开发自己的微信机器人。甚至可以自行拓展，操控桌面其它应用。

本项目的微信机器人能实现以下功能：
* 向指定用户发送微信消息
* 批量或单个获取多个聊天的信息。获取内容有会话名、会话类型（群聊/单聊）、消息发送者昵称、消息内容、发送时间
* 转发消息
* 添加好友（需要将微信设置成不需要好友验证）
* 设置备注
* 延迟或定期循环处理任务

<br>
这些功能都将通过api形式供外部调用。通过dify的Agent功能，能够让AI根据语境自行判断调用哪些功能，可以实现符合自己要求的AI微信机器人。比如设定定期提醒，团队成员任务追踪，微信客服等等。
<br/><br/>如果是做微信客服，也可调用批量获取多个聊天信息功能，获取以往客服跟用户沟通记录，再将记录丢给AI让它生成知识库，再将知识库通过dify提供给AI，让AI按照知识库规范回复用户问题，以此快速构建自己的微信客服。

# 注意事项
微信官方并不支持以脚本形式操作个人微信，因此全网所有微信机器人的使用都是有风险的。尽量用自己的小号构建微信机器人！！！
<br><br>
从我的使用情况来看（三个微信小号），第一周会时不时被踢下线，大概两三天一次，接下来的一个月也有较低概率被踢下线，之后几乎不会被踢下线。

# 快速使用
## 第一次使用：
1. 安装dockerh和dify，教程：https://blog.csdn.net/2301_80314483/article/details/146987475
3. 下载一键启动包。进入release下载压缩包.
4. 修改swagger_output.json里最下方的url，将ip地址改为你本机的内网ip地址。 
5. 申请第三方AI大模型API，将申请到的api_key填入config.ini的api_key里。修改robot_name为你的微信机器人的微信昵称。 
6. docker内启动dify，点击顶部菜单栏的工具->点击自定义->点击创建自定义工具->工具名称随意填写->复制项目里swagger_output.json内容到下面输入框->保存<br>这样就创建好自定义工具了 
7. 点击工作室->点击创建空白应用->点击Agent->名称可随意填写->点击创建 
8. 按自己的功能需要填写提示词。将自己的需求直接描述好即可，填写完后可以点击右上角的“生成”,这样会帮助你生成更好格式的提示词。示例：<br>
    ```xml
    <instruction>
    你是我的个人微信助手，已经接入到微信程序中。请根据以下规则处理微信消息：
    
    输入格式为JSON，包含以下字段：
    - hw_name: 当前微信会话窗口名称（可能是个人或群聊）
    - type: 会话类型（"群聊"或"单聊"）
    - message: 消息数组，包含：
      - user_name: 发送者昵称
      - time: 发送时间（可能有误差）
      - msg: 消息内容
    
    处理规则：
    1. 当type为"群聊"时：
       - 如果msg是给你的任务指令（提到"komnenos"）：
         * 能通过工具执行的任务：调用相应工具，无论成功与否都用send_message_post回复结果（user_name传hw_name值）
         * 非任务但明确提到你：用send_message_post在当前窗口回复
       - 如果msg是给"果夫氨基"的任务：
         * 没有明确时间：用send_message_post询问完成时间
         * 确认时间和内容后：调用schedule_message_post提前提醒，成功后返回任务ID并用send_message_post告知用户
       - 其他情况不回复
    
    2. 当type为"单聊"时：
       - 任务指令：执行并始终用send_message_post回复结果（user_name传hw_name值）
       - 非任务内容：必须用send_message_post回复
    
    3. 工具使用规范：
       - 所有回复必须通过send_message_post工具
       - 定时提醒先调用工具计算目标时间，再用schedule_message_post，成功后告知任务ID
       - 回复时user_name字段始终传hw_name值
    
    输出要求：
    - 不要包含任何XML标签
    - 根据情况调用相应工具或保持沉默
        
    <example>
    示例1（群聊任务）:
    输入：
    [
        {
            "hw_name": "项目群",
            "type": "群聊",
            "message": [
                {
                    "user_name": "同事A",
                    "time": "2025-05-01 10:00:00",
                    "msg": "消息内容"
                }
            ]
        }
    ]
    </example>
    </instruction>
    ```
9. 根据自己的功能需要添加刚刚创建的自定义工具。agent中限制最多添加10个工具。上述示例对应的场景除了send_file_post,add_friend_post,add_note_name_post这三个工具用不上外，其它都要添加。 
10. 调试与预览框上方选择合适AI模型。他本质是调用第三方大模型的API，因此需要去到对应模型官网申请API。 
11. 点击发布更新。 
12. 回到一键启动包，保持微信窗口打开，双击运行api.bat和run.bat，不要关闭命令窗口。

## 后续使用
打开docker启动dify容器，运行api.bat和run.bat。

# 项目结构
## [WeChatWork.py](./robot/WeChatWork.py)
基于uiautomation库提供了操控微信方法。下列是主要方法说明：

| 方法名 | 用途                      |
|--------|-------------------------|
| `init(name: str)` | 初始化机器人名称                |
| `switch_wechat_window()` | 将微信窗口定位到屏幕前             |
| `get_message(user_name: str, max_messages: int)` | 获取指定用户或当前窗口的消息列表        |
| `send_message(msg: str, user_name='')` | 发送文本消息到指定用户或当前窗口        |
| `locate(user_name: str)` | 根据用户名打开聊天窗口             |
| `forward_message(message: str, address: str, postscript: str)` | 转发指定消息到目标用户             |
| `forward_img(address: str, postscript: str)` | 转发当前聊天窗口中的最后一张图片        |
| `forward_link(sub_text: str, address: str, postscript: str)` | 转发包含指定子文本的链接            |
| `forward_more_message(position: list, address: str, postscript: str, user_name: str)` | 转发多条消息到目标用户             |
| `add_friend()` | 添加好友，返回添加状态             |
| `add_note_name(note_name: str, user_name: str)` | 为指定用户添加备注名              |
| `get_user_name()` | 获取当前聊天窗口的用户名            |
| `get_chat_type()` | 获取当前聊天窗口的类型（单聊或群聊）      |
| `send_file(file_path: str, username='')` | 发送文件到指定用户或当前窗口 
| `find_control(control: ui.Control, type: str, name: str, sub_name: str, times)` | 查找指定控件                  |
| `is_cursor_on_control(control: ui.Control)` | 检查光标是否在控件上              |
| `_click_control_fast(control: ui.Control)` | 快速点击控件                  |
| `_right_click_control_fast(control: ui.Control)` | 快速右键点击控件                |
| `scroll(control: ui.Control, scroll_line: int, is_down: bool)` | 滚动控件内容，模拟人类操作           |
| `scroll_page_down(control: ui.Control)` | 向下滚动控件内容，返回是否滚动到底部      |
| `get_hw_message(num_hw: int, max_message: int)` | 获取会话列表中的消息              |
| `json_serial(obj)` | JSON序列化辅助函数，处理非默认可序列化对象 |
| `cancelUpdate()` | 点击取消微信更新弹窗              |

如果上述方法不足以满足需求，可以先学习uiautomation的使用，教程：https://blog.csdn.net/freeking101/article/details/105758387
<br><br>
要想操控windows的软件，得先知道如何定位软件内各个元素，因此通常都需要UI自动化工具Inspect。安装教程：https://blog.csdn.net/qq_45451847/article/details/139271733

## [task.py](./utils/task.py)
提供任务管理功能。能够定时或循环执行项目中任意方法。待执行的任务会记录到数据库中，以防程序停止运行后任务丢失。一旦程序重新运行后，会先检查是否有任务过期，过期了就会立马执行

| 方法名 | 用途 |
|--------|------|
| `schedule_task(self, task_info: str, task_id=create_task_id()) -> str` | 调度新任务，支持单次和循环任务 |
| `_execute_task(self, task_id)` | 执行指定任务（内部方法） |
| `cancel_task(self, task_id: str) -> bool` | 取消已调度的任务 |
| `get_all_tasks(self) -> str` | 获取所有等待执行的任务信息（JSON格式） |

## [api.py](./api.py)
将WeChatWork.py方法转成api。暴露的接口可以看[swagger_output.json](./swagger_output.json)

## [agent.py](./agent/agent.py)

| 方法名 | 用途                     |
|--------|------------------------|
| `send_message(self, query: str, user: str = "default_user", conversation_id: Optional[str] = None)` | 调用dify创建并发布好的agent的API |

## [TimeCalculator.py](./utils/TimeCalculator.py)
AI大模型无法获取当前日期，也无法计算时间跨度，因此需根据平常使用的日期描述习惯开放时间获取与计算方法。通过

| 方法名              | 用途            |
|------------------|---------------|
| `calculate(...)` | 计算时间跨度，详情请看注释 |


## [main.py](./main.py)
检测微信是否有新消息，若有则根据未读消息数量获取会话消息并调用dify的创建并发布Agent的API