"""
检查广东地图图片的颜色分布
"""

from PIL import Image
import numpy as np

def check_colors():
    img = Image.open('C:/Users/17431/AppData/Roaming/Lingma/SharedClientCache/cache/images/93372be6/33-dff27216.png')
    img = img.convert('RGBA')
    
    pixels = np.array(img)
    
    # 采样一些点
    print("采样像素颜色（前50个非白色像素）：")
    count = 0
    for y in range(0, img.height, 20):
        for x in range(0, img.width, 20):
            if count >= 50:
                break
            r, g, b, a = pixels[y, x]
            # 排除白色背景
            if not (r > 240 and g > 240 and b > 240):
                print(f"({x:3d}, {y:3d}): R={r:3d}, G={g:3d}, B={b:3d}, A={a:3d}")
                count += 1
        if count >= 50:
            break
    
    # 统计黄色区域的颜色范围
    print("\n分析陆地区域颜色范围：")
    yellow_pixels = []
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = pixels[y, x]
            # 排除白色和透明
            if not (r > 240 and g > 240 and b > 240) and a > 128:
                yellow_pixels.append((r, g, b))
    
    if yellow_pixels:
        r_vals = [p[0] for p in yellow_pixels]
        g_vals = [p[1] for p in yellow_pixels]
        b_vals = [p[2] for p in yellow_pixels]
        
        print(f"陆地像素数量: {len(yellow_pixels)}")
        print(f"R范围: {min(r_vals)} - {max(r_vals)}, 平均: {np.mean(r_vals):.0f}")
        print(f"G范围: {min(g_vals)} - {max(g_vals)}, 平均: {np.mean(g_vals):.0f}")
        print(f"B范围: {min(b_vals)} - {max(b_vals)}, 平均: {np.mean(b_vals):.0f}")

if __name__ == '__main__':
    check_colors()
