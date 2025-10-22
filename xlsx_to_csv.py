import pandas as pd
import os

# 输入xlsx文件路径
xlsx_path = "D:/potato/Cold_AC_M4_2h.xlsx"
# 输出CSV文件夹路径（自动创建）
csv_dir = "csv_output_Cold_AC_M4_2h"
os.makedirs(csv_dir, exist_ok=True)

# 读取xlsx文件
excel_file = pd.ExcelFile(xlsx_path)

# 遍历所有工作表并转换为csv
for sheet_name in excel_file.sheet_names:
    df = excel_file.parse(sheet_name)
    # 保存为csv，index=False表示不保留行索引
    csv_path = os.path.join(csv_dir, f"{sheet_name}.csv")
    df.to_csv(csv_path, index=False)

print("转换完成！所有工作表已保存为CSV。")