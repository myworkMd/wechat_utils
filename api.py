import json
from flask import Flask, request, jsonify
from flasgger import Swagger
from robot.WeChatWork import init, send_message, get_message, send_file, forward_message, add_friend, add_note_name
from utils.task import TaskScheduler
from datetime import datetime
from utils.TimeCalculator import TimeCalculator
import utils.task as task

# 初始化任务调度器
task_scheduler = TaskScheduler()

app = Flask(__name__)
swagger = Swagger(app)


@app.before_request
def log_request_info():
    """拦截所有请求，打印请求方法和参数"""
    print("\n===== 请求信息 =====")
    print(f"请求方法: {request.method}")
    print(f"请求路径: {request.path}")
    print(f"请求头: {dict(request.headers)}")

    # 打印 GET 请求的查询参数
    if request.args:
        print("查询参数 (GET):", request.args.to_dict())

    # 打印 POST/PUT/PATCH 请求的 JSON Body
    if request.method in ("POST", "PUT", "PATCH") and request.is_json:
        print("请求体 (JSON):", request.get_json())
    elif request.method == "POST" and request.form:
        print("请求体 (Form Data):", request.form.to_dict())
    elif request.method == "POST" and request.data:
        print("请求体 (Raw Data):", request.data.decode("utf-8"))


def filtered_none_json(data):
    return {k: v for k, v in data.items() if v is not None}


