import re
import argparse
# from PIL import Image # 移除 PIL 导入
# import io # 移除 io 导入
import os
import binascii # 用于转换十六进制

def extract_image_data(header_content):
    # 使用正则表达式查找 PROGMEM 数组的内容
    # 这个正则表达式会查找像 const uint8_t t1[] PROGMEM = { ... }; 这样的结构
    # 增加了对数组名的捕获，虽然在这个版本中未使用，但保留以备将来之用
    match = re.search(r'const\s+uint8_t\s+(\w+)\[\]\s+PROGMEM\s*=\s*\{([\s\S]*?)\};', header_content, re.MULTILINE)
    if not match:
        print("未找到 PROGMEM 数组。")
        return None, None, None

    array_name = match.group(1) # 获取数组名
    array_content = match.group(2)
    # 查找所有的十六进制值 (例如 0xAB, 0xFF)
    hex_values = re.findall(r'0x([0-9a-fA-F]{1,2})', array_content)
    if not hex_values:
        print("未在数组中找到有效的十六进制值。")
        return None, None, None

    # 将十六进制字符串列表转换为字节串
    try:
        # 使用 binascii.unhexlify 更健壮地处理十六进制字符串
        byte_data = binascii.unhexlify("".join(hv.zfill(2) for hv in hex_values)) # 确保每个十六进制值都是两位
    except Exception as e:
        print(f"转换十六进制值为字节时出错: {e}")
        return None, None, None

    # 尝试从字节数据中提取宽度和高度 (JPEG SOF0/SOF2 marker) - 这部分保持不变，用于信息展示
    width, height = None, None
    try:
        # 寻找 SOF0 (Start of Frame 0) 标记 (0xFFC0)
        sof_marker_index = byte_data.find(b'\xFF\xC0')
        if sof_marker_index != -1 and sof_marker_index + 8 < len(byte_data): # 需要检查到第8个字节
            height = (byte_data[sof_marker_index + 5] << 8) + byte_data[sof_marker_index + 6]
            width = (byte_data[sof_marker_index + 7] << 8) + byte_data[sof_marker_index + 8]
            print(f"从JPEG头信息 (SOF0) 中提取到尺寸: Width={width}, Height={height}")
        else:
             # 尝试从其他 SOF 标记提取 (SOF2 - Progressive DCT)
            sof_marker_index = byte_data.find(b'\xFF\xC2')
            if sof_marker_index != -1 and sof_marker_index + 8 < len(byte_data): # 需要检查到第8个字节
                height = (byte_data[sof_marker_index + 5] << 8) + byte_data[sof_marker_index + 6]
                width = (byte_data[sof_marker_index + 7] << 8) + byte_data[sof_marker_index + 8]
                print(f"从JPEG头信息 (SOF2) 中提取到尺寸: Width={width}, Height={height}")
            else:
                print("未找到 SOF0 或 SOF2 标记，无法自动提取尺寸。")

    except Exception as e:
        print(f"提取尺寸时出错: {e}")

    return byte_data, width, height

def process_header_file(input_header_file, output_image_file):
    try:
        with open(input_header_file, 'r', encoding='utf-8') as f:
            header_content = f.read()
    except FileNotFoundError:
        print(f"错误：输入文件 '{input_header_file}' 未找到。")
        return
    except Exception as e:
        print(f"读取文件 '{input_header_file}' 时出错: {e}")
        return

    image_data, width, height = extract_image_data(header_content)

    if image_data:
        try:
            # 直接将提取的原始字节数据写入文件
            with open(output_image_file, 'wb') as img_file:
                img_file.write(image_data)
            # 根据是否提取到尺寸，打印不同的成功信息
            if width is not None and height is not None:
                print(f"原始图像字节数据已成功保存到 '{output_image_file}' (提取到的尺寸: {width}x{height})")
            else:
                print(f"原始图像字节数据已成功保存到 '{output_image_file}' (未自动提取尺寸)")

        except IOError as e:
            print(f"写入图像文件 '{output_image_file}' 时出错: {e}")
        except Exception as e:
             print(f"保存图像 '{output_image_file}' 时发生未知错误: {e}")

def main():
    parser = argparse.ArgumentParser(description='从 C/C++ 头文件中的 PROGMEM 数组提取原始图像字节数据并直接保存为文件。')
    parser.add_argument('input_dir', help='包含头文件的输入目录路径。')
    parser.add_argument('output_dir', help='保存生成文件的输出目录路径。')
    # 注意：format 参数现在仅用于确定输出文件的扩展名
    parser.add_argument('--format', default='jpg', help='输出文件的扩展名 (例如: jpg, bin)。默认为 jpg。脚本不进行格式转换。')

    args = parser.parse_args()

    input_dir = args.input_dir
    output_dir = args.output_dir
    output_format = args.format.lower().lstrip('.') # 移除可能的前导点

    # 检查输入目录是否存在
    if not os.path.isdir(input_dir):
        print(f"错误：输入目录 '{input_dir}' 不存在或不是一个有效的目录。")
        return

    # 创建输出目录（如果不存在）
    os.makedirs(output_dir, exist_ok=True)
    print(f"将在 '{output_dir}' 目录中保存文件。")

    # 遍历输入目录中的文件
    processed_count = 0
    for filename in os.listdir(input_dir):
        if filename.lower().endswith('.h'):
            input_header_file = os.path.join(input_dir, filename)
            # 构建输出文件名，使用指定的扩展名
            base_name = os.path.splitext(filename)[0]
            output_image_file = os.path.join(output_dir, f"{base_name}.{output_format}")

            print(f"\n正在处理: {input_header_file}")
            process_header_file(input_header_file, output_image_file)
            processed_count += 1

    if processed_count == 0:
        print(f"在目录 '{input_dir}' 中未找到任何 .h 文件。")
    else:
        print(f"\n处理完成，共处理了 {processed_count} 个头文件。")


if __name__ == '__main__':
    main()
