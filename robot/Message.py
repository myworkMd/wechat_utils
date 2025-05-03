import time
from datetime import datetime, timedelta
from dateutil import parser, relativedelta
import re
from dataclasses import dataclass


@dataclass
class Message:
    user_name: str  # 发送消息用户昵称（取决于当前窗口展示昵称）
    time: datetime  # 消息发送时间
    msg: str  # 消息内容

    @staticmethod
    def is_time_string(time_str: str) -> bool:
        # 匹配 "17:30" 格式
        if re.fullmatch(r"\d{1,2}:\d{2}", time_str):
            return True

        # 匹配 "昨天 17:30" 格式
        if re.fullmatch(r"昨天 \d{1,2}:\d{2}", time_str):
            return True

        # 匹配 "星期一 17:30" 格式
        if re.fullmatch(r"星期[一二三四五六日] \d{1,2}:\d{2}", time_str):
            return True

        # 匹配 "3月28日 17:30" 格式
        if re.fullmatch(r"\d{1,2}月\d{1,2}日 \d{1,2}:\d{2}", time_str):
            return True

        # 匹配 "2021年3月28日 17:30" 格式
        if re.fullmatch(r"\d{4}年\d{1,2}月\d{1,2}日 \d{1,2}:\d{2}", time_str):
            return True

        return False

    @staticmethod
    def parse_time_string(time_str: str) -> datetime:
        now = datetime.now()

        # 1. 处理 "17:30"（今天的时间）
        if re.fullmatch(r"\d{1,2}:\d{2}", time_str):
            time_part = parser.parse(time_str).time()
            return datetime.combine(now.date(), time_part)

        # 2. 处理 "昨天17:30"
        elif time_str.startswith("昨天"):
            time_part = parser.parse(time_str[2:]).time()
            yesterday = now.date() - timedelta(days=1)
            return datetime.combine(yesterday, time_part)

        # 3. 处理 "星期一 17:30"（最近7天内的星期一）
        elif "星期" in time_str:
            weekday_map = {"一": 0, "二": 1, "三": 2, "四": 3, "五": 4, "六": 5, "日": 6}
            weekday_str = re.search(r"星期([一二三四五六日])", time_str).group(1)
            weekday = weekday_map[weekday_str]
            time_part = parser.parse(time_str.split()[-1]).time()

            # 计算最近的该星期几
            target_date = now.date() - timedelta(days=(now.weekday() - weekday) % 7)
            return datetime.combine(target_date, time_part)

        # 4. 处理 "3月28日 17:30"（最近一年内的该日期）
        elif "月" in time_str and "日" in time_str and "年" not in time_str:
            month_day, time_part_str = time_str.split()
            month = int(re.search(r"(\d+)月", month_day).group(1))
            day = int(re.search(r"(\d+)日", month_day).group(1))
            time_part = parser.parse(time_part_str).time()

            # 尝试今年，如果已经过去则用去年
            try:
                target_date = datetime(now.year, month, day).date()
                if target_date > now.date():
                    target_date = datetime(now.year - 1, month, day).date()
            except ValueError:  # 处理非法日期（如2月30日）
                target_date = datetime(now.year - 1, month, day).date()

            return datetime.combine(target_date, time_part)

        # 5. 处理 "2024年3月28日 17:30"（完整日期时间）
        else:
            # 将中文日期转换为标准格式
            time_str = time_str.replace("年", "-").replace("月", "-").replace("日", "")
            return parser.parse(time_str)


@dataclass
class HwMessage:
    hw_name: str
    type:str
    message: list[Message]


if __name__ == '__main__':
    test_cases = [
        "dui17:30",
        "昨天 17:30",
        "星期一 17:30",
        "3月28日 17:30",
        "2021年3月28日 17:30"
    ]

    for case in test_cases:
        if Message.is_time_string(case):
            message = Message(user_name="1", time=datetime.now(), msg="2")
            print(f"输入: {case} -> 输出: {Message.parse_time_string(case)}")

    # time1 = datetime.now()
    # message1 = Message("1",time1,"1")
    # time.sleep(1)
    # time1 = datetime.now()
    # message2 = Message("2",time1,"2")
    # print(message1.time)
    # print(message2.time)
