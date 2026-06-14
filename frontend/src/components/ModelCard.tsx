import type { SplatModel } from '@/types';

const sourceLabel: Record<string, string> = {
  bundled: '内置',
  generated: '重建生成',
  imported: '本地导入',
};

interface ModelCardProps {
  model: SplatModel;
  onOpen: (m: SplatModel) => void;
}

export default function ModelCard({ model, onOpen }: ModelCardProps) {
  return (
    <button
      onClick={() => onOpen(model)}
      className="group flex flex-col overflow-hidden rounded-xl border border-slate-800 bg-panel text-left transition hover:border-accent/60 hover:shadow-lg hover:shadow-accent/10"
    >
      <div className="relative aspect-video w-full overflow-hidden bg-slate-900">
        {model.thumb ? (
          <img
            src={model.thumb}
            alt={model.name}
            className="h-full w-full object-cover transition group-hover:scale-105"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-4xl text-slate-700">
            ◆
          </div>
        )}
        <span className="absolute left-2 top-2 rounded bg-black/60 px-2 py-0.5 text-xs text-slate-200">
          {model.format.toUpperCase()}
        </span>
      </div>
      <div className="flex flex-1 flex-col gap-1 p-3">
        <div className="truncate font-medium text-white">{model.name}</div>
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <span className="rounded bg-slate-800 px-1.5 py-0.5">
            {sourceLabel[model.source] ?? model.source}
          </span>
          {model.engine && <span>{model.engine}</span>}
          {model.metrics?.psnr && <span>PSNR {model.metrics.psnr.toFixed(1)}</span>}
        </div>
      </div>
    </button>
  );
}
