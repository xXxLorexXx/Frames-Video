import os
import cv2
import queue
import threading
import multiprocessing
import time
import json
import logging
import csv
import webbrowser
from pathlib import Path
from PIL import Image, ImageTk
from tkinter import filedialog, messagebox, ttk, Toplevel, Scale, Text, END
import tkinter as tk

# Intenta importar tkinterdnd2 para Drag & Drop
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DRAG_AND_DROP_AVAILABLE = True
except ImportError:
    DRAG_AND_DROP_AVAILABLE = False
    print("[INFO] tkinterdnd2 no instalado. Drag & Drop deshabilitado.")

# ### Sistema de Localización
translations = {
    'en': {
        'created_by': 'Created by Lore',
        'donate': 'Donate',
        'select_files': 'Select Files',
        'select_folder': 'Select Folder',
        'clear_list': 'Clear List',
        'settings': 'Settings',
        'output_folder': 'Output Folder',
        'select_output_folder': 'Select Output Folder',
        'start_extraction': 'Start Extraction',
        'stop': 'Stop',
        'pause': 'Pause',
        'resume': 'Resume',
        'dynamic_preview': 'Dynamic Preview (1st)',
        'progress': 'Progress: {processed} / {total}',
        'finished': 'Finished',
        'frames_extracted_success': 'Frames have been extracted successfully.',
        'language': 'Language',
        'instructions_title': 'Instructions',
        'instructions_text': (
            "Welcome to Frames by Lore.\n\n"
            "Main options:\n"
            "- Frame limit\n"
            "- Output dimensions and Maintain aspect\n"
            "- Max file size (KB)\n"
            "- Frame step\n"
            "- Output format and JPG Quality\n"
            "- Filename pattern (use {basename} and {frame_num})\n"
            "- Use Multiprocessing (experimental)\n\n"
            "To configure advanced settings, manually edit the configuration file or adjust the code.\n"
            "\nEnjoy the app!"
        ),
        'frame_limit': 'Frame Limit:',
        'no_limit': 'No Limit',
        'with_limit': 'With Limit',
        'width': 'Width:',
        'height': 'Height:',
        'maintain_aspect': 'Maintain Aspect',
        'max_file_size': 'Max File Size (KB):',
        'frame_step': 'Frame Step:',
        'output_format': 'Output Format:',
        'jpeg_quality': 'JPEG Quality:',
        'filename_pattern': 'Filename Pattern:',
        'use_multiprocessing': 'Use Multiprocessing (experimental)',
        'save': 'Save',
        'cancel': 'Cancel',
        'view_instructions': 'View Instructions',
        'error': 'Error',
        'warning': 'Warning',
        'info': 'Information',
        'confirm': 'Confirm',
        'yes': 'Yes',
        'no': 'No',
        'processing': 'Processing...',
        'stopped': 'Processing stopped by user.',
        'completed': 'Processing completed.',
        'no_videos': 'No videos selected.',
        'invalid_limit': 'You must specify the frame limit.',
        'invalid_dimensions': 'Output dimensions are required and must be > 0.',
        'invalid_max_size': 'Max file size (KB) is required and must be > 0.',
        'invalid_frame_step': 'Frame step is required and must be >= 1.',
        'invalid_jpeg_quality': 'JPEG quality is required and must be between 1 and 100.',
        'invalid_pattern': 'Pattern must contain {basename} and {frame_num}.',
        'output_folder_not_selected': 'You must select an output folder.',
        'select_output_folder_prompt': 'You have not selected an output folder. Do you want to select one now?',
        'video_files_only': 'Only video files are allowed.',
        'no_videos_in_folder': 'No videos found in the selected folder.',
        'preview_error': 'Could not open the video for preview.',
        'video_corrupted': 'Video has no frames or is corrupted.',
        'stats_saved': 'Statistics saved to {csv_file}.',
        'processing_video': 'Processing {video} | {frames} frames.',
        'completed_video': 'Completed {video}: {frames} frames extracted.',
        'error_processing': 'Error processing {video}: {error}',
        'total_files': 'Total: {count} file(s)',
        'drag_drop_disabled': 'Drag & Drop disabled. Install tkinterdnd2 for full functionality.',
        'donate_dialog_title': 'Donate',
        'paypal': 'Paypal',
        'copy': 'Copy',
        'open_paypal': 'Open Paypal',
        'theme': 'Theme',
        'light': 'Light',
        'dark': 'Dark',
    },
    'es': {
        'created_by': 'Creado por Lore',
        'donate': 'Donar',
        'select_files': 'Seleccionar Archivos',
        'select_folder': 'Seleccionar Carpeta',
        'clear_list': 'Limpiar Lista',
        'settings': 'Configuración',
        'output_folder': 'Carpeta de Salida',
        'select_output_folder': 'Seleccionar Carpeta de Salida',
        'start_extraction': 'Iniciar Extracción',
        'stop': 'Detener',
        'pause': 'Pausar',
        'resume': 'Reanudar',
        'dynamic_preview': 'Vista Previa Dinámica (1º)',
        'progress': 'Progreso: {processed} / {total}',
        'finished': 'Finalizado',
        'frames_extracted_success': 'Se han extraído los fotogramas correctamente.',
        'language': 'Idioma',
        'instructions_title': 'Instrucciones',
        'instructions_text': (
            "Bienvenido/a a Frames by Lore.\n\n"
            "Opciones principales:\n"
            "- Límite de fotogramas\n"
            "- Dimensiones de salida y Mantener aspecto\n"
            "- Tamaño máx. de archivo (KB)\n"
            "- Salto de fotogramas\n"
            "- Formato de salida y Calidad JPG\n"
            "- Patrón de nombre (usa {basename} y {frame_num})\n"
            "- Usar Multiproceso (experimental)\n\n"
            "Para configurar opciones avanzadas, edita manualmente el archivo de configuración o ajusta el código.\n"
            "\n¡Disfruta de la aplicación!"
        ),
        'frame_limit': 'Límite de fotogramas:',
        'no_limit': 'Sin límite',
        'with_limit': 'Con límite',
        'width': 'Ancho:',
        'height': 'Alto:',
        'maintain_aspect': 'Mantener aspecto',
        'max_file_size': 'Tamaño máx. de archivo (KB):',
        'frame_step': 'Salto de fotogramas:',
        'output_format': 'Formato de salida:',
        'jpeg_quality': 'Calidad JPG:',
        'filename_pattern': 'Patrón de nombre:',
        'use_multiprocessing': 'Usar Multiproceso (experimental)',
        'save': 'Guardar',
        'cancel': 'Cancelar',
        'view_instructions': 'Ver Instrucciones',
        'error': 'Error',
        'warning': 'Advertencia',
        'info': 'Información',
        'confirm': 'Confirmar',
        'yes': 'Sí',
        'no': 'No',
        'processing': 'Procesando...',
        'stopped': 'Procesamiento detenido por el usuario.',
        'completed': 'Procesamiento completado.',
        'no_videos': 'No hay videos seleccionados.',
        'invalid_limit': 'Debes especificar el límite de fotogramas.',
        'invalid_dimensions': 'Las dimensiones de salida son obligatorias y deben ser > 0.',
        'invalid_max_size': 'El tamaño máximo (KB) es obligatorio y debe ser > 0.',
        'invalid_frame_step': 'El salto de fotogramas es obligatorio y debe ser >= 1.',
        'invalid_jpeg_quality': 'La calidad JPG es obligatoria y debe estar entre 1 y 100.',
        'invalid_pattern': 'El patrón debe contener {basename} y {frame_num}.',
        'output_folder_not_selected': 'Debes seleccionar una carpeta de salida.',
        'select_output_folder_prompt': 'No has seleccionado una carpeta de salida. ¿Deseas seleccionar una ahora?',
        'video_files_only': 'Solo se permiten archivos de video.',
        'no_videos_in_folder': 'No se encontraron videos en la carpeta seleccionada.',
        'preview_error': 'No se pudo abrir el video para la vista previa.',
        'video_corrupted': 'El video no tiene frames o está corrupto.',
        'stats_saved': 'Estadísticas guardadas en {csv_file}.',
        'processing_video': 'Procesando {video} | {frames} frames.',
        'completed_video': 'Completado {video}: {frames} frames extraídos.',
        'error_processing': 'Error procesando {video}: {error}',
        'total_files': 'Total: {count} archivo(s)',
        'drag_drop_disabled': 'Drag & Drop deshabilitado. Instala tkinterdnd2 para funcionalidad completa.',
        'donate_dialog_title': 'Donar',
        'paypal': 'Paypal',
        'copy': 'Copiar',
        'open_paypal': 'Abrir Paypal',
        'theme': 'Tema',
        'light': 'Claro',
        'dark': 'Oscuro',
    },
    'fr': {
        'created_by': 'Créé par Lore',
        'donate': 'Faire un don',
        'select_files': 'Sélectionner des fichiers',
        'select_folder': 'Sélectionner un dossier',
        'clear_list': 'Effacer la liste',
        'settings': 'Paramètres',
        'output_folder': 'Dossier de sortie',
        'select_output_folder': 'Sélectionner le dossier de sortie',
        'start_extraction': 'Démarrer l’extraction',
        'stop': 'Arrêter',
        'pause': 'Pause',
        'resume': 'Reprendre',
        'dynamic_preview': 'Aperçu dynamique (1er)',
        'progress': 'Progrès : {processed} / {total}',
        'finished': 'Terminé',
        'frames_extracted_success': 'Les images ont été extraites avec succès.',
        'language': 'Langue',
        'instructions_title': 'Instructions',
        'instructions_text': (
            "Bienvenue sur Frames by Lore.\n\n"
            "Options principales :\n"
            "- Limite de trames\n"
            "- Dimensions de sortie et Maintenir les proportions\n"
            "- Taille max. du fichier (Ko)\n"
            "- Pas des trames\n"
            "- Format de sortie et Qualité JPG\n"
            "- Modèle de nom (utilisez {basename} et {frame_num})\n"
            "- Utiliser le multiprocessing (expérimental)\n\n"
            "Pour configurer des options avancées, modifiez manuellement le fichier de configuration ou ajustez le code.\n"
            "\nProfitez de l’application !"
        ),
        'frame_limit': 'Limite de trames :',
        'no_limit': 'Sans limite',
        'with_limit': 'Avec limite',
        'width': 'Largeur :',
        'height': 'Hauteur :',
        'maintain_aspect': 'Maintenir les proportions',
        'max_file_size': 'Taille max. du fichier (Ko) :',
        'frame_step': 'Pas des trames :',
        'output_format': 'Format de sortie :',
        'jpeg_quality': 'Qualité JPG :',
        'filename_pattern': 'Modèle de nom :',
        'use_multiprocessing': 'Utiliser le multiprocessing (expérimental)',
        'save': 'Sauvegarder',
        'cancel': 'Annuler',
        'view_instructions': 'Voir les instructions',
        'error': 'Erreur',
        'warning': 'Avertissement',
        'info': 'Information',
        'confirm': 'Confirmer',
        'yes': 'Oui',
        'no': 'Non',
        'processing': 'Traitement...',
        'stopped': 'Traitement arrêté par l’utilisateur.',
        'completed': 'Traitement terminé.',
        'no_videos': 'Aucune vidéo sélectionnée.',
        'invalid_limit': 'Vous devez spécifier la limite de trames.',
        'invalid_dimensions': 'Les dimensions de sortie sont obligatoires et doivent être > 0.',
        'invalid_max_size': 'La taille max. du fichier (Ko) est obligatoire et doit être > 0.',
        'invalid_frame_step': 'Le pas des trames est obligatoire et doit être >= 1.',
        'invalid_jpeg_quality': 'La qualité JPG est obligatoire et doit être entre 1 et 100.',
        'invalid_pattern': 'Le modèle doit contenir {basename} et {frame_num}.',
        "output_folder_not_selected": "Vous devez sélectionner un dossier de sortie.",
        "select_output_folder_prompt": "Vous n’avez pas sélectionné de dossier de sortie. Voulez-vous en sélectionner un maintenant ?",
        "video_files_only": "Seuls les fichiers vidéo sont autorisés.",
        "no_videos_in_folder": "Aucune vidéo trouvée dans le dossier sélectionné.",
        "preview_error": "Impossible d’ouvrir la vidéo pour l’aperçu.",
        "video_corrupted": "La vidéo n’a pas de trames ou est corrompue.",
        "stats_saved": "Statistiques sauvegardées dans {csv_file}.",
        "processing_video": "Traitement de {video} | {frames} trames.",
        "completed_video": "Terminé {video} : {frames} trames extraites.",
        "error_processing": "Erreur lors du traitement de {video} : {error}",
        "total_files": "Total : {count} fichier(s)",
        "drag_drop_disabled": "Drag & Drop désactivé. Installez tkinterdnd2 pour une fonctionnalité complète.",
        "donate_dialog_title": "Faire un don",
        "paypal": "Paypal",
        "copy": "Copier",
        "open_paypal": "Ouvrir Paypal",
        "theme": "Thème",
        "light": "Clair",
        "dark": "Sombre",
    },
    "it": {
        "created_by": "Creato da Lore",
        "donate": "Dona",
        "select_files": "Seleziona File",
        "select_folder": "Seleziona Cartella",
        "clear_list": "Cancella Lista",
        "settings": "Impostazioni",
        "output_folder": "Cartella di Output",
        "select_output_folder": "Seleziona Cartella di Output",
        "start_extraction": "Avvia Estrazione",
        "stop": "Ferma",
        "pause": "Pausa",
        "resume": "Riprendi",
        "dynamic_preview": "Anteprima Dinamica (1°)",
        "progress": "Progresso: {processed} / {total}",
        "finished": "Completato",
        "frames_extracted_success": "I fotogrammi sono stati estratti con successo.",
        "language": "Lingua",
        "instructions_title": "Istruzioni",
        "instructions_text": (
            "Benvenuto/a su Frames by Lore.\n\n"
            "Opzioni principali:\n"
            "- Limite di fotogrammi\n"
            "- Dimensioni di output e Mantieni proporzioni\n"
            "- Dimensione max del file (KB)\n"
            "- Passo dei fotogrammi\n"
            "- Formato di output e Qualità JPG\n"
            "- Modello del nome (usa {basename} e {frame_num})\n"
            "- Usa Multiprocessing (sperimentale)\n\n"
            "Per configurare opzioni avanzate, modifica manualmente il file di configurazione o regola il codice.\n"
            "\nGoditi l’app!"
        ),
        "frame_limit": "Limite di fotogrammi:",
        "no_limit": "Senza limite",
        "with_limit": "Con limite",
        "width": "Larghezza:",
        "height": "Altezza:",
        "maintain_aspect": "Mantieni proporzioni",
        "max_file_size": "Dimensione max del file (KB):",
        "frame_step": "Passo dei fotogrammi:",
        "output_format": "Formato di output:",
        "jpeg_quality": "Qualità JPG:",
        "filename_pattern": "Modello del nome:",
        "use_multiprocessing": "Usa Multiprocessing (sperimentale)",
        "save": "Salva",
        "cancel": "Annulla",
        "view_instructions": "Visualizza Istruzioni",
        "error": "Errore",
        "warning": "Avvertimento",
        "info": "Informazione",
        "confirm": "Conferma",
        "yes": "Sì",
        "no": "No",
        "processing": "Elaborazione...",
        "stopped": "Elaborazione interrotta dall’utente.",
        "completed": "Elaborazione completata.",
        "no_videos": "Nessun video selezionato.",
        "invalid_limit": "Devi specificare il limite di fotogrammi.",
        "invalid_dimensions": "Le dimensioni di output sono obbligatorie e devono essere > 0.",
        "invalid_max_size": "La dimensione max (KB) è obbligatoria e deve essere > 0.",
        "invalid_frame_step": "Il passo dei fotogrammi è obbligatorio e deve essere >= 1.",
        "invalid_jpeg_quality": "La qualità JPG è obbligatoria e deve essere tra 1 e 100.",
        "invalid_pattern": "Il modello deve contenere {basename} e {frame_num}.",
        "output_folder_not_selected": "Devi selezionare una cartella di output.",
        "select_output_folder_prompt": "Non hai selezionato una cartella di output. Vuoi selezionarne una ora?",
        "video_files_only": "Sono ammessi solo file video.",
        "no_videos_in_folder": "Nessun video trovato nella cartella selezionata.",
        "preview_error": "Impossibile aprire il video per l’anteprima.",
        "video_corrupted": "Il video non ha fotogrammi o è corrotto.",
        "stats_saved": "Statistiche salvate in {csv_file}.",
        "processing_video": "Elaborazione di {video} | {frames} fotogrammi.",
        "completed_video": "Completato {video}: {frames} fotogrammi estratti.",
        "error_processing": "Errore durante l’elaborazione di {video}: {error}",
        "total_files": "Totale: {count} file",
        "drag_drop_disabled": "Drag & Drop disabilitato. Instala tkinterdnd2 per funzionalità completa.",
        "donate_dialog_title": "Dona",
        "paypal": "Paypal",
        "copy": "Copia",
        "open_paypal": "Apri Paypal",
        "theme": "Tema",
        "light": "Chiaro",
        "dark": "Scuro",
    },
    "de": {
        "created_by": "Erstellt von Lore",
        "donate": "Spenden",
        "select_files": "Dateien auswählen",
        "select_folder": "Ordner auswählen",
        "clear_list": "Liste löschen",
        "settings": "Einstellungen",
        "output_folder": "Ausgabeordner",
        "select_output_folder": "Ausgabeordner auswählen",
        "start_extraction": "Extraktion starten",
        "stop": "Stoppen",
        "pause": "Pause",
        "resume": "Fortsetzen",
        "dynamic_preview": "Dynamische Vorschau (1.)",
        "progress": "Fortschritt: {processed} / {total}",
        "finished": "Abgeschlossen",
        "frames_extracted_success": "Die Frames wurden erfolgreich extrahiert.",
        "language": "Sprache",
        "instructions_title": "Anleitungen",
        "instructions_text": (
            "Willkommen bei Frames by Lore.\n\n"
            "Hauptoptionen:\n"
            "- Bildratenbegrenzung\n"
            "- Ausgabegröße und Seitenverhältnis beibehalten\n"
            "- Max. Dateigröße (KB)\n"
            "- Bildschritt\n"
            "- Ausgabeformat und JPG-Qualität\n"
            "- Dateinamenmuster (verwende {basename} und {frame_num})\n"
            "- Multiprocessing verwenden (experimentell)\n\n"
            "Um erweiterte Einstellungen zu konfigurieren, bearbeiten Sie die Konfigurationsdatei manuell oder passen Sie den Code an.\n"
            "\nViel Spaß mit der App!"
        ),
        "frame_limit": "Bildratenbegrenzung:",
        "no_limit": "Kein Limit",
        "with_limit": "Mit Limit",
        "width": "Breite:",
        "height": "Höhe:",
        "maintain_aspect": "Seitenverhältnis beibehalten",
        "max_file_size": "Max. Dateigröße (KB):",
        "frame_step": "Bildschritt:",
        "output_format": "Ausgabeformat:",
        "jpeg_quality": "JPG-Qualität:",
        "filename_pattern": "Dateinamenmuster:",
        "use_multiprocessing": "Multiprocessing verwenden (experimentell)",
        "save": "Speichern",
        "cancel": "Abbrechen",
        "view_instructions": "Anleitungen anzeigen",
        "error": "Fehler",
        "warning": "Warnung",
        "info": "Information",
        "confirm": "Bestätigen",
        "yes": "Ja",
        "no": "Nein",
        "processing": "Verarbeitung...",
        "stopped": "Verarbeitung vom Benutzer gestoppt.",
        "completed": "Verarbeitung abgeschlossen.",
        "no_videos": "Keine Videos ausgewählt.",
        "invalid_limit": "Sie müssen das Bildratenlimit angeben.",
        "invalid_dimensions": "Ausgabegrößen sind erforderlich und müssen > 0 sein.",
        "invalid_max_size": "Max. Dateigröße (KB) ist erforderlich und muss > 0 sein.",
        "invalid_frame_step": "Bildschritt ist erforderlich und muss >= 1 sein.",
        "invalid_jpeg_quality": "JPG-Qualität ist erforderlich und muss zwischen 1 und 100 liegen.",
        "invalid_pattern": "Muster muss {basename} und {frame_num} enthalten.",
        "output_folder_not_selected": "Sie müssen einen Ausgabeordner auswählen.",
        "select_output_folder_prompt": "Sie haben keinen Ausgabeordner ausgewählt. Möchten Sie jetzt einen auswählen?",
        "video_files_only": "Nur Videodateien sind erlaubt.",
        "no_videos_in_folder": "Keine Videos im ausgewählten Ordner gefunden.",
        "preview_error": "Video für Vorschau konnte nicht geöffnet werden.",
        "video_corrupted": "Video hat keine Frames oder ist beschädigt.",
        "stats_saved": "Statistiken in {csv_file} gespeichert.",
        "processing_video": "Verarbeite {video} | {frames} Frames.",
        "completed_video": "Abgeschlossen {video}: {frames} Frames extrahiert.",
        "error_processing": "Fehler bei der Verarbeitung von {video}: {error}",
        "total_files": "Gesamt: {count} Datei(en)",
        "drag_drop_disabled": "Drag & Drop deaktiviert. Installieren Sie tkinterdnd2 für volle Funktionalität.",
        "donate_dialog_title": "Spenden",
        "paypal": "Paypal",
        "copy": "Kopieren",
        "open_paypal": "Paypal öffnen",
        "theme": "Thema",
        "light": "Hell",
        "dark": "Dunkel",
    },
    "pt": {
        "created_by": "Criado por Lore",
        "donate": "Doar",
        "select_files": "Selecionar Arquivos",
        "select_folder": "Selecionar Pasta",
        "clear_list": "Limpar Lista",
        "settings": "Configurações",
        "output_folder": "Pasta de Saída",
        "select_output_folder": "Selecionar Pasta de Saída",
        "start_extraction": "Iniciar Extração",
        "stop": "Parar",
        "pause": "Pausar",
        "resume": "Retomar",
        "dynamic_preview": "Pré-visualização Dinâmica (1º)",
        "progress": "Progresso: {processed} / {total}",
        "finished": "Concluído",
        "frames_extracted_success": "Os quadros foram extraídos com sucesso.",
        "language": "Idioma",
        "instructions_title": "Instruções",
        "instructions_text": (
            "Bem-vindo/a ao Frames by Lore.\n\n"
            "Opções principais:\n"
            "- Limite de quadros\n"
            "- Dimensões de saída e Manter proporção\n"
            "- Tamanho máx. de arquivo (KB)\n"
            "- Passo de quadros\n"
            "- Formato de saída e Qualidade JPG\n"
            "- Padrão de nome (use {basename} e {frame_num})\n"
            "- Usar Multiprocessamento (experimental)\n\n"
            "Para configurar opções avançadas, edite manualmente o arquivo de configuração ou ajuste o código.\n"
            "\nAproveite o aplicativo!"
        ),
        "frame_limit": "Limite de quadros:",
        "no_limit": "Sem limite",
        "with_limit": "Com limite",
        "width": "Largura:",
        "height": "Altura:",
        "maintain_aspect": "Manter proporção",
        "max_file_size": "Tamanho máx. de arquivo (KB):",
        "frame_step": "Passo de quadros:",
        "output_format": "Formato de saída:",
        "jpeg_quality": "Qualidade JPG:",
        "filename_pattern": "Padrão de nome:",
        "use_multiprocessing": "Usar Multiprocessamento (experimental)",
        "save": "Salvar",
        "cancel": "Cancelar",
        "view_instructions": "Ver Instruções",
        "error": "Erro",
        "warning": "Aviso",
        "info": "Informação",
        "confirm": "Confirmar",
        "yes": "Sim",
        "no": "Não",
        "processing": "Processando...",
        "stopped": "Processamento parado pelo usuário.",
        "completed": "Processamento concluído.",
        "no_videos": "Nenhum vídeo selecionado.",
        "invalid_limit": "Você deve especificar o limite de quadros.",
        "invalid_dimensions": "As dimensões de saída são obrigatórias e devem ser > 0.",
        "invalid_max_size": "O tamanho máximo (KB) é obrigatório e deve ser > 0.",
        "invalid_frame_step": "O passo de quadros é obrigatório e deve ser >= 1.",
        "invalid_jpeg_quality": "A qualidade JPG é obrigatória e deve estar entre 1 e 100.",
        "invalid_pattern": "O padrão deve conter {basename} e {frame_num}.",
        "output_folder_not_selected": "Você deve selecionar uma pasta de saída.",
        "select_output_folder_prompt": "Você não selecionou uma pasta de saída. Deseja selecionar uma agora?",
        "video_files_only": "Apenas arquivos de vídeo são permitidos.",
        "no_videos_in_folder": "Nenhum vídeo encontrado na pasta selecionada.",
        "preview_error": "Não foi possível abrir o vídeo para pré-visualização.",
        "video_corrupted": "O vídeo não tem quadros ou está corrompido.",
        "stats_saved": "Estatísticas salvas em {csv_file}.",
        "processing_video": "Processando {video} | {frames} quadros.",
        "completed_video": "Concluído {video}: {frames} quadros extraídos.",
        "error_processing": "Erro ao processar {video}: {error}",
        "total_files": "Total: {count} arquivo(s)",
        "drag_drop_disabled": "Drag & Drop desabilitado. Instale tkinterdnd2 para funcionalidade completa.",
        "donate_dialog_title": "Doar",
        "paypal": "Paypal",
        "copy": "Copiar",
        "open_paypal": "Abrir Paypal",
        "theme": "Tema",
        "light": "Claro",
        "dark": "Escuro",
    }
}

