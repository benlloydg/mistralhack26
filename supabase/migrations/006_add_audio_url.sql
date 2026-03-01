-- Add audio_url column to dispatches for TTS-generated audio playback
ALTER TABLE dispatches ADD COLUMN IF NOT EXISTS audio_url TEXT;
