import os
import zipfile


def zip_files(source_path, output_zip_path):
    """
    将指定文件或文件夹压缩为 ZIP 文件。

    :param source_path: 要压缩的文件或文件夹路径
    :param output_zip_path: 输出的 ZIP 文件路径
    """
    with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        if os.path.isdir(source_path):
            # 压缩整个文件夹
            for root, dirs, files in os.walk(source_path):
                print("root="+root +" dirs="+repr(dirs))
                if root == ".venv":
                    print("hit root="+root)
                    continue
                for file in files:
                    file_path = os.path.join(root, file)
                    print("file_path="+file_path)
                    # 在 ZIP 中的相对路径
                    arcname = os.path.relpath(file_path, source_path)
                    zipf.write(file_path, arcname)
        else:
            # 压缩单个文件
            zipf.write(source_path, os.path.basename(source_path))


if __name__ == "__main__":
    # 示例用法
    source = "./"  # 要压缩的文件或文件夹
    output_zip = "./MyWebSideParser.zip"  # 压缩后 ZIP 文件的路径
    zip_files(source, output_zip)
    print(f"文件已成功压缩到 {output_zip}")
