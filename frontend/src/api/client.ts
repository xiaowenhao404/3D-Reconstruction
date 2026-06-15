import axios from 'axios';
import type {
  CreateJobRequest,
  Dataset,
  Job,
  SplatModel,
} from '@/types';

// 经 Vite 代理转发到后端 :8000（见 vite.config.ts）
export const api = axios.create({ baseURL: '/api', timeout: 30000 });

/** 模型库（后端未就绪时静默返回空，便于前端独立运行） */
export async function fetchModels(): Promise<SplatModel[]> {
  try {
    const { data } = await api.get<SplatModel[]>('/models');
    return data;
  } catch {
    return [];
  }
}

export async function fetchDatasets(): Promise<Dataset[]> {
  try {
    const { data } = await api.get<Dataset[]>('/datasets');
    return data;
  } catch {
    return [];
  }
}

export async function createJob(req: CreateJobRequest): Promise<Job> {
  const { data } = await api.post<Job>('/jobs', req);
  return data;
}

export async function getJob(jobId: string): Promise<Job> {
  const { data } = await api.get<Job>(`/jobs/${jobId}`);
  return data;
}

/** 上传图片/ZIP，返回 upload_id */
export async function uploadFiles(
  files: File[],
  onProgress?: (pct: number) => void,
): Promise<{ upload_id: string; num_images: number }> {
  const form = new FormData();
  files.forEach((f) => form.append('files', f));
  const { data } = await api.post('/uploads', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 0, // 大文件不限时
    onUploadProgress: (e) => {
      if (onProgress && e.total) onProgress(Math.round((e.loaded / e.total) * 100));
    },
  });
  return data;
}

/** 按磁盘路径导入已有模型 */
export async function importByPath(path: string, name?: string): Promise<SplatModel> {
  const { data } = await api.post<SplatModel>('/models/import', { path, name });
  return data;
}

export async function saveModelAs(modelId: string, targetPath: string) {
  const { data } = await api.post(`/models/${modelId}/save-as`, { target_path: targetPath });
  return data as { ok: boolean; saved_to: string };
}

export async function suggestRoot(): Promise<{ root: string; tasks: string }> {
  const { data } = await api.get('/fs/suggest-root');
  return data;
}

export async function validatePath(path: string) {
  const { data } = await api.post('/fs/validate-path', { path });
  return data as { ok: boolean; exists: boolean; writable: boolean; message: string };
}
