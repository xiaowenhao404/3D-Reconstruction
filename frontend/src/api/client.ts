import axios from 'axios';
import type { SplatModel } from '@/types';

// 经 Vite 代理转发到后端 :8000（见 vite.config.ts）
export const api = axios.create({ baseURL: '/api', timeout: 15000 });

/**
 * 拉取后端模型库。后端尚未实现时静默返回空数组，
 * 使前端在 Phase 1（无后端）下仍可独立运行（依赖本地导入 / 样例）。
 */
export async function fetchModels(): Promise<SplatModel[]> {
  try {
    const { data } = await api.get<SplatModel[]>('/models');
    return data;
  } catch {
    return [];
  }
}
