import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import SplatViewer, { type ViewerStats } from '@/components/SplatViewer';
import { useStore } from '@/store/useStore';
import { fetchModels } from '@/api/client';
import type { SplatModel } from '@/types';

export default function ViewerPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const storeModel = useStore((s) => (id ? s.getModelById(id) : undefined));
  const [model, setModel] = useState<SplatModel | undefined>(storeModel);

  // store 中找不到（如从任务完成跳转的后端生成模型 / 刷新页面）则回退到后端查询
  useEffect(() => {
    if (storeModel) {
      setModel(storeModel);
    } else if (id) {
      fetchModels().then((ms) => setModel(ms.find((m) => m.id === id))).catch(() => {});
    }
  }, [id, storeModel]);

  const [stats, setStats] = useState<ViewerStats>({ fps: 0, splatCount: 0 });
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [alphaInput, setAlphaInput] = useState(5);
  const [appliedAlpha, setAppliedAlpha] = useState(5);
  const [freeTumble, setFreeTumble] = useState(false);

  if (!model) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4 text-slate-400">
        <p>未找到模型，可能是页面被刷新（导入的模型仅当前会话有效）。</p>
        <button
          onClick={() => navigate('/')}
          className="rounded-md bg-accent px-4 py-2 text-sm text-white"
        >
          返回模型库
        </button>
      </div>
    );
  }

  return (
    <div className="relative h-full w-full bg-black">
      <SplatViewer
        url={model.url}
        format={model.format}
        alphaThreshold={appliedAlpha}
        freeTumble={freeTumble}
        viewerDefaults={model.viewerDefaults}
        onStats={setStats}
        onLoaded={() => setLoaded(true)}
        onError={(m) => setError(m)}
      />

      {/* 顶部信息条 */}
      <div className="pointer-events-none absolute left-0 right-0 top-0 flex items-start justify-between p-4">
        <div className="pointer-events-auto flex items-center gap-3 rounded-lg bg-black/60 px-3 py-2 backdrop-blur">
          <button
            onClick={() => navigate('/')}
            className="text-sm text-slate-300 hover:text-white"
          >
            ← 返回
          </button>
          <span className="text-sm font-medium text-white">{model.name}</span>
        </div>
        <div className="pointer-events-auto rounded-lg bg-black/60 px-3 py-2 text-xs text-slate-300 backdrop-blur">
          <div>FPS: {stats.fps}</div>
          {stats.splatCount > 0 && (
            <div>高斯数: {stats.splatCount.toLocaleString()}</div>
          )}
        </div>
      </div>

      {/* 底部控制条 */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 rounded-xl bg-black/60 px-4 py-3 text-xs text-slate-300 backdrop-blur">
        <div className="flex items-center gap-4">
          <span>
            {freeTumble ? '左键自由翻滚 · 右键平移 · 滚轮缩放' : '左键旋转 · 右键平移 · 滚轮缩放'}
          </span>
          <button
            onClick={() => setFreeTumble((v) => !v)}
            className={`rounded px-2 py-1 transition ${
              freeTumble
                ? 'bg-accent text-white'
                : 'bg-slate-700 text-slate-200 hover:bg-slate-600'
            }`}
            title="自由翻滚模式：纵向也可无限翻转（Trackball）"
          >
            自由翻滚 {freeTumble ? '开' : '关'}
          </button>
          <div className="flex items-center gap-2">
            <span>剔除阈值 {alphaInput}</span>
            <input
              type="range"
              min={0}
              max={50}
              value={alphaInput}
              onChange={(e) => setAlphaInput(Number(e.target.value))}
              className="w-28"
            />
            <button
              onClick={() => setAppliedAlpha(alphaInput)}
              disabled={alphaInput === appliedAlpha}
              className="rounded bg-accent/80 px-2 py-1 text-white disabled:opacity-40"
            >
              应用
            </button>
          </div>
        </div>
      </div>

      {!loaded && !error && (
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center text-slate-400">
          模型加载中…
        </div>
      )}
      {error && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-black/80 p-6 text-center">
          <p className="text-red-400">模型加载失败：{error}</p>
          <p className="max-w-md text-xs text-slate-500">
            若为内置样例，请先运行 <code>python scripts/download_sample.py</code>{' '}
            下载样例文件；或检查文件格式与显卡 WebGL/WebGPU 支持。
          </p>
          <button
            onClick={() => navigate('/')}
            className="rounded-md bg-accent px-4 py-2 text-sm text-white"
          >
            返回模型库
          </button>
        </div>
      )}
    </div>
  );
}
