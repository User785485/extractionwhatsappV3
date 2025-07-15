"""
DataManager - Source unique de vérité pour toutes les données
"""
import os
import json
import hashlib
from typing import Dict, List, Optional, Set
from datetime import datetime

class DataManager:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.data_file = os.path.join(output_dir, 'whatsapp_data.json')
        self.data = self._load_or_create()
        
    def _load_or_create(self) -> Dict:
        """Charge ou crée la structure de données unifiée"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'version': '3.0',
            'created': datetime.now().isoformat(),
            'contacts': {},  # Structure principale par contact
            'stats': {
                'total_messages': 0,
                'total_audios': 0,
                'total_transcribed': 0,
                'last_update': None
            }
        }
    
    def save(self):
        """Sauvegarde atomique"""
        temp_file = self.data_file + '.tmp'
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        os.replace(temp_file, self.data_file)
    
    def add_contact(self, contact_name: str) -> Dict:
        """Ajoute ou récupère un contact"""
        # Normaliser le nom (garder jusqu'à 200 caractères)
        clean_name = self._normalize_name(contact_name)
        
        if clean_name not in self.data['contacts']:
            self.data['contacts'][clean_name] = {
                'original_name': contact_name,
                'messages': [],
                'audios': [],
                'stats': {
                    'text_count': 0,
                    'audio_count': 0,
                    'transcribed_count': 0
                }
            }
        
        return self.data['contacts'][clean_name]
    
    def add_message(self, contact: str, message: Dict):
        """Ajoute un message texte"""
        contact_data = self.add_contact(contact)
        
        # Créer un ID unique pour le message
        msg_id = hashlib.md5(
            f"{contact}{message.get('date', '')}{message.get('time', '')}{message.get('content', '')}".encode()
        ).hexdigest()[:16]
        
        # Éviter les doublons
        existing_ids = {m['id'] for m in contact_data['messages'] if 'id' in m}
        if msg_id not in existing_ids:
            message['id'] = msg_id
            contact_data['messages'].append(message)
            contact_data['stats']['text_count'] += 1
            self.data['stats']['total_messages'] += 1
    
    def add_audio(self, contact: str, audio_info: Dict) -> str:
        """Ajoute un fichier audio et retourne son ID"""
        contact_data = self.add_contact(contact)
        
        # Créer un ID unique pour l'audio
        audio_id = hashlib.md5(
            f"{contact}{audio_info.get('path', '')}{audio_info.get('date', '')}".encode()
        ).hexdigest()
        
        # Vérifier si déjà existe
        existing_ids = {a['id'] for a in contact_data['audios'] if 'id' in a}
        if audio_id not in existing_ids:
            audio_info['id'] = audio_id
            audio_info['transcription'] = None  # Placeholder
            audio_info['transcription_status'] = 'pending'
            contact_data['audios'].append(audio_info)
            contact_data['stats']['audio_count'] += 1
            self.data['stats']['total_audios'] += 1
        
        return audio_id
    
    def update_transcription(self, contact: str, audio_id: str, transcription: str, status: str = 'success'):
        """Met à jour la transcription d'un audio"""
        contact_data = self.data['contacts'].get(self._normalize_name(contact))
        if not contact_data:
            return False
        
        for audio in contact_data['audios']:
            if audio.get('id') == audio_id:
                audio['transcription'] = transcription
                audio['transcription_status'] = status
                audio['transcribed_at'] = datetime.now().isoformat()
                
                if status == 'success' and transcription:
                    contact_data['stats']['transcribed_count'] += 1
                    self.data['stats']['total_transcribed'] += 1
                
                self.save()
                return True
        
        return False
    
    def get_all_pending_audios(self) -> List[Dict]:
        """Récupère tous les audios non transcrits"""
        pending = []
        
        for contact_name, contact_data in self.data['contacts'].items():
            for audio in contact_data['audios']:
                if audio.get('transcription_status') == 'pending':
                    pending.append({
                        'contact': contact_name,
                        'audio': audio
                    })
        
        return pending
    
    def get_export_data(self) -> Dict[str, str]:
        """Prépare les données pour l'export"""
        export = {}
        
        for contact_name, contact_data in self.data['contacts'].items():
            contents = []
            
            # Messages texte
            for msg in sorted(contact_data['messages'], key=lambda x: (x.get('date', ''), x.get('time', ''))):
                if msg.get('direction') in ['received', 'sent']:  # Inclure les deux
                    contents.append(msg.get('content', ''))
            
            # Transcriptions audio
            for audio in sorted(contact_data['audios'], key=lambda x: (x.get('date', ''), x.get('time', ''))):
                if audio.get('transcription'):
                    contents.append(f"[AUDIO] {audio['transcription']}")
                elif audio.get('transcription_status') == 'error':
                    contents.append(f"[AUDIO] [Erreur: {audio.get('error_message', 'Transcription échouée')}]")
                else:
                    contents.append("[AUDIO] [Non transcrit]")
            
            # Joindre tout le contenu
            export[contact_data.get('original_name', contact_name)] = " | ".join(contents) if contents else "[Aucun contenu]"
        
        return export
    
    def _normalize_name(self, name: str) -> str:
        """Normalise un nom de contact"""
        import re
        # Garder lettres, chiffres, espaces, +, -, _
        clean = re.sub(r'[^a-zA-Z0-9\s+\-_@.]', '', name)
        clean = re.sub(r'\s+', ' ', clean).strip()
        
        # Limiter la longueur
        if len(clean) > 200:
            clean = clean[:200]
        
        # Si vide, générer un nom
        if not clean:
            clean = f"Contact_{hashlib.md5(name.encode()).hexdigest()[:8]}"
        
        return clean
