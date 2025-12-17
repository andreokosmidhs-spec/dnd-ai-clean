import React from 'react';
import { useSearchParams } from 'react-router-dom';
import { CampaignLogPanel } from '../components/CampaignLogPanel';
import { AlertTriangle } from 'lucide-react';

/**
 * DEV PREVIEW PAGE - Remove before production release
 * 
 * Usage: /dev/campaign-log?campaignId=your-campaign-id
 * Falls back to a known working campaign ID if none provided.
 */
const DevCampaignLogPreview = () => {
  const [searchParams] = useSearchParams();
  
  // Get campaignId from query params or use fallback
  const campaignId = searchParams.get('campaignId') || 'b241e7a5-6fcf-49a9-8510-c7c830671d2a';
  const characterId = searchParams.get('characterId') || null;
  
  return (
    <div className="min-h-screen bg-gray-950">
      {/* DEV Banner */}
      <div className="fixed top-0 left-0 right-0 z-[100] bg-yellow-500 text-black py-2 px-4 flex items-center justify-center gap-2 text-sm font-bold">
        <AlertTriangle className="w-4 h-4" />
        DEV PREVIEW – Remove before release
        <AlertTriangle className="w-4 h-4" />
      </div>
      
      {/* Info bar with campaign details */}
      <div className="fixed top-10 left-0 right-0 z-[99] bg-gray-800 text-gray-300 py-2 px-4 text-xs font-mono border-b border-gray-700">
        <span className="text-gray-500">Campaign ID:</span> {campaignId}
        {characterId && (
          <>
            <span className="mx-2 text-gray-600">|</span>
            <span className="text-gray-500">Character ID:</span> {characterId}
          </>
        )}
      </div>
      
      {/* Campaign Log Panel - offset for banners */}
      <div className="pt-20">
        <CampaignLogPanel
          campaignId={campaignId}
          characterId={characterId}
          onClose={() => {
            // In dev preview, just show alert instead of navigating away
            alert('Close clicked - in production this would close the panel');
          }}
        />
      </div>
    </div>
  );
};

export default DevCampaignLogPreview;
