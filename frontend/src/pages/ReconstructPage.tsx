import { useEffect, useState } from 'react';
import UploadZone from '@/components/UploadZone';
import PathPicker from '@/components/PathPicker';
import JobProgress from '@/components/JobProgress';
import ImportButton from '@/components/ImportButton';
import { createJob, fetchDatasets, uploadFiles } from '@/api/client';
import type { CreateJobRequest, Dataset } from '@/types';

const STEP_PRESETS = [
  { v: 3000, label: '预览 3k (仅测流程, 质量差)' },
  { v: 7000, label: '快速 7k (推荐)' },
  { v: 30000, label: '高质量 30k' },
];

export default function ReconstructPage() {
  const [source, setSource] = useState<'dataset' | 'upload'>('dataset');
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [datasetId, setDatasetId] = useState<string | null>(null);
  const [upload, setUpload] = useState<{ upload_id: string; num_images: number } | null>(null);
  const [uploadPct, setUploadPct] = useState<number | null>(null);
  const [maxSteps, setMaxSteps] = useState(7000);
  const [dataFactor, setDataFactor] = useState(4);
  const [outputDir, setOutputDir] = useState('');
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDatasets().then(setDatasets);
  }, []);

  const onUpload = async (files: File[]) => {
    setError(null);
    setUploadPct(0);
    try {
      const res = await uploadFiles(files, setUploadPct);
      setUpload(res);
    } catch {
      setError('上传失败，请检查后端是否运行');
    } finally {
      setUploadPct(null);
    }
  };

  const canSubmit =
    (source === 'dataset' && datasetId) || (source === 'upload' && upload);

  const submit = async () => {
    setError(null);
    const req: CreateJobRequest = {
      source,
      dataset_id: source === 'dataset' ? datasetId ?? undefined : undefined,
      upload_id: source === 'upload' ? upload?.upload_id : undefined,
      max_steps: maxSteps,
      data_factor: dataFactor,
      output_dir: outputDir || undefined,
      name: source === 'dataset' ? `${datasetId}` : '上传重建',
    };
    try {
      const job = await createJob(req);
      setJobId(job.job_id);
    } catch {
      setError('发起重建失败，请检查后端 / CUDA 环境');
    }
  };

  const selectedDs = datasets.find((d) => d.id === datasetId);

  return (
    <div className="mx-auto max-w-3xl p-6">
      <h1 className="text-2xl font-semibold text-white">新建重建</h1>
      <p className="mt-1 text-sm text-slate-400">
        选内置数据集，或上传你自己的一组图片，重建出 3D 高斯模型。
      </p>

      {jobId ? (
        <div className="mt-6 space-y-4">
          <JobProgress jobId={jobId} />
          <button
            onClick={() => setJobId(null)}
            className="text-sm text-slate-400 hover:text-slate-200"
          >
            ← 再建一个
          </button>
        </div>
      ) : (
        <div className="mt-6 space-y-5">
          {/* 来源切换 */}
          <div className="flex gap-2">
            {(['dataset', 'upload'] as const).map((s) => (
              <button
                key={s}
                onClick={() => setSource(s)}
                className={`rounded-md px-4 py-2 text-sm transition ${
                  source === s ? 'bg-accent text-white' : 'bg-slate-800 text-slate-300'
                }`}
              >
                {s === 'dataset' ? '选内置数据集' : '上传图片'}
              </button>
            ))}
          </div>

          {source === 'dataset' ? (
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {datasets.length === 0 && (
                <p className="text-sm text-slate-500">
                  暂无内置数据集（放置到 datasets/ 下，需含 images/）。
                </p>
              )}
              {datasets.map((d) => (
                <button
                  key={d.id}
                  onClick={() => setDatasetId(d.id)}
                  className={`rounded-lg border p-3 text-left text-sm transition ${
                    datasetId === d.id
                      ? 'border-accent bg-accent/10'
                      : 'border-slate-700 hover:border-slate-500'
                  }`}
                >
                  <div className="font-medium text-white">{d.name}</div>
                  <div className="text-xs text-slate-400">
                    {d.num_images} 张 · {d.has_poses ? '已含位姿(跳过SfM)' : '需SfM'}
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <div>
              <UploadZone onFiles={onUpload} disabled={uploadPct !== null} />
              {uploadPct !== null && (
                <p className="mt-2 text-xs text-accent">上传中… {uploadPct}%</p>
              )}
              {upload && (
                <p className="mt-2 text-xs text-emerald-400">
                  ✓ 已上传 {upload.num_images} 张图，可发起重建
                </p>
              )}
            </div>
          )}

          {selectedDs?.has_poses && (
            <p className="text-xs text-emerald-400">
              该数据集已含相机位姿，将跳过 COLMAP 直接训练。
            </p>
          )}

          {/* 参数 */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="mb-1 block text-sm text-slate-300">训练步数</label>
              <select
                value={maxSteps}
                onChange={(e) => setMaxSteps(Number(e.target.value))}
                className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
              >
                {STEP_PRESETS.map((p) => (
                  <option key={p.v} value={p.v}>{p.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm text-slate-300">降采样 (8G显存建议4)</label>
              <select
                value={dataFactor}
                onChange={(e) => setDataFactor(Number(e.target.value))}
                className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100"
              >
                <option value={1}>1 (原分辨率)</option>
                <option value={2}>2</option>
                <option value={4}>4 (省显存)</option>
              </select>
            </div>
          </div>

          <PathPicker value={outputDir} onChange={setOutputDir} />

          {error && <p className="text-sm text-red-400">{error}</p>}

          <div className="flex items-center gap-3">
            <button
              onClick={submit}
              disabled={!canSubmit}
              className="rounded-md bg-accent px-5 py-2.5 text-sm font-medium text-white transition hover:bg-accent/80 disabled:opacity-40"
            >
              发起重建
            </button>
            <span className="text-xs text-slate-500">或</span>
            <ImportButton />
          </div>
        </div>
      )}
    </div>
  );
}
