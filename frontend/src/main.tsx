import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import './index.css';
import App from './App';

// 注意：不使用 StrictMode。StrictMode 在开发模式下会双重挂载 effect，
// 会导致 GaussianSplats3D 创建两个 WebGL 上下文 / Viewer 实例而出错。
createRoot(document.getElementById('root')!).render(
  <BrowserRouter>
    <App />
  </BrowserRouter>,
);
