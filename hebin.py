import pandas as pd
import os
import chardet  # 用于自动检测文件编码


def get_file_encoding(file_path):
    """检测文件编码格式（读取前10000字节，避免读取大文件耗时）"""
    with open(file_path, 'rb') as f:
        raw_data = f.read(10000)  # 读取文件头部数据用于检测
    result = chardet.detect(raw_data)
    return result['encoding']  # 返回检测到的编码（如utf-8、GB2312等）


def merge_csv_files(input_dir, output_file):
    all_data = []  # 存储所有CSV文件的数据
    csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]  # 筛选CSV文件

    if not csv_files:
        print(f"在目录 {input_dir} 中未找到CSV文件")
        return

    for filename in csv_files:
        file_path = os.path.join(input_dir, filename)
        try:
            # 步骤1：检测当前文件的编码
            encoding = get_file_encoding(file_path)
            # 处理编码检测结果（若检测失败，默认用utf-8尝试）
            if encoding is None:
                encoding = 'utf-8'
            print(f"正在处理: {filename}，编码: {encoding}")

            # 步骤2：用检测到的编码读取CSV文件（移除errors参数）
            df = pd.read_csv(file_path, encoding=encoding)

            # 步骤3：将当前文件数据加入列表
            all_data.append(df)
            print(f"成功读取: {filename}，数据行数: {len(df)}")

        except Exception as e:
            # 捕获读取异常（如编码不匹配、文件损坏等）
            print(f"读取 {filename} 失败: {str(e)}，已跳过该文件")
            continue

    # 步骤4：合并所有有效数据并保存
    if all_data:
        merged_df = pd.concat(all_data, ignore_index=True)  # 合并数据，重置索引
        merged_df.to_csv(output_file, index=False, encoding='utf-8')  # 保存为UTF-8编码的CSV
        print(f"\n合并完成！共合并 {len(all_data)} 个CSV文件，总数据行数: {len(merged_df)}")
        print(f"合并后的文件已保存至: {output_file}")
    else:
        print("\n所有CSV文件均读取失败，未生成合并文件")


if __name__ == "__main__":
    # 配置输入目录和输出文件路径（根据实际情况修改）
    INPUT_DIRECTORY = "D:/potato/best"  # 存放待合并CSV的目录
    OUTPUT_FILE = "D:/potato/merged_all.csv"  # 合并后的输出文件

    # 执行合并函数
    merge_csv_files(INPUT_DIRECTORY, OUTPUT_FILE)