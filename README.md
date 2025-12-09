# STEP2GLB 使用说明

本项目使用 Python + Cascadio 将 STEP 文件转换为 GLB，并可选用 Draco 压缩（gltfpack）。

## 环境准备

1. 安装 Python 3.8+（建议 3.9+）。
2. 安装依赖：
   ```bash
   python3 -m pip install -r requirements.txt
   ```
3. 安装 Node.js（用于 gltfpack）。
4. 安装 gltfpack：
   ```bash
   npm install -g gltfpack
   ```
5. 可选验证：
   ```bash
   gltfpack -h
   ```

## 命令行转换（convert.py）

```bash
python3 convert.py <input.step> <output.glb>
```

可选参数：
- `--no-compress`：关闭 Draco 压缩
- `--compression-level=N`：压缩级别 0-10（默认 10）

示例：
```bash
python3 convert.py ./uploads/IRB4400.STEP ./outputs/IRB4400.glb
python3 convert.py ./uploads/IRB4400.STEP ./outputs/IRB4400.glb --no-compress
python3 convert.py ./uploads/IRB4400.STEP ./outputs/IRB4400.glb --compression-level=5
```

注意：`convert.py` 使用位置参数，不支持 `-i/-o`。

## 启动服务（server.py）

```bash
python3 server.py
```

服务地址：`http://localhost:5000`

接口：`POST /convert`（multipart/form-data）
- `file`：上传 `.step`/`.stp` 文件
- `compress`：`true|false`（默认 `true`）
- `compression_level`：`0-10`（默认 `0`）
- `quality`：`low|medium|high`（默认 `medium`）

服务会自动创建 `uploads/` 与 `outputs/` 目录并保存中间/输出文件。
