#!/usr/local/bin/python3

import os
from PIL import Image
import glob

# 输入输出路径
png_dir = "../img/png"
jpg_dir = "../img/jpg"
h_dir = "../img/tianqi"

os.makedirs(jpg_dir, exist_ok=True)
os.makedirs(h_dir, exist_ok=True)

def png_to_jpg_black_bg(png_path, jpg_path):
    img = Image.open(png_path).convert("RGBA")
    bg = Image.new("RGBA", img.size, (0, 0, 0, 255))  # 黑色背景
    bg.paste(img, (0, 0), img)
    rgb_img = bg.convert("RGB")
    rgb_img.save(jpg_path, "JPEG", quality=95)

def jpg_to_c_header(jpg_path, h_path, varname):
    with open(jpg_path, "rb") as f:
        data = f.read()
    array_content = ','.join(f'0x{b:02X}' for b in data)
    lines = []
    lines.append('#include <pgmspace.h>')
    lines.append(f'const uint8_t {varname}[] PROGMEM = {{')
    # 每行16字节
    for i in range(0, len(data), 16):
        chunk = ','.join(f'0x{b:02X}' for b in data[i:i+16])
        lines.append(chunk + ',')
    lines.append('};')
    with open(h_path, "w") as f:
        f.write('\n'.join(lines))

def main():
    png_files = glob.glob(os.path.join(png_dir, "*.png"))
    for png_file in png_files:
        basename = os.path.splitext(os.path.basename(png_file))[0]
        jpg_file = os.path.join(jpg_dir, f"{basename}.jpg")
        h_file = os.path.join(h_dir, f"{basename}.h")
        varname = f"{basename}"
        print(f"处理: {png_file} → {jpg_file} → {h_file}")
        png_to_jpg_black_bg(png_file, jpg_file)
        jpg_to_c_header(jpg_file, h_file, varname)

if __name__ == "__main__":
    main()
