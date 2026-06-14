import type { SplatFormat } from '@/types';

/** 从文件名/URL 推断高斯模型格式 */
export function detectFormat(nameOrUrl: string): SplatFormat | null {
  const lower = nameOrUrl.toLowerCase();
  if (lower.endsWith('.ply')) return 'ply';
  if (lower.endsWith('.ksplat')) return 'ksplat';
  if (lower.endsWith('.splat')) return 'splat';
  return null;
}

/** 人类可读的文件大小 */
export function humanSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`;
}
