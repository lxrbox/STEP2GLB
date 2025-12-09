"""
GLB Draco compression utility using Node.js gltfpack
Provides the best compression using industry-standard gltfpack tool
"""
import os
import subprocess
import tempfile
import shutil
import sys


def _run_cmd(cmd, **kwargs):
    """Run a command with Windows-friendly shell handling."""
    is_windows = os.name == 'nt'
    if is_windows and isinstance(cmd, (list, tuple)):
        cmd = subprocess.list2cmdline(cmd)
    return subprocess.run(cmd, shell=is_windows, **kwargs)


def check_nodejs_installed():
    """Check if Node.js is installed"""
    try:
        result = _run_cmd(['node', '--version'], capture_output=True, timeout=3)
        return result.returncode == 0
    except:
        return False


def check_gltfpack_installed():
    """Check if gltfpack is installed"""
    try:
        # gltfpack doesn't support --version, so we run it without args
        # It will return an error but we know it's installed
        # On Windows, we need to use shell=True to find .cmd files
        result = _run_cmd(
            ['gltfpack'],
            capture_output=True,
            timeout=3,
            text=True
        )
        # If we get here, gltfpack is installed (even if it returns error code)
        return True
    except FileNotFoundError:
        return False
    except subprocess.TimeoutExpired:
        # Command hung, but it exists
        return True
    except Exception as e:
        print(f"[调试] 检测 gltfpack 出错: {e}")
        return False