# Forzar a iniciar siempre en inglés
current_language = 'en'

def get_text(key, **kwargs):
    text = translations[current_language].get(key, key)
    for k, v in kwargs.items():
        text = text.replace(f'{{{k}}}', str(v))
    return text

def update_all_texts(widget):
    if hasattr(widget, 'text_key'):
        if isinstance(widget, (tk.Label, ttk.Label, tk.Button, ttk.Button,
                              tk.Checkbutton, ttk.Checkbutton, tk.Radiobutton, ttk.Radiobutton)):
            widget.config(text=get_text(widget.text_key))
    for child in widget.winfo_children():
        update_all_texts(child)

# ### Configuración General
DEFAULT_SETTINGS = {
    "limit": None,
    "output_width": 1920,
    "output_height": 1080,
    "maintain_aspect": True,
    "output_folder": None,
    "max_file_size_kb": 500,
    "frame_step": 1,
    "output_format": "jpg",
    "jpeg_quality": 95,
    "filename_pattern": "{basename}_frame_{frame_num:06d}",
    # Se retira "send_email_after_processing" y "email_settings"
    "use_multiprocessing": False,
    "theme": "light",
    # Se mantiene en "en"
    "language": "en"
}

SETTINGS_FILE = Path.home() / ".frame_extractor_settings.json"
LOG_FILE = Path.home() / ".frame_extractor_log.txt"
CSV_STATS_FILE = Path.home() / "frame_extractor_stats.csv"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)

