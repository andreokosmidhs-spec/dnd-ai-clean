import React, { useState, useEffect } from 'react';
import { Volume2, VolumeX, Loader2 } from 'lucide-react';
import { Button } from './ui/button';

const NarrationAudioPlayer = ({ text, audioUrl, onGenerateAudio, isGenerating }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [audio] = useState(() => new Audio());

  useEffect(() => {
    const handleEnded = () => setIsPlaying(false);
    audio.addEventListener('ended', handleEnded);
    return () => {
      audio.removeEventListener('ended', handleEnded);
      audio.pause();
    };
  }, [audio]);

  useEffect(() => {
    if (audioUrl) {
      audio.src = audioUrl;
    }
  }, [audioUrl, audio]);

  const handlePlay = async () => {
    if (!audioUrl) {
      // Generate audio if not already generated
      await onGenerateAudio();
      return;
    }

    if (isPlaying) {
      audio.pause();
      audio.currentTime = 0;
      setIsPlaying(false);
    } else {
      try {
        await audio.play();
        setIsPlaying(true);
      } catch (err) {
        console.error('Playback error:', err);
      }
    }
  };

  return (
    <Button
      onClick={handlePlay}
      disabled={isGenerating}
      variant="outline"
      size="sm"
      className="text-xs border-purple-400/50 text-purple-300 hover:bg-purple-600/20 hover:text-purple-200"
      title={isPlaying ? 'Stop narration' : 'Play narration'}
    >
      {isGenerating ? (
        <>
          <Loader2 className="h-3 w-3 mr-1 animate-spin" />
          Generating...
        </>
      ) : isPlaying ? (
        <>
          <VolumeX className="h-3 w-3 mr-1" />
          Stop
        </>
      ) : (
        <>
          <Volume2 className="h-3 w-3 mr-1" />
          Play Narration
        </>
      )}
    </Button>
  );
};

export default NarrationAudioPlayer;
