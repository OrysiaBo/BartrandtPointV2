#!/usr/bin/env python3
"""
Dynamic Messe Stand V4 - Главное приложение С ВЕБ-СЕРВЕРОМ
Bertrandt Interactive Display System mit Remote-Zugriff
"""
import sys
import os
import argparse
import atexit

# Путь для импортов добавить
sys.path.insert(0, os.path.dirname(__file__))

from core.logger import logger
from core.config import config
from models.hardware import hardware_manager
from services.web_server import web_server

def setup_hardware():
    """Инициализирует Hardware-Verbindungen"""
    logger.info("🔌 Hardware-Setup wird gestartet...")
    
    try:
        # ESP32-Verbindungen добавить
        esp32_1 = hardware_manager.add_esp32(config.hardware['esp32_1_port'], 1)
        esp32_2 = hardware_manager.add_esp32(config.hardware['esp32_2_port'], 2)
        esp32_3 = hardware_manager.add_esp32(config.hardware['esp32_3_port'], 3)
        
        # Arduino GIGA добавить
        giga = hardware_manager.add_giga(config.hardware['giga_port'])
        
        # Verbindungen herstellen
        results = hardware_manager.connect_all()
        
        # Результаты логировать
        for device, success in results.items():
            status = "✅ Verbunden" if success else "❌ Fehler"
            logger.info(f"{device}: {status}")
        
        return any(results.values())  # True если минимум одно соединение успешно
        
    except Exception as e:
        logger.error(f"Fehler beim Hardware-Setup: {e}")
        return False

def setup_web_server(auto_start=True):
    """Настройка и автозапуск веб-сервера"""
    logger.info("🌐 Web-Server-Setup wird gestartet...")
    
    try:
        if auto_start:
            success = web_server.start_server()
            if success:
                server_info = web_server.get_server_info()
                logger.info(f"✅ Web-Server gestartet: {server_info['url']}")
                logger.info("📱 Remote-Zugriff verfügbar für Tablet/Smartphone")
                
                # Веб-сервер остановить при выходе из приложения
                atexit.register(cleanup_web_server)
                
                return True
            else:
                logger.warning("❌ Web-Server konnte nicht gestartet werden")
                logger.info("   Port 8080 möglicherweise belegt - kann später manuell gestartet werden")
                return False
        else:
            logger.info("Web-Server konfiguriert (manueller Start)")
            return True
            
    except Exception as e:
        logger.error(f"Fehler beim Web-Server-Setup: {e}")
        return False

def cleanup_web_server():
    """Cleanup-Funktion für Веб-сервер"""
    try:
        if web_server.running:
            web_server.stop_server()
            logger.info("Web-Server gestoppt")
    except Exception as e:
        logger.error(f"Fehler beim Stoppen des Web-Servers: {e}")

def create_and_run_gui(esp32_port=None):
    """Создает и запускает GUI-Anwendung с интеграцией веб-сервера"""
    try:
        # Динамический импорт GUI-Klasse из ui/ директории
        from ui.main_window import MainWindow
        
        logger.info("🖥️ GUI wird initialisiert...")
        gui_app = MainWindow(esp32_port=esp32_port)
        
        logger.info("✅ Dynamic Messe Stand V4 erfolgreich gestartet!")
        logger.info("💡 Drücke F11 für Vollbild, ESC zum Verlassen")
        
        # Информация о веб-сервере
        if web_server.running:
            server_info = web_server.get_server_info()
            logger.info(f"🌐 Web-Interface verfügbar: {server_info['url']}")
            logger.info("📱 Für Remote-Steuerung Browser öffnen und URL eingeben")
        
        # GUI-Hauptschleife запустить
        gui_app.run()
        
    except ImportError as e:
        logger.error(f"GUI-Import-Fehler: {e}")
        logger.info("📄 Fallback: Textbasierte Anwendung wird gestartet...")
        run_text_mode()
    except SyntaxError as e:
        logger.error(f"GUI-Syntax-Fehler: {e}")
        logger.error("🔧 Bitte überprüfen Sie die Syntax in den UI-Dateien")
        logger.info("📄 Fallback: Textbasierte Anwendung wird gestartet...")
        run_text_mode()
    except Exception as e:
        logger.error(f"GUI-Fehler: {e}")
        logger.info("📄 Fallback: Textbasierte Anwendung wird gestartet...")
        run_text_mode()

