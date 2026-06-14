import ImportButton from '@/components/ImportButton';

// Phase 3 将实现：选数据集 / 上传图片 → 发起重建 → SSE 进度条 → 保存路径选择。
export default function ReconstructPage() {
  return (
    <div className="mx-auto max-w-3xl p-6">
      <h1 className="text-2xl font-semibold text-white">新建重建</h1>
      <p className="mt-2 text-sm text-slate-400">
        从内置数据集选一组图片，或上传自己的一系列图片进行三维重建。
      </p>

      <div className="mt-6 rounded-xl border border-dashed border-slate-700 bg-panel p-10 text-center text-slate-500">
        <p>上传与重建管线将在 Phase 2 / Phase 3 接入后端后开放。</p>
        <p className="mt-2 text-xs">
          目前可先「导入本地已重建文件」直接进入拖拽查看。
        </p>
        <div className="mt-4 flex justify-center">
          <ImportButton />
        </div>
      </div>
    </div>
  );
}
