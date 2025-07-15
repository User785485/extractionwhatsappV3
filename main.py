#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WhatsApp Extractor V3 - Version refaite proprement
"""

import os
import sys
import argparse
import configparser
from datetime import datetime

# Imports
from core.data_manager import DataManager
from extractors.unified_extractor import UnifiedExtractor
from processors.smart_transcriber import SmartTranscriber
from exporters.unified_exporter import UnifiedExporter

def load_config():
    """Charge la configuration"""
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    return {
        'html_dir': config.get('Paths', 'html_dir', fallback=''),
        'media_dir': config.get('Paths', 'media_dir', fallback=''),
        'output_dir': config.get('Paths', 'output_dir', fallback='output'),
        'api_key': config.get('API', 'openai_key', fallback='')
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--extract-only', action='store_true', help='Extraction seulement')
    parser.add_argument('--transcribe-only', action='store_true', help='Transcription seulement')
    parser.add_argument('--export-only', action='store_true', help='Export seulement')
    parser.add_argument('--full', action='store_true', help='Processus complet')
    
    args = parser.parse_args()
    
    # Charger config
    config = load_config()
    output_dir = config['output_dir']
    
    # Créer output dir
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialiser le gestionnaire de données
    data_manager = DataManager(output_dir)
    
    print("="*60)
    print("WHATSAPP EXTRACTOR V3")
    print("="*60)
    
    # Processus
    if args.full or args.extract_only or (not any(vars(args).values())):
        # Extraction
        print("\n[1/3] EXTRACTION")
        extractor = UnifiedExtractor(data_manager, config)
        extractor.extract_all()
    
    if args.full or args.transcribe_only:
        # Transcription
        print("\n[2/3] TRANSCRIPTION")
        if config['api_key'] and config['api_key'] != 'sk-xxxxxxxxxxxxxxxxxxxxx':
            transcriber = SmartTranscriber(data_manager, config['api_key'])
            transcriber.transcribe_all_pending()
        else:
            print("[ATTENTION] Clé API OpenAI manquante - Transcription ignorée")
    
    if args.full or args.export_only or (not any(vars(args).values())):
        # Export
        print("\n[3/3] EXPORT")
        exporter = UnifiedExporter(data_manager, output_dir)
        exporter.export_simple()
    
    print("\n" + "="*60)
    print("TERMINÉ!")
    print("="*60)

if __name__ == "__main__":
    main()
