import sys
import os
import time
import cascadio
from draco_compressor import compress_glb_with_draco

def convert(input_path, output_path, enable_compression=True, compression_level=10):
    print("="*60)
    print(f"[开始转换]")
    print(f"  输入文件: {input_path}")
    print(f"  输出文件: {output_path}")
    
    # 获取文件大小
    input_size_mb = os.path.getsize(input_path) / (1024 * 1024)
    print(f"  输入文件大小: {input_size_mb:.2f} MB")
    
    start = time.time()
    try:
        # Import STEP file and export to GLB with colors
        # Cascadio automatically preserves colors from STEP files
        print(f"[正在转换] 使用 cascadio 进行转换...")
        cascadio.step_to_glb(input_path, output_path)
        
        conversion_time = time.time() - start
        output_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        
        print(f"[转换成功]")
        print(f"  输出文件大小: {output_size_mb:.2f} MB")
        print(f"  转换耗时: {conversion_time:.2f} 秒")
        print(f"  转换速度: {input_size_mb / conversion_time:.2f} MB/s")
        
        # Apply Draco compression if enabled
        if enable_compression:
            print(f"[开始压缩] 使用 Draco 压缩...")
            compress_start = time.time()
            try:
                _, original_mb, compressed_mb, ratio = compress_glb_with_draco(
                    output_path, 
                    output_path,
                    compression_level=compression_level
                )
                compress_time = time.time() - compress_start
                print(f"[压缩成功]")
                print(f"  压缩耗时: {compress_time:.2f} 秒")
                print(f"  最终文件大小: {compressed_mb:.2f} MB")
            except Exception as compress_error:
                print(f"[压缩警告] Draco压缩失败，保留未压缩文件: {compress_error}")
        
        print("="*60)
    except Exception as e:
        error_time = time.time() - start
        print(f"[转换失败]")
        print(f"  错误信息: {e}")
        print(f"  失败耗时: {error_time:.2f} 秒")
        print("="*60)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python convert.py <input.step> <output.glb> [--no-compress] [--compression-level=10]")
        print("Options:")
        print("  --no-compress              Disable Draco compression")
        print("  --compression-level=N      Set compression level (0-10, default: 10)")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # Parse optional arguments
    enable_compression = True
    compression_level = 10
    
    for arg in sys.argv[3:]:
        if arg == '--no-compress':
            enable_compression = False
        elif arg.startswith('--compression-level='):
            try:
                compression_level = int(arg.split('=')[1])
                if not 0 <= compression_level <= 10:
                    print("Warning: compression_level should be between 0 and 10, using default 10")
                    compression_level = 10
            except ValueError:
                print("Warning: invalid compression_level value, using default 10")
    
    if not os.path.exists(input_file):
        print(f"Input file not found: {input_file}")
        sys.exit(1)
        
    convert(input_file, output_file, enable_compression, compression_level)
