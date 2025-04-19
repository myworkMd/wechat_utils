import json
from flask import Flask, request, jsonify
from flasgger import Swagger
from WeChatWork import init, send_message, get_message, send_file, forward_message, add_friend, add_note_name

app = Flask(__name__)
swagger = Swagger(app)

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
                description: 目标用户名（可选）
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
    data = request.get_json()
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
    data = request.get_json()
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


if __name__ == '__main__':
    init("komnenos")
    app.run(host='0.0.0.0', port=5000)
