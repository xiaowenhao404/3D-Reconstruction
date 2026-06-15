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

/** 可重建的内置数据集（图片组） */
export interface Dataset {
  id: string;
  name: string;
  num_images: number;
  scene_type: string;
  has_poses: boolean;
  thumb?: string | null;
}

export type JobStatus = 'queued' | 'running' | 'succeeded' | 'failed' | 'canceled';
export type JobStage = 'upload' | 'sfm' | 'undistort' | 'train' | 'compress' | 'done';

/** 重建任务状态（与后端 schemas.Job 对应） */
export interface Job {
  job_id: string;
  name: string;
  status: JobStatus;
  stage: JobStage;
  stage_progress: number;
  overall_progress: number;
  engine: 'gsplat' | 'brush';
  message: string;
  output_dir: string;
  model_id?: string | null;
  error?: string | null;
}

export interface CreateJobRequest {
  source: 'dataset' | 'upload';
  dataset_id?: string;
  upload_id?: string;
  engine?: 'gsplat' | 'brush';
  name?: string;
  output_dir?: string;
  max_steps?: number;
  data_factor?: number;
}

