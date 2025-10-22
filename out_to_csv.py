import csv


def process_out(out_file, csv_file):
    with open(out_file, "r", encoding="utf-8") as infile, \
            open(csv_file, "w", newline="", encoding="utf-8") as outfile:

        writer = csv.writer(outfile)
        # 只保留前两列的表头
        writer.writerow(["参考基因ID", "对比基因ID"])

        for line in infile:
            line = line.strip()
            if not line:
                continue  # 跳过空行

            cols = line.split()  # 按空白分割（支持空格/制表符）
            if len(cols) < 2:
                continue  # 至少需要2列才处理

            # 处理第一列：删除 '.' 及之后的内容
            ref_id = cols[0].split('.')[0] if '.' in cols[0] else cols[0]

            # 处理第二列：
            # 1. 提取 'Smochap' 及之后的部分
            query_str = cols[1]
            if 'Smochap' in query_str:
                query_part = query_str.split('Smochap', 1)[1]  # 保留 'Smochap' 后面的内容
                # 2. 再删除 '.' 及之后的内容
                query_id = 'Smochap' + (query_part.split('.')[0] if '.' in query_part else query_part)
            else:
                # 若没有 'Smochap'，则直接删除 '.' 及之后的内容
                query_id = query_str.split('.')[0] if '.' in query_str else query_str

            # 只写入处理后的前两列
            writer.writerow([ref_id, query_id])


if __name__ == "__main__":
    # 输入输出文件路径
    process_out(
        "D:/potato/best/T206.C830.best",  # 输入文件
        "D:/potato/best/T206_C830.csv"  # 输出文件
    )