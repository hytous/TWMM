

import cv2
import rasterio
import os

tiff_path = r'../test_img/11-44-43-767-radiometric.tiff'
jpg_path = r'../test_img/11-44-43-767-radiometric.jpg'
save_path = r'../what_about_tiff/out_pic'

# 确保保存目录存在
os.makedirs(save_path, exist_ok=True)

# 使用 rasterio 打开 TIFF 图像
with rasterio.open(tiff_path) as dataset:
    img = dataset.read(1)  # 假设只读取第一个通道（灰度图）

    # 获取图像的形状
    height, width = img.shape

# 根据图像的 shape 进行处理
if len(img.shape) == 2:  # 单通道图像（灰度图）
    print("The image is grayscale with shape:", img.shape)
    # 进一步处理灰度图（比如直接应用伪彩色映射）
    img_normalized = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX).astype('uint8')
    rgb_img = cv2.applyColorMap(img_normalized, cv2.COLORMAP_JET)
elif len(img.shape) == 3:  # 三通道彩色图像（RGB或BGR）
    print("The image is a color image with shape:", img.shape)
    # 处理彩色图像（比如对每个通道进行操作）
    rgb_img = img  # 如果图像本身是RGB（或BGR），可以直接使用
else:
    print("Unknown image type or shape:", img.shape)

# 显示原图和处理后的图像
cv2.imshow('Original Image', img_normalized if len(img.shape) == 2 else img)  # 显示灰度图或RGB图
cv2.imshow('Processed Image', rgb_img)  # 显示处理后的图像

# 保存处理后的图像到指定路径
cv2.imwrite(os.path.join(save_path, 'tiff_to_rgb.jpg'), rgb_img)

cv2.waitKey(0)
cv2.destroyAllWindows()
