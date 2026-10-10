import { useAppState } from '../../lib/state/app-state';
import { X } from 'lucide-react';
import DesignButton from './DesignButton';
import { motion, AnimatePresence } from 'motion/react';

export function ToastContainer() {
  const { toasts, dismissToast } = useAppState();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 max-w-sm w-[calc(100%_-_2.5rem)] pointer-events-none">
      <AnimatePresence>
        {toasts.map((toast) => {
          let borderColor = 'border-emerald-200';

          if (toast.type === 'info') {
            borderColor = 'border-blue-200';
          } else if (toast.type === 'warning') {
            borderColor = 'border-amber-200';
          }

          return (
            <motion.div
              key={toast.id}
              id={toast.id}
              className={`pointer-events-auto flex items-start gap-3 p-3.5 bg-white rounded-xl shadow-lg border ${borderColor} text-slate-800 transition-all transform translate-y-0`}
              initial={{ opacity: 0, x: 100 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 100 }}
              transition={{ duration: 0.3, ease: 'easeOut' }}
            >
              
              <div className="flex-1 min-w-0">
                <h4 className="text-xs font-semibold text-slate-900 leading-tight">{toast.title}</h4>
                <p className="text-xs text-slate-600 mt-0.5 leading-snug">{toast.message}</p>
              </div>
<DesignButton
                  onClick={() => dismissToast(toast.id)}
                  className="text-slate-400 hover:text-slate-600 p-0.5 rounded transition"
                  aria-label="Close notification"
                  variant="secondary"
                  size="sm"
                >
                  <X className="w-3.5 h-3.5" />
                </DesignButton>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}

export default ToastContainer;