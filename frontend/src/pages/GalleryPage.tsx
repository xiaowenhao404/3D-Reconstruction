import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ModelCard from '@/components/ModelCard';
import ImportButton from '@/components/ImportButton';
import { fetchModels } from '@/api/client';
import { useStore } from '@/store/useStore';
import type { SplatModel } from '@/types';

// Phase 1 内置样例（由 scripts/download_sample.py 下载到 public/models/sample.splat）。
// 后端就绪后，模型库以 /api/models 为准，此条目仅作离线兜底演示。
const SAMPLE_MODELS: SplatModel[] = [
  {
    id: 'sample-nike',
    name: '样例场景 (Nike)',
    source: 'bundled',
    format: 'splat',
    url: '/models/sample.splat',
    // 不指定相机参数 → 由查看器按包围盒自动框住模型
  },
];

export default function GalleryPage() {
  const navigate = useNavigate();
  const importedModels = useStore((s) => s.importedModels);
  const selectModel = useStore((s) => s.selectModel);
  const [backendModels, setBackendModels] = useState<SplatModel[]>([]);

  useEffect(() => {
    fetchModels().then(setBackendModels);
  }, []);

  const open = (m: SplatModel) => {
    selectModel(m);
    navigate(`/viewer/${m.id}`);
  };

  const allModels = [...importedModels, ...backendModels, ...SAMPLE_MODELS];

  return (
    <div className="mx-auto max-w-6xl p-6">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-white">模型库</h1>
          <p className="mt-1 text-sm text-slate-400">
            选择一个模型拖拽查看，或导入本地文件 / 新建一次重建。
          </p>
        </div>
        <div className="flex gap-3">
          <ImportButton />
          <button
            onClick={() => navigate('/reconstruct')}
            className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white transition hover:bg-accent/80"
          >
            + 新建重建
          </button>
        </div>
      </div>

      {allModels.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-700 p-12 text-center text-slate-500">
          暂无模型。点击「导入本地文件」加载一个 .ply / .splat / .ksplat，或新建重建。
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {allModels.map((m) => (
            <ModelCard key={m.id} model={m} onOpen={open} />
          ))}
        </div>
      )}
    </div>
  );
}
