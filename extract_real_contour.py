"""
从真实广东地图提取精确轮廓并创建mask
"""

from PIL import Image
import numpy as np
from scipy import ndimage

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
    # 根据颜色分析：R~251, G~254, B~211
    count = 0
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[y, x]
            
            # 判断是否为陆地（浅黄色区域）
            # 特征：R和G都很高（>200），B相对较低（<230）
            if (r > 200 and g > 200 and b < 230 and 
                b > 150 and  # B不能太低
                a > 128):    # 排除透明区域
                
                mask[y, x] = 0  # 陆地设为黑色
                count += 1
    
    print(f"✅ 提取到 {count} 个陆地点")
    
    # 使用形态学操作填充内部空洞
    # 将mask反转（陆地为1，背景为0）
    binary_mask = (mask == 0).astype(np.uint8)
    
    # 填充空洞
    filled = ndimage.binary_fill_holes(binary_mask).astype(np.uint8)
    
    # 转回mask格式
    mask = np.where(filled == 1, 0, 255).astype(np.uint8)
    
    # 保存mask
    mask_image = Image.fromarray(mask)
    mask_image.save('guangdong_true_mask.png')
    print("✅ 已保存 guangdong_true_mask.png")
    
    # 显示轮廓点数统计
    contour_y_coords = []
    for y in range(height):
        if np.any(mask[y, :] == 0):
            contour_y_coords.append(y)
    
    if contour_y_coords:
        print(f"✅ 轮廓Y坐标范围: {min(contour_y_coords)} - {max(contour_y_coords)}")
    
    return mask_image

if __name__ == '__main__':
    create_mask_from_real_map()