settings = DEFAULT_SETTINGS.copy()
pending_file_paths = []
current_processor = None
time_start = 0
frames_processed_global = 0
is_processing = False

# ### Funciones de Configuración
def load_settings():
    global settings, current_language
    try:
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                loaded_settings = json.load(f)
            for k in DEFAULT_SETTINGS.keys():
                if k in loaded_settings:
                    settings[k] = loaded_settings[k]
            # Se omite forzar el idioma a partir del archivo para que siempre inicie en inglés
            logging.info("Configuración cargada correctamente.")
        else:
            logging.info("No existe archivo de configuración, usando valores por defecto.")
    except Exception as e:
        logging.error(f"Error al cargar configuración: {e}")

def save_settings():
    try:
        # Siempre guardamos "en" para mantener la preferencia
        settings['language'] = 'en'
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4)
        logging.info("Configuración guardada.")
        return True
    except Exception as e:
        logging.error(f"Error al guardar configuración: {e}")
        messagebox.showerror(get_text('error'), f"Error al guardar configuración: {e}")
        return False

# ### Ventana de Configuración
class SettingsWindow:
    def __init__(self, parent):
        self.parent = parent
        self.config_window = tk.Toplevel(parent)
        self.apply_theme()
        self.config_window.title(get_text('settings'))
        self.config_window.resizable(False, False)
        self.config_window.transient(parent)
        self.config_window.grab_set()
        self.create_widgets()

    def apply_theme(self):
        if settings["theme"] == "dark":
            bg_color = "#2B2B2B"
            fg_color = "#FFFFFF"
        else:
            bg_color = "#F0F0F0"
            fg_color = "#000000"
        self.config_window.configure(bg=bg_color)
        style = ttk.Style()
        style.configure(".", background=bg_color, foreground=fg_color)
        style.configure("TLabel", background=bg_color, foreground=fg_color)
        style.configure("TCheckbutton", background=bg_color, foreground=fg_color)
        style.configure("TRadiobutton", background=bg_color, foreground=fg_color)
        style.configure("TButton", background=bg_color, foreground=fg_color)

    def create_widgets(self):
        cf = ttk.Frame(self.config_window, padding=10)
        cf.pack(fill=tk.BOTH, expand=True)

        frame_limit_label = ttk.Label(cf, text=get_text('frame_limit'))
        frame_limit_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        frame_limit_label.text_key = 'frame_limit'

        self.limit_choice_var = tk.StringVar(value="sin" if settings["limit"] is None else "con")
        no_limit_radio = ttk.Radiobutton(cf, text=get_text('no_limit'), variable=self.limit_choice_var, value="sin")
        no_limit_radio.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        no_limit_radio.text_key = 'no_limit'
        with_limit_radio = ttk.Radiobutton(cf, text=get_text('with_limit'), variable=self.limit_choice_var, value="con")
        with_limit_radio.grid(row=0, column=2, sticky="w", padx=5, pady=5)
        with_limit_radio.text_key = 'with_limit'

        self.limit_entry = ttk.Entry(cf)
        self.limit_entry.grid(row=0, column=3, sticky="w", padx=5, pady=5)
        self.limit_entry.insert(0, str(settings["limit"] or ""))

        width_label = ttk.Label(cf, text=get_text('width'))
        width_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)
        width_label.text_key = 'width'
        self.width_entry = ttk.Entry(cf, width=10)
        self.width_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        self.width_entry.insert(0, str(settings["output_width"]))

        height_label = ttk.Label(cf, text=get_text('height'))
        height_label.grid(row=1, column=2, sticky="w", padx=5, pady=5)
        height_label.text_key = 'height'
        self.height_entry = ttk.Entry(cf, width=10)
        self.height_entry.grid(row=1, column=3, sticky="w", padx=5, pady=5)
        self.height_entry.insert(0, str(settings["output_height"]))

        self.aspect_var = tk.BooleanVar(value=settings["maintain_aspect"])
        maintain_aspect_check = ttk.Checkbutton(cf, text=get_text('maintain_aspect'), variable=self.aspect_var)
        maintain_aspect_check.grid(row=2, column=0, columnspan=4, sticky="w", padx=5, pady=5)
        maintain_aspect_check.text_key = 'maintain_aspect'

        max_file_size_label = ttk.Label(cf, text=get_text('max_file_size'))
        max_file_size_label.grid(row=3, column=0, sticky="w", padx=5, pady=5)
        max_file_size_label.text_key = 'max_file_size'
        self.max_size_entry = ttk.Entry(cf, width=10)
        self.max_size_entry.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        self.max_size_entry.insert(0, str(settings["max_file_size_kb"]))

        frame_step_label = ttk.Label(cf, text=get_text('frame_step'))
        frame_step_label.grid(row=4, column=0, sticky="w", padx=5, pady=5)
        frame_step_label.text_key = 'frame_step'
        self.frame_step_entry = ttk.Entry(cf, width=10)
        self.frame_step_entry.grid(row=4, column=1, sticky="w", padx=5, pady=5)
        self.frame_step_entry.insert(0, str(settings["frame_step"]))

        output_format_label = ttk.Label(cf, text=get_text('output_format'))
        output_format_label.grid(row=5, column=0, sticky="w", padx=5, pady=5)
        output_format_label.text_key = 'output_format'
        self.format_choice = ttk.Combobox(cf, values=["jpg", "png", "webp", "bmp"], state="readonly")
        self.format_choice.set(settings["output_format"])
        self.format_choice.grid(row=5, column=1, sticky="w", padx=5, pady=5)

        self.jpeg_label = ttk.Label(cf, text=get_text('jpeg_quality'))
        self.jpeg_label.grid(row=6, column=0, sticky="w", padx=5, pady=5)
        self.jpeg_label.text_key = 'jpeg_quality'
        self.jpeg_quality_entry = ttk.Entry(cf, width=10)
        self.jpeg_quality_entry.grid(row=6, column=1, sticky="w", padx=5, pady=5)
        self.jpeg_quality_entry.insert(0, str(settings["jpeg_quality"]))

        filename_pattern_label = ttk.Label(cf, text=get_text('filename_pattern'))
        filename_pattern_label.grid(row=7, column=0, sticky="w", padx=5, pady=5)
        filename_pattern_label.text_key = 'filename_pattern'
        self.filename_pattern_entry = ttk.Entry(cf, width=40)
        self.filename_pattern_entry.grid(row=7, column=1, columnspan=3, sticky="w", padx=5, pady=5)
        self.filename_pattern_entry.insert(0, settings["filename_pattern"])

        # Se elimina la opción de enviar email.

        self.multiproc_var = tk.BooleanVar(value=settings["use_multiprocessing"])
        use_multiproc_check = ttk.Checkbutton(cf, text=get_text('use_multiprocessing'), variable=self.multiproc_var)
        use_multiproc_check.grid(row=9, column=0, columnspan=4, sticky="w", padx=5, pady=5)
        use_multiproc_check.text_key = 'use_multiprocessing'

        view_instructions_button = ttk.Button(cf, text=get_text('view_instructions'), command=self.show_instructions)
        view_instructions_button.grid(row=10, column=0, columnspan=4, sticky="w", padx=5, pady=10)
        view_instructions_button.text_key = 'view_instructions'

        btn_frame = ttk.Frame(cf)
        btn_frame.grid(row=11, column=0, columnspan=4, pady=10)
        save_button = ttk.Button(btn_frame, text=get_text('save'), command=self.save_and_close)
        save_button.pack(side=tk.LEFT, padx=5)
        save_button.text_key = 'save'
        cancel_button = ttk.Button(btn_frame, text=get_text('cancel'), command=self.config_window.destroy)
        cancel_button.pack(side=tk.LEFT, padx=5)
        cancel_button.text_key = 'cancel'

        self.format_choice.bind("<<ComboboxSelected>>", self.toggle_jpeg_fields)
        self.toggle_jpeg_fields()

    def toggle_jpeg_fields(self, event=None):
        is_jpg = (self.format_choice.get() == "jpg")
        if not is_jpg:
            self.jpeg_label.grid_remove()
            self.jpeg_quality_entry.grid_remove()
        else:
            self.jpeg_label.grid()
            self.jpeg_quality_entry.grid()

    def show_instructions(self):
        instr_win = Toplevel(self.config_window)
        instr_win.title(get_text('instructions_title'))
        instr_label = ttk.Label(instr_win, text=get_text('instructions_text'), padding=10)
        instr_label.pack()
        instr_label.text_key = 'instructions_text'

    def save_and_close(self):
        try:
            if self.limit_choice_var.get() == "con":
                limit_value = self.limit_entry.get().strip()
                if not limit_value:
                    raise ValueError(get_text('invalid_limit'))
                settings["limit"] = int(limit_value)
            else:
                settings["limit"] = None

            w = self.width_entry.get().strip()
            h = self.height_entry.get().strip()
            if not w or not h:
                raise ValueError(get_text('invalid_dimensions'))
            w = int(w)
            h = int(h)
            if w <= 0 or h <= 0:
                raise ValueError(get_text('invalid_dimensions'))
            settings["output_width"] = w
            settings["output_height"] = h

            settings["maintain_aspect"] = self.aspect_var.get()

            max_kb = self.max_size_entry.get().strip()
            if not max_kb:
                raise ValueError(get_text('invalid_max_size'))
            max_kb = int(max_kb)
            if max_kb <= 0:
                raise ValueError(get_text('invalid_max_size'))
            settings["max_file_size_kb"] = max_kb

            fs = self.frame_step_entry.get().strip()
            if not fs:
                raise ValueError(get_text('invalid_frame_step'))
            fs = int(fs)
            if fs < 1:
                raise ValueError(get_text('invalid_frame_step'))
            settings["frame_step"] = fs

            settings["output_format"] = self.format_choice.get()
            if settings["output_format"] == "jpg":
                jpeg_q = self.jpeg_quality_entry.get().strip()
                if not jpeg_q:
                    raise ValueError(get_text('invalid_jpeg_quality'))
                jpeg_q = int(jpeg_q)
                if jpeg_q < 1 or jpeg_q > 100:
                    raise ValueError(get_text('invalid_jpeg_quality'))
                settings["jpeg_quality"] = jpeg_q

            pattern = self.filename_pattern_entry.get().strip()
            if not pattern or "{basename}" not in pattern or "{frame_num" not in pattern:
                raise ValueError(get_text('invalid_pattern'))
            settings["filename_pattern"] = pattern

            settings["use_multiprocessing"] = self.multiproc_var.get()

            if save_settings():
                messagebox.showinfo(get_text('settings'), "Configuración guardada.")
                self.config_window.destroy()
        except ValueError as ve:
            messagebox.showerror(get_text('error'), str(ve))