@app.route('/send_message', methods=['POST'])
def api_send_message():
    """
    发送消息
    ---
    tags:
      - 消息操作
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              message:
                type: string
                description: 消息内容
              user_name:
                type: string
                description: 目标用户名（可选）,不填则在当前打开的聊天发送消息
    responses:
      200:
        description: 消息发送成功
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "请求体不能为空"}), 400

        msg = data.get('message')
        user_name = data.get('user_name', '')

        if not msg:
            return jsonify({"status": "error", "message": "message字段不能为空"}), 400

        send_message(msg, user_name)
        return jsonify({"status": "success", "message": "Message sent"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/get_message', methods=['GET'])
def api_get_message():
    """
    获取消息
    ---
    tags:
      - 消息操作
    parameters:
      - in: query
        name: user_name
        type: string
        required: false
        description: 目标用户名
      - in: query
        name: max_messages
        type: integer
        required: false
        description: 最大获取消息数量（默认-1表示获取所有）
    responses:
      200:
        description: 消息获取成功
    """
    user_name = request.args.get('user_name', '')
    max_messages = int(request.args.get('max_messages', -1))
    messages = get_message(user_name, max_messages)
    return jsonify({"status": "success", "messages": messages})


@app.route('/send_file', methods=['POST'])
def api_send_file():
    """
    发送文件
    ---
    tags:
      - 文件操作
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              file_path:
                type: string
                description: 文件路径
              user_name:
                type: string
                description: 目标用户名（可选）
    responses:
      200:
        description: 文件发送成功
    """
    data = filtered_none_json(request.get_json())
    file_path = data.get('file_path')
    user_name = data.get('user_name', '')
    send_file(file_path, user_name)
    return jsonify({"status": "success", "message": "File sent"})


@app.route('/forward_message', methods=['POST'])
def api_forward_message():
    """
    转发消息
    ---
    tags:
      - 消息操作
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              message:
                type: string
                description: 消息内容
              address:
                type: string
                description: 转发对象
              postscript:
                type: string
                description: 转发附言（可选）
    responses:
      200:
        description: 消息转发成功
    """
    data = filtered_none_json(request.get_json())
    message = data.get('message')
    address = data.get('address')
    postscript = data.get('postscript', '')
    forward_message(message, address, postscript)
    return jsonify({"status": "success", "message": "Message forwarded"})


@app.route('/add_friend', methods=['POST'])
def api_add_friend():
    """
    添加好友
    ---
    tags:
      - 好友管理
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties: {}
    responses:
      200:
        description: 添加好友成功
    """
    result = add_friend()
    return jsonify({"status": "success", "result": result})


@app.route('/add_note_name', methods=['POST'])
def api_add_note_name():
    """
    添加备注名
    ---
    tags:
      - 好友管理
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              note_name:
                type: string
                description: 备注名
              user_name:
                type: string
                description: 目标用户名
    responses:
      200:
        description: 备注名添加成功
    """
    data = request.get_json()
    note_name = data.get('note_name', '')
    user_name = data.get('user_name', '')
    result = add_note_name(note_name, user_name)
    return jsonify({"status": "success", "result": result})


@app.before_request
def enforce_content_type():
    if request.method in ['POST', 'PUT', 'PATCH']:
        request.environ['CONTENT_TYPE'] = 'application/json'
        if not request.is_json:
            return jsonify({"status": "error", "message": "Content-Type must be application/json"}), 415

@app.route('/schedule_message', methods=['POST'])
def api_schedule_message():
    """
    定时发送消息或循环发送消息
    ---
    tags:
      - 消息操作
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              message:
                type: string
                description: 消息内容
              description:
                type: string
                description: 任务描述，准确的任务描述方便后面查找时定位
              user_name:
                type: string
                description: 发送消息的目标用户名（可选），不填则在当前打开的聊天发送消息
              exec_time:
                type: string
                description: 期望执行时间（可选）,单次执行必填，循环执行不填，格式为"YYYY-MM-DD HH:MM:SS"
              interval_type:
                type: string
                description: 循环类型（可选），单次执行不填，循环执行必填，可选值：seconds, minutes, hours, days, weeks, weekday, monthday, yearly
              interval_value:
                type: string
                description: 循环间隔值（可选），单次执行不填，循环执行必填，与interval_type配合使用：'seconds' - 每过多少秒 ，'minutes' - 每过多少分钟 ，'hours' - 每过多少小时 ，'days' - 每过多少天 ，'weeks' - 每过多少周 ，'weekday' - 每个星期几（0-6，0表示周一）
    responses:
      200:
        description: 任务调度成功
    """
    try:
        data = filtered_none_json(request.get_json())
        if not data:
            return jsonify({"status": "error", "message": "请求体不能为空"}), 400

        msg = data.get('message')
        user_name = data.get('user_name', '')
        description = data.get('description','')
        exec_time = data.get('exec_time')
        interval_type = data.get('interval_type')
        interval_value = data.get('interval_value')

        if not msg:
            return jsonify({"status": "error", "message": "message字段不能为空"}), 400
        if not exec_time:
            return jsonify({"status": "error", "message": "exec_time字段不能为空"}), 400

        # 创建任务信息
        task_info = json.dumps({
            "method": "robot.WeChatWork.send_message",
            "args": [msg, user_name],
            "kwargs": {},
            "description": description,
            "exec_time": exec_time,
            "interval_type": interval_type,
            "interval_value": interval_value
        })

        # 调度任务
        task_id = task_scheduler.schedule_task(task_info)
        return jsonify({"status": "success", "task_id": task_id})
    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/cancel_task', methods=['POST'])
def api_cancel_task():
    """
    取消任务
    ---
    tags:
      - 任务调度
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              task_id:
                type: string
                description: 要取消的任务ID
    responses:
      200:
        description: 任务取消成功
    """
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        
        if not task_id:
            return jsonify({"status": "error", "message": "task_id字段不能为空"}), 400
            
        success = task_scheduler.cancel_task(task_id)
        if success:
            return jsonify({"status": "success", "message": "Task cancelled"})
        else:
            return jsonify({"status": "error", "message": "Task not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get_all_tasks', methods=['GET'])
def api_get_all_tasks():
    """
    获取所有任务
    ---
    tags:
      - 任务调度
    responses:
      200:
        description: 获取任务列表成功
    """
    try:
        tasks = task_scheduler.get_all_tasks()
        return jsonify({"status": "success", "tasks": tasks})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/get_now_time', methods=['GET'])
def api_get_now_time():
    """
    获取所有任务
    ---
    tags:
      - 任务调度
    responses:
      200:
        description: 获取当前时间成功
    """
    try:
        # 获取当前时间
        current_time = datetime.now()

        # 格式化为字符串
        time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
        return jsonify({"status": "success", "now_time": time_str})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/calculate_time', methods=['POST'])
def api_calculate_time():
    """
    时间计算
    ---
    tags:
      - 时间计算
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              delta_years:
                type: integer
                description: 年增量（可选）
              delta_months:
                type: integer
                description: 月增量（可选）
              delta_weeks:
                type: integer
                description: 周增量（可选）
              delta_days:
                type: integer
                description: 日增量（可选）
              delta_hours:
                type: integer
                description: 小时增量（可选）
              delta_minutes:
                type: integer
                description: 分钟增量（可选）
              delta_seconds:
                type: integer
                description: 秒增量（可选）
              fixed_year:
                type: integer
                description: 固定年份（可选）
              fixed_month:
                type: integer
                description: 固定月份（可选）
              fixed_day:
                type: integer
                description: 固定日期（可选）
              fixed_hour:
                type: integer
                description: 固定小时（可选）
              fixed_minute:
                type: integer
                description: 固定分钟（可选）
              fixed_second:
                type: integer
                description: 固定秒数（可选）
              fixed_weekday:
                type: integer
                description: 固定星期几（可选）
              base_time:
                type: string
                description: 基准时间（可选），格式为"YYYY-MM-DD HH:MM:SS"
    responses:
      200:
        description: 时间计算成功
    """
    try:
        data = filtered_none_json(request.get_json())
        print(data)
        # 解析基准时间
        base_time = None
        if data.get('base_time'):
            base_time = datetime.strptime(data.get('base_time'), "%Y-%m-%d %H:%M:%S")

        # 调用时间计算方法
        result = TimeCalculator.calculate(
            base_time=base_time,
            delta_years=data.get('delta_years', 0),
            delta_months=data.get('delta_months', 0),
            delta_weeks=data.get('delta_weeks', 0),
            delta_days=data.get('delta_days', 0),
            delta_hours=data.get('delta_hours', 0),
            delta_minutes=data.get('delta_minutes', 0),
            delta_seconds=data.get('delta_seconds', 0),
            fixed_year=data.get('fixed_year'),
            fixed_month=data.get('fixed_month'),
            fixed_day=data.get('fixed_day'),
            fixed_hour=data.get('fixed_hour'),
            fixed_minute=data.get('fixed_minute'),
            fixed_second=data.get('fixed_second'),
            fixed_weekday=data.get('fixed_weekday')
        )
        
        return jsonify({"status": "success", "calculated_time": result})
    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    init("komnenos")
    app.run(host='0.0.0.0', port=5000)
