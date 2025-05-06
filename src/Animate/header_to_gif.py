import os
import re
from PIL import Image
from io import BytesIO
import logging

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def extract_frame_number(frame_name):
    """从帧名称中提取数字部分用于排序 (例如 'i10' -> 10, 'hutao_5' -> 5)"""
    match = re.search(r'\d+$', frame_name)
    return int(match.group(0)) if match else -1

def parse_byte_array_string(byte_array_str):
    """解析C语言风格的十六进制字节数组字符串"""
    # 移除注释和不必要的字符
    byte_array_str = re.sub(r'//.*', '', byte_array_str) # 移除行内注释
    byte_array_str = byte_array_str.replace('\n', '').replace('\r', '') # 移除换行符
    
    hex_values = []
    for part in byte_array_str.split(','):
        part = part.strip()
        if part.startswith('0x'):
            try:
                hex_values.append(int(part, 16))
            except ValueError:
                logging.warning(f"跳过无效的十六进制值: {part}")
    return bytes(hex_values)

def create_gif_from_header(header_file_path, output_dir):
    """从C头文件创建GIF"""
    try:
        with open(header_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        logging.error(f"文件未找到: {header_file_path}")
        return
    except Exception as e:
        logging.error(f"读取文件时出错 {header_file_path}: {e}")
        return

    # 正则表达式查找所有帧数据
    # const uint8_t i0[] PROGMEM = { ... };
    # const uint8_t hutao_0[] PROGMEM = { ... };
    frame_pattern = re.compile(
        r"const\s+uint8_t\s+([a-zA-Z0-9_]+)\[\]\s+PROGMEM\s*=\s*\{([\s\S]*?)\};"
    )
    
    matches = frame_pattern.findall(content)
    
    if not matches:
        logging.info(f"在 {header_file_path} 中未找到图像帧数据。")
        return

    frames_data = []
    for frame_name, byte_array_content in matches:
        logging.debug(f"找到帧: {frame_name} in {header_file_path}")
        image_bytes = parse_byte_array_string(byte_array_content)
        if image_bytes:
            frames_data.append({'name': frame_name, 'bytes': image_bytes})
        else:
            logging.warning(f"未能解析帧 {frame_name} 的字节数据。")

    if not frames_data:
        logging.info(f"在 {header_file_path} 中没有可用的帧来创建GIF。")
        return

    # 根据帧名称中的数字排序
    frames_data.sort(key=lambda x: extract_frame_number(x['name']))

    images = []
    for frame_data in frames_data:
        try:
            image = Image.open(BytesIO(frame_data['bytes']))
            # 确保图像是RGB模式，GIF通常需要P模式，Pillow会自动处理转换
            # 如果图像已经是P模式，保留它。如果不是，转换为RGBA再由Pillow处理为P。
            if image.mode != 'P':
                 # 转换为RGBA以保留透明度（如果原始JPEG支持，尽管不太可能）
                 # 然后Pillow在保存为GIF时会进行调色板化
                image = image.convert('RGBA')
            images.append(image)
        except Exception as e:
            logging.error(f"处理帧 {frame_data['name']} 时出错: {e}")
            # 可以选择跳过损坏的帧或停止处理此文件
            # continue

    if not images:
        logging.info(f"未能从 {header_file_path} 加载任何图像帧。")
        return

    base_name = os.path.splitext(os.path.basename(header_file_path))[0]
    output_gif_path = os.path.join(output_dir, f"{base_name}.gif")

    try:
        images[0].save(
            output_gif_path,
            save_all=True,
            append_images=images[1:],
            duration=100,  # 每帧持续时间（毫秒），例如100ms = 10 FPS
            loop=0,        # 0表示无限循环
            optimize=False # 可以尝试设置为True以减小文件大小，但可能增加处理时间
        )
        logging.info(f"成功创建GIF: {output_gif_path}")
    except Exception as e:
        logging.error(f"保存GIF {output_gif_path} 时出错: {e}")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_img_dir = os.path.join(script_dir, "img")
    output_dir = script_dir # 将GIF保存在脚本所在的目录

    if not os.path.isdir(input_img_dir):
        logging.error(f"输入目录 'img' 未找到于: {input_img_dir}")
        return

    logging.info(f"开始处理 {input_img_dir} 中的头文件...")
    for filename in os.listdir(input_img_dir):
        if filename.endswith(".h"):
            header_file_path = os.path.join(input_img_dir, filename)
            logging.info(f"正在处理文件: {header_file_path}")
            create_gif_from_header(header_file_path, output_dir)
    logging.info("处理完成。")

if __name__ == "__main__":
    # 确保Pillow已安装
    try:
        from PIL import Image
    except ImportError:
        logging.error("Pillow库未安装。请使用 'pip install Pillow' 命令安装。")
        exit(1)
    main()

