"""
UnifiedExtractor - Extraction unifiée depuis toutes les sources
"""
import os
import json
import re
from bs4 import BeautifulSoup
from typing import Dict, List
from core.data_manager import DataManager

class UnifiedExtractor:
    def __init__(self, data_manager: DataManager, config: dict):
        self.data_manager = data_manager
        self.config = config
        
    def extract_all(self):
        """Extrait depuis toutes les sources disponibles"""
        print("[EXTRACTION] Début de l'extraction unifiée...")
        
        # 1. HTML WhatsApp
        html_dir = self.config.get('html_dir')
        if html_dir and os.path.exists(html_dir):
            self._extract_from_html(html_dir)
        
        # 2. Dossiers de contacts existants
        output_dir = self.config.get('output_dir')
        if output_dir and os.path.exists(output_dir):
            self._extract_from_folders(output_dir)
        
        # Sauvegarder
        self.data_manager.save()
        
        # Stats
        total_contacts = len(self.data_manager.data['contacts'])
        total_messages = self.data_manager.data['stats']['total_messages']
        total_audios = self.data_manager.data['stats']['total_audios']
        
        print(f"[EXTRACTION] Terminée: {total_contacts} contacts, {total_messages} messages, {total_audios} audios")
    
    def _extract_from_html(self, html_dir: str):
        """Extrait depuis les fichiers HTML"""
        html_files = [f for f in os.listdir(html_dir) if f.endswith('.html')]
        
        for html_file in html_files:
            try:
                with open(os.path.join(html_dir, html_file), 'r', encoding='utf-8') as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                
                # Extraire le nom du contact
                contact_name = self._extract_contact_name(soup)
                
                # Extraire les messages
                self._extract_messages(soup, contact_name)
                
            except Exception as e:
                print(f"[ERREUR] HTML {html_file}: {e}")
    
    def _extract_from_folders(self, output_dir: str):
        """Extrait depuis les dossiers existants (conversation.json, etc.)"""
        for folder in os.listdir(output_dir):
            folder_path = os.path.join(output_dir, folder)
            
            if not os.path.isdir(folder_path) or folder.startswith('.'):
                continue
            
            # Chercher conversation.json
            conv_file = os.path.join(folder_path, 'conversation.json')
            if os.path.exists(conv_file):
                try:
                    with open(conv_file, 'r', encoding='utf-8') as f:
                        messages = json.load(f)
                    
                    for msg in messages:
                        self.data_manager.add_message(folder, msg)
                        
                        # Si c'est un audio
                        if msg.get('type') == 'audio' and msg.get('media_path'):
                            audio_info = {
                                'path': msg['media_path'],
                                'date': msg.get('date'),
                                'time': msg.get('time'),
                                'direction': msg.get('direction')
                            }
                            self.data_manager.add_audio(folder, audio_info)
                            
                except Exception as e:
                    print(f"[ERREUR] conversation.json {folder}: {e}")
    
    def _extract_contact_name(self, soup) -> str:
        """Extrait le nom depuis le HTML"""
        # Logique d'extraction du nom
        h3 = soup.find('h3')
        if h3:
            return h3.text.strip()
        
        title = soup.find('title')
        if title:
            return title.text.replace("'s WhatsApp", "").strip()
        
        return "Contact_Inconnu"
    
    def _extract_messages(self, soup, contact_name: str):
        """Extrait tous les messages du HTML"""
        # Pattern pour les messages
        date_pattern = re.compile(r'(\d{4}/\d{2}/\d{2})\s+(\d{2}:\d{2})')
        
        # Parcourir les éléments
        messages = []
        for msg_div in soup.find_all('div', class_=['message', 'msg']):
            try:
                # Déterminer la direction (reçu ou envoyé)
                is_received = 'received' in msg_div.get('class', []) or 'from' in msg_div.get('class', [])
                is_sent = 'sent' in msg_div.get('class', []) or 'to' in msg_div.get('class', [])
                
                direction = 'received' if is_received else 'sent' if is_sent else 'unknown'
                
                # Trouver la date/heure
                date_div = msg_div.find('div', class_=['date', 'time'])
                date_str = ""
                time_str = ""
                
                if date_div and date_div.text:
                    date_match = date_pattern.search(date_div.text)
                    if date_match:
                        date_str = date_match.group(1)
                        time_str = date_match.group(2)
                
                # Trouver le contenu
                content_div = msg_div.find('div', class_=['text', 'content'])
                content = content_div.text.strip() if content_div else ""
                
                # Vérifier si c'est un audio
                is_audio = msg_div.find('audio') is not None or 'audio' in msg_div.get('class', [])
                
                if is_audio:
                    # Extraire le chemin audio s'il existe
                    audio_elem = msg_div.find('audio')
                    audio_path = ""
                    if audio_elem and audio_elem.get('src'):
                        audio_path = audio_elem['src']
                    
                    # Ajouter l'audio
                    audio_info = {
                        'path': audio_path,
                        'date': date_str,
                        'time': time_str,
                        'direction': direction
                    }
                    self.data_manager.add_audio(contact_name, audio_info)
                else:
                    # Ajouter le message texte
                    message = {
                        'date': date_str,
                        'time': time_str,
                        'content': content,
                        'direction': direction,
                        'type': 'text'
                    }
                    self.data_manager.add_message(contact_name, message)
                    
            except Exception as e:
                print(f"[ERREUR] Extraction message: {e}")
