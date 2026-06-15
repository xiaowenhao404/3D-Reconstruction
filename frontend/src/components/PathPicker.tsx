import { useEffect, useState } from 'react';
import { suggestRoot, validatePath } from '@/api/client';

interface PathPickerProps {
  value: string;
  onChange: (path: string) => void;
}

/** 输出保存路径选择：默认 workspace，可改为任意绝对路径，实时校验可写。 */
export default function PathPicker({ value, onChange }: Readonly<PathPickerProps>) {
  const [status, setStatus] = useState<{ ok: boolean; msg: string } | null>(null);

  // 初始化默认根目录
  useEffect(() => {
    if (!value) suggestRoot().then((r) => onChange(r.root)).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 防抖校验
  useEffect(() => {
    if (!value) return;
    const t = setTimeout(() => {
      validatePath(value)
        .then((r) => setStatus({ ok: r.ok, msg: r.message }))
        .catch(() => setStatus({ ok: false, msg: '校验失败' }));
    }, 400);
    return () => clearTimeout(t);
  }, [value]);

  return (
    <div>
      <label className="mb-1 block text-sm text-slate-300">保存路径</label>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="产物保存目录（默认 workspace）"
        className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 outline-none focus:border-accent"
      />
      {status && (
        <p className={`mt-1 text-xs ${status.ok ? 'text-emerald-400' : 'text-red-400'}`}>
          {status.ok ? '✓ 可写' : `✗ ${status.msg}`}
        </p>
      )}
    </div>
  );
}
