# 微信各项操作
import os
import random
import time
from datetime import datetime

import pyperclip
import uiautomation as ui
import re

# ... 其他导入 ...
from robot.Message import Message, HwMessage  # 使用绝对导入
import json

ui.SetGlobalSearchTimeout(3)
assest_window = ui.WindowControl(Name="assest - 文件资源管理器", searchDepth=1)
# assest_window.SwitchToThisWindow()
time.sleep(1)
wx = ui.WindowControl(Name="微信", searchDepth=1)
wx.SwitchToThisWindow()
hw = wx.ListControl(Name="会话")
messageListControl = wx.ListControl(Name='消息')
aides = ui.WindowControl(Name='文件传输助手')
# aides.SwitchToThisWindow()

aides_edit = aides.EditControl()

robot_name: str = ''


def init(name: str):
    global robot_name
    robot_name = name


# 复制文件到剪贴板，方便粘贴发送文件
def copy_file_to_clipboard(file_path):
    # 使用 PowerShell 命令将文件复制到剪贴板
    command = f'powershell -sta "$sc=New-Object System.Collections.Specialized.StringCollection;$sc.Add(\'{file_path}\');Add-Type -Assembly \'System.Windows.Forms\';[System.Windows.Forms.Clipboard]::SetFileDropList($sc);"'
    os.system(command)


def _remove_quote_text(input_str):
    # 定义正则表达式匹配规则，匹配引用某某的消息文本
    pattern = r'\n引用(.|\n|\r)*'

    # 使用 sub 方法替换匹配到的部分为空
    output_str = re.sub(pattern, '', input_str)
    return output_str


def switch_wechat_window():
    # 将微信窗口定位到屏幕前
    wx.SwitchToThisWindow()
    return


def get_message(user_name: str, max_messages: int = -1) -> list[Message]:
    if user_name:
        locate(user_name)
    messageListControl = find_control(wx, type='ListControl', name='消息')
    while True:
        messages = []
        msg_list = messageListControl.GetChildren()
        date = None
        if len(msg_list) > max_messages or msg_list[0].Name != "查看更多消息":  # 如果消息数量少就不必要再检测内容了
            for item_list in msg_list:
                msg_master = find_msg_master(item_list)
                if msg_master and msg_master != item_list.Name:  # 存在发送消息的人且发送者昵称跟内容名称不能一致
                    messages.append(Message(msg_master, date, item_list.Name))
                elif Message.is_time_string(item_list.Name):
                    date = Message.parse_time_string(item_list.Name)

        # 检查是否需要滚动加载更多消息
        if max_messages == -1 or len(messages) < max_messages:
            # 滚动前检查第一个item是否为"查看更多消息"
            first_item = msg_list[0].Name if msg_list else ""
            if first_item == "查看更多消息":
                # 滚动加载更多消息
                scroll(messageListControl,5,False)
            else:
                # 没有更多消息可加载
                break
        else:
            break

    if len(messages) > max_messages:
        return messages[-max_messages:]
    return messages


# 找到发消息的用户昵称
def find_msg_master(msg_control: ui.Control) -> str:
    msg_children_list = msg_control.GetChildren()
    for item in msg_children_list:
        if item.Name and item.ControlTypeName == 'ButtonControl':  # 按钮名称认为是用户名
            return item.Name
        elif len(item.GetChildren()) > 0:
            result = find_msg_master(item)
            if not result == "":
                return result
    return ""


def send_message(msg: str, user_name=''):
    # 发送文本，不输入发送对象，默认在当前窗口发送文本
    # msg = msg.replace("\n","{SHIFT}{ENTER}")
    if user_name:
        locate(user_name)
    # parent_control = wx.ButtonControl(Name="发送文件").GetParentControl().GetParentControl()
    parent_control = find_control(wx, "ButtonControl", "发送文件").GetParentControl().GetParentControl()
    # edit = parent_control.EditControl()
    edit = find_control(parent_control, type='EditControl')
    # edit.Click()
    _click_control_fast(edit)
    pyperclip.copy(msg)
    edit.SendKeys("{Ctrl}v", waitTime=0)
    edit.SendKeys("{Enter}", waitTime=0)


