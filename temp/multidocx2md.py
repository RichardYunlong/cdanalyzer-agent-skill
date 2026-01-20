import os
import subprocess

# 配置：修改为你的主文件夹路径
root_folder = r"D:\BaiduNetdiskDownload\小说-云龙战神\正文"

# 递归遍历主文件夹及其所有子文件夹
for root, dirs, files in os.walk(root_folder):
    for file_name in files:
        # 筛选出后缀为.docx的文件（排除Word临时文件）
        if file_name.endswith(".docx") and not file_name.startswith("~$"):
            # 构建完整的输入docx路径和输出md路径
            docx_path = os.path.join(root, file_name)
            md_file_name = os.path.splitext(file_name)[0] + ".md"
            md_path = os.path.join(root, md_file_name)
            
            # 调用 python -m docx2md 执行转换
            try:
                subprocess.run(
                    ["python", "-m", "docx2md", docx_path, md_path],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    encoding="utf-8"
                )
                print(f"✅ 转换成功：{os.path.join(root, file_name)} → {md_path}")
            except subprocess.CalledProcessError as e:
                print(f"❌ 转换失败：{os.path.join(root, file_name)}，错误信息：{e.stderr}")