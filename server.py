import os
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import cascadio
import time
from draco_compressor import compress_glb_with_custom_settings

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/convert', methods=['POST'])
def convert_step_to_gltf():
    request_start_time = time.time()
    print("="*60)
    print(f"[请求开始] 接收到新的转换请求")
    # 解析 multipart/form-data 及头部耗时（从请求到可访问 request.files）
    parse_elapsed = time.time() - request_start_time
    print(f"[请求解析] 解析请求耗时: {parse_elapsed:.2f} 秒")
    
    if 'file' not in request.files:
        print("[错误] 请求中没有文件")
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    file_field_elapsed = time.time() - request_start_time
    print(f"[请求解析] 获取 file 字段耗时: {file_field_elapsed:.2f} 秒")
    if file.filename == '':
        print("[错误] 未选择文件")
        return jsonify({'error': 'No selected file'}), 400
    
    if file and (file.filename.lower().endswith('.step') or file.filename.lower().endswith('.stp')):
        import hashlib
        print(f"[文件信息] 原始文件名: {file.filename}")
        
        # 读取文件内容到内存并计算SHA-256
        upload_start = time.time()
        file_bytes = file.read()
        file_size_mb = len(file_bytes) / (1024 * 1024)
        print(f"[上传完成] 文件大小: {file_size_mb:.2f} MB, 耗时: {time.time() - upload_start:.2f} 秒")
        
        hash_start = time.time()
        sha256 = hashlib.sha256(file_bytes).hexdigest()
        print(f"[哈希计算] SHA-256: {sha256}, 耗时: {time.time() - hash_start:.3f} 秒")
        
        # 生成唯一输出文件名
        gltf_filename = f"{sha256}.glb"
        gltf_path = os.path.join(OUTPUT_FOLDER, gltf_filename)
        
        # 如果已存在则直接返回
        if os.path.exists(gltf_path):
            cached_size_mb = os.path.getsize(gltf_path) / (1024 * 1024)
            send_start = time.time()
            print(f"[缓存命中] 文件已存在，准备返回缓存结果 (大小: {cached_size_mb:.2f} MB)")
            response = send_file(gltf_path, as_attachment=True)
            send_prep_time = time.time() - send_start
            total_time = time.time() - request_start_time
            print(f"[文件准备] 耗时: {send_prep_time:.2f} 秒")
            print(f"[请求完成] 总耗时: {total_time:.2f} 秒 (注意: 实际传输时间不包含在此)")
            print("="*60)
            return response
        
        # 保存上传文件到uploads目录
        save_start = time.time()
        step_path = os.path.join(UPLOAD_FOLDER, f"{sha256}.step")
        with open(step_path, 'wb') as f:
            f.write(file_bytes)
        print(f"[文件保存] 保存至: {step_path}, 耗时: {time.time() - save_start:.3f} 秒")
        # Get quality settings from request args or form data
        quality = request.form.get('quality', 'medium')
        # Get compression settings
        # Draco compression level: 0-10 (0=fastest/best quality, 10=slowest/highest compression)
        # For CAD models, use 3-5 to avoid visual artifacts (unwanted lines/edges)
        enable_compression = request.form.get('compress', 'true').lower() == 'true'
        compression_level = int(request.form.get('compression_level', '0'))
        
        # Default tolerances (medium)
        tol = 0.1
        ang_tol = 0.1
        if quality == 'low':
            tol = 1.0
            ang_tol = 0.3
        elif quality == 'high':
            tol = 0.01
            ang_tol = 0.05
        
        print(f"[转换设置] 质量等级: {quality}, 公差: {tol}, 角度公差: {ang_tol}")
        print(f"[压缩设置] 启用压缩: {enable_compression}, 压缩级别: {compression_level}")
        
        try:
            print(f"[开始转换] {step_path} -> {gltf_path}")
            conversion_start = time.time()
            
            # Use Cascadio to convert STEP to GLB with colors preserved
            cascadio.step_to_glb(step_path, gltf_path)
            
            conversion_time = time.time() - conversion_start
            output_size_mb = os.path.getsize(gltf_path) / (1024 * 1024)
            
            print(f"[转换完成] 输出文件大小: {output_size_mb:.2f} MB")
            print(f"[转换耗时] {conversion_time:.2f} 秒")
            
            # Apply Draco compression if enabled
            if enable_compression:
                compress_start = time.time()
                try:
                    _, original_mb, compressed_mb, ratio = compress_glb_with_custom_settings(
                        gltf_path,
                        gltf_path,
                        compression_level=compression_level,
                        position_bits=14,
                        normal_bits=10,
                    )
                    compress_time = time.time() - compress_start
                    print(f"[压缩耗时] {compress_time:.2f} 秒")
                except Exception as compress_error:
                    print(f"[压缩警告] Draco压缩失败，返回未压缩文件: {compress_error}")
            
            total_time = time.time() - request_start_time
            final_size_mb = os.path.getsize(gltf_path) / (1024 * 1024)
            
            print(f"[最终文件] 大小: {final_size_mb:.2f} MB")
            print(f"[请求完成] 总耗时: {total_time:.2f} 秒 (上传+转换+压缩+处理，不含实际网络传输)")
            print("="*60)
            
            return send_file(gltf_path, as_attachment=True)
        except Exception as e:
            error_time = time.time() - request_start_time
            print(f"[转换失败] 错误: {e}")
            print(f"[请求失败] 总耗时: {error_time:.2f} 秒")
            print("="*60)
            return jsonify({'error': str(e)}), 500
    
    print(f"[错误] 无效的文件类型: {file.filename}")
    print("="*60)
    return jsonify({'error': 'Invalid file type. Please upload a .step or .stp file.'}), 400

if __name__ == '__main__':
    print("Starting STEP to GLTF converter server on port 5000...")
    app.run(host='0.0.0.0',port=5000, debug=True)
