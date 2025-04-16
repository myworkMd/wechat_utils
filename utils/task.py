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
                    exec_time TEXT NOT NULL
                )
            ''')

    def _load_tasks(self):
        """
        从数据库加载所有任务并重新调度
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT * FROM tasks')
            for row in cursor.fetchall():
                task_id, method, args, kwargs, description, exec_time = row
                self.tasks[task_id] = {
                    'task_id': task_id,
                    'method': method,
                    'args': json.loads(args) if args else [],
                    'kwargs': json.loads(kwargs) if kwargs else {},
                    'description': description,
                    'exec_time': exec_time
                }
                schedule.every().day.at(exec_time).do(self._execute_task, task_id)


    def _execute_task(self, task_id):
        task = self.tasks[task_id]
        # 解析模块路径和方法名
        module_path, method_name = task['method'].rsplit('.', 1)
        # 动态导入模块
        module = __import__(module_path, fromlist=[method_name])
        # 获取方法
        method = getattr(module, method_name)
        # 调用方法
        method(*task['args'], **task.get('kwargs', {}))
        self._remove_task_from_db(task_id)
        del self.tasks[task_id]


    def _save_task_to_db(self, task_id, task_data):
        """
        将任务保存到数据库
        :param task_id: 任务ID
        :param task_data: 任务数据
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO tasks (id, method, args, kwargs, description, exec_time)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                task_id,
                task_data['method'],
                json.dumps(task_data.get('args', [])),
                json.dumps(task_data.get('kwargs', {})),
                task_data.get('description', ''),
                task_data['exec_time']
            ))

    def _remove_task_from_db(self, task_id):
        """
        从数据库删除任务
        :param task_id: 要删除的任务ID
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM tasks WHERE id = ?', (task_id,))


    def schedule_task(self, task_info: str, exec_time: str) -> str:
        """
        调度新任务
        :param task_info: 包含方法名、参数和任务描述的json字符串
        :param exec_time: 执行时间字符串，格式为"YYYY-MM-DD HH:MM:SS"或"HH:MM"
        :return: 新创建的任务ID
        """
        task_data = json.loads(task_info)
        task_id = str(uuid4())
        
        # 解析执行时间
        try:
            # 尝试解析为完整时间格式
            exec_datetime = datetime.strptime(exec_time, "%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            delay_seconds = (exec_datetime - now).total_seconds()
            
            # 如果时间已经过去，立即执行
            if delay_seconds <= 0:
                delay_seconds = 0
            
            # 使用schedule的every方法设置延迟执行
            schedule.every(delay_seconds).seconds.do(self._execute_task, task_id)
        except ValueError:
            # 如果解析失败，使用原来的每天固定时间格式
            schedule.every().day.at(exec_time).do(self._execute_task, task_id)
        
        self.tasks[task_id] = {
            'task_id': task_id,
            'method': task_data['method'],
            'args': task_data.get('args', []),
            'kwargs': task_data.get('kwargs', {}),
            'description': task_data.get('description', ''),
            'exec_time': exec_time
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