def locate(user_name: str):
    """
    根据用户名打开窗口
    :param user_name: 用户名
    :return:
    """
    user_control = find_control(hw, "ButtonControl", user_name)
    if user_control is not None:
        # user_control.Click()
        _click_control_fast(user_control)
    else:
        user_control = find_control(hw, "ListItemControl", user_name)
        if user_control is not None:
            _click_control_fast(user_control)
            return
        search = wx.EditControl(Name="搜索")
        search.Click()
        pyperclip.copy(user_name)
        search.SendKeys("{Ctrl}v", waitTime=0)
        search_list_control = find_control(wx, "ListControl", "@str:IDS_FAV_SEARCH_RESULT:3780")
        if user_name == '文件传输助手':
            wx.TextControl(Name='<em>' + user_name + '</em>').Click()
            _click_control_fast(find_control(search_list_control, "TextControl", "<em>文件传输助手</em>"))
        else:
            _click_control_fast(find_control(search_list_control, "ButtonControl", user_name))
    time.sleep(1)  # 点击后，消息窗口需要一点时间加载内容


# 转发消息
def forward_message(message: str, address: str, postscript: str = ""):
    """
    转发消息
    :param message: 消息文本
    :param address: 转发对象
    :param postscript: 转发附言
    :return:
    """
    message_list = messageListControl.GetChildren()
    for i in range(len(message_list) - 1, -1, -1):
        if _remove_quote_text(message_list[i].Name) == message:
            if message == '[图片]':
                message_list[i].ButtonControl(Name='').RightClick()
                ment = ui.MenuControl(ClassName="CMenuWnd")
                ment.TextControl(Name="转发...").Click()
                break
            else:
                message_list[i].TextControl(Name=message).RightClick()
                ment = ui.MenuControl(ClassName="CMenuWnd")
                ment.TextControl(Name="转发...").Click()
                break
    _forward_window_choose_people(address, postscript)


def forward_img(address: str, postscript: str = ""):
    """
    转发当前聊天窗口中最后一张图，需确保图片已经展示在当前屏幕中
    :param address: 转发对象
    :param postscript: 转发附言
    :return:
    """
    message_list = messageListControl.GetChildren()
    for i in range(len(message_list) - 1, -1, -1):
        if _remove_quote_text(message_list[i].Name) == '[图片]':
            message_control = message_list[i].ButtonControl(Name='')
            message_control.RightClick()
            # ment = wx.MenuControl(ClassName="CMenuWnd")
            # forward = ment.TextControl(Name="转发...")
            ment = find_control(wx, "MenuControl")
            while ment is None:
                ment = find_control(wx, "MenuControl")
            forward = find_control(ment, "TextControl", "转发...")
            while forward is None:
                cursor_point = ui.GetCursorPos()
                ui.RightClick(cursor_point[0] - 5, cursor_point[1])
                message_control.RightClick()
                ment = ui.MenuControl(ClassName="CMenuWnd")
                forward = ment.TextControl(Name="转发...")
            forward.Click()
            break
    _forward_window_choose_people(address, postscript)


# 转发链接
def forward_link(sub_text: str, address: str, postscript: str = ""):
    message_list = messageListControl.GetChildren()
    for i in range(len(message_list) - 1, -1, -1):
        if message_list[i].TextControl(SubName=sub_text):
            message_list[i].ButtonControl(Name='').RightClick()
            ment = ui.MenuControl(ClassName="CMenuWnd")
            ment.TextControl(Name="转发...").Click()
            break
    _forward_window_choose_people(address, postscript)


# 转发更多消息
def forward_more_message(position: list['int'], address: str, postscript: str, user_name: str):
    messageListControl = find_control(wx, type='ListControl', name='消息')
    msg_list = messageListControl.GetChildren()
    item_robot_position = 0
    is_right_click = False
    for item in msg_list:
        msg_master = find_msg_master(user_name, robot_name, item)
        if msg_master == 2:
            item_robot_position += 1
            if item_robot_position in position:
                item_button = find_control(item, "TextControl")
                if not is_right_click:
                    _right_click_control_fast(item_button)
                    ment = find_control(wx, "MenuControl")
                    while ment is None:
                        ment = find_control(wx, "MenuControl")
                    forward = find_control(ment, "TextControl", "多选")
                    _click_control_fast(forward)
                    is_right_click = True
                else:
                    _click_control_fast(item_button)
    #     逐条转发
    find_control(messageListControl.GetParentControl().GetParentControl().GetParentControl(), "ButtonControl",
                 "逐条转发").Click()
    _forward_window_choose_people(address, postscript)


