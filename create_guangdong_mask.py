"""
创建广东省地图轮廓的mask图像，用于词云形状
"""

from PIL import Image, ImageDraw
import numpy as np

def create_guangdong_mask():
    """
    创建一个简化的广东省轮廓mask
    使用多边形近似广东省的形状
    """
    # 创建白色背景
    width, height = 800, 600
    mask = Image.new('L', (width, height), 255)  # 白色背景
    draw = ImageDraw.Draw(mask)
    
    # 广东省轮廓的近似坐标（简化版）
    # 这些坐标是基于广东省地图的大致形状
    guangdong_outline = [
        (150, 100),   # 北部起点
        (200, 80),
        (280, 90),
        (350, 85),
        (420, 95),
        (500, 100),
        (550, 120),
        (600, 150),
        (630, 200),
        (650, 250),
        (660, 300),
        (650, 350),
        (620, 400),
        (580, 450),
        (520, 480),
        (450, 500),
        (380, 510),
        (300, 500),
        (220, 480),
        (150, 450),
        (100, 400),
        (80, 350),
        (70, 300),
        (75, 250),
        (90, 200),
        (110, 150),
        (130, 120),
        (150, 100),   # 闭合
    ]
    
    # 绘制黑色填充的广东省轮廓
    draw.polygon(guangdong_outline, fill=0)  # 黑色=0，白色=255
    
    # 保存mask
    mask.save('guangdong_mask.png')
    print("✅ 已创建 guangdong_mask.png")
    
    return mask

if __name__ == '__main__':
    create_guangdong_mask()