# ### Drag & Drop
def add_drag_and_drop_support(listbox):
    if DRAG_AND_DROP_AVAILABLE:
        listbox.drop_target_register(DND_FILES)
        listbox.dnd_bind('<<Drop>>', on_file_drop)
    else:
        print("[INFO] " + get_text('drag_drop_disabled'))

def on_file_drop(event):
    data = event.data
    paths = parse_drop_files(data)
    add_files_to_pending(paths)

def parse_drop_files(data):
    lines = data.split('\n')
    cleaned_paths = []
    for line in lines:
        line = line.strip()
        if line.startswith('{') and line.endswith('}'):
            line = line[1:-1]
        if line:
            cleaned_paths.append(line)
    return cleaned_paths

# ### Manejo de Archivos
def add_files_to_pending(file_paths):
    global pending_file_paths
    video_extensions = (".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv",
                        ".mpeg", ".3gp", ".webm", ".ts", ".ogv")
    valid = [fp for fp in file_paths if fp.lower().endswith(video_extensions)]
    if not valid:
        messagebox.showinfo(get_text('info'), get_text('video_files_only'))
        return
    pending_file_paths.extend(valid)
    update_file_list_display()
    messagebox.showinfo(get_text('info'), f"{len(valid)} archivo(s) seleccionados.")

