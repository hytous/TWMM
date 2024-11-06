import cv2
import rasterio
import os

tiff_path = r'../test_img/11-44-43-767-radiometric.tiff'
jpg_path = r'../test_img/11-44-43-767-radiometric.jpg'
save_path = r'../what_about_tiff/out_pic'

# 确保保存目录存在
os.makedirs(os.path.dirname(save_path), exist_ok=True)

# 读取 JPG 图像
img = cv2.imread(jpg_path)

# 假设 img 是伪彩色图像（RGB 或 BGR），将其转换为灰度图像
gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # 使用 BGR 转灰度

# 直接按比例放大像素值（0-255 放大到 0-65535）
gray_img_stretched = (gray_img.astype('float32') * 255).astype('uint16')

# 保存为 TIFF 格式（灰度图）
save_tiff_path = os.path.join(save_path, 'gray_image_stretched.tiff')

# 使用 rasterio 保存为 TIFF 格式
height, width = gray_img_stretched.shape
with rasterio.open(
    save_tiff_path, 'w', driver='GTiff',
    height=height, width=width, count=1, dtype='uint16'
) as dst:
    dst.write(gray_img_stretched, 1)  # 写入第一个通道

print(f"Gray image saved as {save_tiff_path}")
