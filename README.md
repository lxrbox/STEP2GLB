# STEP2GLB 使用说明

本项目使用 Python + Cascadio 将 STEP 文件转换为 GLB，并可选用 Draco 压缩（gltfpack）。
## GLB 格式简介
STEP（.step/.stp）更适合工程设计与制造交换，但不适合直接在网页/移动端做实时渲染展示：文件通常较大、加载慢、对解析环境要求高。为了解决这些问题，本项目将 STEP 转换为 GLB（glTF Binary），并可选启用 Draco 压缩，让模型更轻量、更易分发。

GLB 的优势（主流 3D 展示格式）
GLB 是目前非常主流的 3D 展示文件格式之一，特点是：
单文件交付（模型/材质等可打包在一个文件中）
加载快、兼容强（浏览器/WebGL 与各类引擎支持度高）
适合在线展示（可进一步压缩，便于传输与预览）

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

---

## Draco 压缩效果参考（实测）

> 说明：使用 `gltfpack` 进行 Draco 压缩后，模型体积通常可显著下降。
> 我实测压缩率约 **80%**（即压缩后体积约为原来的 **20%**）。
> 具体结果与模型复杂度（面数、材质、是否含纹理等）有关。

| 模型名称    | 原始 GLB 大小 | Draco 压缩后 GLB 大小 |    体积减少 | 压缩率 |
| ------- | --------: | ---------------: | ------: | --: |
| IRB4400 |     50 MB |            9 MB |  -40 MB | 82% |
| 示例B     |    120 MB |            24 MB |  -96 MB | 80% |
| 示例C     |      8 MB |           1.6 MB | -6.4 MB | 80% |

📌 **计算方式：**

* 压缩率 = `(原始大小 - 压缩后大小) / 原始大小`
* 若压缩率 80%，则 `压缩后大小 ≈ 原始大小 × 20%`

---
模型渲染图
![alt text](/image/image.png)
