"""
从真实广东地图提取精确轮廓并创建mask（不使用scipy）
"""

from PIL import Image, ImageDraw
import numpy as np

def create_mask_from_real_map():
    """
    从真实广东地图图片提取陆地轮廓创建mask
    """
    # 打开真实地图
    print("正在加载真实广东地图...")
    map_image = Image.open('C:/Users/17431/AppData/Roaming/Lingma/SharedClientCache/cache/images/93372be6/33-dff27216.png').convert('RGBA')
    
    width, height = map_image.size
    print(f"地图尺寸: {width} x {height}")
    
    # 转换为numpy数组
    pixels = np.array(map_image)
    
    # 创建mask（白色背景=255，黑色轮廓=0）
    mask = np.ones((height, width), dtype=np.uint8) * 255
    
    # 提取陆地部分（浅黄色区域）
    count = 0
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[y, x]
            
            # 判断是否为陆地（浅黄色区域）
            if (r > 200 and g > 200 and b < 230 and 
                b > 150 and
                a > 128):
                
                mask[y, x] = 0
                count += 1
    
    print(f"✅ 提取到 {count} 个陆地点")
    
    # 使用PIL的floodfill填充内部空洞
    # 先创建临时图像
    temp_img = Image.fromarray(mask)
    draw = ImageDraw.Draw(temp_img)
    
    # 从四个角开始填充白色（背景）
    # 这样可以确保外部是白色，内部陆地是黑色
    seed_points = [
        (0, 0),
        (width-1, 0),
        (0, height-1),
        (width-1, height-1)
    ]
    
    for seed in seed_points:
        x, y = seed
        if mask[y, x] == 255:  # 如果是白色，开始填充
            # 使用floodfill
            ImageDraw.floodfill(temp_img, seed, 255)
    
    # 转回numpy数组
    mask = np.array(temp_img)
    
    # 保存mask
    mask_image = Image.fromarray(mask)
    mask_image.save('guangdong_true_mask.png')
    print("✅ 已保存 guangdong_true_mask.png")
    
    # 统计信息
    land_pixels = np.sum(mask == 0)
    print(f"✅ 陆地像素: {land_pixels}")
    
    return mask_image

if __name__ == '__main__':
    create_mask_from_real_map()
