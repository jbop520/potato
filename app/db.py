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