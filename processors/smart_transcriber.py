"""
SmartTranscriber - Transcription intelligente avec gestion d'erreurs
"""
import os
import re
import time
import openai
from typing import Optional
from core.data_manager import DataManager

class SmartTranscriber:
    def __init__(self, data_manager: DataManager, api_key: str):
        self.data_manager = data_manager
        self.client = openai.OpenAI(api_key=api_key)
        self.max_retries = 3
        self.retry_delay = 5
        
    def transcribe_all_pending(self):
        """Transcrit tous les audios en attente"""
        pending = self.data_manager.get_all_pending_audios()
        
        if not pending:
            print("[TRANSCRIPTION] Aucun audio en attente")
            return
        
        print(f"[TRANSCRIPTION] {len(pending)} audios à transcrire...")
        
        success_count = 0
        error_count = 0
        
        for item in pending:
            contact = item['contact']
            audio = item['audio']
            
            # Vérifier que le fichier existe
            audio_path = audio.get('path')
            if not audio_path or not os.path.exists(audio_path):
                # Chercher dans les dossiers audio_mp3
                audio_path = self._find_audio_file(contact, audio)
            
            if not audio_path:
                self.data_manager.update_transcription(
                    contact, 
                    audio['id'], 
                    None, 
                    'error'
                )
                error_count += 1
                continue
            
            # Transcrire
            transcription = self._transcribe_with_retry(audio_path)
            
            if transcription:
                self.data_manager.update_transcription(
                    contact,
                    audio['id'],
                    transcription,
                    'success'
                )
                success_count += 1
                print(f"[OK] {contact}: {os.path.basename(audio_path)}")
            else:
                self.data_manager.update_transcription(
                    contact,
                    audio['id'],
                    None,
                    'error'
                )
                error_count += 1
                print(f"[ERREUR] {contact}: {os.path.basename(audio_path)}")
            
            # Pause pour éviter rate limit
            time.sleep(1)
        
        print(f"[TRANSCRIPTION] Terminée: {success_count} succès, {error_count} erreurs")
    
    def _transcribe_with_retry(self, audio_path: str) -> Optional[str]:
        """Transcrit avec retry intelligent"""
        for attempt in range(self.max_retries):
            try:
                with open(audio_path, 'rb') as audio_file:
                    response = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language="fr"
                    )
                
                if isinstance(response, str):
                    return response.strip()
                else:
                    return response.text.strip()
                    
            except Exception as e:
                error_msg = str(e)
                
                # Gestion intelligente des erreurs
                if "rate limit" in error_msg.lower():
                    wait_time = self.retry_delay * (attempt + 1)
                    print(f"[RATE LIMIT] Attente {wait_time}s...")
                    time.sleep(wait_time)
                elif "invalid" in error_msg.lower() or "api" in error_msg.lower():
                    print(f"[ERREUR API] {error_msg}")
                    return None
                else:
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                    else:
                        return None
        
        return None
    
    def _find_audio_file(self, contact: str, audio_info: dict) -> Optional[str]:
        """Cherche le fichier audio dans les dossiers"""
        # Logique pour retrouver les fichiers audio
        output_dir = self.data_manager.output_dir
        
        # Chercher dans audio_mp3
        audio_dir = os.path.join(output_dir, contact, 'audio_mp3')
        if os.path.exists(audio_dir):
            for file in os.listdir(audio_dir):
                if file.endswith('.mp3'):
                    # Matcher par date/heure ou autre critère
                    file_date = None
                    audio_date = audio_info.get('date')
                    
                    # Essayer d'extraire la date du nom de fichier
                    date_match = re.search(r'(\d{4}[-_]\d{2}[-_]\d{2})', file)
                    if date_match:
                        file_date = date_match.group(1)
                    
                    # Si on a une date dans l'audio_info et qu'elle correspond au fichier
                    if audio_date and file_date and audio_date in file_date:
                        return os.path.join(audio_dir, file)
            
            # Si pas de match par date, prendre le premier fichier
            if os.listdir(audio_dir):
                return os.path.join(audio_dir, os.listdir(audio_dir)[0])
        
        return None
