# 📘 接口文档

基于 uiautomation 的微信桌面版自动化操作工具，支持消息发送、消息获取、转发、文件传输、添加好友等功能。适用于构建自动化聊天机器人、客服工具、消息收集器等场景。
<br/><br/>
以下是所有主要公开方法及其说明：

| 方法名 | 功能描述 | 参数                                                                                                             | 示例 |
|--------|----------|----------------------------------------------------------------------------------------------------------------|------|
| `init(name)` | 初始化机器人名称（用于标记身份） | `name: str` – 机器人名称                                                                                            | `init("my_bot")` |
| `send_message(msg, user_name='')` | 向指定用户发送文本消息 | `msg: str` – 消息内容<br>`user_name: str` – 联系人名称（默认当前窗口）                                                          | `send_message("你好", "文件传输助手")` |
| `send_file(file_path, username='')` | 向指定用户发送文件 | `file_path: str` – 本地文件路径<br>`username: str` – 联系人名称（可选，不填则默认当前窗口）                                                   | `send_file("C:/demo.pdf", "文件传输助手")` |
| `get_message(user_name, max_messages=-1)` | 获取指定用户的历史消息 | `user_name: str` – 联系人名称<br>`max_messages: int` – 获取数量（默认全部）                                                   | `get_message("文件传输助手", 20)` |
| `get_hw_message(num_hw=-1, max_message=30)` | 获取多个会话的历史消息 | `num_hw: int` – 会话数量（-1表示全部）<br>`max_message: int` – 每个会话的消息数量                                                 | `get_hw_message(5, 10)` |
| `forward_message(message, address, postscript='')` | 转发指定的文本消息 | `message: str` – 文本消息<br>`address: str` – 接收方<br>`postscript: str` – 附言（可选）                                    | `forward_message("你好", "张三")` |
| `forward_img(address, postscript='')` | 转发当前聊天窗口中最后一张图片 | `address: str` – 接收方<br>`postscript: str` – 附言（可选）                                                             | `forward_img("张三")` |
| `forward_link(sub_text, address, postscript='')` | 转发带有指定子文本的链接消息 | `sub_text: str` – 链接中的关键字<br>`address: str` – 接收方<br>`postscript: str` – 附言（可选）                                | `forward_link("点击查看", "张三")` |
| `forward_more_message(position, address, postscript, user_name)` | 批量转发多条消息 | `position: list[int]` – 要转发的消息序号<br>`address: str` – 接收方<br>`postscript: str` – 附言<br>`user_name: str` – 消息发送者 | `forward_more_message([1, 3], "张三", "请查看", "李四")` |
| `add_friend()` | 添加当前聊天用户为好友 | 无                                                                                                              | `add_friend()` |
| `add_note_name(note_name, user_name)` | 为用户添加备注名称 | `note_name: str` – 新备注名<br>`user_name: str` – 联系人原名                                                            | `add_note_name("客户A", "张三")` |
| `switch_wechat_window()` | 将微信窗口切换到前台激活 | 无                                                                                                              | `switch_wechat_window()` |
| `list_message2json(list)` | 将消息列表序列化为 JSON 字符串 | `list: list[HwMessage]` – 消息对象列表                                                                               | `list_message2json(msg_list)` |

---

