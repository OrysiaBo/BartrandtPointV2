#!/usr/bin/env python3
"""
Demo Tab für die Bertrandt GUI - С ПОЛНОЭКРАННЫМ РЕЖИМОМ
Презентационный режим с Slide-Navigation и автоматическим управлением
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from core.theme import theme_manager
from core.logger import logger
from ui.components.slide_renderer import SlideRenderer
from models.content import content_manager
from services.demo import demo_service

class DemoTab:
    """Demo-Tab для Live-Презентаций с полноэкранным режимом"""
    
    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window
        self.visible = False
        self.current_slide = 1
        self.total_slides = 10
        self.auto_play = False
        self.auto_play_interval = 5  # Секунды
        self.auto_play_thread = None
        self.slide_buttons = {}
        self.last_update_time = 0
        
        # Полноэкранный режим
        self.fullscreen_window = None
        self.is_fullscreen_mode = False
        
        # Demo-Service конфигурация
        self.demo_running = False
        
        self.create_demo_content()
        
        # Content-Manager Observer добавить
        content_manager.add_observer(self.on_content_changed)
        
    def on_content_changed(self, slide_id, slide_data, action='update'):
        """Обработчик изменения контента (синхронизация с Creator) - оптимизированный"""
        try:
            current_time = time.time()
            # Ограничение частоты обновлений - не больше раза в секунду
            if current_time - self.last_update_time < 1.0:
                return
            
            if action == 'update' or action == 'load':
                # Обновлять список слайдов только если изменился заголовок
                if hasattr(slide_data, 'title'):
                    current_button = self.slide_buttons.get(slide_id)
                    if current_button:
                        # Обновить только конкретную кнопку
                        title = slide_data.title
                        display_title = title[:20] + "..." if len(title) > 20 else title
                        current_button.configure(text=f"{slide_id}\n{display_title}")
                    else:
                        # Полностью пересоздать список только если кнопки не существует
                        self.create_slides_list()
                
                # Перерисовать текущий слайд если он был изменен
                if slide_id == self.current_slide:
                    self.render_current_slide()
                    # Также обновить полноэкранный режим если активен
                    if self.is_fullscreen_mode and self.fullscreen_window:
                        self.update_fullscreen_slide()
                
                self.last_update_time = current_time
                logger.debug(f"Demo synchronized with content changes for slide {slide_id}")
                
            elif action == 'delete':
                # Обработать удаление слайда
                if slide_id == self.current_slide and self.current_slide > 1:
                    self.current_slide -= 1
                
                self.create_slides_list()
                self.load_current_slide()
        
        except Exception as e:
            logger.error(f"Error handling content change in demo: {e}")
        
    def create_demo_content(self):
        """Создает контент Demo-Tab"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        # Главный контейнер
        self.container = tk.Frame(self.parent, bg=colors['background_primary'])
        
        # Header-Toolbar
        self.create_demo_header()
        
        # 2-колоночный Layout
        content_frame = tk.Frame(self.container, bg=colors['background_primary'])
        content_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Grid-Layout
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=0, minsize=300)  # Slide-Navigation (слева)
        content_frame.grid_columnconfigure(1, weight=1, minsize=900)  # Slide-Display (справа)
        
        # Колонка 1: Slide-Navigation
        self.create_slide_navigation(content_frame)
        
        # Колонка 2: Haupt-Display
        self.create_slide_display(content_frame)
        
        # Footer с Controls
        self.create_demo_footer()
    
    def create_demo_header(self):
        """Создает Demo-Header с кнопкой полноэкранного режима"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        header_frame = tk.Frame(
            self.container,
            bg=colors['background_secondary'],
            relief='flat',
            bd=0,
            height=80
        )
        header_frame.pack(fill='x', padx=10, pady=(10, 5))
        header_frame.pack_propagate(False)
        
        # Заголовок
        title_frame = tk.Frame(header_frame, bg=colors['background_secondary'])
        title_frame.pack(side='left', fill='y', padx=(15, 30))
        
        title_label = tk.Label(
            title_frame,
            text="🎯 Live Demo",
            font=fonts['title'],
            fg=colors['accent_primary'],
            bg=colors['background_secondary']
        )
        title_label.pack(anchor='w', pady=(15, 0))
        
        subtitle_label = tk.Label(
            title_frame,
            text="Interaktive Präsentation",
            font=fonts['caption'],
            fg=colors['text_secondary'],
            bg=colors['background_secondary']
        )
        subtitle_label.pack(anchor='w')
        
        # Demo-Управление
        controls_frame = tk.Frame(header_frame, bg=colors['background_secondary'])
        controls_frame.pack(side='left', fill='y', padx=20)
        
        # Start/Stop Demo
        self.demo_button = tk.Button(
            controls_frame,
            text="▶ Demo starten",
            font=fonts['button'],
            bg=colors['accent_secondary'],
            fg='white',
            relief='flat',
            bd=0,
            padx=20,
            pady=10,
            cursor='hand2',
            command=self.toggle_demo
        )
        self.demo_button.pack(side='left', padx=(0, 10), pady=15)
        
        # Auto-Play Toggle
        self.autoplay_button = tk.Button(
            controls_frame,
            text="🔄 Auto-Play",
            font=fonts['button'],
            bg=colors['background_tertiary'],
            fg=colors['text_primary'],
            relief='flat',
            bd=0,
            padx=20,
            pady=10,
            cursor='hand2',
            command=self.toggle_autoplay
        )
        self.autoplay_button.pack(side='left', padx=(0, 10), pady=15)
        
        # НОВАЯ КНОПКА: Полноэкранный режим
        self.fullscreen_button = tk.Button(
            controls_frame,
            text="🖥️ Vollbild",
            font=fonts['button'],
            bg=colors['accent_primary'],
            fg='white',
            relief='flat',
            bd=0,
            padx=20,
            pady=10,
            cursor='hand2',
            command=self.toggle_presentation_fullscreen
        )
        self.fullscreen_button.pack(side='left', padx=(0, 10), pady=15)
        
        # Slide-Info
        info_frame = tk.Frame(header_frame, bg=colors['background_secondary'])
        info_frame.pack(side='right', fill='y', padx=(20, 15))
        
        self.slide_info_label = tk.Label(
            info_frame,
            text="Slide 1 von 10",
            font=fonts['subtitle'],
            fg=colors['text_primary'],
            bg=colors['background_secondary']
        )
        self.slide_info_label.pack(pady=(20, 5))
        
        # Progress Bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            info_frame,
            variable=self.progress_var,
            maximum=100,
            length=150,
            mode='determinate'
        )
        self.progress_bar.pack()
    
    def create_slide_navigation(self, parent):
        """Создает Slide-Navigation (слева)"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        # Navigation Frame
        nav_frame = tk.Frame(
            parent,
            bg=colors['background_secondary'],
            relief='solid',
            bd=1,
            width=300
        )
        nav_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 5))
        nav_frame.grid_propagate(False)
        
        # Header
        nav_header = tk.Frame(nav_frame, bg=colors['background_secondary'])
        nav_header.pack(fill='x', padx=15, pady=(15, 10))
        
        header_label = tk.Label(
            nav_header,
            text="📑 Folien-Übersicht",
            font=fonts['title'],
            fg=colors['text_primary'],
            bg=colors['background_secondary']
        )
        header_label.pack(anchor='w')
        
        # Navigation Buttons
        nav_buttons_frame = tk.Frame(nav_header, bg=colors['background_secondary'])
        nav_buttons_frame.pack(fill='x', pady=(10, 0))
        
        prev_btn = tk.Button(
            nav_buttons_frame,
            text="◀",
            font=fonts['button'],
            bg=colors['accent_primary'],
            fg='white',
            relief='flat',
            bd=0,
            width=3,
            pady=5,
            cursor='hand2',
            command=self.previous_slide
        )
        prev_btn.pack(side='left', padx=(0, 5))
        
        next_btn = tk.Button(
            nav_buttons_frame,
            text="▶",
            font=fonts['button'],
            bg=colors['accent_primary'],
            fg='white',
            relief='flat',
            bd=0,
            width=3,
            pady=5,
            cursor='hand2',
            command=self.next_slide
        )
        next_btn.pack(side='left', padx=(5, 0))
        
        # Slides List Container
        list_frame = tk.Frame(nav_frame, bg=colors['background_secondary'])
        list_frame.pack(fill='both', expand=True, padx=15, pady=(10, 15))
        
        # Scrollable Slides List
        canvas = tk.Canvas(list_frame, bg=colors['background_secondary'], highlightthickness=0)
        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.slides_frame = tk.Frame(canvas, bg=colors['background_secondary'])
        
        self.slides_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.slides_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=(0, 5))
        scrollbar.pack(side="right", fill="y")
        
        # Создать slides
        self.create_slides_list()
    
    def create_slides_list(self):
        """Создает Slides-Liste оптимизированный"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        # Content-Manager использовать
        slides = content_manager.get_all_slides()
        
        if not slides:
            logger.warning("Keine Slides gefunden für Demo")
            return
        
        # Удалить только если полностью новая структура нужна
        if len(self.slide_buttons) != len(slides):
            for widget in self.slides_frame.winfo_children():
                widget.destroy()
            self.slide_buttons.clear()
        
        for slide_id, slide in slides.items():
            try:
                # Проверить есть ли Button уже
                if slide_id in self.slide_buttons:
                    # Обновить только текст
                    button = self.slide_buttons[slide_id]
                    title = slide.title
                    display_title = title[:20] + "..." if len(title) > 20 else title
                    button.configure(text=f"{slide_id}\n{display_title}")
                    continue
                
                # Создать новый Button только если нужно
                slide_container = tk.Frame(
                    self.slides_frame,
                    bg=colors['background_secondary']
                )
                slide_container.pack(fill='x', pady=2)
                
                # Button Style в зависимости от активности
                is_active = slide_id == self.current_slide
                bg_color = colors['accent_primary'] if is_active else colors['background_tertiary']
                
                title = slide.title
                display_title = title[:20] + "..." if len(title) > 20 else title
                
                slide_btn = tk.Button(
                    slide_container,
                    text=f"{slide_id}\n{display_title}",
                    font=fonts['body'],
                    bg=bg_color,
                    fg='white' if is_active else colors['text_primary'],
                    relief='flat',
                    bd=0,
                    width=25,
                    height=3,
                    cursor='hand2',
                    command=lambda sid=slide_id: self.goto_slide(sid),
                    justify='left',
                    anchor='w'
                )
                slide_btn.pack(fill='x', ipady=3)
                
                self.slide_buttons[slide_id] = slide_btn
                
            except Exception as e:
                logger.error(f"Fehler beim Erstellen von Slide-Button {slide_id}: {e}")
        
        # Total slides обновить
        self.total_slides = len(slides)
        self.update_slide_info()
    
    def create_slide_display(self, parent):
        """Создает Haupt-Slide-Display (справа)"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        # Display Frame
        display_frame = tk.Frame(
            parent,
            bg=colors['background_secondary'],
            relief='solid',
            bd=1
        )
        display_frame.grid(row=0, column=1, sticky='nsew', padx=5)
        
        # Header
        display_header = tk.Frame(display_frame, bg=colors['background_secondary'])
        display_header.pack(fill='x', padx=20, pady=(15, 10))
        
        self.current_slide_label = tk.Label(
            display_header,
            text="Demo-Folie wird geladen...",
            font=fonts['display'],
            fg=colors['text_primary'],
            bg=colors['background_secondary']
        )
        self.current_slide_label.pack(anchor='w')
        
        # Slide Canvas - Основной дисплей
        canvas_frame = tk.Frame(display_frame, bg=colors['background_secondary'])
        canvas_frame.pack(fill='both', expand=True, padx=10, pady=(10, 10))
        
        # Создать Slide Canvas
        self.slide_canvas = tk.Canvas(
            canvas_frame,
            bg='#FFFFFF',  # Белый для слайдов
            relief='flat',
            bd=2,
            highlightthickness=0
        )
        self.slide_canvas.pack(fill='both', expand=True)
        
        # Отслеживать размер Canvas
        self.slide_canvas.bind('<Configure>', self.on_canvas_resize)
        
        # Начальный Slide загрузить
        self.slide_canvas.after(100, self.load_current_slide)
    
    def create_demo_footer(self):
        """Создает Demo-Footer"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        footer_frame = tk.Frame(
            self.container,
            bg=colors['background_secondary'],
            height=50
        )
        footer_frame.pack(fill='x', padx=10, pady=5)
        footer_frame.pack_propagate(False)
        
        # Слева: Timer-Info
        timer_frame = tk.Frame(footer_frame, bg=colors['background_secondary'])
        timer_frame.pack(side='left', fill='y', padx=15)
        
        self.timer_label = tk.Label(
            timer_frame,
            text="Demo bereit",
            font=fonts['caption'],
            fg=colors['text_secondary'],
            bg=colors['background_secondary']
        )
        self.timer_label.pack(pady=15)
        
        # Справа: Vollbild Controls
        controls_frame = tk.Frame(footer_frame, bg=colors['background_secondary'])
        controls_frame.pack(side='right', fill='y', padx=15)
        
        # Кнопка полноэкранного режима приложения (не презентации)
        app_fullscreen_btn = tk.Button(
            controls_frame,
            text="⛶ App Vollbild",
            font=fonts['caption'],
            bg=colors['background_tertiary'],
            fg=colors['text_primary'],
            relief='flat',
            bd=0,
            padx=15,
            pady=8,
            cursor='hand2',
            command=self.main_window.toggle_fullscreen
        )
        app_fullscreen_btn.pack(pady=8)
    
    def toggle_presentation_fullscreen(self):
        """Переключает полноэкранный режим презентации"""
        try:
            if not self.is_fullscreen_mode:
                self.enter_presentation_fullscreen()
            else:
                self.exit_presentation_fullscreen()
        except Exception as e:
            logger.error(f"Error toggling presentation fullscreen: {e}")
    
    def enter_presentation_fullscreen(self):
        """Входит в полноэкранный режим презентации"""
        try:
            # Создать новое полноэкранное окно
            self.fullscreen_window = tk.Toplevel(self.main_window.root)
            self.fullscreen_window.title("Bertrandt Präsentation - Vollbild")
            
            # Настройки полноэкранного окна
            self.fullscreen_window.attributes('-fullscreen', True)
            self.fullscreen_window.attributes('-topmost', True)
            self.fullscreen_window.configure(bg='black')
            
            # Canvas для слайда во весь экран
            self.fullscreen_canvas = tk.Canvas(
                self.fullscreen_window,
                bg='#FFFFFF',
                highlightthickness=0,
                bd=0
            )
            self.fullscreen_canvas.pack(fill='both', expand=True)
            
            # Управление с клавиатуры
            self.fullscreen_window.bind('<KeyPress>', self.on_fullscreen_key)
            self.fullscreen_window.bind('<Button-1>', self.on_fullscreen_click)
            self.fullscreen_window.focus_set()
            
            # Обработчик закрытия
            self.fullscreen_window.protocol("WM_DELETE_WINDOW", self.exit_presentation_fullscreen)
            
            # Отрисовать текущий слайд
            self.fullscreen_window.after(100, self.update_fullscreen_slide)
            
            self.is_fullscreen_mode = True
            
            # Обновить кнопку
            self.fullscreen_button.configure(
                text="📱 Fenster",
                bg=theme_manager.get_colors()['accent_warning']
            )
            
            logger.info("Presentation fullscreen mode activated")
            
        except Exception as e:
            logger.error(f"Error entering presentation fullscreen: {e}")
    
    def exit_presentation_fullscreen(self):
        """Выходит из полноэкранного режима презентации"""
        try:
            if self.fullscreen_window:
                self.fullscreen_window.destroy()
                self.fullscreen_window = None
            
            self.is_fullscreen_mode = False
            
            # Восстановить кнопку
            self.fullscreen_button.configure(
                text="🖥️ Vollbild",
                bg=theme_manager.get_colors()['accent_primary']
            )
            
            logger.info("Presentation fullscreen mode deactivated")
            
        except Exception as e:
            logger.error(f"Error exiting presentation fullscreen: {e}")
    
    def on_fullscreen_key(self, event):
        """Обработчик клавиш в полноэкранном режиме"""
        try:
            if event.keysym == 'Escape':
                self.exit_presentation_fullscreen()
            elif event.keysym in ['Right', 'space', 'Next']:
                self.next_slide()
            elif event.keysym in ['Left', 'Prior']:
                self.previous_slide()
            elif event.keysym == 'F5':
                self.toggle_demo()
            elif event.keysym.isdigit():
                slide_num = int(event.keysym)
                if 1 <= slide_num <= self.total_slides:
                    self.goto_slide(slide_num)
        except Exception as e:
            logger.error(f"Error handling fullscreen key: {e}")
    
    def on_fullscreen_click(self, event):
        """Обработчик кликов в полноэкранном режиме - переход к следующему слайду"""
        try:
            self.next_slide()
        except Exception as e:
            logger.error(f"Error handling fullscreen click: {e}")
    
    def update_fullscreen_slide(self):
        """Обновляет слайд в полноэкранном режиме"""
        try:
            if not self.is_fullscreen_mode or not self.fullscreen_window or not self.fullscreen_canvas:
                return
            
            slide = content_manager.get_slide(self.current_slide)
            if not slide:
                return
            
            # Получить размеры полноэкранного canvas
            self.fullscreen_window.update_idletasks()
            canvas_width = self.fullscreen_canvas.winfo_width()
            canvas_height = self.fullscreen_canvas.winfo_height()
            
            if canvas_width > 10 and canvas_height > 10:
                # Подготовить данные слайда
                slide_data = {
                    'title': slide.title,
                    'content': slide.content,
                    'slide_number': self.current_slide,
                    'background_color': '#FFFFFF',
                    'text_color': '#1F1F1F'
                }
                
                # Использовать тот же рендерер
                SlideRenderer.render_slide_to_canvas(
                    self.fullscreen_canvas,
                    slide_data,
                    canvas_width,
                    canvas_height
                )
                
                logger.debug(f"Updated fullscreen slide {self.current_slide}")
                
        except Exception as e:
            logger.error(f"Error updating fullscreen slide: {e}")
    
    def load_current_slide(self):
        """Загружает и показывает текущий слайд"""
        try:
            slide = content_manager.get_slide(self.current_slide)
            
            if slide:
                # Обновить заголовок слайда
                self.current_slide_label.configure(text=f"Demo-Folie {self.current_slide}: {slide.title}")
                
                # Отрисовать слайд
                self.render_current_slide()
                
                # Обновить navigation
                self.update_slide_navigation()
                self.update_slide_info()
                
                logger.debug(f"Loaded slide {self.current_slide}: {slide.title}")
            else:
                logger.warning(f"Slide {self.current_slide} not found")
                self.current_slide_label.configure(text=f"Slide {self.current_slide} nicht gefunden")
                
        except Exception as e:
            logger.error(f"Error loading slide {self.current_slide}: {e}")
    
    def render_current_slide(self):
        """Рендерит текущий слайд на Canvas"""
        try:
            slide = content_manager.get_slide(self.current_slide)
            
            if not slide:
                return
            
            # Получить размер Canvas
            canvas_width = self.slide_canvas.winfo_width()
            canvas_height = self.slide_canvas.winfo_height()
            
            if canvas_width > 10 and canvas_height > 10:
                # Подготовить данные слайда
                slide_data = {
                    'title': slide.title,
                    'content': slide.content,
                    'slide_number': self.current_slide,
                    'background_color': '#FFFFFF',
                    'text_color': '#1F1F1F'
                }
                
                # Слайд с тем же рендерером что Creator рендерить
                SlideRenderer.render_slide_to_canvas(
                    self.slide_canvas,
                    slide_data,
                    canvas_width,
                    canvas_height
                )
                
                logger.debug(f"Rendered slide {self.current_slide} in demo")
            
        except Exception as e:
            logger.error(f"Error rendering slide: {e}")
    
    def on_canvas_resize(self, event):
        """Обработчик изменения размера Canvas"""
        # Перерисовать слайд при изменении размера
        self.main_window.root.after(100, self.render_current_slide)
    
    def update_slide_navigation(self):
        """Обновляет Slide-Navigation Buttons"""
        colors = theme_manager.get_colors()
        
        for slide_id, button in self.slide_buttons.items():
            if slide_id == self.current_slide:
                button.configure(
                    bg=colors['accent_primary'],
                    fg='white'
                )
            else:
                button.configure(
                    bg=colors['background_tertiary'],
                    fg=colors['text_primary']
                )
    
    def update_slide_info(self):
        """Обновляет Slide-Information"""
        try:
            self.slide_info_label.configure(text=f"Slide {self.current_slide} von {self.total_slides}")
            
            # Обновить Progress Bar
            if self.total_slides > 0:
                progress = (self.current_slide / self.total_slides) * 100
                self.progress_var.set(progress)
        except Exception as e:
            logger.error(f"Error updating slide info: {e}")
    
    def goto_slide(self, slide_id):
        """Переходит к определенному слайду"""
        try:
            self.current_slide = slide_id
            self.load_current_slide()
            
            # Обновить полноэкранный режим если активен
            if self.is_fullscreen_mode:
                self.update_fullscreen_slide()
                
            logger.info(f"Demo: Navigated to slide {slide_id}")
        except Exception as e:
            logger.error(f"Error going to slide {slide_id}: {e}")
    
    def previous_slide(self):
        """Переходит к предыдущему слайду"""
        if self.current_slide > 1:
            self.current_slide -= 1
            self.load_current_slide()
            
            # Обновить полноэкранный режим если активен
            if self.is_fullscreen_mode:
                self.update_fullscreen_slide()
    
    def next_slide(self):
        """Переходит к следующему слайду"""
        if self.current_slide < self.total_slides:
            self.current_slide += 1
            self.load_current_slide()
        elif self.auto_play:  # Restart при Auto-Play
            self.current_slide = 1
            self.load_current_slide()
        
        # Обновить полноэкранный режим если активен
        if self.is_fullscreen_mode:
            self.update_fullscreen_slide()
    
    def toggle_demo(self):
        """Запускает или останавливает Demo"""
        colors = theme_manager.get_colors()
        
        if not self.demo_running:
            # Запустить Demo
            self.demo_running = True
            demo_service.start_demo(self.current_slide)
            
            self.demo_button.configure(
                text="⏹ Demo stoppen",
                bg=colors['accent_warning']
            )
            
            self.timer_label.configure(text="Demo läuft...")
            logger.info("Demo gestartet")
            
        else:
            # Остановить Demo
            self.demo_running = False
            demo_service.stop_demo()
            
            self.demo_button.configure(
                text="▶ Demo starten",
                bg=colors['accent_secondary']
            )
            
            self.timer_label.configure(text="Demo bereit")
            self.stop_autoplay()
            logger.info("Demo gestoppt")
    
    def toggle_autoplay(self):
        """Включает/выключает Auto-Play"""
        colors = theme_manager.get_colors()
        
        if not self.auto_play:
            self.start_autoplay()
            self.autoplay_button.configure(
                text="⏸ Auto-Play",
                bg=colors['accent_primary']
            )
        else:
            self.stop_autoplay()
            self.autoplay_button.configure(
                text="🔄 Auto-Play",
                bg=colors['background_tertiary']
            )
    
    def start_autoplay(self):
        """Запускает Auto-Play"""
        self.auto_play = True
        self.auto_play_thread = threading.Thread(target=self.autoplay_worker, daemon=True)
        self.auto_play_thread.start()
        logger.info("Auto-Play gestartet")
    
    def stop_autoplay(self):
        """Останавливает Auto-Play"""
        self.auto_play = False
        if self.auto_play_thread and self.auto_play_thread.is_alive():
            self.auto_play_thread.join(timeout=0.5)
        logger.info("Auto-Play gestoppt")
    
    def autoplay_worker(self):
        """Auto-Play Worker-Thread"""
        while self.auto_play:
            time.sleep(self.auto_play_interval)
            if self.auto_play:  # Еще раз проверить после sleep
                self.main_window.root.after(0, self.next_slide)
    
    def refresh_theme(self):
        """Обновляет тему для Demo-Tab"""
        try:
            colors = theme_manager.get_colors()
            
            if hasattr(self, 'container'):
                self.container.configure(bg=colors['background_primary'])
            
            # Заново создать Slides-Liste для обновления темы
            self.create_slides_list()
            
            logger.debug("Demo-Tab Theme обновлен")
        except Exception as e:
            logger.error(f"Error refreshing demo theme: {e}")
    
    def show(self):
        """Показывает Demo-Tab"""
        if not self.visible:
            self.container.pack(fill='both', expand=True)
            self.visible = True
            
            # Загрузить текущий слайд
            self.load_current_slide()
            
            logger.debug("Demo-Tab angezeigt")
    
    def hide(self):
        """Скрывает Demo-Tab"""
        if self.visible:
            # Остановить Demo если запущен
            if self.demo_running:
                self.toggle_demo()
            
            # Выйти из полноэкранного режима если активен
            if self.is_fullscreen_mode:
                self.exit_presentation_fullscreen()
            
            self.container.pack_forget()
            self.visible = False
            logger.debug("Demo-Tab versteckt")
