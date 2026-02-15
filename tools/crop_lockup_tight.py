from pathlib import Path
from PIL import Image

src = Path("docs/latex_theme/assets/warning_lockup.png")
dst = Path("docs/latex_theme/assets/warning_lockup_tight.png")

im = Image.open(src).convert("RGBA")
px = im.load()
w, h = im.size

# 更狠的裁切策略：
# 1) alpha 要足够高（去掉半透明阴影）
# 2) 同时排除“近白色”区域（防止透明但有白边）
ALPHA_TH = 200
RGB_TH = 245  # 越小越狠

minx, miny, maxx, maxy = w, h, -1, -1
for y in range(h):
    for x in range(w):
        r, g, b, a = px[x, y]
        if a >= ALPHA_TH and (r <= RGB_TH or g <= RGB_TH or b <= RGB_TH):
            if x < minx: minx = x
            if y < miny: miny = y
            if x > maxx: maxx = x
            if y > maxy: maxy = y

if maxx < 0:
    raise SystemExit("No content found with given thresholds")

# Pillow crop box: (left, top, right+1, bottom+1)
crop_box = (minx, miny, maxx + 1, maxy + 1)
cropped = im.crop(crop_box)
cropped.save(dst)
print("saved:", dst)
print("orig:", (w, h), "crop_box:", crop_box, "new:", cropped.size)
