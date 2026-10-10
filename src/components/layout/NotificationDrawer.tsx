import { useModalDialog } from '../../lib/hooks/use-modal-dialog';
import { useAppState } from '../../lib/state/app-state';
import { Bell, CheckCheck, X, ArrowRight, ShieldAlert, CheckCircle2, Sparkles, BookOpen } from 'lucide-react';
import { useState } from 'react';
import DesignButton from '../common/DesignButton';
import { motion, AnimatePresence } from 'motion/react';

interface NotificationDrawerProps {
  open: boolean;
  onClose: () => void;
}

export function NotificationDrawer({ open, onClose }: NotificationDrawerProps) {
  const { notifications, markNotificationRead, markAllNotificationsRead, setActiveTab } = useAppState();
  const [filter, setFilter] = useState<'all' | 'unread'>('all');

  const dialogRef = useModalDialog(open, onClose);
  if (!open) return null;

  const filtered = notifications.filter((n) => (filter === 'unread' ? !n.read : true));

  const handleNotificationClick = (id: string, linkTab?: string) => {
    markNotificationRead(id);
    if (linkTab) {
      setActiveTab(linkTab);
      onClose();
    }
  };

  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-50 overflow-hidden">
          <motion.div
            className="absolute inset-0 bg-slate-900/30 backdrop-blur-xs"
            onClick={onClose}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
          />

          <motion.div
            ref={dialogRef}
            role="dialog"
            aria-modal="true"
            aria-label="Notification center"
            tabIndex={-1}
            className="absolute inset-y-0 right-0 max-w-md w-full bg-white shadow-2xl flex flex-col border-l border-slate-200"
            initial={{ opacity: 0, x: 300 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 300 }}
            transition={{ duration: 0.3, ease: 'easeOut' }}
          >
            {/* Header */}
            <div className="p-4 border-b border-slate-100 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="p-2 bg-slate-100 rounded-lg text-slate-700">
                  <Bell className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Notification Center</h3>
                  <p className="text-xs text-slate-500">Living competency model alerts</p>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <DesignButton
                  onClick={markAllNotificationsRead}
                  className="px-2.5 py-1 text-xs font-medium text-slate-600 hover:text-teal-700 hover:bg-slate-100 rounded-lg transition flex items-center gap-1 cursor-pointer"
                  variant="secondary"
                  size="sm"
                >
                  <CheckCheck className="w-3.5 h-3.5" />
                  <span>Mark all read</span>
                </DesignButton>
                <DesignButton
                  aria-label="Close notifications"
                  onClick={onClose}
                  className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition"
                  variant="secondary"
                  size="sm"
                >
                  <X className="w-4 h-4" />
                </DesignButton>
              </div>
            </div>

            {/* Filter Pills */}
            <div className="px-4 py-2 bg-slate-50 border-b border-slate-100 flex gap-2 text-xs">
              <button
                onClick={() => setFilter('all')}
                className={`px-3 py-1 rounded-md font-medium transition ${
                  filter === 'all'
                    ? 'bg-white text-slate-900 shadow-xs border border-slate-200'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                All ({notifications.length})
              </button>
              <button
                onClick={() => setFilter('unread')}
                className={`px-3 py-1 rounded-md font-medium transition ${
                  filter === 'unread'
                    ? 'bg-white text-slate-900 shadow-xs border border-slate-200'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Unread ({notifications.filter((n) => !n.read).length})
              </button>
            </div>

            {/* List */}
            <div className="flex-1 overflow-y-auto p-4 space-y-2.5">
              {filtered.length === 0 ? (
                <motion.div
                  className="py-12 text-center"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, ease: 'easeOut' }}
                >
                  <CheckCircle2 className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                  <div className="text-xs font-medium text-slate-500">No notifications found</div>
                </motion.div>
              ) : (
                filtered.map((item, index) => {
                  return (
                    <motion.div
                      key={item.id}
                      role="button"
                      tabIndex={0}
                      onKeyDown={e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); handleNotificationClick(item.id, item.linkTab); } }}
                      onClick={() => handleNotificationClick(item.id, item.linkTab)}
                      className={`p-3.5 rounded-xl border transition cursor-pointer flex items-start gap-3 ${
                        item.read
                          ? 'bg-white border-slate-100 hover:bg-slate-50 text-slate-600'
                          : 'bg-teal-50/40 border-teal-100 hover:bg-teal-50/70 text-slate-900 font-medium'
                      }`}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      transition={{ duration: 0.2, delay: index * 0.05 }}
                      whileHover={{ x: 4, scale: 1.01 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <div
                        className={`p-2 rounded-lg shrink-0 mt-0.5 ${
                          item.type === 'verification'
                            ? 'bg-emerald-100 text-emerald-700'
                            : item.type === 'assessment'
                            ? 'bg-blue-100 text-blue-700'
                            : item.type === 'roadmap'
                            ? 'bg-amber-100 text-amber-700'
                            : 'bg-slate-100 text-slate-700'
                        }`}
                      >
                        {item.type === 'verification' && <CheckCircle2 className="w-3.5 h-3.5" />}
                        {item.type === 'assessment' && <Sparkles className="w-3.5 h-3.5" />}
                        {item.type === 'roadmap' && <BookOpen className="w-3.5 h-3.5" />}
                        {item.type === 'system' && <ShieldAlert className="w-3.5 h-3.5" />}
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-1 mb-1">
                          <span className="text-xs font-bold text-slate-900 truncate">{item.title}</span>
                          <span className="text-[10px] text-slate-600 shrink-0">{item.timestamp}</span>
                        </div>
                        <p className="text-xs text-slate-600 leading-snug">{item.message}</p>
                        {item.linkTab && (
                          <div className="mt-2 text-[11px] text-teal-700 font-semibold flex items-center gap-1">
                            <span>Go to {item.linkTab}</span>
                            <ArrowRight className="w-3 h-3" />
                          </div>
                        )}
                      </div>
                    </motion.div>
                  );
                })
              )}
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}