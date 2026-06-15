import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getJob } from '@/api/client';
import { subscribeJob } from '@/api/sse';
import type { Job, JobStage } from '@/types';

const STAGE_LABELS: { key: JobStage; label: string }[] = [
  { key: 'upload', label: '准备' },
  { key: 'sfm', label: 'SfM 位姿' },
  { key: 'train', label: '高斯训练' },
  { key: 'compress', label: '产物' },
  { key: 'done', label: '完成' },
];

/** 监听任务 SSE 进度，展示阶段 + 进度条；成功后跳转查看器。 */
export default function JobProgress({ jobId }: Readonly<{ jobId: string }>) {
  const navigate = useNavigate();
  const [job, setJob] = useState<Job | null>(null);

  useEffect(() => {
    // 先拉一次当前状态，再订阅增量
    getJob(jobId).then(setJob).catch(() => {});
    const stop = subscribeJob(jobId, setJob, () => getJob(jobId).then(setJob).catch(() => {}));
    // 轮询兜底：万一 SSE 经代理被缓冲，仍能更新进度
    const poll = setInterval(() => {
      getJob(jobId)
        .then((j) => {
          setJob(j);
          if (j.status === 'succeeded' || j.status === 'failed' || j.status === 'canceled') {
            clearInterval(poll);
          }
        })
        .catch(() => {});
    }, 2500);
    return () => {
      stop();
      clearInterval(poll);
    };
  }, [jobId]);

  if (!job) return <div className="text-slate-400">连接任务中…</div>;

  const curIdx = STAGE_LABELS.findIndex((s) => s.key === job.stage);
  const failed = job.status === 'failed';
  const done = job.status === 'succeeded';

  return (
    <div className="rounded-xl border border-slate-800 bg-panel p-5">
      <div className="mb-3 flex items-center justify-between">
        <span className="font-medium text-white">{job.name}</span>
        <span className="text-xs text-slate-400">{job.status}</span>
      </div>

      {/* 阶段指示 */}
      <div className="mb-3 flex items-center gap-2 text-xs">
        {STAGE_LABELS.map((s, i) => (
          <div key={s.key} className="flex items-center gap-2">
            <span
              className={
                done || i < curIdx
                  ? 'text-emerald-400'
                  : i === curIdx
                    ? 'text-accent'
                    : 'text-slate-600'
              }
            >
              {done || i < curIdx ? '●' : i === curIdx ? '◉' : '○'} {s.label}
            </span>
            {i < STAGE_LABELS.length - 1 && <span className="text-slate-700">—</span>}
          </div>
        ))}
      </div>

      {/* 进度条 */}
      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800">
        <div
          className={`h-full transition-all ${failed ? 'bg-red-500' : 'bg-accent'}`}
          style={{ width: `${job.overall_progress}%` }}
        />
      </div>
      <p className="mt-2 truncate text-xs text-slate-400">
        {job.overall_progress.toFixed(0)}% · {job.message}
      </p>

      {failed && (
        <p className="mt-2 text-sm text-red-400">重建失败：{job.error ?? job.message}</p>
      )}
      {done && job.model_id && (
        <button
          onClick={() => navigate(`/viewer/${job.model_id}`)}
          className="mt-3 rounded-md bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent/80"
        >
          查看重建结果 →
        </button>
      )}
    </div>
  );
}
