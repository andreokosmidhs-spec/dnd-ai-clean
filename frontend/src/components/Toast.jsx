import React, { useState, useEffect } from 'react';
import { CheckCircle, Info, AlertCircle, X } from 'lucide-react';

let toastId = 0;
let showToastCallback = null;

// Global function to show toasts
window.showToast = (message, type = 'info', duration = 3000) => {
  if (showToastCallback) {
    showToastCallback(message, type, duration);
  }
};

const Toast = () => {
  const [toasts, setToasts] = useState([]);

  useEffect(() => {
    showToastCallback = (message, type, duration) => {
      const id = toastId++;
      const newToast = { id, message, type, duration };
      setToasts(prev => [...prev, newToast]);
      
      setTimeout(() => {
        setToasts(prev => prev.filter(t => t.id !== id));
      }, duration);
    };

    return () => {
      showToastCallback = null;
    };
  }, []);

  const removeToast = (id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  };

  const getIcon = (type) => {
    switch (type) {
      case 'success':
        return <CheckCircle className="h-5 w-5" />;
      case 'error':
        return <AlertCircle className="h-5 w-5" />;
      case 'info':
      default:
        return <Info className="h-5 w-5" />;
    }
  };

  const getStyles = (type) => {
    switch (type) {
      case 'success':
        return 'bg-green-600 border-green-400 text-green-50';
      case 'error':
        return 'bg-red-600 border-red-400 text-red-50';
      case 'info':
      default:
        return 'bg-violet-600 border-violet-400 text-violet-50';
    }
  };

  return (
    <div className="fixed top-20 right-4 z-[9999] space-y-2 pointer-events-none">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`${getStyles(toast.type)} border-2 rounded-lg shadow-lg backdrop-blur-sm px-4 py-3 flex items-center gap-3 min-w-[300px] max-w-[400px] animate-in slide-in-from-right-5 duration-300 pointer-events-auto`}
        >
          <div className="flex-shrink-0">
            {getIcon(toast.type)}
          </div>
          <div className="flex-1 text-sm font-medium">
            {toast.message}
          </div>
          <button
            onClick={() => removeToast(toast.id)}
            className="flex-shrink-0 hover:opacity-70 transition-opacity"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      ))}
    </div>
  );
};

export default Toast;
