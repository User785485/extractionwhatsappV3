"""
UnifiedExporter - Export simple et efficace
"""
import os
import csv
from core.data_manager import DataManager

class UnifiedExporter:
    def __init__(self, data_manager: DataManager, output_dir: str):
        self.data_manager = data_manager
        self.output_dir = output_dir
        
    def export_simple(self):
        """Export simple en CSV avec tous les contacts et contenus"""
        export_data = self.data_manager.get_export_data()
        
        if not export_data:
            print("[EXPORT] Aucune donnée à exporter")
            return
        
        # Fichier CSV
        csv_path = os.path.join(self.output_dir, 'whatsapp_export.csv')
        
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Contact', 'Contenu'])
            
            for contact, content in sorted(export_data.items()):
                writer.writerow([contact, content])
        
        print(f"[EXPORT] CSV créé: {csv_path} ({len(export_data)} contacts)")
        
        # Fichier TXT
        txt_path = os.path.join(self.output_dir, 'whatsapp_export.txt')
        
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("EXPORT WHATSAPP - TOUS LES CONTACTS\n")
            f.write("="*50 + "\n\n")
            
            for contact, content in sorted(export_data.items()):
                f.write(f"CONTACT: {contact}\n")
                f.write(f"{content}\n")
                f.write("-"*50 + "\n\n")
        
        print(f"[EXPORT] TXT créé: {txt_path}")
        
        # Stats
        contacts_with_content = sum(1 for c in export_data.values() if c != "[Aucun contenu]")
        print(f"[EXPORT] {contacts_with_content}/{len(export_data)} contacts ont du contenu")