# 添加好友
def add_friend():
    # 添加好友，返回是1:用户申请添加好友后，又删除好友，2:老用户，3：新用户添加成功
    # add_friend_control = messageListControl.GetParentControl().GetParentControl().GetParentControl().ButtonControl(
    #     Name="添加", searchDepth=3)
    add_friend_control = find_control(messageListControl.GetParentControl().GetParentControl().GetParentControl(),
                                      type='ButtonControl', name='添加')
    if add_friend_control is not None:
        add_friend_control.Click()
        # cancel = wx.ButtonControl(Name="取消", )
        cancel = find_control(control=wx, type='ButtonControl', name='取消')
        # 用户申请添加好友后，又删除好友
        if cancel is not None:
            cancel.Click()
            return 1
        return 3
    return 2


def add_note_name(note_name: str = '', user_name: str = ""):
    """
    为没有添加过备注名的用户添加备注名，注意：必须是没有添加过备注名的用户
    :param note_name: 需要设置的用户名
    :param user_name: 目标用户
    :return:
    """
    # 点击聊天中的头像添加备注
    msg_list = messageListControl.GetChildren()
    left, right = get_edit_position()
    for item in msg_list[::-1]:
        msg_master = find_msg_master(user_name, robot_name, item)
        if msg_master == 1:
            avatar = find_control(item, name=user_name, type='ButtonControl')
            rect_avatar = avatar.BoundingRectangle
            if avatar is not None and rect_avatar.top > 0:
                _click_control_fast(avatar)
                add_note_button = find_control(wx, 'ButtonControl', '点击添加备注')
                is_success_add_note = False
                if add_note_button is not None:
                    _click_control_fast(add_note_button)
                    add_note_parent = add_note_button.GetParentControl()
                    pyperclip.copy(note_name)
                    add_note_parent.SendKeys("{Ctrl}v", waitTime=0)
                    ui.Click(left, right)  # 点击消息编辑区关闭备注窗口
                    is_success_add_note = True
                else:
                    ui.Click(left, right)  # 点击消息编辑区关闭备注窗口
                return is_success_add_note
    # 如果上面循环完找不到头像，则点击右上角...添加备注
    # chat_info_buttom = wx.ButtonControl(Name='聊天信息')
    chat_info_buttom = find_control(wx, "ButtonControl", "聊天信息")
    user_name = user_name
    if note_name == '':
        note_name = get_user_name()
    chat_info_buttom.Click()
    # chat_list_control = wx.ListControl(Name="聊天成员")
    chat_list_control = find_control(wx, "ListControl", "聊天成员")
    chat_list_control.ButtonControl(Name=user_name).Click()
    # add_note_button = wx.ButtonControl(Name='点击添加备注')
    add_note_button = find_control(wx, 'ButtonControl', '点击添加备注')
    is_success_add_note = False
    if add_note_button is not None:
        add_note_button.Click()
        add_note_parent = add_note_button.GetParentControl()
        pyperclip.copy(note_name)
        add_note_parent.SendKeys("{Ctrl}v", waitTime=0)
        chat_list_control.ButtonControl(Name=user_name).Click()
        is_success_add_note = True
    else:
        chat_list_control.ButtonControl(Name=user_name).RightClick()
    chat_info_buttom.Click()
    return is_success_add_note

def get_edit_position():
    parent_control = find_control(wx, "ButtonControl", "发送文件").GetParentControl().GetParentControl()
    edit = find_control(parent_control, type='EditControl')
    rect = edit.BoundingRectangle
    return rect.left, rect.right

# 获取用户名
def get_user_name() -> str:
    chat_info_buttom = find_control(wx, "ButtonControl",
                                    "聊天信息").GetParentControl().GetParentControl().GetParentControl()
    user_name_buttom = find_control(chat_info_buttom, "TextControl")
    return user_name_buttom.Name