def install_gltfpack():
    """Install gltfpack via npm"""
    print(f"[安装] 正在安装 gltfpack...")
    try:
        result = _run_cmd(
            ['npm', 'install', '-g', 'gltfpack'],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            print(f"[安装] gltfpack 安装成功")
            return True
        else:
            print(f"[安装] gltfpack 安装失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"[安装] 安装过程出错: {e}")
        return False


def compress_glb_with_draco(input_path, output_path=None, compression_level=10):
    """
    使用 Draco 压缩 GLB 文件 (通过 Node.js gltfpack)
    
    Args:
        input_path (str): 输入 GLB 文件路径
        output_path (str): 输出压缩后的 GLB 文件路径 (可选，默认覆盖原文件)
        compression_level (int): 压缩级别 (0-10，越高压缩越多但越慢)
                                 默认为 10 (最大压缩)
    
    Returns:
        tuple: (output_path, original_size_mb, compressed_size_mb, compression_ratio)
    
    安装要求:
        1. 安装 Node.js: https://nodejs.org/
        2. 运行: npm install -g gltfpack
    """
    if output_path is None:
        output_path = input_path
    
    # 获取原始文件大小
    original_size = os.path.getsize(input_path)
    original_size_mb = original_size / (1024 * 1024)
    
    print(f"[Draco压缩] 开始压缩: {input_path}")
    print(f"[Draco压缩] 原始大小: {original_size_mb:.2f} MB")
    print(f"[Draco压缩] 压缩级别: {compression_level}")
    
    # 检查 Node.js
    if not check_nodejs_installed():
        error_msg = (
            "Node.js 未安装！\n"
            "请访问 https://nodejs.org/ 下载安装 Node.js\n"
            "安装后重启终端并重试"
        )
        print(f"[错误] {error_msg}")
        raise Exception(error_msg)
    
    # 检查 gltfpack
    if not check_gltfpack_installed():
        print(f"[Draco压缩] gltfpack 未安装")
        print(f"[Draco压缩] 正在尝试自动安装 gltfpack...")
        
        if not install_gltfpack():
            error_msg = (
                "gltfpack 安装失败！\n"
                "请手动运行: npm install -g gltfpack\n"
                "如果遇到权限问题，尝试以管理员身份运行"
            )
            print(f"[错误] {error_msg}")
            raise Exception(error_msg)
    
    # 使用 gltfpack 压缩
    return _compress_with_gltfpack(input_path, output_path, compression_level)
    


def _compress_with_gltfpack(input_path, output_path, compression_level):
    """使用 gltfpack 进行 Draco 压缩 (最佳压缩方案)"""
    original_size = os.path.getsize(input_path)
    original_size_mb = original_size / (1024 * 1024)
    
    print(f"[gltfpack] 使用 Draco 压缩...")
    
    temp_output = None
    try:
        # 如果输入输出相同，使用临时文件
        if input_path == output_path:
            temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.glb')
            temp_output.close()
            target_path = temp_output.name
        else:
            target_path = output_path
        
        # 构建 gltfpack 命令
        # -i: 输入文件
        # -o: 输出文件
        # -cc: 高级 Draco 压缩 (或 -c 标准压缩)
        # -tc: 纹理压缩 (可选)
        # compression_level 10 = -cc (最高压缩)
        # compression_level < 10 = -c (标准压缩)
        
        compression_arg = '-cc' if compression_level >= 8 else '-c'
        
        cmd = [
            'gltfpack',
            '-i', input_path,
            '-o', target_path,
            compression_arg,  # Draco 几何压缩
            '-tc'  # 纹理压缩
        ]
        
        print(f"[gltfpack] 执行命令: {' '.join(cmd)}")
        
        result = _run_cmd(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            raise Exception(f"gltfpack 执行失败: {result.stderr}")
        
        # 如果使用了临时文件，移动到最终位置
        if temp_output:
            # 在 Windows 上需要先删除目标文件（如果存在）
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except:
                    pass
            # 使用 copy + delete 代替 move，避免 Windows 文件句柄问题
            shutil.copy2(target_path, output_path)
            try:
                os.unlink(target_path)
            except:
                pass  # 忽略删除临时文件的错误
        
        compressed_size = os.path.getsize(output_path)
        compressed_size_mb = compressed_size / (1024 * 1024)
        compression_ratio = (1 - compressed_size / original_size) * 100
        
        print(f"[gltfpack] 压缩完成")
        print(f"[gltfpack] 压缩后大小: {compressed_size_mb:.2f} MB")
        print(f"[gltfpack] 压缩率: {compression_ratio:.1f}%")
        print(f"[gltfpack] 节省空间: {original_size_mb - compressed_size_mb:.2f} MB")
        
        return output_path, original_size_mb, compressed_size_mb, compression_ratio
        
    except subprocess.TimeoutExpired:
        if temp_output and os.path.exists(temp_output.name):
            os.unlink(temp_output.name)
        raise Exception("gltfpack 执行超时 (>5分钟)")
    except Exception as e:
        if temp_output and os.path.exists(temp_output.name):
            os.unlink(temp_output.name)
        raise e


def compress_glb_with_custom_settings(input_path, output_path=None, 
                                      compression_level=10,
                                      position_bits=10,
                                      normal_bits=10,
                                      texcoord_bits=12,
                                      color_bits=8):
    """
    使用自定义量化设置进行 Draco 压缩 (需要 gltfpack)
    
    Args:
        input_path (str): 输入 GLB 文件路径
        output_path (str): 输出压缩后的 GLB 文件路径
        compression_level (int): Draco 压缩级别 (0-10)
        position_bits (int): 位置量化位数 (10-16, 默认 14)
        normal_bits (int): 法线量化位数 (8-12, 默认 10)
        texcoord_bits (int): UV坐标量化位数 (10-14, 默认 12)
        color_bits (int): 颜色量化位数 (8-10, 默认 8)
    
    Returns:
        tuple: (output_path, original_size_mb, compressed_size_mb, compression_ratio)
    """
    if output_path is None:
        output_path = input_path
    
    original_size = os.path.getsize(input_path)
    original_size_mb = original_size / (1024 * 1024)
    
    print(f"[Draco自定义压缩] 开始压缩: {input_path}")
    print(f"[Draco自定义压缩] 原始大小: {original_size_mb:.2f} MB")
    print(f"[Draco自定义压缩] 设置: 级别={compression_level}, 位置={position_bits}bit, 法线={normal_bits}bit, UV={texcoord_bits}bit, 颜色={color_bits}bit")
    
    # 检查 gltfpack 是否可用
    if not check_gltfpack_installed():
        if not check_nodejs_installed():
            raise Exception("Node.js 未安装。请访问 https://nodejs.org/ 安装")
        raise Exception("gltfpack 未安装。请运行: npm install -g gltfpack")
    
    temp_output = None
    try:
        if input_path == output_path:
            temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.glb')
            temp_output.close()
            target_path = temp_output.name
        else:
            target_path = output_path
        
        # 构建带自定义量化的 gltfpack 命令
        compression_arg = '-cc' if compression_level >= 8 else '-c'
        
        cmd = [
            'gltfpack',
            '-i', input_path,
            '-o', target_path,
            compression_arg,  # 启用 Draco 压缩
            '-tc',  # 纹理压缩
            '-vp', str(position_bits),    # 位置量化
            '-vn', str(normal_bits),      # 法线量化
            '-vt', str(texcoord_bits),    # UV量化
            '-vc', str(color_bits)        # 颜色量化
        ]
        
        print(f"[gltfpack] 执行命令: {' '.join(cmd)}")
        
        result = _run_cmd(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            raise Exception(f"gltfpack 执行失败: {result.stderr}")
        
        if temp_output:
            # 在 Windows 上需要先删除目标文件（如果存在）
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except:
                    pass
            # 使用 copy + delete 代替 move，避免 Windows 文件句柄问题
            shutil.copy2(target_path, output_path)
            try:
                os.unlink(target_path)
            except:
                pass  # 忽略删除临时文件的错误
        
    except subprocess.TimeoutExpired:
        if temp_output and os.path.exists(temp_output.name):
            os.unlink(temp_output.name)
        raise Exception("gltfpack 执行超时 (>5分钟)")
    except Exception as e:
        if temp_output and os.path.exists(temp_output.name):
            os.unlink(temp_output.name)
        raise e
    
    compressed_size = os.path.getsize(output_path)
    compressed_size_mb = compressed_size / (1024 * 1024)
    compression_ratio = (1 - compressed_size / original_size) * 100
    
    print(f"[Draco自定义压缩] 压缩完成")
    print(f"[Draco自定义压缩] 压缩后大小: {compressed_size_mb:.2f} MB")
    print(f"[Draco自定义压缩] 压缩率: {compression_ratio:.1f}%")
    
    return output_path, original_size_mb, compressed_size_mb, compression_ratio
