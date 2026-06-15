import type { Job } from '@/types';

/**
 * 订阅重建任务的 SSE 进度流。返回取消函数。
 * 后端按 "data: {job json}\n\n" 推送，结束时发送 event: end。
 */
export function subscribeJob(
  jobId: string,
  onEvent: (job: Job) => void,
  onEnd?: () => void,
): () => void {
  const es = new EventSource(`/api/jobs/${jobId}/events`);
  let closed = false;
  const close = () => {
    if (!closed) {
      closed = true;
      es.close();
      onEnd?.();
    }
  };
  es.onmessage = (e) => {
    try {
      onEvent(JSON.parse(e.data) as Job);
    } catch {
      /* 忽略非 JSON 心跳 */
    }
  };
  es.addEventListener('end', close);
  es.onerror = close; // 连接关闭（含正常结束）即停止，避免自动重连
  return () => {
    closed = true;
    es.close();
  };
}
