// Phase 4 将实现：同一场景 gsplat vs Brush 并排视图 + PSNR/SSIM/LPIPS/时间/体积 对比表。
export default function ComparePage() {
  return (
    <div className="mx-auto max-w-3xl p-6">
      <h1 className="text-2xl font-semibold text-white">引擎对比</h1>
      <p className="mt-2 text-sm text-slate-400">
        gsplat (CUDA) vs Brush (WebGPU) 在同一场景上的质量 / 速度 / 体积对比。
      </p>
      <div className="mt-6 rounded-xl border border-dashed border-slate-700 bg-panel p-10 text-center text-slate-500">
        将在 Phase 4 实现。
      </div>
    </div>
  );
}
