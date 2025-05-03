"""
任务调度器模块

核心功能：
1. 支持定时任务的调度和执行
2. 任务信息持久化到SQLite数据库，程序重启后可恢复
3. 支持通过任务ID取消已调度的任务
4. 支持查看所有等待执行的任务
5. 支持通过方法名动态调用任意模块的方法

使用示例：
1. 调度任务：
   task_info = json.dumps({
       'method': "robot.WeChatWork.send_message",
       'args': ["测试消息", "文件传输助手"],  # 位置参数
       'kwargs': {},  # 关键字参数
       'description': '测试任务'
   })
   exec_time = (datetime.now() + timedelta(minutes=10)).strftime("%H:%M")
   task_id = task_scheduler.schedule_task(task_info, exec_time)

2. 取消任务：
   task_scheduler.cancel_task(task_id)

3. 查看所有任务：
   tasks = task_scheduler.get_all_tasks()
   print(tasks)

4. 停止调度器：
   task_scheduler.stop()
"""

import schedule
import time
import json
from uuid import uuid4
from threading import Thread
import sqlite3
from datetime import datetime


def create_task_id() -> str:
    return str(uuid4())


class TaskScheduler:
    def __init__(self, db_path='tasks.db'):
        """
        初始化任务调度器
        :param db_path: SQLite数据库文件路径，默认为'tasks.db'
        """
        self.tasks = {}
        self.running = True
        self.thread = Thread(target=self.run_pending)
        self.db_path = db_path
        self._init_db()
        self._load_tasks()
        self.thread.start()

    def _init_db(self):
        """
        初始化数据库，创建任务表（如果不存在）
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    method TEXT NOT NULL,
                    args TEXT,
                    kwargs TEXT,
                    description TEXT,
                    exec_time TEXT NOT NULL,
                    interval_type TEXT,
                    interval_value TEXT
                )
            ''')

    def _load_tasks(self):
        """
        从数据库加载所有任务并重新调度
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT * FROM tasks')
            for row in cursor.fetchall():
                task_id, method, args, kwargs, description, exec_time, interval_type, interval_value = row
                self.tasks[task_id] = {
                    'task_id': task_id,
                    'method': method,
                    'args': json.loads(args) if args else [],
                    'kwargs': json.loads(kwargs) if kwargs else {},
                    'description': description,
                    'exec_time': exec_time,
                    'interval_type': interval_type,
                    'interval_value': interval_value
                }
                print(self.tasks[task_id])
                # 重新调度任务
                if interval_type is None:
                    # 单次任务
                    try:
                        exec_datetime = datetime.strptime(exec_time, "%Y-%m-%d %H:%M:%S")
                        now = datetime.now()
                        delay_seconds = (exec_datetime - now).total_seconds()
                        if delay_seconds <= 0:
                            delay_seconds = 1
                        print("1")
                        schedule.every(delay_seconds).seconds.do(self._execute_task, task_id)
                    except ValueError:
                        print("2")
                        schedule.every().day.at(exec_time).do(self._execute_task, task_id)
                else:
                    # 循环任务
                    if interval_type == 'seconds':
                        schedule.every(int(interval_value)).seconds.do(self._execute_task, task_id)
                    elif interval_type == 'minutes':
                        schedule.every(int(interval_value)).minutes.do(self._execute_task, task_id)
                    elif interval_type == 'hours':
                        schedule.every(int(interval_value)).hours.do(self._execute_task, task_id)
                    elif interval_type == 'days':
                        schedule.every(int(interval_value)).days.do(self._execute_task, task_id)
                    elif interval_type == 'weeks':
                        schedule.every(int(interval_value)).weeks.do(self._execute_task, task_id)
                    elif interval_type == 'weekday':
                        schedule.every().week.at(exec_time).do(self._execute_task, task_id)
                    elif interval_type == 'monthday':
                        schedule.every().month.at(exec_time).do(self._execute_task, task_id)
                    elif interval_type == 'yearly':
                        schedule.every().year.at(exec_time).do(self._execute_task, task_id)

    def _save_task_to_db(self, task_id, task_data):
        """
        将任务保存到数据库
        :param task_id: 任务ID
        :param task_data: 任务数据
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO tasks (id, method, args, kwargs, description, exec_time, interval_type, interval_value)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task_id,
                task_data['method'],
                json.dumps(task_data.get('args', [])),
                json.dumps(task_data.get('kwargs', {})),
                task_data.get('description', ''),
                task_data['exec_time'],
                task_data.get('interval_type'),
                task_data.get('interval_value')
            ))

    def _execute_task(self, task_id):
        # 检查任务是否存在
        if task_id not in self.tasks:
            return

        task = self.tasks[task_id]
        # 解析模块路径和方法名
        module_path, method_name = task['method'].rsplit('.', 1)
        # 动态导入模块
        module = __import__(module_path, fromlist=[method_name])
        # 获取方法
        method = getattr(module, method_name)
        # 调用方法
        method(*task['args'], **task.get('kwargs', {}))
        interval_type = task.get('interval_type')

        if interval_type is None:
            # 单次执行
            self._remove_task_from_db(task_id)
            del self.tasks[task_id]

        else:
            # 循环执行
            print("循环执行")

    def _remove_task_from_db(self, task_id):
        """
        从数据库删除任务
        :param task_id: 要删除的任务ID
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM tasks WHERE id = ?', (task_id,))

    def schedule_task(self, task_info: str, task_id=create_task_id()) -> str:
        """
        调度任务
        :param task_id: 指定任务Id
        :param task_info: 包含任务信息的json字符串，格式如下：
            {
                "method": "模块路径.方法名",  # 要执行的方法，例如"robot.WeChatWork.send_message"
                "args": [],  # 位置参数列表（可选）
                "kwargs": {},  # 关键字参数字典（可选）
                "description": "任务描述",  # 任务描述信息（可选）
                "exec_time": "执行时间",  # 执行时间，格式为"YYYY-MM-DD HH:MM:SS"
                "interval_type": "循环类型",  # 可选，支持以下值：
                                            # 'seconds' - 每过多少秒
                                            # 'minutes' - 每过多少分钟
                                            # 'hours' - 每过多少小时
                                            # 'days' - 每过多少天
                                            # 'weeks' - 每过多少周
                                            # 'weekday' - 每个星期几（0-6，0表示周一）
                "interval_value": "循环间隔值"  # 可选，与interval_type配合使用
            }
        :return: 新创建的任务ID
        """
        task_data = json.loads(task_info)

        # 解析执行时间
        exec_datetime = datetime.strptime(task_data['exec_time'], "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        delay_seconds = (exec_datetime - now).total_seconds()

        # 如果时间已经过去，立即执行
        if delay_seconds <= 0:
            delay_seconds = 1

        # 判断是否为循环任务
        interval_type = task_data.get('interval_type')
        interval_value = task_data.get('interval_value')

        if interval_type is None:
            # 单次执行
            print("单次执行")
            schedule.every(delay_seconds).seconds.do(self._execute_task, task_id)
        else:
            # 循环执行
            print("循环执行")
            if interval_type == 'seconds':
                schedule.every(interval_value).seconds.do(self._execute_task, task_id)
            elif interval_type == 'minutes':
                schedule.every(interval_value).minutes.do(self._execute_task, task_id)
            elif interval_type == 'hours':
                schedule.every(interval_value).hours.do(self._execute_task, task_id)
            elif interval_type == 'days':
                schedule.every(interval_value).days.do(self._execute_task, task_id)
            elif interval_type == 'weeks':
                schedule.every(interval_value).weeks.do(self._execute_task, task_id)
            elif interval_type == 'weekday':
                schedule.every().week.at(task_data['exec_time']).do(self._execute_task, task_id)
            # elif interval_type == 'monthday':
            #     schedule.every().month.at(task_data['exec_time']).do(self._execute_task, task_id)
            # elif interval_type == 'yearly':
            #     month, day = interval_value.split('-')
            #     schedule.every().year.at(task_data['exec_time']).do(self._execute_task, task_id)
            else:
                raise ValueError(f"不支持的循环类型: {interval_type}")

        # 保存任务信息
        self.tasks[task_id] = {
            'task_id': task_id,
            'method': task_data['method'],
            'args': task_data.get('args', []),
            'kwargs': task_data.get('kwargs', {}),
            'description': task_data.get('description', ''),
            'exec_time': task_data['exec_time'],
            'interval_type': interval_type,
            'interval_value': interval_value
        }
        self._save_task_to_db(task_id, self.tasks[task_id])
        return task_id

    def cancel_task(self, task_id: str) -> bool:
        """
        取消已调度的任务
        :param task_id: 要取消的任务ID
        :return: 是否成功取消
        """
        if task_id in self.tasks:
            schedule.clear(tag=task_id)
            self._remove_task_from_db(task_id)
            del self.tasks[task_id]
            return True
        return False

    def get_all_tasks(self) -> str:
        """
        获取所有等待执行的任务
        :return: 包含所有任务信息的json字符串
        """
        return json.dumps(list(self.tasks.values()))

    def run_pending(self):
        """
        后台运行任务调度，定期检查并执行到期任务
        """
        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def stop(self):
        """
        停止任务调度器，关闭后台线程
        """
        self.running = False
        self.thread.join()
