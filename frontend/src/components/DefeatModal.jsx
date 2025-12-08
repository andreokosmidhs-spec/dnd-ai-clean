import React from 'react';
import { Skull, Heart } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import { Button } from './ui/button';

const DefeatModal = ({ isOpen, onContinue, playerName, currentHP, maxHP, injuryCount, xpPenalty = 0 }) => {
  return (
    <Dialog open={isOpen} onOpenChange={() => {}}>
      <DialogContent className="sm:max-w-md bg-gray-900 border-2 border-red-600">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-red-400 text-xl">
            <Skull className="h-6 w-6" />
            Defeated
          </DialogTitle>
          <DialogDescription className="text-gray-300 text-sm mt-3">
            <div className="space-y-3">
              <p>
                Darkness closes in as you fall to the ground. Your vision blurs,
                but your story isn't over yet...
              </p>
              
              <div className="bg-gray-800 rounded-lg p-3 border border-red-600/30">
                <div className="flex items-center gap-2 mb-2">
                  <Heart className="h-4 w-4 text-red-400" />
                  <span className="text-red-300 font-semibold text-sm">Status</span>
                </div>
                <div className="text-xs text-gray-300 space-y-1">
                  <p>You wake up at a safer location, wounded but alive.</p>
                  <p className="text-yellow-300">
                    HP Restored: {currentHP}/{maxHP} (50% of maximum)
                  </p>
                  <p className="text-orange-300">
                    Injuries Sustained: {injuryCount}
                  </p>
                  {xpPenalty > 0 && (
                    <p className="text-red-300">
                      Experience Lost: -{xpPenalty} XP
                    </p>
                  )}
                </div>
              </div>

              <p className="text-sm text-gray-400 italic">
                The road ahead may be harder, but {playerName || 'you'} will persevere.
              </p>
            </div>
          </DialogDescription>
        </DialogHeader>
        
        <div className="flex justify-center mt-4">
          <Button
            onClick={onContinue}
            className="bg-red-700 hover:bg-red-600 text-white font-semibold"
          >
            Continue Your Journey
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default DefeatModal;
