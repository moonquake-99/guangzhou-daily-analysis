"""
根据真实广东地图图片创建mask，用于词云形状
"""

from PIL import Image, ImageDraw
import numpy as np

def create_guangdong_mask_from_image():
    """
    从真实广东地图图片提取轮廓创建mask
    """
    # 打开广东地图图片
    map_image = Image.open('guangdong_real_map.png').convert('RGBA')
    
    # 获取图片尺寸
    width, height = map_image.size
    
    # 创建mask（与地图相同尺寸）
    mask = Image.new('L', (width, height), 255)  # 白色背景
    draw = ImageDraw.Draw(mask)
    
    # 将图片转换为数组，提取绿色区域（陆地部分）
    pixels = np.array(map_image)
    
    # 遍历像素，找出绿色区域（陆地）
    # 广东地图的绿色区域通常是陆地
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[y, x]
            
            # 判断是否为绿色区域（陆地）
            # 陆地通常是绿色系，海洋是白色或浅蓝色
            # 简单判断：绿色分量明显大于其他
            if g > 100 and g > r and g > b:
                # 这是陆地，设为黑色（0）
                draw.point((x, y), fill=0)
    
    # 保存mask
    mask.save('guangdong_mask.png')
    print(f"✅ 已创建 guangdong_mask.png ({width}x{height})")
    
    return mask

def create_guangdong_mask_manual():
    """
    手动绘制更精确的广东地图轮廓
    基于真实地图形状
    """
    width, height = 1000, 750
    mask = Image.new('L', (width, height), 255)  # 白色背景
    draw = ImageDraw.Draw(mask)
    
    # 广东地图轮廓坐标（更精确的版本）
    # 基于真实地图的形状，包括湛江半岛、潮汕地区等
    guangdong_outline = [
        # 北部起点（湖南交界）
        (200, 50),
        (250, 40),
        (300, 35),
        (350, 45),
        (400, 40),
        (450, 50),
        (500, 45),
        (550, 55),
        (600, 50),
        (650, 60),
        (700, 70),
        # 东部（梅州、潮州、汕头）
        (750, 80),
        (800, 100),
        (850, 130),
        (900, 160),
        (920, 200),
        (930, 250),
        (920, 300),
        (900, 350),
        (870, 400),
        (850, 450),
        (820, 500),
        # 东南部（汕尾、揭阳）
        (780, 530),
        (750, 560),
        (720, 580),
        # 南部沿海（深圳、珠海）
        (680, 600),
        (640, 620),
        (600, 640),
        (550, 650),
        (500, 660),
        (450, 655),
        (400, 640),
        # 西南部（阳江、茂名、湛江）
        (350, 650),
        (300, 670),
        (250, 690),
        (200, 710),
        (150, 720),
        (120, 700),
        # 湛江半岛
        (100, 680),
        (80, 650),
        (70, 620),
        (80, 590),
        (100, 570),
        # 西部（云浮、肇庆）
        (130, 550),
        (150, 520),
        (180, 490),
        (200, 460),
        (220, 430),
        # 西北部（清远、韶关）
        (200, 400),
        (180, 370),
        (160, 340),
        (150, 300),
        (160, 260),
        (170, 220),
        (180, 180),
        (190, 140),
        (200, 100),
        (200, 50),  # 闭合
    ]
    
    # 绘制黑色填充的广东省轮廓
    draw.polygon(guangdong_outline, fill=0)  # 黑色=0，白色=255
    
    # 保存mask
    mask.save('guangdong_mask.png')
    print(f"✅ 已创建 guangdong_mask.png ({width}x{height})")
    
    return mask

if __name__ == '__main__':
    # 先尝试手动创建
    create_guangdong_mask_manual()
