import { Routes, Route } from 'react-router-dom';
import Layout from '@/components/Layout';
import GalleryPage from '@/pages/GalleryPage';
import ViewerPage from '@/pages/ViewerPage';
import ReconstructPage from '@/pages/ReconstructPage';
import ComparePage from '@/pages/ComparePage';

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<GalleryPage />} />
        <Route path="reconstruct" element={<ReconstructPage />} />
        <Route path="compare" element={<ComparePage />} />
      </Route>
      {/* 查看器全屏，不含通用布局 */}
      <Route path="viewer/:id" element={<ViewerPage />} />
    </Routes>
  );
}
