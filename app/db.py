import pymysql
from flask import current_app


def get_conn():
    """获取数据库连接（保持原有逻辑不变）"""
    cfg = current_app.config
    return pymysql.connect(
        host=cfg["DB_HOST"],
        port=cfg["DB_PORT"],
        user=cfg["DB_USER"],
        password=cfg["DB_PASS"],
        database=cfg["DB_NAME"],
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


def query_one_table(table: str, key_col: str, key_value: str):
    """
    支持条件查询与全表查询的通用函数
    - 全表查询：key_col传递"*"，忽略key_value
    - 条件查询：key_col传递字段名，key_value传递查询值
    """
    # 全表查询逻辑（新增）
    if key_col == "*":
        sql = f"SELECT * FROM `{table}`"
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
                return cur.fetchall()
        finally:
            conn.close()

    # 原有条件查询逻辑（保留）
    sql = f"SELECT * FROM `{table}` WHERE `{key_col}`=%s"
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (key_value,))
            return cur.fetchall()
    finally:
        conn.close()

def query_db(sql: str, params: tuple = None, one: bool = False):
    """
    执行自定义SQL查询
    :param sql: 自定义SQL语句（使用%s作为参数占位符）
    :param params: SQL参数（元组类型，可选）
    :param one: 是否只返回单条结果，默认False（返回所有结果）
    :return: 查询结果（字典或字典列表）
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            if params:
                cur.execute(sql, params)
            else:
                cur.execute(sql)
            # 根据 one 参数决定返回单条还是所有结果
            return cur.fetchone() if one else cur.fetchall()
    finally:
        conn.close()
