from pathlib import Path
import cv2
import os
import rasterio
from PIL import Image
import numpy as np
# 文件夹路径
visual_file_path = r'D:\S\study\postg_1\Mygo\registration\ir_visi_img\haiNingZhengTai70Mi\visible'
thermal_file_path = r'D:\S\study\postg_1\Mygo\registration\ir_visi_img\haiNingZhengTai70Mi\thermal'
tiff_file_path = r'D:\S\study\postg_1\Mygo\registration\ir_visi_img\haiNingZhengTai70Mi\tiff'


def get_my_image_path():
    folder_paths = [Path(visual_file_path), Path(thermal_file_path), Path(tiff_file_path)]
    path_collect = []
    name_only = []
    for folder_path in folder_paths:
        # 获取文件夹内所有 .jpg 文件，使用大小写不敏感匹配
        jpg_files = list(folder_path.glob('*.jpg')) + list(folder_path.glob('*.JPG')) + list(folder_path.glob('*.tiff'))
        # 获取第一个 jpg 文件的路径
        if jpg_files:
            first_jpg_path = jpg_files[0]
            print("First JPG file path:", first_jpg_path)
            path_collect.append(first_jpg_path)  # 记录路径
            # 拆分路径，获取文件名（带扩展名）
            file_name = first_jpg_path.name
            print("File name:", file_name)
            # 获取文件名，不带扩展名
            file_name_without_extension = first_jpg_path.stem
            name_only.append(file_name_without_extension)  # 记录图片名字
            print("File name without extension:", file_name_without_extension)
        else:
            print(f"No JPG files found in the folder: {folder_path}")
    if len(path_collect) <= 2:
        print("雀食没有tiff图")
        # thermal_img = cv2.imread(path_collect[1])  # imread不能读取中文路径
        # cv2.imshow('thermal_img', thermal_img)
        # 使用 Pillow 打开图片
        thermal_img = Image.open(path_collect[1])
        # 显示图像
        thermal_img.show()
        # 转换为灰度图
        gray_img = thermal_img.convert('L')
        # 显示灰度图
        gray_img.show()
        # 将 PIL 图像转换为 numpy 数组
        gray_img_np = np.array(gray_img)

        # 直接按比例放大像素值（0-255 放大到 0-65535）
        gray_img_stretched = (gray_img_np.astype('float32') * 255).astype('uint16')

        # TIFF 的保存路径+文件名
        save_tiff_path = os.path.join(tiff_file_path, name_only[1] + '.tiff')
        print("tiff的路径：", save_tiff_path)
        # 使用 rasterio 保存为 TIFF 格式
        height, width = gray_img_stretched.shape
        with rasterio.open(
                save_tiff_path, 'w', driver='GTiff',
                height=height, width=width, count=1, dtype='uint16'
        ) as dst:
            dst.write(gray_img_stretched, 1)  # 写入第一个通道
        path_collect.append(save_tiff_path)
    return str(path_collect[0]), str(path_collect[1]), str(path_collect[2])


if __name__ == '__main__':
    path0, path1, path2 = get_my_image_path()
    print(path0)
    print(path1)
    print(path2)
