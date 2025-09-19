#!/usr/bin/env python3
"""
Main Window für Dynamic Messe Stand V4 - С ВЕБ-СЕРВЕРОМ
Haupt-GUI-Fenster с responsive Design и удаленной трансляцией
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import subprocess
import socket
from core.config import config
from core.theme import theme_manager, THEME_VARS, _mix
from core.logger import logger
from ui.components.header import HeaderComponent
from ui.components.status_panel import StatusPanelComponent
from ui.components.footer import FooterComponent
from ui.tabs.home_tab import HomeTab
from ui.tabs.creator_tab import CreatorTab
from ui.tabs.presentation_tab import PresentationTab

# Импорт веб-сервера
from services.web_server import web_server

class MainWindow:
    """Haupt-GUI-Fenster с веб-сервером для удаленной трансляции"""
    
    def __init__(self, esp32_port=None):
        logger.info("🚀 Starte Dynamic Messe Stand V4...")
        
        # Tkinter Root
        self.root = tk.Tk()
        self.root.title(config.gui['title'])
        
        # Базовые переменные
        self.esp32_port = esp32_port
        self.fullscreen = False
        self.current_tab = "home"
        
        # Веб-сервер статус
        self.web_server_status = False
        
        # Setup
        self.setup_window()
        self.setup_responsive_design()
        self.setup_styles()
        self.setup_gui_components()
        self.setup_tabs()
        
        # Настройка веб-сервера
        self.setup_web_server()
        
        # Начальный tab
        self.switch_tab("home")
        
        logger.info("✅ Dynamic Messe Stand V4 erfolgreich initialisiert!")
        self.setup_content_synchronization()

    def setup_web_server(self):
        """Настройка веб-сервера для удаленной трансляции"""
        try:
            # Определить IP-адрес для отображения пользователю
            self.local_ip = self.get_local_ip()
            
            # Добавить callback для обработки команд от веб-интерфейса
            web_server.add_slide_change_callback(self.handle_web_command)
            
            logger.info(f"Web server konfiguriert für Remote-Zugriff auf {self.local_ip}:8080")
            
        except Exception as e:
            logger.error(f"Error setting up web server: {e}")

    def get_local_ip(self):
        """Получить локальный IP-адрес"""
        try:
            # Создать временное соединение чтобы определить локальный IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            return "127.0.0.1"

    def handle_web_command(self, action, slide_id):
        """Обработчик команд от веб-интерфейса планшета"""
        try:
            logger.debug(f"Web command received: {action}, slide: {slide_id}")
            
            if action == 'next':
                if hasattr(self, 'tabs') and 'demo' in self.tabs:
                    self.tabs['demo'].next_slide()
            elif action == 'prev':
                if hasattr(self, 'tabs') and 'demo' in self.tabs:
                    self.tabs['demo'].previous_slide()
            elif action == 'goto':
                if hasattr(self, 'tabs') and 'demo' in self.tabs:
                    self.tabs['demo'].goto_slide(slide_id)
            elif action == 'play':
                if hasattr(self, 'tabs') and 'demo' in self.tabs:
                    # Переключиться на demo tab если не активен
                    if self.current_tab != 'demo':
                        self.switch_tab('demo')
                    self.tabs['demo'].toggle_demo()
            elif action == 'stop':
                if hasattr(self, 'tabs') and 'demo' in self.tabs:
                    if self.tabs['demo'].demo_running:
                        self.tabs['demo'].toggle_demo()
            
        except Exception as e:
            logger.error(f"Error handling web command: {e}")

    def toggle_web_server(self):
        """Переключить веб-сервер вкл/выкл"""
        try:
            if not self.web_server_status:
                # Запустить веб-сервер
                if web_server.start_server():
                    self.web_server_status = True
                    self.show_web_server_info()
                else:
                    messagebox.showerror(
                        "Web Server Fehler", 
                        "Web-Server konnte nicht gestartet werden.\n"
                        "Port 8080 möglicherweise bereits belegt."
                    )
            else:
                # Остановить веб-сервер
                if web_server.stop_server():
                    self.web_server_status = False
                    messagebox.showinfo("Web Server", "Web-Server gestoppt")
                    
        except Exception as e:
            logger.error(f"Error toggling web server: {e}")
            messagebox.showerror("Fehler", f"Web-Server Fehler: {e}")

    def show_web_server_info(self):
        """Показать информацию о веб-сервере"""
        try:
            server_url = f"http://{self.local_ip}:8080"
            
            # Создать информационное окно
            info_window = tk.Toplevel(self.root)
            info_window.title("Remote-Präsentation - Web Server")
            info_window.geometry("500x400")
            info_window.configure(bg=THEME_VARS["bg"])
            info_window.grab_set()  # Модальное окно
            
            # Центрировать окно
            info_window.transient(self.root)
            info_window.geometry("+{}+{}".format(
                self.root.winfo_rootx() + 100,
                self.root.winfo_rooty() + 100
            ))
            
            # Контент
            main_frame = ttk.Frame(info_window, style="TFrame", padding=20)
            main_frame.pack(fill='both', expand=True)
            
            # Заголовок
            title_label = ttk.Label(
                main_frame,
                text="🌐 Remote-Präsentation aktiv!",
                style="H1.TLabel"
            )
            title_label.pack(pady=(0, 20))
            
            # Информация
            info_text = f"""Web-Server ist gestartet und bereit für Remote-Zugriff.

