import React from 'react';
import { Loader2 } from 'lucide-react';
import { Card, CardContent } from './ui/card';

const LoadingModal = ({ progress = 0, isOpen = true }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
      <Card className="w-96 bg-gradient-to-br from-purple-900/90 to-blue-900/90 border-2 border-purple-500/50 shadow-2xl">
        <CardContent className="p-8 text-center">
          {/* Spinning Icon */}
          <div className="flex justify-center mb-6">
            <Loader2 className="h-16 w-16 text-purple-400 animate-spin" />
          </div>

          {/* Percentage Display */}
          <div className="mb-6">
            <div className="text-6xl font-bold text-purple-300 mb-2">
              {progress}%
            </div>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-gray-700/50 rounded-full h-3 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-purple-500 to-blue-500 transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>

          {/* Flavor Text */}
          <div className="mt-6 text-purple-200 text-sm opacity-80">
            Forging your legend...
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default LoadingModal;
