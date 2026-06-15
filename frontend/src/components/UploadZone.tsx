import { useRef, useState } from 'react';

interface UploadZoneProps {
  onFiles: (files: File[]) => void;
  disabled?: boolean;
}

/** 拖拽 / 点击上传多张图片或一个 ZIP 包。 */
export default function UploadZone({ onFiles, disabled }: Readonly<UploadZoneProps>) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const handle = (list: FileList | null) => {
    if (!list || list.length === 0) return;
    onFiles(Array.from(list));
  };

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled) setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        if (!disabled) handle(e.dataTransfer.files);
      }}
      onClick={() => !disabled && inputRef.current?.click()}
      className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-10 text-center transition ${
        dragging ? 'border-accent bg-accent/10' : 'border-slate-700 hover:border-slate-500'
      } ${disabled ? 'pointer-events-none opacity-50' : ''}`}
    >
      <input
        ref={inputRef}
        type="file"
        multiple
        accept="image/*,.zip"
        className="hidden"
        onChange={(e) => handle(e.target.files)}
      />
      <div className="text-3xl text-slate-600">⬆</div>
      <p className="mt-2 text-sm text-slate-300">拖拽图片到此，或点击选择</p>
      <p className="mt-1 text-xs text-slate-500">支持多张 jpg/png，或一个 .zip 包（建议 30–80 张环绕拍摄）</p>
    </div>
  );
}
