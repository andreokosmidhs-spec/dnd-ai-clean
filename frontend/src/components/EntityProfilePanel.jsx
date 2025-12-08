import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { Badge } from './ui/badge';
import { 
  X, 
  BookOpen, 
  MessageSquare, 
  Package, 
  Users,
  StickyNote,
  Plus,
  Edit2,
  Trash2,
  Save,
  XCircle,
  Loader2
} from 'lucide-react';
import apiClient from '../lib/apiClient';

/**
 * EntityProfilePanel - Right-side sliding panel showing player-known information
 * Features:
 * - Only displays information from KnowledgeFacts (never GM secrets)
 * - Full CRUD for player notes
 * - Persists in view while reading
 * - All entities use orange theme
 */
export const EntityProfilePanel = ({ 
  entity, // {type, id, name}
  campaignId,
  characterId,
  onClose 
}) => {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Note editing state
  const [editingNoteId, setEditingNoteId] = useState(null);
  const [editNoteText, setEditNoteText] = useState('');
  const [isAddingNote, setIsAddingNote] = useState(false);
  const [newNoteText, setNewNoteText] = useState('');
  const [noteLoading, setNoteLoading] = useState(false);
  
  useEffect(() => {
    if (entity) {
      loadProfile();
    }
  }, [entity?.id]);
  
  const loadProfile = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params = { campaign_id: campaignId };
      if (characterId) params.character_id = characterId;
      
      console.log('🔍 Loading entity profile:', entity.type, entity.id, 'campaign:', campaignId);
      
      // URL encode the entity ID to handle special characters like apostrophes
      const encodedEntityId = encodeURIComponent(entity.id);
      
      const response = await apiClient.get(
        `/api/knowledge/entity-profile/${entity.type}/${encodedEntityId}`,
        { params }
      );
      
      console.log('✅ Profile loaded:', response.data);
      setProfile(response.data);
    } catch (err) {
      console.error('❌ Failed to load entity profile:', err);
      if (err.response?.status === 404) {
        setError('No information known about this entity yet. Explore more to learn about it!');
      } else if (err.response?.status === 422) {
        setError('This entity exists but you haven\'t learned about it yet. Keep exploring!');
      } else {
        setError(`Failed to load entity profile: ${err.message}`);
      }
    } finally {
      setLoading(false);
    }
  };
  
  // Create new note
  const handleAddNote = async () => {
    if (!newNoteText.trim()) return;
    
    setNoteLoading(true);
    try {
      console.log('📝 Adding note for:', entity.type, entity.id);
      await apiClient.post('/api/knowledge/notes', {
        campaign_id: campaignId,
        character_id: characterId,
        entity_type: entity.type,
        entity_id: entity.id,
        note_text: newNoteText
      });
      
      console.log('✅ Note added successfully');
      setNewNoteText('');
      setIsAddingNote(false);
      await loadProfile(); // Refresh profile to show new note
    } catch (err) {
      console.error('❌ Failed to add note:', err);
      alert(`Failed to add note: ${err.response?.data?.error?.message || err.message}`);
    } finally {
      setNoteLoading(false);
    }
  };
  
  // Update existing note
  const handleUpdateNote = async (noteId) => {
    if (!editNoteText.trim()) return;
    
    setNoteLoading(true);
    try {
      await apiClient.put(`/api/knowledge/notes/${noteId}`, {
        note_text: editNoteText
      });
      
      setEditingNoteId(null);
      setEditNoteText('');
      await loadProfile();
    } catch (err) {
      console.error('Failed to update note:', err);
      alert('Failed to update note');
    } finally {
      setNoteLoading(false);
    }
  };
  
  // Delete note
  const handleDeleteNote = async (noteId) => {
    if (!confirm('Delete this note?')) return;
    
    setNoteLoading(true);
    try {
      await apiClient.delete(`/api/knowledge/notes/${noteId}`);
      await loadProfile();
    } catch (err) {
      console.error('Failed to delete note:', err);
      alert('Failed to delete note');
    } finally {
      setNoteLoading(false);
    }
  };
  
  const startEditNote = (note) => {
    setEditingNoteId(note.id);
    setEditNoteText(note.text);
  };
  
  const cancelEditNote = () => {
    setEditingNoteId(null);
    setEditNoteText('');
  };
  
  if (!entity) return null;
  
  return (
    <div className="fixed right-4 top-20 bottom-4 w-96 z-50 animate-in slide-in-from-right duration-300">
      <Card className="h-full bg-gray-900/95 border-orange-600/30 backdrop-blur-sm flex flex-col shadow-2xl shadow-orange-600/20">
        <CardHeader className="border-b border-orange-600/20 flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex-1 min-w-0">
              <CardTitle className="text-orange-400 text-lg truncate">{entity.name}</CardTitle>
              <div className="flex items-center gap-2 mt-1">
                <Badge variant="outline" className="text-xs border-orange-400/50 text-orange-300 capitalize">
                  {entity.type}
                </Badge>
                {profile && (
                  <span className="text-xs text-gray-400">
                    {profile.total_facts} {profile.total_facts === 1 ? 'fact' : 'facts'} known
                  </span>
                )}
              </div>
            </div>
            <Button
              onClick={onClose}
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0 text-orange-400 hover:text-orange-200 hover:bg-orange-600/20 flex-shrink-0"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        
        <CardContent className="flex-1 overflow-y-auto p-4">
          {loading ? (
            <div className="flex items-center justify-center h-full text-gray-400">
              <Loader2 className="h-6 w-6 animate-spin mr-2" />
              Loading...
            </div>
          ) : error ? (
            <div className="text-center text-gray-400 p-4">
              <p>{error}</p>
            </div>
          ) : (
            <Tabs defaultValue="overview" className="w-full">
              <TabsList className="grid w-full grid-cols-4 bg-gray-800/50">
                <TabsTrigger value="overview" className="text-xs">
                  <BookOpen className="h-3 w-3" />
                </TabsTrigger>
                <TabsTrigger value="interactions" className="text-xs">
                  <MessageSquare className="h-3 w-3" />
                </TabsTrigger>
                <TabsTrigger value="relations" className="text-xs">
                  <Users className="h-3 w-3" />
                </TabsTrigger>
                <TabsTrigger value="notes" className="text-xs">
                  <StickyNote className="h-3 w-3" />
                </TabsTrigger>
              </TabsList>
              
              {/* Overview Tab */}
              <TabsContent value="overview" className="mt-4 space-y-4">
                {profile.known_summary && (
                  <div>
                    <h4 className="text-sm font-semibold text-orange-400 mb-2">What You Know</h4>
                    <p className="text-sm text-gray-300 leading-relaxed">{profile.known_summary}</p>
                  </div>
                )}
                
                {profile.first_seen && (
                  <div className="text-xs text-gray-500">
                    First encountered: {new Date(profile.first_seen).toLocaleDateString()}
                  </div>
                )}
                
                {profile.known_purpose && (
                  <div>
                    <h4 className="text-sm font-semibold text-orange-400 mb-2">Purpose</h4>
                    <p className="text-sm text-gray-300">{profile.known_purpose}</p>
                  </div>
                )}
                
                {profile.appearance && (
                  <div>
                    <h4 className="text-sm font-semibold text-orange-400 mb-2">Appearance</h4>
                    <p className="text-sm text-gray-300">{profile.appearance}</p>
                  </div>
                )}
                
                {profile.known_threats.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-red-400 mb-2">Known Threats</h4>
                    <ul className="list-disc list-inside space-y-1">
                      {profile.known_threats.map((threat, idx) => (
                        <li key={idx} className="text-sm text-gray-300">{threat}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {profile.known_rumors.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-purple-400 mb-2">Rumors Heard</h4>
                    <ul className="list-disc list-inside space-y-1">
                      {profile.known_rumors.map((rumor, idx) => (
                        <li key={idx} className="text-sm text-gray-300">{rumor}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </TabsContent>
              
              {/* Interactions Tab */}
              <TabsContent value="interactions" className="mt-4 space-y-4">
                {profile.important_interactions.length > 0 ? (
                  <div>
                    <h4 className="text-sm font-semibold text-orange-400 mb-3">Important Interactions</h4>
                    <div className="space-y-3">
                      {profile.important_interactions.map((interaction, idx) => (
                        <div key={idx} className="p-3 bg-gray-800/50 rounded border-l-2 border-orange-400/50">
                          <p className="text-sm text-gray-300">{interaction}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-gray-500 text-center py-8">No recorded interactions yet</p>
                )}
                
                {profile.quest_items_given.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-orange-400 mb-2">Items Given/Found</h4>
                    <ul className="list-disc list-inside space-y-1">
                      {profile.quest_items_given.map((item, idx) => (
                        <li key={idx} className="text-sm text-gray-300">{item}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {profile.related_quests.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-orange-400 mb-2">Related Quests</h4>
                    <ul className="list-disc list-inside space-y-1">
                      {profile.related_quests.map((quest, idx) => (
                        <li key={idx} className="text-sm text-gray-300">{quest}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </TabsContent>
              
              {/* Relations Tab */}
              <TabsContent value="relations" className="mt-4 space-y-4">
                {profile.known_factions.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-orange-400 mb-2">Factions</h4>
                    <div className="space-y-2">
                      {profile.known_factions.map((faction, idx) => (
                        <div key={idx} className="flex items-center justify-between p-2 bg-gray-800/50 rounded">
                          <span className="text-sm text-gray-300">{faction.name}</span>
                          {faction.role && (
                            <Badge variant="outline" className="text-xs">{faction.role}</Badge>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {profile.known_members.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-orange-400 mb-2">Known Members</h4>
                    <div className="space-y-2">
                      {profile.known_members.map((member, idx) => (
                        <div key={idx} className="flex items-center justify-between p-2 bg-gray-800/50 rounded">
                          <span className="text-sm text-gray-300">{member.name}</span>
                          {member.role && (
                            <Badge variant="outline" className="text-xs">{member.role}</Badge>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {profile.notable_npcs.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-orange-400 mb-2">Notable Figures</h4>
                    <div className="space-y-2">
                      {profile.notable_npcs.map((npc, idx) => (
                        <div key={idx} className="p-2 bg-gray-800/50 rounded">
                          <span className="text-sm text-gray-300">{npc.name}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {profile.known_features.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-orange-400 mb-2">Known Features</h4>
                    <ul className="list-disc list-inside space-y-1">
                      {profile.known_features.map((feature, idx) => (
                        <li key={idx} className="text-sm text-gray-300">{feature}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {profile.relationship_status && (
                  <div>
                    <h4 className="text-sm font-semibold text-orange-400 mb-2">Relationship</h4>
                    <Badge 
                      variant="outline" 
                      className={
                        profile.relationship_status === 'ally' ? 'border-green-400 text-green-300' :
                        profile.relationship_status === 'hostile' ? 'border-red-400 text-red-300' :
                        'border-gray-400 text-gray-300'
                      }
                    >
                      {profile.relationship_status}
                    </Badge>
                  </div>
                )}
                
                {profile.known_factions.length === 0 && 
                 profile.known_members.length === 0 && 
                 profile.notable_npcs.length === 0 && 
                 profile.known_features.length === 0 && (
                  <p className="text-sm text-gray-500 text-center py-8">No known relationships yet</p>
                )}
              </TabsContent>
              
              {/* Notes Tab with CRUD */}
              <TabsContent value="notes" className="mt-4 space-y-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-sm font-semibold text-orange-400">Your Notes</h4>
                  {!isAddingNote && (
                    <Button
                      onClick={() => setIsAddingNote(true)}
                      size="sm"
                      className="h-7 text-xs bg-orange-600/20 text-orange-400 hover:bg-orange-600/30"
                    >
                      <Plus className="h-3 w-3 mr-1" />
                      Add Note
                    </Button>
                  )}
                </div>
                
                {/* Add Note Form */}
                {isAddingNote && (
                  <div className="p-3 bg-gray-800/50 rounded border border-orange-400/30 space-y-2">
                    <Textarea
                      value={newNoteText}
                      onChange={(e) => setNewNoteText(e.target.value)}
                      placeholder="Write your note..."
                      className="min-h-[80px] bg-gray-900/50 border-gray-700 text-sm"
                    />
                    <div className="flex gap-2">
                      <Button
                        onClick={handleAddNote}
                        size="sm"
                        disabled={noteLoading || !newNoteText.trim()}
                        className="text-xs bg-orange-600 hover:bg-orange-700"
                      >
                        {noteLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <Save className="h-3 w-3 mr-1" />}
                        Save
                      </Button>
                      <Button
                        onClick={() => {
                          setIsAddingNote(false);
                          setNewNoteText('');
                        }}
                        size="sm"
                        variant="ghost"
                        className="text-xs"
                      >
                        <XCircle className="h-3 w-3 mr-1" />
                        Cancel
                      </Button>
                    </div>
                  </div>
                )}
                
                {/* Notes List */}
                {profile.player_notes.length > 0 ? (
                  <div className="space-y-3">
                    {profile.player_notes.map((note) => (
                      <div key={note.id} className="p-3 bg-gray-800/50 rounded border border-gray-700">
                        {editingNoteId === note.id ? (
                          <div className="space-y-2">
                            <Textarea
                              value={editNoteText}
                              onChange={(e) => setEditNoteText(e.target.value)}
                              className="min-h-[80px] bg-gray-900/50 border-gray-700 text-sm"
                            />
                            <div className="flex gap-2">
                              <Button
                                onClick={() => handleUpdateNote(note.id)}
                                size="sm"
                                disabled={noteLoading}
                                className="text-xs bg-orange-600 hover:bg-orange-700"
                              >
                                {noteLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <Save className="h-3 w-3 mr-1" />}
                                Save
                              </Button>
                              <Button
                                onClick={cancelEditNote}
                                size="sm"
                                variant="ghost"
                                className="text-xs"
                              >
                                Cancel
                              </Button>
                            </div>
                          </div>
                        ) : (
                          <>
                            <p className="text-sm text-gray-300 mb-2">{note.text}</p>
                            <div className="flex items-center justify-between">
                              <span className="text-xs text-gray-500">
                                {new Date(note.updated_at || note.created_at).toLocaleDateString()}
                              </span>
                              <div className="flex gap-1">
                                <Button
                                  onClick={() => startEditNote(note)}
                                  size="sm"
                                  variant="ghost"
                                  className="h-6 w-6 p-0 text-gray-400 hover:text-orange-400"
                                >
                                  <Edit2 className="h-3 w-3" />
                                </Button>
                                <Button
                                  onClick={() => handleDeleteNote(note.id)}
                                  size="sm"
                                  variant="ghost"
                                  className="h-6 w-6 p-0 text-gray-400 hover:text-red-400"
                                >
                                  <Trash2 className="h-3 w-3" />
                                </Button>
                              </div>
                            </div>
                          </>
                        )}
                      </div>
                    ))}
                  </div>
                ) : !isAddingNote && (
                  <p className="text-sm text-gray-500 text-center py-8">No notes yet. Click Add Note to start.</p>
                )}
              </TabsContent>
            </Tabs>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default EntityProfilePanel;