# 发送文件
def send_file(file_path: str, username=''):
    copy_file_to_clipboard(file_path)
    if username:
        locate(username)
    parent_control = find_control(wx, "ButtonControl", "发送文件").GetParentControl().GetParentControl()
    edit = find_control(parent_control, type='EditControl')
    _click_control_fast(edit)
    ui.SendKeys("{Ctrl}v", waitTime=0)
    ui.SendKeys("{Enter}", waitTime=0)


def _forward_window_choose_people(address: str, postscript: str, wx: ui.Control = wx):
    # forward_window = wx.ListControl(Name='已选择的联系人').GetParentControl().GetParentControl()
    forward_window = find_control(wx, type="ListControl", name='已选择的联系人',
                                  times=-1).GetParentControl().GetParentControl()
    people = find_control(forward_window, type="CheckBoxControl", name=address, times=2)
    if people is None:
        # search = forward_window.EditControl(Name='搜索')
        search = find_control(forward_window, "EditControl", name='搜索')
        _click_control_fast(search)
        pyperclip.copy(address)
        search.SendKeys("{Ctrl}v", waitTime=0)
        people = find_control(forward_window, type="CheckBoxControl", name=address, times=2)
    # forward_window.CheckBoxControl(Name=address).Click()
    _click_control_fast(people)
    if not postscript == '':
        # messageControl = forward_window.EditControl(Name="给朋友留言")
        messageControl = find_control(forward_window, "EditControl", '给朋友留言')
        _click_control_fast(messageControl)
        pyperclip.copy(postscript)
        messageControl.SendKeys("{Ctrl}v", waitTime=0)
    # forward_window.ButtonControl(Name="发送").Click()
    send_button = find_control(forward_window, "ButtonControl", "发送")
    _click_control_fast(send_button)


# 寻找控件
def find_control(control: ui.Control, type: str = '', name: str = '', sub_name: str = '', times=1):
    if times > 0:
        for i in range(1, times + 1):
            control = _find_control_one(control, type, name, sub_name)
            if control is not None:
                return control
    else:
        control = _find_control_one(control, type, name, sub_name)
        while control is None:
            control = _find_control_one(control, type, name, sub_name)
        return control


def _find_control_one(control: ui.Control, type: str, name: str, sub_name: str = '') -> ui.Control:
    for item in control.GetChildren():
        if (not type or type == item.ControlTypeName) and (not name or name == item.Name) and (
                not sub_name or sub_name in item.Name):
            return item
        else:
            result = _find_control_one(item, type, name, sub_name)
            if result is not None:
                return result
    return None


def is_cursor_on_control(control: ui.Control):
    cursor_point = ui.GetCursorPos()
    print(cursor_point)
    control_rect = control.BoundingRectangle
    if control_rect.left <= cursor_point[0] <= control_rect.right and control_rect.top <= cursor_point[
        1] <= control_rect.bottom:
        return True
    return False


# 快速点击控件
def _click_control_fast(control: ui.Control):
    control_rect = control.BoundingRectangle
    center_x = (control_rect.left + control_rect.right) // 2
    center_y = (control_rect.top + control_rect.bottom) // 2
    ui.Click(center_x, center_y)


# 快速右键控件
def _right_click_control_fast(control: ui.Control):
    control_rect = control.BoundingRectangle
    center_x = (control_rect.left + control_rect.right) // 2
    center_y = (control_rect.top + control_rect.bottom) // 2
    ui.SetCursorPos(center_x, center_y)
    control.RightClick()


def scroll(control: ui.Control, scroll_line: int,is_down: bool = True):
    hw_rect = control.BoundingRectangle
    # 计算会话列表的中心点
    hw_rect = control.BoundingRectangle
    # 计算会话列表的中心点
    center_x = (hw_rect.left + hw_rect.right) // 2
    center_y = (hw_rect.top + hw_rect.bottom) // 2

    # 将鼠标移动到会话列表中心，并添加随机偏移
    offset_x = random.randint(-10, 10)
    offset_y = random.randint(-10, 10)
    ui.SetCursorPos(center_x + offset_x, center_y + offset_y)
     # 随机滚动距离和间隔时间
    scroll_times = random.randint(scroll_line-1, scroll_line+1)  # 每次滚动1-3次
    scroll_delay = random.uniform(0.1, 0.3)  # 滚动间隔时间
    if is_down:
        ui.WheelDown(wheelTimes=scroll_times)
    else:
        ui.WheelUp(wheelTimes=scroll_times)
    time.sleep(scroll_delay)

    # 随机添加鼠标微动
    if random.random() < 0.3:  # 30%概率添加鼠标微动
        current_pos = ui.GetCursorPos()
        move_x = current_pos[0] + random.randint(-5, 5)
        move_y = current_pos[1] + random.randint(-5, 5)
        ui.SetCursorPos(move_x, move_y)
        time.sleep(random.uniform(0.05, 0.1))


