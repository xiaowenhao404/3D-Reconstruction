import { create } from 'zustand';
import type { SplatModel } from '@/types';

interface AppState {
  /** 本地导入的模型（blob URL，仅当前会话有效） */
  importedModels: SplatModel[];
  /** 当前选中、将在查看器中打开的模型 */
  selectedModel: SplatModel | null;
  addImportedModel: (m: SplatModel) => void;
  selectModel: (m: SplatModel) => void;
  getModelById: (id: string) => SplatModel | undefined;
}

export const useStore = create<AppState>((set, get) => ({
  importedModels: [],
  selectedModel: null,
  addImportedModel: (m) =>
    set((s) => ({ importedModels: [m, ...s.importedModels] })),
  selectModel: (m) => set({ selectedModel: m }),
  getModelById: (id) =>
    get().importedModels.find((m) => m.id === id) ??
    (get().selectedModel?.id === id ? get().selectedModel ?? undefined : undefined),
}));
