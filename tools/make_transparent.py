from PIL import Image

src = "docs/latex_theme/assets/warning_lockup.jpg"
dst = "docs/latex_theme/assets/warning_lockup.png"

im = Image.open(src).convert("RGBA")
pix = im.getdata()

new = []
for r,g,b,a in pix:
    # 把接近白色的像素变透明（阈值可调 240~250）
    if r > 245 and g > 245 and b > 245:
        new.append((r,g,b,0))
    else:
        new.append((r,g,b,255))

im.putdata(new)
im.save(dst)
print("saved:", dst)