def run_text_mode():
    """Fallback-Режим без GUI с веб-управлением"""
    logger.info("📝 Textmodus aktiv - Drücke 'q' + Enter zum Beenden")
    logger.info("🌐 Web-Interface bleibt verfügbar für Remote-Steuerung")
    
    try:
        # Показать доступные команды
        print("\n" + "="*50)
        print("BERTRANDT DYNAMIC MESSE STAND V4 - TEXT MODUS")
        print("="*50)
        
        if web_server.running:
            server_info = web_server.get_server_info()
            print(f"📱 Web-Interface: {server_info['url']}")
            print("   Öffnen Sie diese URL im Browser für Remote-Steuerung")
        
        print("\nVerfügbare Befehle:")
        print("  status  - System-Status anzeigen")
        print("  web     - Web-Server Status/Toggle")
        print("  slides  - Präsentations-Info")
        print("  demo    - Demo starten/stoppen")
        print("  test    - Hardware-Test durchführen")
        print("  q       - Beenden")
        print("-"*50)
        
        while True:
            user_input = input("\nEingabe > ").strip().lower()
            
            if user_input == 'q':
                break
            elif user_input == 'status':
                show_system_status()
            elif user_input == 'web':
                handle_web_command()
            elif user_input == 'slides':
                show_slides_info()
            elif user_input == 'demo':
                handle_demo_command()
            elif user_input == 'test':
                logger.info("🧪 Hardware-Test wird durchgeführt...")
                setup_hardware()
            elif user_input == 'help' or user_input == '?':
                print("Verfügbare Befehle: status, web, slides, demo, test, q")
            elif user_input == '':
                continue
            else:
                logger.info(f"Unbekannter Befehl: {user_input}")
                print("Tipp: 'help' für verfügbare Befehle")
                
    except KeyboardInterrupt:
        logger.info("👋 Textmodus durch Benutzer beendet")

def show_system_status():
    """Показывает системный статус в текстовом режиме"""
    logger.info("📊 System-Status wird angezeigt...")
    
    # Hardware Status
    hw_status = hardware_manager.get_status_summary()
    print("\n🔌 Hardware Status:")
    for device, status in hw_status.items():
        status_icon = "✅" if status == "connected" else "❌"
        print(f"  {status_icon} {device}: {status}")
    
    # Web Server Status
    server_info = web_server.get_server_info()
    print(f"\n🌐 Web-Server: {'✅ Läuft' if server_info['running'] else '❌ Gestoppt'}")
    if server_info['running']:
        print(f"  URL: {server_info['url']}")
        print(f"  Aktuelle Folie: {server_info['current_slide']}")
    
    # Content Status
    from models.content import content_manager
    print(f"\n📋 Präsentation: {content_manager.get_slide_count()} Folien verfügbar")

def handle_web_command():
    """Обработка веб-команд в текстовом режиме"""
    server_info = web_server.get_server_info()
    
    if server_info['running']:
        print(f"\n🌐 Web-Server läuft: {server_info['url']}")
        choice = input("Web-Server stoppen? (j/n): ").strip().lower()
        if choice == 'j' or choice == 'y':
            if web_server.stop_server():
                print("✅ Web-Server gestoppt")
            else:
                print("❌ Fehler beim Stoppen")
    else:
        print("\n🌐 Web-Server ist gestoppt")
        choice = input("Web-Server starten? (j/n): ").strip().lower()
        if choice == 'j' or choice == 'y':
            if web_server.start_server():
                new_info = web_server.get_server_info()
                print(f"✅ Web-Server gestartet: {new_info['url']}")
            else:
                print("❌ Fehler beim Starten (Port belegt?)")

def show_slides_info():
    """Показывает информацию о слайдах"""
    from models.content import content_manager
    
    slides = content_manager.get_all_slides()
    print(f"\n📋 Präsentation: {len(slides)} Folien")
    
    for slide_id, slide in sorted(slides.items()):
        title = slide.title[:40] + "..." if len(slide.title) > 40 else slide.title
        print(f"  {slide_id:2d}. {title}")
    
    stats = content_manager.get_presentation_statistics()
    print(f"\n📊 Statistiken:")
    print(f"  Gesamt Bilder: {stats['total_images']}")
    print(f"  Gesamt Text: {stats['total_content_length']} Zeichen")