def select_files():
    paths = filedialog.askopenfilenames(
        title=get_text('select_files'),
        filetypes=[("Videos", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.mpeg *.3gp *.webm *.ts *.ogv")]
    )
    if paths:
        add_files_to_pending(paths)

def select_folder():
    folder = filedialog.askdirectory(title=get_text('select_folder'))
    if not folder:
        return
    video_extensions = (".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv",
                        ".mpeg", ".3gp", ".webm", ".ts", ".ogv")
    found = [os.path.join(root_dir, f) for root_dir, _, files in os.walk(folder)
             for f in files if f.lower().endswith(video_extensions)]
    if found:
        add_files_to_pending(found)
    else:
        messagebox.showinfo(get_text('info'), get_text('no_videos_in_folder'))

def clear_file_list():
    global pending_file_paths
    pending_file_paths = []
    update_file_list_display()
    log_text.delete("1.0", tk.END)
    progress_bar["value"] = 0
    progress_label.config(text=get_text('progress', processed=0, total=0))

def update_file_list_display():
    file_list_box.delete(0, tk.END)
    max_display = 100
    for fp in pending_file_paths[:max_display]:
        file_list_box.insert(tk.END, os.path.basename(fp))
    if len(pending_file_paths) > max_display:
        file_list_box.insert(tk.END, f"... y {len(pending_file_paths) - max_display} más")
    files_count_label.config(text=get_text('total_files', count=len(pending_file_paths)))

def select_output_folder():
    folder = filedialog.askdirectory(title=get_text('select_output_folder'))
    if folder:
        settings["output_folder"] = folder
        save_settings()
        output_folder_label.config(text=f"{get_text('output_folder')}: {truncate_path(folder, 40)}")

def truncate_path(path_str, max_length=40):
    if not path_str:
        return "No seleccionada"
    if len(path_str) <= max_length:
        return path_str
    parts = path_str.split(os.sep)
    if len(parts) <= 2:
        return path_str
    return os.path.join(parts[0], "...", parts[-1])

# ### Previsualización Dinámica
def show_dynamic_preview(video_path):
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            messagebox.showerror(get_text('error'), get_text('preview_error'))
            return
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            messagebox.showerror(get_text('error'), get_text('video_corrupted'))
            cap.release()
            return
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = total_frames / fps if fps > 0 else 0
        cap.release()

        preview_win = Toplevel(root)
        preview_win.title(f"{get_text('dynamic_preview')} - {os.path.basename(video_path)}")

        info_frame = ttk.Frame(preview_win)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        resolution_label = ttk.Label(info_frame, text=f"Resolución: {width}x{height}")
        resolution_label.pack(side=tk.LEFT, padx=5)
        fps_label = ttk.Label(info_frame, text=f"FPS: {fps:.2f}")
        fps_label.pack(side=tk.LEFT, padx=5)
        duration_label = ttk.Label(info_frame, text=f"Duración: {duration:.2f}s")
        duration_label.pack(side=tk.LEFT, padx=5)
        frames_label = ttk.Label(info_frame, text=f"Frames: {total_frames}")
        frames_label.pack(side=tk.LEFT, padx=5)

        img_label = ttk.Label(preview_win)
        img_label.pack(padx=10, pady=10)

        scale_frame = ttk.Frame(preview_win)
        scale_frame.pack(fill=tk.X, padx=10, pady=5)

        def update_preview(pos):
            frm = int(pos)
            cap2 = cv2.VideoCapture(video_path)
            cap2.set(cv2.CAP_PROP_POS_FRAMES, frm)
            ret, frame = cap2.read()
            cap2.release()
            if not ret:
                return
            processor = VideoProcessor(lambda x,y: None, lambda x: None, lambda x: None)
            frame = processor.resize_frame_according_to_settings(frame)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)

            screen_w = int(root.winfo_screenwidth() * 0.8)
            screen_h = int(root.winfo_screenheight() * 0.8)
            img_w, img_h = pil_img.size
            scale_factor = min(screen_w/img_w, screen_h/img_h)
            if scale_factor < 1:
                pil_img = pil_img.resize(
                    (int(img_w*scale_factor), int(img_h*scale_factor)),
                    Image.Resampling.LANCZOS
                )
            tk_img = ImageTk.PhotoImage(pil_img)
            img_label.config(image=tk_img)
            img_label.image = tk_img

        scale = Scale(scale_frame, from_=0, to=total_frames-1, orient=tk.HORIZONTAL, command=update_preview)
        scale.pack(fill=tk.X, expand=True)
        update_preview("0")

    except Exception as e:
        messagebox.showerror(get_text('error'), f"Error en previsualización: {e}")

# ### Procesador de Videos
class VideoProcessor:
    def __init__(self, progress_cb, error_cb, log_cb):
        self.progress_cb = progress_cb
        self.error_cb = error_cb
        self.log_cb = log_cb
        self.stop_requested = False
        self.pause_requested = False

    def process_videos(self, file_paths):
        folder = settings["output_folder"]
        if not folder:
            return
        os.makedirs(folder, exist_ok=True)
        total_frames = self.calculate_total_frames(file_paths)
        if total_frames == 0:
            self.error_cb(get_text('no_videos'))
            return

        self.log_cb(f"Iniciando extracción de {len(file_paths)} video(s) con {total_frames} frames estimados.")
        global frames_processed_global
        frames_processed_global = 0
        global time_start
        time_start = time.time()

        stats_data = []
        for video_path in file_paths:
            if self.stop_requested:
                break
            frames_saved = 0
            try:
                frames_saved = self.extract_frames_from_video(video_path, total_frames)
            except Exception as e:
                self.error_cb(get_text('error_processing', video=os.path.basename(video_path), error=str(e)))
            stats_data.append((os.path.basename(video_path), frames_saved))

        self.progress_cb(total_frames, total_frames)
        if self.stop_requested:
            self.log_cb(get_text('stopped'))
        else:
            self.log_cb(get_text('completed'))
            self.save_stats_csv(stats_data)
            root.bell()
            messagebox.showinfo(get_text('finished'), get_text('frames_extracted_success'))

    def calculate_total_frames(self, file_paths):
        est_total = 0
        for vp in file_paths:
            try:
                cap = cv2.VideoCapture(vp)
                if not cap.isOpened():
                    self.error_cb(f"No se pudo abrir {vp}")
                    continue
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                cap.release()
                step_frames = frame_count // settings["frame_step"]
                possible_frames = step_frames
                if settings["limit"] is not None:
                    possible_frames = min(possible_frames, settings["limit"])
                est_total += possible_frames
            except:
                pass
        return est_total

    def extract_frames_from_video(self, video_path, total_frames_est):
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise IOError(f"No se pudo abrir {video_path}")

        base_name = Path(video_path).stem
        total_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.log_cb(get_text('processing_video', video=os.path.basename(video_path), frames=total_video_frames))

        frame_index = 0
        frames_saved = 0
        global frames_processed_global

        while True:
            if self.stop_requested:
                break

            while self.pause_requested:
                if self.stop_requested:
                    break
                time.sleep(0.1)
            if self.stop_requested:
                break

            ret, frame = cap.read()
            if not ret:
                break
            if settings["limit"] is not None and frames_saved >= settings["limit"]:
                break
            if frame_index % settings["frame_step"] == 0:
                self.save_frame(frame, settings["output_folder"], base_name, frame_index)
                frames_saved += 1
                frames_processed_global += 1
                self.update_progress(frames_processed_global, total_frames_est)

            frame_index += 1

        cap.release()
        self.log_cb(get_text('completed_video', video=os.path.basename(video_path), frames=frames_saved))
        return frames_saved

    def update_progress(self, processed, total):
        self.progress_cb(processed, total)
        elapsed = time.time() - time_start
        if processed > 0:
            rate = processed / elapsed
            remaining = total - processed
            if rate > 0:
                est_time_left = remaining / rate
                minutes, seconds = divmod(est_time_left, 60)
                progress_label.config(
                    text=f"{get_text('progress', processed=processed, total=total)} ({int(minutes)}m {int(seconds)}s restantes)"
                )

    def save_frame(self, frame, folder, base_name, frame_num):
        frame = self.resize_frame_according_to_settings(frame)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(frame_rgb)

        filename = settings["filename_pattern"].format(basename=base_name, frame_num=frame_num)
        ext = settings["output_format"]
        fullpath = os.path.join(folder, f"{filename}.{ext}")
        fullpath = self.get_unique_filepath(fullpath)

        if ext == "jpg":
            max_bytes = settings["max_file_size_kb"] * 1024
            quality = settings["jpeg_quality"]
            while True:
                pil_img.save(fullpath, "JPEG", quality=quality, optimize=True)
                if os.path.getsize(fullpath) <= max_bytes or quality <= 10:
                    break
                quality -= 5
        elif ext in ["png", "webp", "bmp"]:
            pil_img.save(fullpath, ext.upper())
        else:
            pil_img.save(fullpath, "JPEG", quality=settings["jpeg_quality"])

    def resize_frame_according_to_settings(self, frame):
        h, w = frame.shape[:2]
        tw = settings["output_width"]
        th = settings["output_height"]

        if settings["maintain_aspect"]:
            orig_ratio = w / h
            target_ratio = tw / th
            if orig_ratio > target_ratio:
                new_w = tw
                new_h = int(new_w / orig_ratio)
            else:
                new_h = th
                new_w = int(new_h * orig_ratio)
        else:
            new_w, new_h = tw, th

        return cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)

    def get_unique_filepath(self, fp):
        if not os.path.exists(fp):
            return fp
        base, ext = os.path.splitext(fp)
        counter = 1
        while True:
            new_fp = f"{base}_{counter}{ext}"
            if not os.path.exists(new_fp):
                return new_fp
            counter += 1

    def save_stats_csv(self, data_list):
        with open(CSV_STATS_FILE, "a", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Fecha", time.strftime("%Y-%m-%d %H:%M:%S")])
            writer.writerow(["Video", "Frames Extraídos"])
            for item in data_list:
                writer.writerow(item)
            writer.writerow([])

    def stop(self):
        self.stop_requested = True

    def toggle_pause(self):
        self.pause_requested = not self.pause_requested

# ### Inicio del Procesamiento
def start_processing():
    global is_processing, current_processor
    if is_processing:
        messagebox.showerror(get_text('error'), "Ya hay un proceso en curso.")
        return
    if not pending_file_paths:
        messagebox.showerror(get_text('error'), get_text('no_videos'))
        return
    if not settings["output_folder"]:
        answer = messagebox.askyesno(get_text('confirm'), get_text('select_output_folder_prompt'))
        if answer:
            select_output_folder()
            if not settings["output_folder"]:
                messagebox.showerror(get_text('error'), get_text('output_folder_not_selected'))
                return
        else:
            return

    is_processing = True

    def process_in_thread():
        global is_processing, current_processor
        try:
            if settings["use_multiprocessing"]:
                # Aquí se podría implementar multiprocessing si fuera necesario.
                current_processor = VideoProcessor(update_progress, show_error, log_message)
                current_processor.process_videos(pending_file_paths)
            else:
                current_processor = VideoProcessor(update_progress, show_error, log_message)
                current_processor.process_videos(pending_file_paths)
        finally:
            is_processing = False
            current_processor = None

    t = threading.Thread(target=process_in_thread, daemon=True)
    t.start()

def stop_processing():
    global current_processor
    if not is_processing or current_processor is None:
        return
    answer = messagebox.askyesno(get_text('confirm'), "¿Detener el procesamiento?")
    if answer:
        current_processor.stop()

paused = False
def toggle_pause_processing():
    global current_processor, paused
    if not is_processing or current_processor is None:
        return
    current_processor.toggle_pause()
    paused = not paused
    if paused:
        pause_button.config(text=get_text('resume'))
    else:
        pause_button.config(text=get_text('pause'))

# ### Log y Progreso
def log_message(msg):
    logging.info(msg)
    log_text.insert(tk.END, msg + "\n")
    log_text.see(tk.END)

def show_error(msg):
    logging.error(msg)
    log_text.insert(tk.END, f"[{get_text('error')}] " + msg + "\n", "error")
    log_text.see(tk.END)

def update_progress(processed, total):
    val = (processed / total) * 100 if total else 0
    progress_bar["value"] = val
    progress_label.config(text=get_text('progress', processed=processed, total=total))

# ### Ventana Principal
if DRAG_AND_DROP_AVAILABLE:
    root = TkinterDnD.Tk()
else:
    root = tk.Tk()

root.title("Frames by Lore")
load_settings()

def apply_main_theme():
    if settings["theme"] == "dark":
        bg_color = "#2B2B2B"
        fg_color = "#FFFFFF"
    else:
        bg_color = "#F0F0F0"
        fg_color = "#000000"
    root.configure(bg=bg_color)
    style = ttk.Style()
    style.configure(".", background=bg_color, foreground=fg_color)
    style.configure("TLabel", background=bg_color, foreground=fg_color)
    style.configure("TCheckbutton", background=bg_color, foreground=fg_color)
    style.configure("TRadiobutton", background=bg_color, foreground=fg_color)
    style.configure("TButton", background=bg_color, foreground=fg_color)
    style.configure("Yellow.TButton", background="yellow", foreground="black")

apply_main_theme()

main_frame = ttk.Frame(root, padding=10)
main_frame.pack(fill=tk.BOTH, expand=True)

language_frame = ttk.Frame(main_frame)
language_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

language_label = ttk.Label(language_frame, text=get_text('language'))
language_label.pack(side=tk.LEFT, padx=5)
language_label.text_key = 'language'

language_var = tk.StringVar(value=current_language)
language_menu = ttk.Combobox(language_frame, textvariable=language_var,
                            values=['en', 'es', 'fr', 'it', 'de', 'pt'], state='readonly')
language_menu.pack(side=tk.LEFT, padx=5)

def change_language():
    global current_language
    current_language = language_var.get()
    # Aunque se cambie, se forzará a guardar en inglés, pero la UI puede cambiar en runtime
    update_all_texts(root)

language_menu.bind("<<ComboboxSelected>>", lambda event: change_language())

header_frame = ttk.Frame(main_frame)
header_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

created_by_label = ttk.Label(header_frame, text=get_text('created_by'))
created_by_label.pack(side=tk.RIGHT, padx=10)
created_by_label.text_key = 'created_by'
created_by_label.configure(foreground="red")

def open_donate_dialog():
    donate_win = tk.Toplevel(root)
    donate_win.title(get_text('donate_dialog_title'))
    donate_win.resizable(False, False)
    donate_win.configure(padx=10, pady=10)

    paypal_label = ttk.Label(donate_win, text=get_text('paypal'))
    paypal_label.pack(side=tk.LEFT, padx=5)
    paypal_label.text_key = 'paypal'

    email_entry = ttk.Entry(donate_win, width=30)
    email_entry.insert(0, "Artiet007@hotmail.com")
    email_entry.pack(side=tk.LEFT, padx=5)

    def block_edit(event):
        if event.keysym in ("Left", "Right", "Up", "Down", "Shift_L", "Shift_R", "Control_L", "Control_R"):
            return None
        if (event.state & 4) and event.keysym in ("v", "x"):
            return "break"
        return "break"

    email_entry.bind("<Key>", block_edit)

    menu = tk.Menu(email_entry, tearoff=0)
    menu.add_command(label=get_text('copy'), command=lambda: email_entry.event_generate("<<Copy>>"))

    def show_menu(event):
        menu.tk_popup(event.x_root, event.y_root)

    email_entry.bind("<Button-3>", show_menu)

    def open_paypal():
        webbrowser.open("https://www.paypal.com/")

    paypal_button = ttk.Button(donate_win, text="⬜", command=open_paypal, width=2)
    paypal_button.pack(side=tk.LEFT, padx=5)

donate_button = ttk.Button(header_frame, text=get_text('donate'), style="Yellow.TButton", command=open_donate_dialog)
donate_button.pack(side=tk.RIGHT, padx=5)
donate_button.text_key = 'donate'

top_frame = ttk.LabelFrame(main_frame, text="Video Selection")
top_frame.pack(fill=tk.X, padx=5, pady=5)

select_files_button = ttk.Button(top_frame, text=get_text('select_files'), command=select_files)
select_files_button.pack(side=tk.LEFT, padx=5, pady=5)
select_files_button.text_key = 'select_files'

select_folder_button = ttk.Button(top_frame, text=get_text('select_folder'), command=select_folder)
select_folder_button.pack(side=tk.LEFT, padx=5, pady=5)
select_folder_button.text_key = 'select_folder'

clear_list_button = ttk.Button(top_frame, text=get_text('clear_list'), command=clear_file_list)
clear_list_button.pack(side=tk.LEFT, padx=5, pady=5)
clear_list_button.text_key = 'clear_list'

settings_button = ttk.Button(top_frame, text=get_text('settings'), command=lambda: SettingsWindow(root))
settings_button.pack(side=tk.LEFT, padx=5, pady=5)
settings_button.text_key = 'settings'

file_list_frame = ttk.Frame(main_frame)
file_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

file_list_box = tk.Listbox(file_list_frame, height=8)
file_list_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

scrollbar = ttk.Scrollbar(file_list_frame, orient=tk.VERTICAL, command=file_list_box.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
file_list_box.config(yscrollcommand=scrollbar.set)

files_count_label = ttk.Label(file_list_frame, text=get_text('total_files', count=0))
files_count_label.pack(anchor="se", padx=5, pady=5)
files_count_label.text_key = 'total_files'

add_drag_and_drop_support(file_list_box)

output_frame = ttk.LabelFrame(main_frame, text=get_text('output_folder'))
output_frame.pack(fill=tk.X, padx=5, pady=5)
output_frame.text_key = 'output_folder'

select_output_button = ttk.Button(output_frame, text=get_text('select_output_folder'), command=select_output_folder)
select_output_button.pack(side=tk.LEFT, padx=5, pady=5)
select_output_button.text_key = 'select_output_folder'

output_folder_label = ttk.Label(output_frame, text=f"{get_text('output_folder')}: {truncate_path(settings['output_folder'], 40)}")
output_folder_label.pack(side=tk.LEFT, padx=5, pady=5)
output_folder_label.text_key = 'output_folder'

action_frame = ttk.Frame(main_frame)
action_frame.pack(fill=tk.X, padx=5, pady=5)

start_button = ttk.Button(action_frame, text=get_text('start_extraction'), command=start_processing)
start_button.pack(side=tk.LEFT, padx=5)
start_button.text_key = 'start_extraction'

stop_button = ttk.Button(action_frame, text=get_text('stop'), command=stop_processing)
stop_button.pack(side=tk.LEFT, padx=5)
stop_button.text_key = 'stop'

pause_button = ttk.Button(action_frame, text=get_text('pause'), command=toggle_pause_processing)
pause_button.pack(side=tk.LEFT, padx=5)
pause_button.text_key = 'pause'

def preview_first():
    if pending_file_paths:
        show_dynamic_preview(pending_file_paths[0])
    else:
        messagebox.showinfo(get_text('info'), get_text('no_videos'))

preview_button = ttk.Button(action_frame, text=get_text('dynamic_preview'), command=preview_first)
preview_button.pack(side=tk.LEFT, padx=5)
preview_button.text_key = 'dynamic_preview'

progress_frame = ttk.Frame(main_frame)
progress_frame.pack(fill=tk.X, padx=5, pady=5)

progress_label = ttk.Label(progress_frame, text=get_text('progress', processed=0, total=0), width=60, anchor='w')
progress_label.pack(side=tk.LEFT, padx=5)
progress_label.text_key = 'progress'

progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=300, mode='determinate')
progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

log_frame = ttk.LabelFrame(main_frame, text="Registro de Eventos")
log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

log_text = tk.Text(log_frame, wrap="word", height=8)
log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=log_text.yview)
log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
log_text.config(yscrollcommand=log_scroll.set)
log_text.tag_config("error", foreground="red")

update_file_list_display()

root.mainloop()
