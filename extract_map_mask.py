"""
从真实广东地图图片提取轮廓创建mask
"""

from PIL import Image
import numpy as np

def create_mask_from_real_map():
    """
    从真实的广东地图图片提取陆地轮廓
    """
    # 打开真实地图
    print("正在加载真实广东地图...")
    map_image = Image.open('guangdong_real_map.png').convert('RGBA')
    
    width, height = map_image.size
    print(f"地图尺寸: {width} x {height}")
    
    # 转换为numpy数组
    pixels = np.array(map_image)
    
    # 创建mask（白色背景=255，黑色轮廓=0）
    mask = np.ones((height, width), dtype=np.uint8) * 255
    
    # 提取陆地部分（绿色区域）
    # 陆地通常有较高的绿色分量
    count = 0
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[y, x]
            
            # 判断是否为陆地（绿色区域）
            # 排除白色背景、文字、海洋
            # 陆地特征：绿色明显，且不是纯白/纯黑
            if (g > 150 and g > r and g > b and 
                r < 200 and b < 200 and
                not (r > 240 and g > 240 and b > 240)):  # 排除白色背景
                
                mask[y, x] = 0  # 陆地设为黑色
                count += 1
    
    print(f"✅ 提取到 {count} 个陆地点")
    
    # 保存mask
    mask_image = Image.fromarray(mask)
    mask_image.save('guangdong_mask.png')
    print("✅ 已保存 guangdong_mask.png")
    
    return mask_image

if __name__ == '__main__':
    create_mask_from_real_map()