def handle_demo_command():
    """Обработка demo-команд"""
    from services.demo import demo_service
    
    status = demo_service.get_status()
    
    if status['running']:
        print(f"\n▶️ Demo läuft (Folie {status['current_slide']}/{status['total_slides']})")
        choice = input("Demo stoppen? (j/n): ").strip().lower()
        if choice == 'j' or choice == 'y':
            demo_service.stop_demo()
            print("✅ Demo gestoppt")
    else:
        print(f"\n⏹️ Demo gestoppt (Folie {status['current_slide']}/{status['total_slides']})")
        choice = input("Demo starten? (j/n): ").strip().lower()
        if choice == 'j' or choice == 'y':
            demo_service.start_demo()
            print("✅ Demo gestartet")

def main():
    """Hauptfunktion с расширенными опциями"""
    # Argument-Parser
    parser = argparse.ArgumentParser(description='Dynamic Messe Stand V4 mit Web-Server')
    parser.add_argument('--esp32-port', help='ESP32 Port (Standard: /dev/ttyUSB0)')
    parser.add_argument('--no-hardware', action='store_true', help='Ohne Hardware-Verbindungen starten')
    parser.add_argument('--no-web', action='store_true', help='Web-Server nicht automatisch starten')
    parser.add_argument('--web-port', type=int, default=8080, help='Web-Server Port (Standard: 8080)')
    parser.add_argument('--debug', action='store_true', help='Debug-Modus aktivieren')
    parser.add_argument('--text-mode', action='store_true', help='Textmodus ohne GUI starten')
    
    args = parser.parse_args()
    
    # Logging-Level setzen
    if args.debug:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("Debug-Modus aktiviert")
    
    # Web-Server Port konfigurieren
    if args.web_port != 8080:
        web_server.port = args.web_port
        logger.info(f"Web-Server Port geändert: {args.web_port}")
    
    logger.info("🚀 Dynamic Messe Stand V4 wird gestartet...")
    logger.info(f"Python Version: {sys.version}")
    logger.info(f"Arbeitsverzeichnis: {os.getcwd()}")
    
    try:
        # Web-Server Setup (falls gewünscht)
        if not args.no_web:
            web_success = setup_web_server(auto_start=True)
            if not web_success:
                logger.warning("⚠️ Web-Server konnte nicht automatisch gestartet werden")
        else:
            logger.info("🔧 Web-Server-Setup übersprungen (--no-web)")
        
        # Hardware-Setup (falls gewünscht)
        if not args.no_hardware:
            hardware_success = setup_hardware()
            if not hardware_success:
                logger.warning("⚠️ Keine Hardware-Verbindungen erfolgreich - Anwendung startet trotzdem")
        else:
            logger.info("🔧 Hardware-Setup übersprungen (--no-hardware)")
        
        # Anwendung starten
        if args.text_mode:
            run_text_mode()
        else:
            create_and_run_gui(esp32_port=args.esp32_port)
        
    except KeyboardInterrupt:
        logger.info("👋 Anwendung durch Benutzer beendet")
    except Exception as e:
        logger.error(f"💥 Unerwarteter Fehler: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        logger.info("🧹 Cleanup wird durchgeführt...")
        
        # Web-Server останавливать
        try:
            if web_server.running:
                web_server.stop_server()
        except Exception as e:
            logger.error(f"Fehler beim Stoppen des Web-Servers: {e}")
        
        # Hardware-Verbindungen trennen
        try:
            hardware_manager.disconnect_all()
        except Exception as e:
            logger.error(f"Fehler beim Trennen der Hardware: {e}")
        
        # Demo stoppen
        try:
            from services.demo import demo_service
            demo_service.stop_demo()
        except Exception as e:
            logger.error(f"Fehler beim Stoppen der Demo: {e}")
        
        logger.info("👋 Dynamic Messe Stand V4 beendet")

if __name__ == "__main__":
    main()
