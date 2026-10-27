import React from 'react';
import { NavLink, useNavigate, Link } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  Briefcase,
  GitCompare,
  Compass,
  History,
  Settings,
  LogOut,
  BrainCircuit,
  HelpCircle,
  LifeBuoy,
  LogIn,
  Bot
} from 'lucide-react';
import { api } from '../../services/api';

interface SidebarProps {
  collapsed?: boolean;
}

export const Sidebar: React.FC<SidebarProps> = () => {
  const navigate = useNavigate();
  const token = localStorage.getItem('skillbridge_token');
  const userJson = localStorage.getItem('skillbridge_user');
  const user = userJson ? JSON.parse(userJson) : null;

  const handleLogout = async () => {
    try {
      await api.logout();
    } catch {
      // ignore
    } finally {
      localStorage.removeItem('skillbridge_token');
      localStorage.removeItem('skillbridge_user');
      navigate('/login');
    }
  };

  const handleOpenAssistant = () => {
    window.dispatchEvent(new CustomEvent('skillbridge:open-chat'));
  };

  const navItems = [
    { name: 'Home', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Jobs', path: '/jobs', icon: Briefcase },
    { name: 'Resume', path: '/resumes', icon: FileText },
    { name: 'Skill Match', path: '/matches', icon: GitCompare },
    { name: 'Learning Roadmap', path: '/roadmap/latest', icon: Compass },
    { name: 'Help & FAQ', path: '/faq', icon: HelpCircle },
    { name: 'Support', path: '/support', icon: LifeBuoy },
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between h-screen sticky top-0 select-none shrink-0">
      <div className="overflow-y-auto">
        {/* Brand Header */}
        <Link to="/" className="h-16 flex items-center px-6 border-b border-slate-800 gap-3 hover:bg-slate-850/50 transition-colors">
          <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <BrainCircuit className="h-5 w-5 text-white" />
          </div>
          <div>
            <div className="font-bold text-lg text-white flex items-center gap-1.5">
              SkillBridge
            </div>
            <p className="text-[11px] text-slate-400 leading-none">Career Development Platform</p>
          </div>
        </Link>

        {/* Navigation Links */}
        <nav className="p-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30 font-semibold'
                      : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
                  }`
                }
              >
                <Icon className="h-4 w-4 shrink-0" />
                <span>{item.name}</span>
              </NavLink>
            );
          })}

          {/* Direct Career Assistant Launcher in Navigation */}
          <button
            onClick={handleOpenAssistant}
            className="w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium text-slate-400 hover:text-slate-100 hover:bg-slate-800/60 transition-colors cursor-pointer text-left"
          >
            <Bot className="h-4 w-4 shrink-0 text-violet-400" />
            <span>Career Assistant</span>
          </button>
        </nav>
      </div>

      {/* User Footer Profile & Logout or Guest Callout */}
      <div className="p-4 border-t border-slate-800">
        {token ? (
          <div className="p-3 rounded-lg bg-slate-800/40 border border-slate-700/50 flex items-center justify-between">
            <div className="overflow-hidden pr-2">
              <p className="text-xs font-semibold text-white truncate">
                {user?.first_name ? `${user.first_name} ${user.last_name || ''}`.trim() : user?.email || 'Member Profile'}
              </p>
              <p className="text-[11px] text-slate-400 truncate">{user?.email || 'Active Session'}</p>
            </div>
            <button
              onClick={handleLogout}
              title="Sign out"
              className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-md transition-colors cursor-pointer"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <div className="p-3 rounded-lg bg-indigo-950/40 border border-indigo-500/20 text-center space-y-2">
            <p className="text-xs text-slate-300 font-medium">Ready to advance your career?</p>
            <Link
              to="/login"
              className="w-full py-1.5 px-3 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg flex items-center justify-center gap-1.5 transition-colors"
            >
              <LogIn className="h-3.5 w-3.5" />
              <span>Sign In</span>
            </Link>
          </div>
        )}
      </div>
    </aside>
  );
};
