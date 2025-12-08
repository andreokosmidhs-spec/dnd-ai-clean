import React, { useRef, useEffect } from 'react';
import { Card, CardContent } from './ui/card';
import { ScrollArea } from './ui/scroll-area';
import { Badge } from './ui/badge';
import { Dice6, Swords, Eye, MessageSquare, Loader2 } from 'lucide-react';

const AdventureLog = ({ gameLog, isProcessing, hasGameSession }) => {
  const scrollRef = useRef();

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [gameLog]);

  const getMessageIcon = (entry) => {
    switch (entry.type) {
      case 'dice':
        return <Dice6 className="h-4 w-4 flex-shrink-0" />;
      case 'combat':
        return <Swords className="h-4 w-4 flex-shrink-0" />;
      case 'npc':
        return <MessageSquare className="h-4 w-4 flex-shrink-0" />;
      default:
        return <Eye className="h-4 w-4 flex-shrink-0" />;
    }
  };

  const getMessageStyle = (entry) => {
    switch (entry.type) {
      case 'player':
        return 'bg-blue-600/15 border-l-2 border-blue-400 text-blue-50';
      case 'npc':
        return 'bg-purple-600/15 border-l-2 border-purple-400 text-purple-50';
      case 'system':
        return 'bg-gray-600/15 border-l-2 border-gray-400 text-gray-50';
      case 'dice':
        return `${entry.success ? 'bg-green-600/15 border-l-2 border-green-400 text-green-50' : 'bg-red-600/15 border-l-2 border-red-400 text-red-50'}`;
      case 'combat':
        return 'bg-red-600/15 border-l-2 border-red-400 text-red-50';
      case 'success':
        return 'bg-yellow-600/15 border-l-2 border-yellow-400 text-yellow-50';
      default:
        return 'bg-gray-600/15 border-l-2 border-gray-400 text-gray-50';
    }
  };

  const formatMessage = (message) => {
    // Break long paragraphs into readable chunks
    if (typeof message !== 'string') return message;
    
    const sentences = message.split(/(?<=[.!?])\s+/);
    if (sentences.length <= 2) return message;
    
    // Group sentences into paragraphs of 2-3 sentences max
    const paragraphs = [];
    let currentParagraph = [];
    
    sentences.forEach((sentence, idx) => {
      currentParagraph.push(sentence);
      if (currentParagraph.length >= 3 || idx === sentences.length - 1) {
        paragraphs.push(currentParagraph.join(' '));
        currentParagraph = [];
      }
    });
    
    return paragraphs.map((paragraph, idx) => (
      <p key={idx} className={idx > 0 ? 'mt-2' : ''}>
        {paragraph}
      </p>
    ));
  };

  return (
    <Card className="h-full bg-black/95 border-amber-600/30 backdrop-blur-sm overflow-hidden">
      <CardContent className="p-0 h-full flex flex-col">
        {/* Header */}
        <div className="p-3 border-b border-amber-600/20 flex-shrink-0">
          <div className="flex items-center justify-between">
            <h2 className="text-amber-400 font-semibold text-sm flex items-center gap-2">
              <Eye className="h-4 w-4" />
              Adventure Log
            </h2>
            {hasGameSession && (
              <Badge variant="outline" className="text-xs border-green-400/50 text-green-300">
                AI Active
              </Badge>
            )}
          </div>
        </div>

        {/* Messages */}
        <ScrollArea className="flex-1 log" ref={scrollRef}>
          <div className="p-3 space-y-3">
            {gameLog.map((entry, idx) => (
              <div
                key={idx}
                className={`p-3 rounded-lg ${getMessageStyle(entry)} animate-in slide-in-from-left-5 duration-200`}
              >
                <div className="flex items-start gap-3 w-full min-w-0">
                  <div className="flex-shrink-0 mt-0.5">
                    {getMessageIcon(entry)}
                  </div>
                  <div className="flex-1 min-w-0 overflow-hidden">
                    {entry.speaker && (
                      <div className="font-medium text-sm mb-1 text-white">
                        {entry.speaker}:
                      </div>
                    )}
                    <div className="text-sm leading-relaxed text-current max-w-none">
                      {formatMessage(entry.message)}
                    </div>
                    {entry.timestamp && (
                      <div className="text-xs opacity-60 mt-2 font-mono">
                        {new Date(entry.timestamp).toLocaleTimeString()}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
            
            {isProcessing && (
              <div className="flex items-center gap-3 text-amber-400 p-3">
                <Loader2 className="animate-spin h-4 w-4 flex-shrink-0" />
                <span className="text-sm">
                  {hasGameSession ? 'AI is thinking...' : 'Processing your action...'}
                </span>
              </div>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
};

export default AdventureLog;