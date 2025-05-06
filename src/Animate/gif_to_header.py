import os
from PIL import Image, ImageSequence
import logging
from io import BytesIO

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def gif_to_c_header(gif_path, output_dir):
    """将GIF文件转换为C头文件。"""
    try:
        img = Image.open(gif_path)
    except FileNotFoundError:
        logging.error(f"GIF文件未找到: {gif_path}")
        return
    except Exception as e:
        logging.error(f"打开GIF文件时出错 {gif_path}: {e}")
        return

    # 清理文件名以用作C变量名
    base_name = os.path.splitext(os.path.basename(gif_path))[0]
    base_name = re.sub(r'[^a-zA-Z0-9_]', '_', base_name) # 确保变量名有效

    header_file_name = f"{base_name}.h"
    header_file_path = os.path.join(output_dir, header_file_name)

    frames_data = []
    frame_sizes = [] # 重新引入以存储每帧的大小

    logging.info(f"正在处理GIF: {gif_path} -> {header_file_path}")

    try:
        for i, frame_pil in enumerate(ImageSequence.Iterator(img)):
            # 将帧转换为RGB模式（如果不是的话）
            frame_rgb = frame_pil.convert('RGB')
            
            # 将帧保存为JPEG字节流（与项目中的 .h.old 文件格式一致）
            jpeg_buffer = BytesIO()
            # 您可以根据需要调整 quality 参数 (0-100)
            frame_rgb.save(jpeg_buffer, format="JPEG", quality=85) 
            frame_bytes = jpeg_buffer.getvalue()
            
            frames_data.append({
                'name': f"{base_name}_{i}",
                'bytes': frame_bytes
            })
            frame_sizes.append(len(frame_bytes)) # 存储帧大小
            logging.debug(f"已处理 {base_name} 的第 {i} 帧, 大小: {len(frame_bytes)} 字节")

    except Exception as e:
        logging.error(f"处理 {gif_path} 的帧时出错: {e}")
        return

    if not frames_data:
        logging.warning(f"未能从 {gif_path} 提取任何帧")
        return

    try:
        with open(header_file_path, 'w', encoding='utf-8') as f:
            f.write("#include <pgmspace.h>\n\n")

            # 为每一帧写入字节数组
            for frame_info in frames_data:
                f.write(f"const uint8_t {frame_info['name']}[] PROGMEM = {{\n")
                hex_bytes = [f"0x{byte:02X}" for byte in frame_info['bytes']]
                # 每行写入16个字节
                for j in range(0, len(hex_bytes), 16):
                    line_bytes = hex_bytes[j:j+16]
                    f.write("\t" + ",".join(line_bytes))
                    # 如果不是数组的最后一个字节，则添加逗号
                    if j + len(line_bytes) < len(hex_bytes):
                        f.write(",")
                    f.write("\n")
                f.write("};\n\n") # 在每个数组定义后添加一个额外的换行符

            # 添加帧指针数组 (例如: const uint8_t *hutao[32] PROGMEM {...};)
            if frames_data:
                f.write(f"const uint8_t *{base_name}[{len(frames_data)}] PROGMEM {{\n") # 移除了等号
                for k, frame_info in enumerate(frames_data):
                    f.write(f"\t{frame_info['name']}")
                    if k < len(frames_data) - 1:
                        f.write(",")
                    f.write("\n")
                f.write("};\n\n")

                # 添加帧大小数组 (例如: const uint32_t hutao_size[32] PROGMEM {...};)
                f.write(f"const uint32_t {base_name}_size[{len(frames_data)}] PROGMEM {{\n") # 移除了等号
                for k, size in enumerate(frame_sizes):
                    f.write(f"\t{size}")
                    if k < len(frame_sizes) - 1:
                        f.write(",")
                    f.write("\n")
                f.write("};\n") # 最后一个数组定义后只有一个换行符，以匹配hutao.h.old

        # 确保文件末尾只有一个换行符（如果上面最后一个数组后是\n\n则调整）
        # hutao.h.old 的最后一个数组定义后只有一个换行符，所以上面已经调整为 f.write("};\n")
        
        logging.info(f"成功创建头文件: {header_file_path}")

    except Exception as e:
        logging.error(f"写入头文件 {header_file_path} 时出错: {e}")


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # GIF输入目录为脚本所在目录下的 'img' 子目录
    input_gif_dir = os.path.join(script_dir, "img") 
    # 头文件输出目录也为 'img' 子目录
    output_header_dir = os.path.join(script_dir, "img") 

    if not os.path.isdir(input_gif_dir):
        logging.error(f"输入GIF目录 'img' 未找到于: {input_gif_dir}")
        return
    
    # 确保输出目录存在 (通常 'img' 目录已存在)
    if not os.path.isdir(output_header_dir):
        try:
            os.makedirs(output_header_dir)
            logging.info(f"已创建输出目录: {output_header_dir}")
        except Exception as e:
            logging.error(f"无法创建输出目录 {output_header_dir}: {e}")
            return

    logging.info(f"开始在 {input_gif_dir} 中转换GIF到头文件...")
    found_gifs = False
    for filename in os.listdir(input_gif_dir):
        if filename.lower().endswith(".gif"):
            found_gifs = True
            gif_file_path = os.path.join(input_gif_dir, filename)
            gif_to_c_header(gif_file_path, output_header_dir)
    
    if not found_gifs:
        logging.info(f"在 {input_gif_dir} 中未找到GIF文件")
    else:
        logging.info("GIF到头文件转换完成。")

if __name__ == "__main__":
    # 确保Pillow库已安装
    try:
        from PIL import Image, ImageSequence
    except ImportError:
        logging.error("Pillow库未安装。请使用 'pip install Pillow' 命令安装。")
        # 在某些环境中，exit(1)可能不适用或被禁止
        print("Pillow库未安装。请使用 'pip install Pillow' 命令安装。") 
    else:
        # 导入 re 模块，用于清理文件名
        import re
        main()

