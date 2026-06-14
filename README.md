# 3D-Reconstruction · 基于 3D Gaussian Splatting 的交互式三维重建与可视化系统

> 计算机视觉课程设计。从一组图片重建出三维高斯模型，并在浏览器中以可拖拽旋转的实时 3D 视口呈现。

## ✨ 功能

- **选数据集 / 上传图片** → 一键发起三维重建（COLMAP/GLOMAP + gsplat 3DGS-MCMC）
- **可视化进度条**：SfM → 训练 → 压缩 三阶段实时进度（SSE 推送）
- **浏览器内拖拽 3D 视口**：左键旋转 / 右键平移 / 滚轮缩放，支持 `.ply / .splat / .ksplat`
- **产物管理**：重建结果可存到根目录或自定义路径；历史文件可再次导入直接查看（无需 GPU）
- **引擎对比（亮点）**：gsplat (CUDA) vs Brush (WebGPU) 的质量/速度/体积对比

## 🏗️ 技术栈

| 层 | 技术 |
|---|---|
| 重建（主） | COLMAP + GLOMAP（SfM）→ gsplat（CUDA, 3DGS-MCMC） |
| 重建（对比） | Brush（Rust + WebGPU，无 CUDA） |
| 后端 | FastAPI + 单队列串行任务 + SSE 进度 |
| 前端 | React 18 + TypeScript + Vite + Three.js + `@mkkellogg/gaussian-splats-3d` + Tailwind |
| 压缩 | PLY → `.ksplat`（无损裁剪 + 量化） |

完整设计见 [`DEV_SPEC.md`](DEV_SPEC.md)，理论推导见研究报告 `.md`。

## 🚀 快速开始

> 详细安装（原生 Windows / WSL2 两套方案）将在开发完成后补全。当前进度见下方。

```bash
# 前端
cd frontend && npm install && npm run dev      # http://localhost:5173

# 后端（需 NVIDIA GPU + CUDA 11.8）
cd backend && uv sync && uv run uvicorn app.main:app --reload --port 8000
```

## 📦 项目结构

```
3D-Reconstruction/
├── DEV_SPEC.md          # 开发规范（技术选型/架构/API 契约/里程碑）
├── backend/             # FastAPI 后端 + 重建服务
├── frontend/            # React 前端 + 3D 查看器
├── scripts/             # 数据集准备 + 预训练
└── workspace/           # 运行产物（gitignore，默认输出根目录）
```

## 📅 开发进度

- [x] 选型 & 开发规范（DEV_SPEC.md）
- [ ] Phase 1：查看器闭环（浏览器拖拽看 3D 模型）
- [ ] Phase 2：重建主链路（图片 → .ksplat）
- [ ] Phase 3：上传 + 产物管理
- [ ] Phase 4：Brush 对比 + 打磨
- [ ] Phase 5：README + 报告对齐

## 📄 许可与引用

本仓库代码以 MIT 许可发布。依赖的第三方组件：
- 原始 **3D Gaussian Splatting**（INRIA）为**非商业研究许可**，仅用于学术课程。
- **gsplat**（Apache-2.0）、**COLMAP/GLOMAP**（BSD）、**Brush**（Apache-2.0）、**GaussianSplats3D**（MIT）。

学术使用请引用对应论文（见 DEV_SPEC §2.2）。