def scroll_page_down(control: ui.Control) -> bool:
    """
    向下滚动会话列表，模拟人类操作模式
    通过随机滚动距离和间隔时间，避免被检测为机器操作
    返回True：滚动到最底部无法滚动。False：还可以再滚动
    """
    # 获取会话列表的边界矩形
    hw_rect = control.BoundingRectangle
    # 计算会话列表的中心点
    center_x = (hw_rect.left + hw_rect.right) // 2
    center_y = (hw_rect.top + hw_rect.bottom) // 2

    # 将鼠标移动到会话列表中心，并添加随机偏移
    offset_x = random.randint(-10, 10)
    offset_y = random.randint(-10, 10)
    ui.SetCursorPos(center_x + offset_x, center_y + offset_y)

    last_item_name = control.GetLastChildControl().Name

    first_item_same_times = 0  # 判断滚动多次后，视图中第一项名字相同次数，用于判断是否滑动到底部了
    first_item_name = control.GetFirstChildControl().Name
    # 持续向下滚动
    while True:
        if first_item_name == control.GetFirstChildControl().Name:
            first_item_same_times = first_item_same_times + 1
        else:
            first_item_same_times = 0

        if first_item_same_times > 3:
            return True

        # 检查是否已经滚动到底部
        has_last_item = False
        for item in control.GetChildren():
            if item.Name == last_item_name:
                has_last_item = True
                break

        if not has_last_item or last_item_name == control.GetFirstChildControl().Name:
            return False

        # 随机滚动距离和间隔时间
        scroll_times = random.randint(2, 4)  # 每次滚动1-3次
        scroll_delay = random.uniform(0.1, 0.3)  # 滚动间隔时间
        ui.WheelDown(wheelTimes=scroll_times)
        time.sleep(scroll_delay)

        # 随机添加鼠标微动
        if random.random() < 0.3:  # 30%概率添加鼠标微动
            current_pos = ui.GetCursorPos()
            move_x = current_pos[0] + random.randint(-5, 5)
            move_y = current_pos[1] + random.randint(-5, 5)
            ui.SetCursorPos(move_x, move_y)
            time.sleep(random.uniform(0.05, 0.1))


def get_hw_message(num_hw: int = -1, max_message: int = 30) -> list[HwMessage]:
    """
    获取会话列表中的消息
    :param num_hw: 要获取的会话数量，-1表示获取所有
    :return: 包含HwMessage对象的列表
    """
    hw_messages = []
    processed_names = set()  # 用于记录已处理的会话名称，避免重复

    while True:
        # 获取当前可见的会话项
        hw_items = hw.GetChildren()

        for item in hw_items:
            if item.Name in processed_names:
                continue

            # 获取会话消息
            messages = get_message(item.Name.replace("已置顶", ""), max_message)
            hw_messages.append(HwMessage(hw_name=item.Name, message=messages))
            processed_names.add(item.Name)

            # 如果达到指定数量则返回
            if num_hw != -1 and len(hw_messages) >= num_hw:
                return hw_messages

        # 如果获取所有会话或者已经获取到足够数量，则返回
        if num_hw == -1 or len(hw_messages) >= num_hw:
            return hw_messages

        # 向下滚动，如果已经滚动到底部则返回
        if scroll_page_down(hw):
            return hw_messages


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat().replace('T', ' ')
    elif isinstance(obj, Message):
        return {
            'user_name': obj.user_name,
            'time': obj.time.isoformat().replace('T', ' ') if obj.time else None,
            'msg': obj.msg
        }
    return obj.__dict__

def list_message2json(list: list[HwMessage]) -> str:
    return json.dumps(list, default=json_serial, ensure_ascii=False)


if __name__ == '__main__':
    time.sleep(2)
    init("komnenos")
    forward_message("在？","haha")
