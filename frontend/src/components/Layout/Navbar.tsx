import React from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import { Bot, LogIn, UserPlus, LogOut, Sparkles } from 'lucide-react';
import { api } from '../../services/api';

export const Navbar: React.FC = () => {
  const location = useLocation();
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

  const getPageTitle = (path: string) => {
    if (path === '/' || path.startsWith('/dashboard')) return token ? 'Career Dashboard' : 'Find Your Next Opportunity';
    if (path.startsWith('/resumes')) return 'Resume Management';
    if (path.startsWith('/jobs')) return 'Explore Jobs';
    if (path.startsWith('/matches')) return 'Skill Match Analysis';
    if (path.startsWith('/roadmap')) return 'Learning Roadmap';
    if (path.startsWith('/history')) return 'Activity History';
    if (path.startsWith('/faq')) return 'Help & FAQ';
    if (path.startsWith('/support')) return 'Support Desk';
    if (path.startsWith('/settings')) return 'Account Settings';
    return 'SkillBridge';
  };

  const handleOpenAssistant = () => {
    window.dispatchEvent(new CustomEvent('skillbridge:open-chat'));
  };

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/60 backdrop-blur-md px-4 sm:px-8 flex items-center justify-between sticky top-0 z-30">
      <div>
        <h1 className="text-base font-semibold text-white tracking-tight">
          {getPageTitle(location.pathname)}
        </h1>
      </div>

      <div className="flex items-center gap-3">
        {/* User-friendly Assistant Action */}
        <button
          onClick={handleOpenAssistant}
          className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/20 text-indigo-300 text-xs font-medium transition-colors cursor-pointer"
        >
          <Bot className="h-3.5 w-3.5 text-indigo-400" />
          <span>Career Assistant</span>
        </button>

        {/* Auth Navigation State */}
        {token ? (
          <div className="flex items-center gap-3">
            <span className="hidden sm:inline text-xs text-slate-300 font-medium">
              {user?.first_name || user?.email}
            </span>
            <button
              onClick={handleLogout}
              className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors cursor-pointer"
              title="Sign Out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <Link
              to="/login"
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-1.5 transition-colors"
            >
              <LogIn className="h-3.5 w-3.5" />
              <span>Sign In</span>
            </Link>
            <Link
              to="/register"
              className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-md shadow-indigo-600/25"
            >
              <UserPlus className="h-3.5 w-3.5" />
              <span>Create Account</span>
            </Link>
          </div>
        )}
      </div>
    </header>
  );
};
