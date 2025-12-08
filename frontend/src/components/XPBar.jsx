import React, { useMemo, useEffect, useState } from 'react';
import PropTypes from 'prop-types';

/**
 * Minecraft-Style XP Bar Component
 * Displays character level and XP progress with segmented, glowing bar
 */
const XPBar = ({ level, currentXp, xpForNextLevel, className = '' }) => {
  const [prevXp, setPrevXp] = useState(currentXp);
  const [showLevelUp, setShowLevelUp] = useState(false);

  // Calculate progress percentage
  const progressPercent = useMemo(() => {
    if (xpForNextLevel === 0) return 0;
    return Math.min((currentXp / xpForNextLevel) * 100, 100);
  }, [currentXp, xpForNextLevel]);

  // Detect XP changes for animations
  useEffect(() => {
    if (currentXp > prevXp) {
      // XP gained - could trigger animation here
      setPrevXp(currentXp);
    }
  }, [currentXp, prevXp]);

  // Detect level up
  useEffect(() => {
    if (level > 1 && progressPercent < 10) {
      // Level just increased (XP reset)
      setShowLevelUp(true);
      setTimeout(() => setShowLevelUp(false), 2000);
    }
  }, [level, progressPercent]);

  return (
    <div className={`w-full ${className}`}>
      {/* XP Bar Container */}
      <div 
        className="relative w-full h-8 bg-gray-900 border-2 border-gray-700 rounded overflow-hidden shadow-lg"
        role="progressbar"
        aria-valuenow={currentXp}
        aria-valuemin={0}
        aria-valuemax={xpForNextLevel}
        aria-label={`Level ${level}, ${currentXp} out of ${xpForNextLevel} XP`}
      >
        {/* Progress Fill with Segmented Minecraft Style */}
        <div
          className={`absolute inset-0 transition-all duration-500 ease-out ${
            showLevelUp ? 'animate-pulse' : ''
          }`}
          style={{
            width: `${progressPercent}%`,
            background: 'linear-gradient(to right, #10b981, #34d399)',
            boxShadow: progressPercent > 0 ? '0 0 20px rgba(16, 185, 129, 0.5), inset 0 0 20px rgba(16, 185, 129, 0.3)' : 'none',
            // Minecraft-style segments
            backgroundImage: 'repeating-linear-gradient(90deg, transparent 0%, transparent 4.5%, rgba(0,0,0,0.15) 4.5%, rgba(0,0,0,0.15) 5%, transparent 5%)'
          }}
        >
          {/* Inner glow effect */}
          <div 
            className="absolute inset-0 opacity-40"
            style={{
              background: 'linear-gradient(to bottom, rgba(255,255,255,0.3) 0%, transparent 50%, rgba(0,0,0,0.2) 100%)'
            }}
          />
        </div>

        {/* Level Number (Centered) */}
        <div 
          className="absolute inset-0 flex items-center justify-center z-10"
        >
          <span 
            className={`text-xl font-bold text-white transition-transform duration-300 ${
              showLevelUp ? 'scale-125' : 'scale-100'
            }`}
            style={{ 
              textShadow: '2px 2px 4px rgba(0,0,0,0.9), 0 0 8px rgba(0,0,0,0.5)'
            }}
          >
            {level}
          </span>
        </div>

        {/* Optional: XP Text on Hover */}
        <div className="absolute inset-0 flex items-center justify-end pr-4 opacity-0 hover:opacity-100 transition-opacity duration-300 z-20">
          <span className="text-xs font-semibold text-gray-300" style={{ textShadow: '1px 1px 2px rgba(0,0,0,0.8)' }}>
            {currentXp} / {xpForNextLevel} XP
          </span>
        </div>

        {/* Level Up Flash Effect */}
        {showLevelUp && (
          <div 
            className="absolute inset-0 pointer-events-none animate-pulse"
            style={{
              background: 'radial-gradient(circle, rgba(52, 211, 153, 0.6) 0%, transparent 70%)',
              animation: 'pulse 1s ease-in-out 2'
            }}
          />
        )}
      </div>

      {/* Optional: Level Up Notification */}
      {showLevelUp && (
        <div className="text-center mt-1 animate-bounce">
          <span className="text-sm font-bold text-emerald-400" style={{ textShadow: '0 0 10px rgba(16, 185, 129, 0.8)' }}>
            ⭐ LEVEL UP! ⭐
          </span>
        </div>
      )}
    </div>
  );
};

XPBar.propTypes = {
  level: PropTypes.number.isRequired,
  currentXp: PropTypes.number.isRequired,
  xpForNextLevel: PropTypes.number.isRequired,
  className: PropTypes.string
};

XPBar.defaultProps = {
  className: ''
};

export default XPBar;
