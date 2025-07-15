"""
Helpers - Fonctions utilitaires pour WhatsApp Extractor
"""
import os
import re
import hashlib
from datetime import datetime
from typing import Optional, Dict

def ensure_directory(path: str) -> bool:
    """Crée un répertoire s'il n'existe pas déjà"""
    if not os.path.exists(path):
        try:
            os.makedirs(path)
            return True
        except Exception as e:
            print(f"[ERREUR] Impossible de créer le répertoire {path}: {e}")
            return False
    return True

def sanitize_filename(filename: str) -> str:
    """Nettoie un nom de fichier pour qu'il soit valide"""
    # Remplacer les caractères non autorisés par _
    clean = re.sub(r'[\\/*?:"<>|]', '_', filename)
    # Limiter la longueur
    if len(clean) > 100:
        clean = clean[:97] + '...'
    return clean

def format_date(date_str: str) -> str:
    """Formatage de date cohérent"""
    # Accepte divers formats et les convertit en YYYY-MM-DD
    formats = [
        '%Y/%m/%d',
        '%d/%m/%Y',
        '%Y-%m-%d',
        '%d-%m-%Y',
        '%d.%m.%Y',
        '%Y.%m.%d'
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    return date_str  # Si aucun format ne correspond

def generate_checksum(file_path: str) -> Optional[str]:
    """Calcule le checksum MD5 d'un fichier"""
    if not os.path.exists(file_path):
        return None
    
    try:
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return None

def log_error(error_msg: str, log_file: str = None):
    """Enregistre une erreur dans la console et éventuellement dans un fichier"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    formatted_error = f"[{timestamp}] ERROR: {error_msg}"
    
    print(formatted_error)
    
    if log_file:
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(formatted_error + "\n")
        except Exception:
            pass  # Silencieux si le log échoue

def get_file_info(file_path: str) -> Dict:
    """Récupère des informations sur un fichier"""
    if not os.path.exists(file_path):
        return {
            'exists': False,
            'size': 0,
            'modified': None,
            'extension': None
        }
    
    try:
        stats = os.stat(file_path)
        _, ext = os.path.splitext(file_path)
        
        return {
            'exists': True,
            'size': stats.st_size,
            'modified': datetime.fromtimestamp(stats.st_mtime).isoformat(),
            'extension': ext.lstrip('.').lower() if ext else None
        }
    except Exception:
        return {
            'exists': False,
            'size': 0,
            'modified': None,
            'extension': None
        }
