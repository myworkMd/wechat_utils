import sqlite3
from typing import Dict

"""
存储agent的聊天窗口Id。程序开始运行时，先将数据库里的user_name和对话id存入map中。
需要用id时，先看下user_map里有没有，没有的话，由外部创建新的聊天并生成会话id，再通过handle_new_user存入新的id
"""

# 初始化SQLite数据库连接
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_name TEXT PRIMARY KEY,
            id TEXT
        )
    ''')
    conn.commit()
    return conn


# 从数据库加载数据到字典
def load_users_to_map(conn) -> Dict[str, str]:
    cursor = conn.cursor()
    cursor.execute('SELECT user_name, id FROM users')
    users = {row[0]: row[1] for row in cursor.fetchall()}
    return users


# 处理新用户，更新user_map以及数据库
def handle_new_user(conn, user_map: Dict[str, str], user_name: str, id: str):
    if user_name not in user_map:
        user_map[user_name] = id
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (user_name, id) VALUES (?, ?)', (user_name, id))
            conn.commit()
        except sqlite3.IntegrityError:
            print(f"User {user_name} already exists in the database.")
    else:
        print(f"User {user_name} already exists in the map.")


def test():
    conn = init_db()
    user_map = load_users_to_map(conn)

    # 示例：检查并添加新用户
    handle_new_user(conn, user_map, "Alice", "asf")
    handle_new_user(conn, user_map, "Bob", "sferw")
    handle_new_user(conn, user_map, "Alice", "1")  # 重复添加

    print("Current user map:", user_map)
    conn.close()

if __name__ == "__main__":
    test()