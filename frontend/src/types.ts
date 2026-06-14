// 全局共享类型定义

export type SplatFormat = 'ply' | 'splat' | 'ksplat';

export type ModelSource = 'bundled' | 'generated' | 'imported';

export interface ViewerDefaults {
  cameraUp?: [number, number, number];
  initialCameraPosition?: [number, number, number];
  initialCameraLookAt?: [number, number, number];
}

export interface ModelMetrics {
  psnr?: number;
  ssim?: number;
  lpips?: number;
  train_seconds?: number;
  ply_mb?: number;
  ksplat_mb?: number;
}

/** 一个可供查看器加载的高斯模型条目 */
export interface SplatModel {
  id: string;
  name: string;
  source: ModelSource;
  format: SplatFormat;
  /** http(s) URL 或 blob: URL（本地导入） */
  url: string;
  thumb?: string;
  engine?: 'gsplat' | 'brush';
  metrics?: ModelMetrics;
  viewerDefaults?: ViewerDefaults;
  created_at?: string;
}
