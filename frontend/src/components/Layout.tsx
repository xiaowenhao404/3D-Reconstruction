import { NavLink, Outlet } from 'react-router-dom';

const navItems = [
  { to: '/', label: '模型库', end: true },
  { to: '/reconstruct', label: '新建重建' },
  { to: '/compare', label: '引擎对比' },
];

export default function Layout() {
  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center gap-6 border-b border-slate-800 bg-panel px-6 py-3">
        <div className="flex items-center gap-2">
          <span className="text-lg font-semibold text-white">3DGS</span>
          <span className="text-sm text-slate-400">三维重建与可视化系统</span>
        </div>
        <nav className="flex gap-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `rounded-md px-3 py-1.5 text-sm transition ${
                  isActive
                    ? 'bg-accent/20 text-accent'
                    : 'text-slate-300 hover:bg-slate-800'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <a
          href="https://github.com/xiaowenhao404/3D-Reconstruction"
          target="_blank"
          rel="noreferrer"
          className="ml-auto text-xs text-slate-500 hover:text-slate-300"
        >
          GitHub
        </a>
      </header>
      <main className="relative flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
