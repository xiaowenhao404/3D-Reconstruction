import { useEffect, useRef } from 'react';
import * as GaussianSplats3D from '@mkkellogg/gaussian-splats-3d';
import type { SplatFormat, ViewerDefaults } from '@/types';

// GaussianSplats3D.SceneFormat 枚举：Ply=0, Splat=1, KSplat=2
const FORMAT_ENUM: Record<SplatFormat, number> = { ply: 0, splat: 1, ksplat: 2 };

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
        gpuAcceleratedSort: true,
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
          onLoaded?.();
          runStatsLoop();
        })
        .catch((e: unknown) => {
          if (!disposed) onError?.(e instanceof Error ? e.message : String(e));
        });
    } catch (e) {
      onError?.(e instanceof Error ? e.message : String(e));
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
