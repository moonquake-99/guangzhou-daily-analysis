"""
从真实广东地图轮廓图片提取精确的边界坐标
"""

from PIL import Image
import numpy as np

def extract_contour_from_image():
    """
    从广东地图图片提取外轮廓坐标
    """
    # 打开图片
    img = Image.open('C:/Users/17431/AppData/Roaming/Lingma/SharedClientCache/cache/images/93372be6/33-dff27216.png')
    img = img.convert('RGBA')
    
    width, height = img.size
    print(f"图片尺寸: {width} x {height}")
    
    # 转换为数组
    pixels = np.array(img)
    
    # 创建mask
    mask = np.ones((height, width), dtype=np.uint8) * 255
    
    # 提取黄色陆地区域
    # 黄色区域：R和G都高，B较低
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[y, x]
            
            # 黄色陆地特征：R>200, G>200, B<150
            if r > 200 and g > 200 and b < 150:
                mask[y, x] = 0
    
    # 找到轮廓点
    contour_points = []
    
    # 从上到下，从左到右扫描边缘
    for y in range(height):
        for x in range(width):
            if mask[y, x] == 0:
                # 检查是否是边界点（周围有白色像素）
                is_boundary = False
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < height and 0 <= nx < width:
                            if mask[ny, nx] == 255:
                                is_boundary = True
                                break
                    if is_boundary:
                        break
                
                if is_boundary:
                    contour_points.append((x, y))
    
    print(f"找到 {len(contour_points)} 个边界点")
    
    # 简化轮廓（每隔N个点取一个）
    # 按照y坐标排序，然后按顺时针方向排列
    # 这里简化处理：按y分组，每组取最左和最右的点
    
    simplified = []
    step = 10  # 每10行取一次
    
    for y in range(0, height, step):
        points_at_y = [p for p in contour_points if abs(p[1] - y) < step]
        if points_at_y:
            # 取最左边的点
            left = min(points_at_y, key=lambda p: p[0])
            # 取最右边的点
            right = max(points_at_y, key=lambda p: p[0])
            simplified.append(left)
            simplified.append(right)
    
    # 进一步简化：使用Douglas-Peucker算法思想
    # 这里简单处理：每隔几个点取一个
    final_points = simplified[::3]
    
    print(f"简化后: {len(final_points)} 个点")
    
    # 保存坐标到文件
    with open('guangdong_contour_coords.txt', 'w', encoding='utf-8') as f:
        f.write("广东省轮廓坐标（简化版）：\n")
        f.write("outline = [\n")
        for i, (x, y) in enumerate(final_points):
            f.write(f"    ({x}, {y}),\n")
        f.write("]\n")
    
    print("✅ 坐标已保存到 guangdong_contour_coords.txt")
    
    # 同时保存mask
    mask_img = Image.fromarray(mask)
    mask_img.save('guangdong_true_mask.png')
    print("✅ mask已保存到 guangdong_true_mask.png")
    
    return final_points

if __name__ == '__main__':
    extract_contour_from_image()
