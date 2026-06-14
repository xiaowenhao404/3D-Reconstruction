import { useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useStore } from '@/store/useStore';
import { detectFormat } from '@/utils/format';
import type { SplatModel } from '@/types';

/**
 * 选择本地 .ply/.splat/.ksplat 文件 → 创建 blob URL → 注册为导入模型 → 跳转查看器。
 * 满足 US-6：无需 GPU、无需后端即可直接查看历史/外部模型文件。
 */
export default function ImportButton({ className }: { className?: string }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const addImportedModel = useStore((s) => s.addImportedModel);
  const selectModel = useStore((s) => s.selectModel);

  const onPick = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = ''; // 允许重复选择同一文件
    if (!file) return;
    const format = detectFormat(file.name);
    if (!format) {
      alert('不支持的格式，请选择 .ply / .splat / .ksplat 文件');
      return;
    }
    const id = `imported-${Date.now()}`;
    const model: SplatModel = {
      id,
      name: file.name,
      source: 'imported',
      format,
      url: URL.createObjectURL(file),
    };
    addImportedModel(model);
    selectModel(model);
    navigate(`/viewer/${id}`);
  };

  return (
    <>
      <input
        ref={inputRef}
        type="file"
        accept=".ply,.splat,.ksplat"
        className="hidden"
        onChange={onPick}
      />
      <button
        onClick={() => inputRef.current?.click()}
        className={
          className ??
          'rounded-md border border-accent/50 bg-accent/10 px-4 py-2 text-sm font-medium text-accent transition hover:bg-accent/20'
        }
      >
        导入本地文件
      </button>
    </>
  );
}
