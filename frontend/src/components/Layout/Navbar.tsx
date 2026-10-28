import React from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import { Bot, LogIn, UserPlus, LogOut, Menu } from 'lucide-react';
import { api } from '../../services/api';

interface NavbarProps {
  onOpenMobileMenu?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onOpenMobileMenu }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const token = localStorage.getItem('skillbridge_token');
  const isGuest = localStorage.getItem('skillbridge_is_guest') === 'true';
  const userJson = localStorage.getItem('skillbridge_user');
  const user = userJson ? JSON.parse(userJson) : null;
  const isAuthenticated = Boolean(token && !isGuest && user && user.email !== 'Guest Session');

  const handleLogout = async () => {
    try {
      await api.logout();
    } catch {
      // ignore
    } finally {
      localStorage.removeItem('skillbridge_token');
      localStorage.removeItem('skillbridge_user');
      localStorage.removeItem('skillbridge_is_guest');
      navigate('/login');
    }
  };

  const getPageTitle = (path: string) => {
    if (path === '/' || path.startsWith('/dashboard')) return isAuthenticated ? 'Career Dashboard' : 'SkillBridge';
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
    <header className="h-16 border-b border-slate-800 bg-slate-900/80 backdrop-blur-md px-3 sm:px-6 md:px-8 flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-center gap-2 sm:gap-2.5 min-w-0 mr-2">
        {/* Hamburger Menu Toggle (Visible only on mobile/tablet < md) */}
        {onOpenMobileMenu && (
          <button
            onClick={onOpenMobileMenu}
            className="p-2 -ml-1 text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg md:hidden cursor-pointer shrink-0 transition-colors"
            aria-label="Open mobile navigation menu"
          >
            <Menu className="h-5 w-5" />
          </button>
        )}

        <h1 className="text-sm sm:text-base font-semibold text-white tracking-tight truncate">
          {getPageTitle(location.pathname)}
        </h1>
      </div>

      <div className="flex items-center gap-2 sm:gap-3 shrink-0">
        {/* Assistant Quick Launcher */}
        <button
          onClick={handleOpenAssistant}
          className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/20 text-indigo-300 text-xs font-medium transition-colors cursor-pointer"
        >
          <Bot className="h-3.5 w-3.5 text-indigo-400" />
          <span>Career Assistant</span>
        </button>

        {/* Auth Navigation State */}
        {isAuthenticated ? (
          <div className="flex items-center gap-2 sm:gap-3 shrink-0">
            <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-slate-800/60 border border-slate-700/50">
              <div className="h-6 w-6 rounded-md bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center text-indigo-300 text-xs font-bold shrink-0">
                {(user?.first_name?.[0] || user?.email?.[0] || 'U').toUpperCase()}
              </div>
              <span className="hidden sm:inline text-xs text-slate-200 font-medium truncate max-w-[140px]">
                {user?.first_name ? `${user.first_name} ${user.last_name || ''}`.trim() : user?.email}
              </span>
            </div>
            <button
              onClick={handleLogout}
              className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors cursor-pointer shrink-0"
              title="Sign Out"
              aria-label="Sign Out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
            <Link
              to="/login"
              className="px-2.5 sm:px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-1.5 transition-colors shrink-0"
            >
              <LogIn className="h-3.5 w-3.5" />
              <span>Sign In</span>
            </Link>
            <Link
              to="/register"
              className="px-2.5 sm:px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-md shadow-indigo-600/25 shrink-0"
            >
              <UserPlus className="h-3.5 w-3.5" />
              <span>Sign Up</span>
            </Link>
          </div>
        )}
      </div>
    </header>
  );
};
