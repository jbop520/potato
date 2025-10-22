import pandas as pd

# 尝试不同的编码格式读取文件
try:
    # 先尝试GBK编码（中文Windows系统常见）
    df = pd.read_csv("D:/potato/cold_links.csv", encoding='gbk')
except UnicodeDecodeError:
    try:
        # 再尝试GB2312编码
        df = pd.read_csv("D:/potato/cold_links.csv", encoding='gb2312')
    except UnicodeDecodeError:
        # 最后尝试UTF-8编码
        df = pd.read_csv("D:/potato/cold_links.csv", encoding='utf-8')

# 计算起始行索引（从0开始）
start_index = 460712  # 从第460712条数据开始处理


# 定义处理函数：保留Smo及之后的部分
def keep_smo_and_after(text):
    # 查找"Smo"的位置
    smo_index = text.find("Smo")
    if smo_index != -1:  # 如果找到了"Smo"
        return text[smo_index:]  # 返回从"Smo"开始的子字符串
    return text  # 如果没有找到"Smo"，返回原字符串


# 从指定行开始处理"参考基因ID"列
df.loc[start_index:, "参考基因ID"] = df.loc[start_index:, "参考基因ID"].apply(keep_smo_and_after)

# 保存处理后的文件
df.to_csv("D:/potato/processed1_cold_links.csv", index=False, encoding='utf-8')

print(f"处理完成！已从第{start_index + 1}行开始保留参考基因ID中的Smo及之后部分")