🖥️ Server-Adresse:
{server_url}

📱 Für Tablet/Smartphone:
1. Stellen Sie sicher, dass beide Geräte im selben WLAN sind
2. Öffnen Sie einen Webbrowser auf dem Tablet
3. Geben Sie die obige Adresse ein
4. Steuern Sie die Präsentation remote!

⌨️ Tastatur-Steuerung im Vollbild:
• Pfeiltasten: Vor/Zurück navigieren
• Leertaste: Nächste Folie
• ESC: Vollbild verlassen
• F5: Demo starten/stoppen
• Zahlen 1-9: Zu Folie springen

🔄 Die Präsentation wird automatisch synchronisiert."""
            
            info_label = ttk.Label(
                main_frame,
                text=info_text,
                style="TLabel",
                justify='left'
            )
            info_label.pack(pady=(0, 20), fill='both', expand=True)
            
            # Buttons
            button_frame = ttk.Frame(main_frame, style="TFrame")
            button_frame.pack(fill='x', pady=(10, 0))
            
            # URL in Zwischenablage kopieren
            def copy_url():
                info_window.clipboard_clear()
                info_window.clipboard_append(server_url)
                copy_btn.configure(text="✅ Kopiert!")
                info_window.after(2000, lambda: copy_btn.configure(text="📋 URL kopieren"))
            
            copy_btn = ttk.Button(
                button_frame,
                text="📋 URL kopieren",
                command=copy_url,
                style="Primary.TButton"
            )
            copy_btn.pack(side='left', padx=(0, 10))
            
            # Web-Server stoppen
            def stop_server():
                self.toggle_web_server()
                info_window.destroy()
            
            stop_btn = ttk.Button(
                button_frame,
                text="🛑 Server stoppen",
                command=stop_server,
                style="TButton"
            )
            stop_btn.pack(side='left', padx=(0, 10))
            
            # Schließen
            close_btn = ttk.Button(
                button_frame,
                text="Schließen",
                command=info_window.destroy,
                style="TButton"
            )
            close_btn.pack(side='right')
            
        except Exception as e:
            logger.error(f"Error showing web server info: {e}")

    def setup_content_synchronization(self):
        """Настройка синхронизации контента между tabs и веб-сервером"""
        try:
            from models.content import content_manager
            
            # Подписать MainWindow на изменения контента
            content_manager.add_observer(self.on_content_changed)
            
            logger.debug("Content synchronization setup complete")
            
        except Exception as e:
            logger.error(f"Error setting up content synchronization: {e}")

    def on_content_changed(self, slide_id, slide_data, action='update'):
        """Обработчик изменений контента для синхронизации всех tabs и веб-сервера"""
        try:
            # Синхронизировать Demo Tab
            if hasattr(self, 'tabs') and 'demo' in self.tabs:
                # Demo tab имеет собственный обработчик, он автоматически обновится
                pass
            
            # Синхронизировать Creator Tab
            if hasattr(self, 'tabs') and 'creator' in self.tabs:
                # Обновить thumbnails в Creator
                if hasattr(self.tabs['creator'], 'create_slide_thumbnails'):
                    self.tabs['creator'].create_slide_thumbnails()
            
            # Синхронизировать Home Tab если есть
            if hasattr(self, 'tabs') and 'home' in self.tabs:
                if hasattr(self.tabs['home'], 'refresh_content'):
                    self.tabs['home'].refresh_content()
            
            # Синхронизировать веб-сервер
            if self.web_server_status:
                web_server.set_current_slide(slide_id)
            
            logger.debug(f"All tabs and web server synchronized for slide {slide_id} change")
            
        except Exception as e:
            logger.error(f"Error synchronizing tabs and web server: {e}")

    def refresh_all_tabs(self):
        """Принудительно обновляет все tabs после загрузки презентации"""
        try:
            # Обновить Demo Tab
            if hasattr(self, 'tabs') and 'demo' in self.tabs:
                if hasattr(self.tabs['demo'], 'create_slides_list'):
                    self.tabs['demo'].create_slides_list()
                if hasattr(self.tabs['demo'], 'load_current_slide'):
                    self.tabs['demo'].load_current_slide()
            
            # Обновить Creator Tab
            if hasattr(self, 'tabs') and 'creator' in self.tabs:
                if hasattr(self.tabs['creator'], 'create_slide_thumbnails'):
                    self.tabs['creator'].create_slide_thumbnails()
                if hasattr(self.tabs['creator'], 'load_slide_to_editor'):
                    # Перезагрузить текущий слайд
                    current_slide = getattr(self.tabs['creator'], 'current_edit_slide', 1)
                    self.tabs['creator'].load_slide_to_editor(current_slide)
            
            # Обновить Home Tab
            if hasattr(self, 'tabs') and 'home' in self.tabs:
                if hasattr(self.tabs['home'], 'refresh_content'):
                    self.tabs['home'].refresh_content()
            
            logger.info("All tabs refreshed successfully")
            
        except Exception as e:
            logger.error(f"Error refreshing all tabs: {e}")
    
    def setup_window(self):
        """Konfiguriert das Hauptfenster für 24" RTC Monitor"""
        # Hauptmonitor ermitteln (primärer Monitor)
        self.detect_primary_monitor()
        
        # Für 24" RTC Monitor optimiert
        self.window_width = self.primary_width
        self.window_height = self.primary_height
        
        logger.info(f"Hauptmonitor erkannt: {self.window_width}x{self.window_height} bei ({self.primary_x}, {self.primary_y})")
        
        # Fenster explizit auf Hauptmonitor positionieren
        self.root.geometry(f"{self.window_width}x{self.window_height}+{self.primary_x}+{self.primary_y}")
        self.root.minsize(config.gui['min_width'], config.gui['min_height'])
        
        # Vollbild-Bindings
        self.root.bind('<F11>', self.toggle_fullscreen)
        self.root.bind('<Escape>', self.exit_fullscreen)
        
        # Sofort in Vollbild auf Hauptmonitor
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)  # Immer im Vordergrund
        self.fullscreen = True
        
        # Fenster auf Hauptmonitor forcieren
        self.root.wm_attributes('-zoomed', True)  # Linux maximieren
        self.root.focus_force()    # Fokus erzwingen
        self.root.lift()           # Fenster nach vorne bringen
        
        # Sicherstellen, dass Fenster auf Hauptmonitor bleibt
        self.root.after(100, self.ensure_primary_monitor)
        
        # Theme anwenden
        colors = theme_manager.get_colors()
        self.root.configure(bg=colors['background_primary'])
    
    def detect_primary_monitor(self):
        """Erkennt den primären Monitor (Hauptbildschirm)"""
        try:
            # Tkinter-Methode für primären Monitor
            self.root.update_idletasks()
            
            # Gesamte Bildschirmgröße
            total_width = self.root.winfo_screenwidth()
            total_height = self.root.winfo_screenheight()
            
            # Primärer Monitor ist normalerweise bei (0,0)
            self.primary_x = 0
            self.primary_y = 0
            self.primary_width = total_width
            self.primary_height = total_height
            
            # Versuche Multi-Monitor Setup zu erkennen
            try:
                import subprocess
                result = subprocess.run(['xrandr'], capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if ' connected primary ' in line:
                            # Primärer Monitor gefunden
                            parts = line.split()
                            for part in parts:
                                if 'x' in part and '+' in part:
                                    # Format: 1920x1080+0+0
                                    resolution_pos = part.split('+')
                                    if len(resolution_pos) >= 3:
                                        resolution = resolution_pos[0]
                                        self.primary_x = int(resolution_pos[1])
                                        self.primary_y = int(resolution_pos[2])
                                        
                                        if 'x' in resolution:
                                            w, h = resolution.split('x')
                                            self.primary_width = int(w)
                                            self.primary_height = int(h)
                                    break
                            break
            except:
                pass  # Fallback auf Standard-Werte
            
            logger.info(f"Primärer Monitor: {self.primary_width}x{self.primary_height} bei ({self.primary_x}, {self.primary_y})")
            
        except Exception as e:
            logger.warning(f"Monitor-Erkennung fehlgeschlagen: {e}")
            # Fallback-Werte
            self.primary_x = 0
            self.primary_y = 0
            self.primary_width = 1920
            self.primary_height = 1080
    
    def ensure_primary_monitor(self):
        """Stellt sicher, dass das Fenster auf dem Hauptmonitor bleibt"""
        try:
            # Fenster-Position prüfen und korrigieren
            current_x = self.root.winfo_x()
            current_y = self.root.winfo_y()
            
            # Falls Fenster nicht auf Hauptmonitor, zurück bewegen
            if current_x != self.primary_x or current_y != self.primary_y:
                self.root.geometry(f"{self.primary_width}x{self.primary_height}+{self.primary_x}+{self.primary_y}")
                logger.info(f"Fenster auf Hauptmonitor zurück bewegt: ({self.primary_x}, {self.primary_y})")
            
        except Exception as e:
            logger.warning(f"Monitor-Korrektur fehlgeschlagen: {e}")
    
    def setup_responsive_design(self):
        """Konfiguriert responsive Design-Elemente"""
        # Scale Factor für responsive Design
        self.scale_factor = min(self.window_width, self.window_height) / config.design['scale_factor_base']
        
        # Responsive Schriftarten
        self.fonts = theme_manager.get_fonts(self.window_width, self.window_height)
        
        logger.debug(f"Responsive Design: {self.window_width}x{self.window_height}, Scale: {self.scale_factor:.2f}")
    
    def setup_styles(self):
        """Wendet das komplette Bertrandt Dark Theme an - überschreibt alle anderen Styles"""
        # Bertrandt Dark Theme direkt anwenden
        from core.theme import apply_bertrandt_dark_theme
        apply_bertrandt_dark_theme(self.root, reapply=True)
        self.style = ttk.Style()
        
        # Zusätzliche moderne Styles für bessere Integration
        colors = theme_manager.get_colors()
        spacing = theme_manager.get_spacing()
        
        # Überschreibe alle Standard-Styles mit Bertrandt Theme
        # Frames
        self.style.configure('TFrame', 
                           background=THEME_VARS["bg"],
                           relief='flat',
                           borderwidth=0)
        
        # Labels - alle mit Bertrandt Farben
        self.style.configure('TLabel',
                           background=THEME_VARS["bg"],
                           foreground=THEME_VARS["text"],
                           font=(THEME_VARS["font_family"], THEME_VARS["size_body"]))
        
        # Buttons - alle mit Bertrandt Styles
        self.style.configure('TButton',
                           background=THEME_VARS["brand_600"],
                           foreground="#ffffff",
                           font=(THEME_VARS["font_family"], THEME_VARS["size_body"], "bold"),
                           relief='flat',
                           borderwidth=0,
                           padding=(THEME_VARS["pad"], THEME_VARS["pad"] // 2))
    
    def setup_gui_components(self):
        """Erstellt die Bertrandt Layout-Struktur nach Referenz"""
        # Hauptcontainer mit Bertrandt Padding (14px)
        self.main_container = ttk.Frame(self.root, style="TFrame")
        self.main_container.pack(fill='both', expand=True, padx=14, pady=12)
        
        # Navbar (Glass-Frame oben) - nach Bertrandt Referenz
        self.navbar = ttk.Frame(self.main_container, style="Glass.TFrame", padding=(12, 10))
        self.navbar.pack(side="top", fill="x", pady=(0, 12))
        self.setup_navbar()
        
        # Hero-Bereich (große Karte) - nach Bertrandt Referenz
        self.hero_outer, self.hero = self.make_glass_card(self.main_container, padding=16)
        self.hero_outer.pack(fill="x", pady=(0, 12))
        self.setup_hero()
        
        # Grid-Container (3-Spalten-Layout) - nach Bertrandt Referenz
        self.grid_container = ttk.Frame(self.main_container, style="TFrame")
        self.grid_container.pack(fill="both", expand=True, pady=(0, 12))
        self.grid_container.columnconfigure((0,1,2), weight=1)
        self.grid_container.rowconfigure((0,1), weight=1)
        
        # Content-Bereich für Tabs - nimmt das komplette Grid ein
        self.content_frame = self.grid_container
        self.tab_content_frame = self.grid_container
        
        # Footer mit Separator - nach Bertrandt Referenz
        self.footer_frame = ttk.Frame(self.main_container, style="TFrame")
        self.footer_frame.pack(side="bottom", fill="x")
        ttk.Separator(self.footer_frame).pack(fill="x", pady=6)
        
        # Footer с дополнительной информацией о веб-сервере
        self.create_enhanced_footer()
        
        logger.info("✅ Bertrandt Layout-Struktur mit Web-Server erstellt")
    
    def create_enhanced_footer(self):
        """Создать улучшенный footer с информацией о веб-сервере"""
        footer_content_frame = ttk.Frame(self.footer_frame, style="TFrame")
        footer_content_frame.pack(fill="x")
        
        # Основная информация (слева)
        main_info = ttk.Label(
            footer_content_frame, 
            text="© 2025 Bertrandt AG - Dynamic Messe Stand V4 - Marvin Mayer", 
            style="Muted.TLabel"
        )
        main_info.pack(side='left')
        
        # Веб-сервер информация (справа)
        web_info_frame = ttk.Frame(footer_content_frame, style="TFrame")
        web_info_frame.pack(side='right')
        
        # Статус веб-сервера
        self.web_status_label = ttk.Label(
            web_info_frame,
            text=f"Web: http://{self.local_ip}:8080" if self.web_server_status else "Web: Inaktiv",
            style="Muted.TLabel"
        )
        self.web_status_label.pack(side='left', padx=(0, 10))
        
        # Кнопка управления веб-сервером
        self.web_toggle_btn = ttk.Button(
            web_info_frame,
            text="🌐 Web starten" if not self.web_server_status else "🌐 Web stoppen",
            style="TButton",
            command=self.toggle_web_server
        )
        self.web_toggle_btn.pack(side='left')
    
    def make_glass_card(self, parent, padding=12):
        """Erstellt eine Glass-Card im Bertrandt-Style"""
        from core.theme import THEME_VARS, _mix
        
        # Outer Frame
        outer = ttk.Frame(parent, style="TFrame")
        
        # Canvas für Hintergrund-Effekt
        cv = tk.Canvas(outer, bg=THEME_VARS["bg"], highlightthickness=0, bd=0, height=1)
        cv.grid(row=0, column=0, sticky="nsew")
        outer.grid_rowconfigure(0, weight=1)
        outer.grid_columnconfigure(0, weight=1)
        
        # Inner Frame mit Glass-Style
        inner = ttk.Frame(outer, style="Glass.TFrame", padding=padding)
        inner.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Redraw-Funktion für Glass-Effekt
        def _redraw(_evt=None):
            cv.delete("all")
            w = outer.winfo_width()
            h = outer.winfo_height()
            if w < 2 or h < 2: 
                return
            # Simulierte Kontur
            cv.create_rectangle(
                1, 1, w-2, h-2,
                outline=THEME_VARS["elev_outline"],
                width=1
            )
            # Leichte Innenfläche ("Glas")
            cv.create_rectangle(
                2, 2, w-3, h-3,
                outline="",
                fill=_mix(THEME_VARS["panel"], "#ffffff", 0.04)
            )
        
        outer.bind("<Configure>", _redraw)
        return outer, inner
    
    def setup_navbar(self):
        """Erstellt die Navbar nach Bertrandt Referenz mit Web-Controls"""
        # Left side - Brand Badge + Title
        left_frame = ttk.Frame(self.navbar, style="TFrame")
        left_frame.pack(side="left")
        
        # Bertrandt Logo
        self.load_logo(left_frame)
        
        # Title
        title_label = ttk.Label(left_frame, text="Dynamic Messe Stand V4", style="H2.TLabel")
        title_label.pack(side="left")
        
        # Right side - Navigation Buttons
        right_frame = ttk.Frame(self.navbar, style="TFrame")
        right_frame.pack(side="right")
        
        # Navigation Buttons
        nav_buttons = [
            ("Home", "home"),
            ("Demo", "demo"), 
            ("Creator", "creator"),
            ("Presentation", "presentation")
        ]
        
        self.nav_buttons = {}
        for text, tab_name in nav_buttons:
            btn = ttk.Button(
                right_frame, 
                text=text, 
                style="Ghost.TButton",
                command=lambda t=tab_name: self.switch_tab(t)
            )
            btn.pack(side="left", padx=6)
            self.nav_buttons[tab_name] = btn
        
        # Theme Toggle Button
        theme_btn = ttk.Button(
            right_frame, 
            text="🌙", 
            style="Ghost.TButton",
            command=self.toggle_theme
        )
        theme_btn.pack(side="left", padx=6)
        
        # Web Server Button (НОВЫЙ)
        self.web_server_btn = ttk.Button(
            right_frame,
            text="📱 Remote" if not self.web_server_status else "📱 Aktiv",
            style="Ghost.TButton" if not self.web_server_status else "Primary.TButton",
            command=self.toggle_web_server
        )
        self.web_server_btn.pack(side="left", padx=6)
        
        # Primary Action Button
        primary_btn = ttk.Button(
            right_frame, 
            text="System Status", 
            style="Primary.TButton",
            command=self.show_system_status
        )
        primary_btn.pack(side="left", padx=6)
    
    def setup_hero(self):
        """Erstellt den Hero-Bereich nach Bertrandt Referenz с Web-Info"""
        # Eyebrow Text
        eyebrow = ttk.Label(
            self.hero, 
            text="Interaktives Messestand-System mit Remote-Zugriff", 
            foreground=_mix(THEME_VARS["brand_600"], "#9cc7fb", 0.5)
        )
        eyebrow.pack(anchor="w")
        
        # Main Title
        title = ttk.Label(
            self.hero, 
            text="Bertrandt Dynamic Messe Stand V4", 
            style="H1.TLabel"
        )
        title.pack(anchor="w", pady=(4, 4))
        
        # Description с упоминанием веб-функций
        description_text = (
            "Professionelles Touch-Interface für interaktive Messestände mit Hardware-Integration, "
            "Live-Demos und Remote-Steuerung via Tablet/Smartphone."
        )
        
        description = ttk.Label(
            self.hero, 
            text=description_text,
            style="Muted.TLabel", 
            wraplength=900, 
            justify="left"
        )
        description.pack(anchor="w")
    
    def load_logo(self, parent_frame):
        """Lädt das passende Logo basierend auf dem aktuellen Theme"""
        try:
            from PIL import Image, ImageTk
            from core.theme import get_logo_filename
            import os
            
            # Logo-Dateiname basierend auf Theme
            logo_filename = get_logo_filename()
            logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", logo_filename)
            
            # Logo laden und skalieren
            logo_image = Image.open(logo_path)
            
            # Logo auf passende Größe skalieren (Höhe: 28px, Breite proportional)
            logo_height = 28
            logo_width = int((logo_image.width * logo_height) / logo_image.height)
            logo_image = logo_image.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
            
            # PhotoImage erstellen
            self.logo_photo = ImageTk.PhotoImage(logo_image)
            
            # Logo Label erstellen oder aktualisieren
            if hasattr(self, 'logo_label'):
                self.logo_label.configure(image=self.logo_photo)
            else:
                self.logo_label = ttk.Label(parent_frame, image=self.logo_photo, style="TLabel")
                self.logo_label.pack(side="left", padx=(0, 10))
            
        except Exception as e:
            logger.warning(f"Bertrandt Logo konnte nicht geladen werden: {e}")
            # Fallback: Canvas Badge
            if not hasattr(self, 'logo_badge'):
                self.logo_badge = tk.Canvas(parent_frame, width=28, height=28, bg=THEME_VARS["panel"], highlightthickness=0)
                self.logo_badge.pack(side="left", padx=(0, 10))
            
            self.logo_badge.configure(bg=THEME_VARS["panel"])
            self.logo_badge.delete("all")
            self.logo_badge.create_rectangle(2, 2, 26, 26, outline="", fill=_mix(THEME_VARS["brand_600"], THEME_VARS["brand_500"], 0.5))

    def toggle_theme(self):
        """Wechselt zwischen Dark und Light Theme"""
        from core.theme import toggle_theme, apply_bertrandt_theme
        
        # Theme wechseln
        new_theme = toggle_theme()
        
        # Theme auf die Anwendung anwenden
        apply_bertrandt_theme(self.root, reapply=True)
        
        # Styles neu anwenden
        self.setup_styles()
        
        # Logo neu laden
        if hasattr(self, 'logo_label'):
            parent = self.logo_label.master
            self.load_logo(parent)
        
        # Alle Tabs über Theme-Wechsel benachrichtigen
        self.refresh_all_tabs()
        
        # Toast anzeigen
        from core.theme import _toast
        theme_name = "Hell" if new_theme == "light" else "Dunkel"
        _toast(self.root, f"Theme gewechselt: {theme_name}")
        
        logger.info(f"Theme gewechselt zu: {new_theme}")
    
    def show_system_status(self):
        """Zeigt System-Status in einem Toast mit Web-Server Info"""
        from core.theme import _toast
        web_status = "aktiv" if self.web_server_status else "inaktiv"
        _toast(self.root, f"System läuft optimal - Web-Server: {web_status}")
    
    def update_navbar_active_tab(self, active_tab):
        """Aktualisiert die aktive Tab-Anzeige in der Navbar"""
        for tab_name, button in self.nav_buttons.items():
            if tab_name == active_tab:
                button.configure(style="Primary.TButton")
            else:
                button.configure(style="Ghost.TButton")
    
    def setup_tabs(self):
        """Initialisiert alle Tab-Komponenten"""
        # Импортируем DemoTab
        from ui.tabs.demo_tab import DemoTab
        
        self.tabs = {
            'home': HomeTab(self.tab_content_frame, self),
            'demo': DemoTab(self.tab_content_frame, self),
            'creator': CreatorTab(self.tab_content_frame, self),
            'presentation': PresentationTab(self.tab_content_frame, self)
        }
        
        # Все Tabs изначально скрыть
        for tab in self.tabs.values():
            tab.hide()
    
    def switch_tab(self, tab_name):
        """Переключение между tabs с автоматическим сохранением и синхронизацией веб-сервера"""
        try:
            # Сохранить текущие изменения в Creator перед переключением
            if (hasattr(self, 'tabs') and 'creator' in self.tabs and 
                hasattr(self.tabs['creator'], 'save_current_slide_content') and
                self.current_tab == 'creator'):
                self.tabs['creator'].save_current_slide_content()
            
            # Скрыть текущий tab
            if hasattr(self, 'tabs') and self.current_tab in self.tabs:
                self.tabs[self.current_tab].hide()
            
            # Показать новый tab
            if hasattr(self, 'tabs') and tab_name in self.tabs:
                self.tabs[tab_name].show()
                
                # Обновить контент в новом tab
                if tab_name == 'demo' and hasattr(self.tabs['demo'], 'load_current_slide'):
                    self.tabs['demo'].load_current_slide()
                    # Синхронизировать веб-сервер с текущим слайдом demo
                    if self.web_server_status:
                        current_slide = getattr(self.tabs['demo'], 'current_slide', 1)
                        web_server.set_current_slide(current_slide)
                elif tab_name == 'creator' and hasattr(self.tabs['creator'], 'load_slide_to_editor'):
                    current_slide = getattr(self.tabs['creator'], 'current_edit_slide', 1)
                    self.tabs['creator'].load_slide_to_editor(current_slide)
            
            # Обновить navbar navigation
            self.update_navbar_active_tab(tab_name)
            
            self.current_tab = tab_name
            logger.debug(f"Switched to {tab_name} tab with web server synchronization")
            
        except Exception as e:
            logger.error(f"Error switching to {tab_name} tab: {e}")
    
    def toggle_fullscreen(self, event=None):
        """Wechselt zwischen Vollbild und Fenster-Modus"""
        self.fullscreen = not self.fullscreen
        self.root.attributes('-fullscreen', self.fullscreen)
        logger.debug(f"Vollbild: {'aktiviert' if self.fullscreen else 'deaktiviert'}")
    
    def exit_fullscreen(self, event=None):
        """Verlässt den Vollbild-Modus (aber bleibt auf Hauptmonitor)"""
        if self.fullscreen:
            self.fullscreen = False
            self.root.attributes('-fullscreen', False)
            self.root.attributes('-topmost', False)  # Topmost deaktivieren
            
            # Fenster auf Hauptmonitor in normaler Größe
            self.root.geometry(f"{self.primary_width}x{self.primary_height}+{self.primary_x}+{self.primary_y}")
            logger.debug("Vollbild deaktiviert - bleibt auf Hauptmonitor")
    
    def restart_application(self):
        """Startet die Anwendung neu"""
        logger.info("Anwendung wird neu gestartet...")
        
        # Веб-сервер остановить
        if self.web_server_status:
            web_server.stop_server()
        
        subprocess.Popen([sys.executable] + sys.argv)
        self.quit_application()
    
    def quit_application(self):
        """Beendet die Anwendung"""
        logger.info("Anwendung wird beendet...")
        
        # Веб-сервер остановить
        if self.web_server_status:
            web_server.stop_server()
        
        # Hardware-Verbindungen trennen
        from models.hardware import hardware_manager
        hardware_manager.disconnect_all()
        
        # Demo stoppen
        from services.demo import demo_service
        demo_service.stop_demo()
        
        # GUI schließen
        self.root.quit()
        sys.exit(0)
    
    def run(self):
        """Startet die GUI-Hauptschleife"""
        try:
            logger.info("GUI-Hauptschleife gestartet")
            self.root.mainloop()
        except KeyboardInterrupt:
            logger.info("Anwendung durch Benutzer unterbrochen")
            self.quit_application()
        except Exception as e:
            logger.error(f"Unerwarteter Fehler in GUI-Hauptschleife: {e}")
            self.quit_application()
