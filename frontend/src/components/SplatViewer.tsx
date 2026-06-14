import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import * as GaussianSplats3D from '@mkkellogg/gaussian-splats-3d';
import type { SplatFormat, ViewerDefaults } from '@/types';

// 直接取库内真实枚举值（实际为 Splat=0, KSplat=1, Ply=2），避免硬编码出错
const FORMAT_ENUM: Record<SplatFormat, number> = {
  splat: GaussianSplats3D.SceneFormat.Splat,
  ksplat: GaussianSplats3D.SceneFormat.KSplat,
  ply: GaussianSplats3D.SceneFormat.Ply,
};

export interface ViewerStats {
  fps: number;
  splatCount: number;
}

interface SplatViewerProps {
  /** 模型 URL（http 或 blob:） */
  url: string;
  format: SplatFormat;
  /** 不透明度剔除阈值 0-255，过滤边缘飞散噪点 */
  alphaThreshold?: number;
  viewerDefaults?: ViewerDefaults;
  onStats?: (s: ViewerStats) => void;
  onLoaded?: () => void;
  onError?: (message: string) => void;
}

/**
 * 3DGS 拖拽查看器。封装 @mkkellogg/gaussian-splats-3d 的命令式 Viewer：
 * 内置 OrbitControls（左键旋转 / 右键平移 / 滚轮缩放），挂载即渲染，卸载即释放 GPU。
 * 复用其渲染管线，不自写 splat 光栅化。
 */
export default function SplatViewer({
  url,
  format,
  alphaThreshold = 5,
  viewerDefaults,
  onStats,
  onLoaded,
  onError,
}: SplatViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  // url / format / alphaThreshold 变化时重建查看器（alpha 需重载场景才能生效）
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    let disposed = false;
    let rafId = 0;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let viewer: any = null;

    try {
      viewer = new GaussianSplats3D.Viewer({
        rootElement: container,
        // 关闭共享内存可避免对 COOP/COEP 跨域隔离响应头的依赖
        sharedMemoryForWorkers: false,
        useBuiltInControls: true,
        // GPU 排序在部分驱动/浏览器组合下静默失效导致 splat 不渲染，改用 WASM CPU 排序更稳
        gpuAcceleratedSort: false,
        cameraUp: viewerDefaults?.cameraUp ?? [0, 1, 0],
        initialCameraPosition: viewerDefaults?.initialCameraPosition ?? [0, -1, 6],
        initialCameraLookAt: viewerDefaults?.initialCameraLookAt ?? [0, 0, 0],
      });

      viewer
        .addSplatScene(url, {
          format: FORMAT_ENUM[format],
          splatAlphaRemovalThreshold: alphaThreshold,
          showLoadingUI: true,
          progressiveLoad: false,
        })
        .then(() => {
          if (disposed) return;
          viewer.start();
          // 中性深灰背景，避免深色模型在纯黑底上看不清
          try {
            viewer.renderer?.setClearColor(new THREE.Color(0x3a4150), 1);
          } catch {
            /* 渲染器不可用时忽略 */
          }
          // 未显式指定相机位置时，按模型包围盒自动框住，确保任意模型都可见
          if (!viewerDefaults?.initialCameraPosition) {
            try {
              autoFrame();
            } catch (err) {
              console.error('[SplatViewer] autoFrame 失败:', err);
            }
          }
          onLoaded?.();
          runStatsLoop();
        })
        .catch((e: unknown) => {
          if (!disposed) onError?.(e instanceof Error ? e.message : String(e));
        });
    } catch (e) {
      onError?.(e instanceof Error ? e.message : String(e));
    }

    /** 计算模型包围盒，把相机摆到能完整看到模型的位置 */
    function autoFrame() {
      const box: THREE.Box3 = viewer.splatMesh.computeBoundingBox(true);
      const center = new THREE.Vector3();
      const size = new THREE.Vector3();
      box.getCenter(center);
      box.getSize(size);
      const radius = Math.max(size.x, size.y, size.z) * 0.5 || 1;
      const cam = viewer.camera;
      const fov = ((cam.fov ?? 60) * Math.PI) / 180;
      const dist = (radius / Math.sin(fov / 2)) * 1.3;
      const dir = new THREE.Vector3(0.5, 0.3, 1).normalize();
      cam.position.copy(center.clone().add(dir.multiplyScalar(dist)));
      cam.lookAt(center);
      cam.updateProjectionMatrix?.();
      if (viewer.controls) {
        viewer.controls.target.copy(center);
        viewer.controls.update();
      }
    }

    function runStatsLoop() {
      let frames = 0;
      let last = performance.now();
      const tick = () => {
        frames += 1;
        const now = performance.now();
        if (now - last >= 1000) {
          let splatCount = 0;
          try {
            splatCount = viewer?.splatMesh?.getSplatCount?.() ?? 0;
          } catch {
            /* 某些版本无此方法，忽略 */
          }
          onStats?.({ fps: frames, splatCount });
          frames = 0;
          last = now;
        }
        rafId = requestAnimationFrame(tick);
      };
      rafId = requestAnimationFrame(tick);
    }

    return () => {
      disposed = true;
      cancelAnimationFrame(rafId);
      try {
        viewer?.dispose?.();
      } catch {
        /* ignore */
      }
      if (container) container.innerHTML = '';
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url, format, alphaThreshold]);

  return <div ref={containerRef} className="absolute inset-0" />;
}
