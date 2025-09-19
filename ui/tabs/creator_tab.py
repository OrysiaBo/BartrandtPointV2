#!/usr/bin/env python3
"""
Creator Tab für die Bertrandt GUI - ИСПРАВЛЕННАЯ ВЕРСИЯ
3-Spalten Drag & Drop Editor для Demo-Folien с улучшенным сохранением изображений
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import json
import base64
import tempfile
import shutil
from io import BytesIO
from PIL import Image, ImageTk
from core.theme import theme_manager
from core.logger import logger
from ui.components.slide_renderer import SlideRenderer
from models.content import content_manager
from datetime import datetime

class CreatorTab:
    """3-Spalten Creator-Tab для Demo-Folien Bearbeitung с улучшенным сохранением"""
    
    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window
        self.visible = False
        self.current_edit_slide = 1
        self.current_slide = None
        self.auto_save_timer_id = None
        self.edit_mode = False
        self.edit_widgets = {}
        self.manual_save = False
        
        # Drag & Drop переменные
        self.drag_data = {'element_type': None, 'widget': None}
        self.slide_width = 1920
        self.slide_height = 1080
        self.scale_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0
        
        # Папка для сохранения изображений
        self.images_dir = os.path.join("data", "images")
        os.makedirs(self.images_dir, exist_ok=True)
        
        self.create_creator_content()
        self.schedule_auto_save()
        
    def schedule_auto_save(self):
        """Планирует автоматическое сохранение через 3 секунды"""
        if self.auto_save_timer_id:
            self.main_window.root.after_cancel(self.auto_save_timer_id)
        self.auto_save_timer_id = self.main_window.root.after(3000, self.auto_save_presentation)

    def manual_save_slide(self):
        """Ручное сохранение слайда"""
        self.manual_save = True
        self.save_current_slide_content()

    def save_image_to_file(self, pil_image, slide_id, element_id=None):
        """Сохраняет изображение в файл и возвращает путь"""
        try:
            if element_id is None:
                element_id = datetime.now().strftime("%H%M%S")
            
            filename = f"slide_{slide_id}_{element_id}.png"
            filepath = os.path.join(self.images_dir, filename)
            
            # Сохранить изображение в файл
            pil_image.save(filepath, format='PNG')
            logger.debug(f"Image saved to: {filepath}")
            
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving image to file: {e}")
            return None

    def load_image_from_file(self, filepath):
        """Загружает изображение из файла"""
        try:
            if os.path.exists(filepath):
                return Image.open(filepath)
            else:
                logger.warning(f"Image file not found: {filepath}")
                return None
        except Exception as e:
            logger.error(f"Error loading image from file: {e}")
            return None

    def save_current_slide_content(self):
        """Сохраняет контент текущего слайда с улучшенным сохранением изображений"""
        try:
            if not hasattr(self, 'current_slide') or not self.current_slide:
                logger.warning("No current slide to save")
                return False
            
            title_text = ""
            content_text = ""
            canvas_elements = []
            
            if self.edit_mode and hasattr(self, 'edit_widgets'):
                # Режим редактирования - получать из виджетов
                if 'title' in self.edit_widgets:
                    title_text = self.edit_widgets['title'].get('1.0', 'end-1c')
                if 'content' in self.edit_widgets:
                    content_text = self.edit_widgets['content'].get('1.0', 'end-1c')
            else:
                # Режим предварительного просмотра - получать из canvas widgets
                for item in self.slide_canvas.find_all():
                    if self.slide_canvas.type(item) == 'window':
                        try:
                            widget = self.slide_canvas.nametowidget(self.slide_canvas.itemcget(item, 'window'))
                            coords = self.slide_canvas.coords(item)
                            
                            if isinstance(widget, tk.Label) and hasattr(widget, 'image'):
                                # Это изображение - сохранить данные о нем
                                try:
                                    # Получить изображение из PhotoImage
                                    if hasattr(widget, '_pil_image'):
                                        pil_image = widget._pil_image
                                    else:
                                        # Попробовать восстановить из PhotoImage
                                        pil_image = ImageTk.getimage(widget.image)
                                        widget._pil_image = pil_image  # Сохранить для следующего раза
                                    
                                    # Сохранить изображение в файл
                                    element_id = str(len(canvas_elements))
                                    image_filepath = self.save_image_to_file(pil_image, self.current_edit_slide, element_id)
                                    
                                    if image_filepath:
                                        image_data = {
                                            'type': 'image',
                                            'x': coords[0] if coords else 0,
                                            'y': coords[1] if coords else 0,
                                            'width': widget.winfo_width(),
                                            'height': widget.winfo_height(),
                                            'file_path': image_filepath,
                                            'relative_path': os.path.relpath(image_filepath, self.images_dir)
                                        }
                                        
                                        canvas_elements.append(image_data)
                                        
                                except Exception as e:
                                    logger.error(f"Error saving image element: {e}")
                                    
                            elif isinstance(widget, tk.Text):
                                text_content = widget.get('1.0', 'end-1c')
                                
                                # Определить тип на основе font или позиции
                                font = widget.cget('font')
                                if isinstance(font, tuple) and len(font) >= 2:
                                    font_size = font[1] if isinstance(font[1], int) else int(font[1])
                                    
                                    # Большой шрифт = заголовок
                                    if font_size >= 20 or 'bold' in str(font):
                                        if not title_text:  # Первый большой текст = заголовок
                                            title_text = text_content
                                        else:
                                            content_text += text_content + "\n"
                                    else:
                                        content_text += text_content + "\n"
                                else:
                                    content_text += text_content + "\n"
                                
                                # Сохранить позицию текста
                                canvas_elements.append({
                                    'type': 'text',
                                    'content': text_content,
                                    'x': coords[0] if coords else 0,
                                    'y': coords[1] if coords else 0,
                                    'font': font
                                })
                                    
                        except Exception as e:
                            logger.debug(f"Could not process canvas widget: {e}")
                            continue
            
            # Очистить лишние переносы строк
            content_text = content_text.strip()
            
            # Если не нашли заголовок, использовать первую строку контента
            if not title_text and content_text:
                lines = content_text.split('\n')
                title_text = lines[0] if lines else f"Demo-Folie {self.current_edit_slide}"
                content_text = '\n'.join(lines[1:]) if len(lines) > 1 else ""
            
            # Если все еще нет заголовка, использовать по умолчанию
            if not title_text:
                title_text = f"Demo-Folie {self.current_edit_slide}"
            
            # Сохранить через content_manager для синхронизации
            success = content_manager.update_slide_content(
                self.current_edit_slide,
                title_text,
                content_text,
                {'canvas_elements': canvas_elements} if canvas_elements else None
            )
            
            if success:
                # Показать успешное сохранение только при ручном сохранении
                if hasattr(self, 'slide_info_label') and getattr(self, 'manual_save', False):
                    original_text = self.slide_info_label.cget('text')
                    self.slide_info_label.configure(
                        text=f"✅ Demo-Folie {self.current_edit_slide} gespeichert: {title_text[:30]}..."
                    )
                    
                    # Вернуть оригинальный текст через 2 секунды
                    def restore_text():
                        if hasattr(self, 'slide_info_label'):
                            self.slide_info_label.configure(text=original_text)
                    
                    self.main_window.root.after(2000, restore_text)
                    self.manual_save = False  # Сбросить флаг
                
                logger.info(f"Successfully saved slide {self.current_edit_slide}: {title_text[:30]}...")
            else:
                logger.error(f"Failed to save slide {self.current_edit_slide}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error saving current slide content: {e}")
            return False

    def restore_canvas_elements(self, canvas_elements):
        """Восстанавливает сохраненные элементы canvas с улучшенной загрузкой изображений"""
        try:
            if not canvas_elements:
                return
                
            for element in canvas_elements:
                if element['type'] == 'image':
                    self.restore_image_element(element)
                elif element['type'] == 'text':
                    self.restore_text_element(element)
                    
        except Exception as e:
            logger.error(f"Error restoring canvas elements: {e}")

    def restore_image_element(self, image_data):
        """Восстанавливает изображение с улучшенной обработкой файлов"""
        try:
            image = None
            
            # Попробовать загрузить из абсолютного пути
            if 'file_path' in image_data and os.path.exists(image_data['file_path']):
                try:
                    image = self.load_image_from_file(image_data['file_path'])
                except Exception as e:
                    logger.warning(f"Could not load image from absolute path: {e}")
            
            # Попробовать загрузить из относительного пути
            if image is None and 'relative_path' in image_data:
                try:
                    full_path = os.path.join(self.images_dir, image_data['relative_path'])
                    if os.path.exists(full_path):
                        image = self.load_image_from_file(full_path)
                except Exception as e:
                    logger.warning(f"Could not load image from relative path: {e}")
            
            # Если файлы недоступны, попробовать base64 данные (fallback)
            if image is None and 'image_data' in image_data:
                try:
                    image_bytes = base64.b64decode(image_data['image_data'])
                    image = Image.open(BytesIO(image_bytes))
                except Exception as e:
                    logger.warning(f"Could not load image from base64: {e}")
            
            if image:
                # Масштабировать изображение до разумного размера
                max_width, max_height = 400, 300
                image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                
                # Создать PhotoImage
                photo = ImageTk.PhotoImage(image)
                
                # Создать Label с изображением
                image_label = tk.Label(
                    self.slide_canvas,
                    image=photo,
                    bg='white',
                    relief='solid',
                    bd=1
                )
                image_label.image = photo  # Сохранить ссылку
                image_label._pil_image = image  # Сохранить PIL изображение для будущего использования
                
                if 'file_path' in image_data:
                    image_label.image_path = image_data['file_path']
                
                # Разместить на canvas в сохраненной позиции
                canvas_item = self.slide_canvas.create_window(
                    image_data['x'], image_data['y'],
                    window=image_label,
                    anchor='nw'
                )
                
                # Сделать изображение перемещаемым
                self.make_canvas_item_movable(image_label, canvas_item)
                
                logger.debug(f"Restored image at position ({image_data['x']}, {image_data['y']})")
            else:
                logger.warning("Could not restore image from any source")
            
        except Exception as e:
            logger.error(f"Error restoring image element: {e}")

    def add_image_element(self):
        """Добавляет изображение на слайд с улучшенной обработкой"""
        try:
            # Открыть диалог выбора файла
            file_path = filedialog.askopenfilename(
                title="Bild auswählen",
                filetypes=[
                    ("Bilddateien", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff"),
                    ("PNG", "*.png"),
                    ("JPEG", "*.jpg *.jpeg"),
                    ("GIF", "*.gif"),
                    ("Alle Dateien", "*.*")
                ]
            )
            
            if file_path:
                # Переключиться в режим редактирования если не в нем
                if not self.edit_mode:
                    self.toggle_edit_mode()
                
                # Загрузить и подготовить изображение
                original_image = Image.open(file_path)
                
                # Создать копию изображения в папке проекта
                element_id = datetime.now().strftime("%H%M%S%f")
                saved_image_path = self.save_image_to_file(original_image, self.current_edit_slide, element_id)
                
                if not saved_image_path:
                    messagebox.showerror("Fehler", "Bild konnte nicht gespeichert werden")
                    return
                
                # Масштабировать изображение до разумного размера для отображения
                display_image = original_image.copy()
                max_width, max_height = 400, 300
                display_image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                
                # Создать PhotoImage
                photo = ImageTk.PhotoImage(display_image)
                
                # Создать Label с изображением
                image_label = tk.Label(
                    self.slide_canvas,
                    image=photo,
                    bg='white',
                    relief='solid',
                    bd=1
                )
                image_label.image = photo  # Сохранить ссылку
                image_label._pil_image = original_image  # Сохранить оригинальное изображение
                image_label.image_path = saved_image_path  # Сохранить путь к файлу
                
                # Разместить на canvas
                canvas_item = self.slide_canvas.create_window(
                    200, 300,  # Начальная позиция
                    window=image_label,
                    anchor='nw'
                )
                
                # Сделать изображение перемещаемым
                self.make_canvas_item_movable(image_label, canvas_item)
                
                logger.info(f"Image added to slide: {os.path.basename(file_path)}")
                
                # Автоматически сохранить
                self.schedule_auto_save()
                
                # Показать сообщение об успехе
                messagebox.showinfo("Bild hinzugefügt", f"Bild erfolgreich hinzugefügt:\n{os.path.basename(file_path)}")
                
        except Exception as e:
            logger.error(f"Error adding image: {e}")
            messagebox.showerror("Fehler", f"Fehler beim Hinzufügen des Bildes:\n{e}")

    def add_text_element(self):
        """Добавляет текстовый элемент на слайд"""
        try:
            # Переключиться в режим редактирования если не в нем
            if not self.edit_mode:
                self.toggle_edit_mode()
            
            colors = theme_manager.get_colors()
            fonts = self.main_window.fonts
            
            # Создать новый текстовый виджет
            text_widget = tk.Text(
                self.slide_canvas,
                width=30,
                height=3,
                font=(fonts['body'][0], 14),
                bg='white',
                fg='#2C3E50',
                relief='solid',
                bd=1,
                wrap='word',
                insertbackground='#2C3E50'
            )
            
            # Добавить placeholder текст
            text_widget.insert('1.0', 'Neuer Text - hier bearbeiten')
            
            # Разместить на canvas
            canvas_item = self.slide_canvas.create_window(
                150, 400,  # Начальная позиция
                window=text_widget,
                anchor='nw'
            )
            
            # Сделать перемещаемым
            self.make_canvas_item_movable(text_widget, canvas_item)
            
            # Автосохранение при редактировании
            text_widget.bind('<KeyRelease>', lambda e: self.schedule_auto_save())
            
            logger.info("Text element added to slide")
            
        except Exception as e:
            logger.error(f"Error adding text element: {e}")
            messagebox.showerror("Fehler", f"Fehler beim Hinzufügen des Textes:\n{e}")

    def add_symbol_element(self, symbol):
        """Добавляет символ в активный текстовый виджет"""
        try:
            # Найти активный текстовый виджет
            focused_widget = self.main_window.root.focus_get()
            
            if isinstance(focused_widget, tk.Text):
                # Вставить символ в позиции курсора
                focused_widget.insert(tk.INSERT, symbol)
                self.schedule_auto_save()
                logger.debug(f"Symbol inserted: {symbol}")
            else:
                # Если нет активного текстового поля, создать новое с символом
                self.add_text_element()
                # Найти только что созданный виджет и вставить символ
                canvas_items = self.slide_canvas.find_all()
                for item in reversed(canvas_items):  # Последний добавленный
                    if self.slide_canvas.type(item) == 'window':
                        widget = self.slide_canvas.nametowidget(self.slide_canvas.itemcget(item, 'window'))
                        if isinstance(widget, tk.Text):
                            widget.delete('1.0', 'end')
                            widget.insert('1.0', symbol)
                            widget.focus_set()
                            break
                            
        except Exception as e:
            logger.error(f"Error adding symbol: {e}")

    def load_slide_to_editor(self, slide_id):
        """Загружает Demo-Folie в редактор с правильной синхронизацией"""
        try:
            # Сохранить текущий слайд перед переключением
            if hasattr(self, 'current_edit_slide') and hasattr(self, 'current_slide') and self.current_slide:
                self.save_current_slide_content()
            
            # Загрузить новый слайд из content_manager
            slide = content_manager.get_slide(slide_id)
            
            if slide:
                self.current_edit_slide = slide_id
                self.current_slide = slide
                
                # Очистить canvas
                self.clear_slide_canvas()
                
                # Восстановить сохраненные элементы если есть
                if hasattr(slide, 'extra_data') and slide.extra_data and 'canvas_elements' in slide.extra_data:
                    self.restore_canvas_elements(slide.extra_data['canvas_elements'])
                else:
                    # Показать предварительный просмотр если нет дополнительных элементов
                    self.render_slide_preview()
                
                # Обновить UI
                self.update_thumbnail_selection()
                self.update_slide_counter()
                
                if hasattr(self, 'slide_info_label'):
                    self.slide_info_label.configure(
                        text=f"Demo-Folie {slide_id}: {slide.title}"
                    )
                
                logger.debug(f"Loaded slide {slide_id} into editor: {slide.title}")
                
            else:
                logger.warning(f"Slide {slide_id} not found")
                
        except Exception as e:
            logger.error(f"Error loading slide to editor: {e}")

    def restore_text_element(self, text_data):
        """Восстанавливает текстовый элемент из сохраненных данных"""
        try:
            colors = theme_manager.get_colors()
            fonts = self.main_window.fonts
            
            # Создать текстовый виджет
            text_widget = tk.Text(
                self.slide_canvas,
                width=30,
                height=3,
                font=text_data.get('font', (fonts['body'][0], 14)),
                bg='white',
                fg='#2C3E50',
                relief='solid',
                bd=1,
                wrap='word',
                insertbackground='#2C3E50'
            )
            
            # Вставить сохраненный текст
            text_widget.insert('1.0', text_data.get('content', ''))
            
            # Разместить на canvas в сохраненной позиции
            canvas_item = self.slide_canvas.create_window(
                text_data['x'], text_data['y'],
                window=text_widget,
                anchor='nw'
            )
            
            # Сделать перемещаемым
            self.make_canvas_item_movable(text_widget, canvas_item)
            
            # Автосохранение при редактировании
            text_widget.bind('<KeyRelease>', lambda e: self.schedule_auto_save())
            
            logger.debug(f"Restored text element at position ({text_data['x']}, {text_data['y']})")
            
        except Exception as e:
            logger.error(f"Error restoring text element: {e}")

    def render_slide_preview(self):
        """Рендерит предварительный просмотр слайда используя тот же рендерер что и Demo"""
        try:
            if not hasattr(self, 'slide_canvas') or not self.current_slide:
                return
                
            canvas_width = self.slide_canvas.winfo_width()
            canvas_height = self.slide_canvas.winfo_height()
            
            if canvas_width > 10 and canvas_height > 10:
                # Подготовать данные слайда
                slide_data = {
                    'title': self.current_slide.title,
                    'content': self.current_slide.content,
                    'slide_number': self.current_edit_slide,
                    'background_color': '#FFFFFF',
                    'text_color': '#1F1F1F'
                }
                
                # Использовать тот же рендерер что и Demo
                SlideRenderer.render_slide_to_canvas(
                    self.slide_canvas,
                    slide_data,
                    canvas_width,
                    canvas_height
                )
                
                logger.debug(f"Rendered slide preview {self.current_edit_slide} in creator")
                
        except Exception as e:
            logger.error(f"Error rendering slide preview: {e}")

    def clear_slide_canvas(self):
        """Очищает canvas от всего контента"""
        try:
            # Удалить все элементы кроме dropzone
            all_items = self.slide_canvas.find_all()
            for item in all_items:
                tags = self.slide_canvas.gettags(item)
                if 'dropzone' not in tags:
                    self.slide_canvas.delete(item)
            
            logger.debug("Canvas cleared")
            
        except Exception as e:
            logger.error(f"Error clearing canvas: {e}")

    def update_thumbnail_selection(self):
        """Обновляет выделение thumbnail в списке слайдов"""
        try:
            colors = theme_manager.get_colors()
            
            if hasattr(self, 'thumbnail_buttons'):
                for slide_id, button in self.thumbnail_buttons.items():
                    if slide_id == self.current_edit_slide:
                        button.configure(
                            bg=colors['accent_primary'],
                            fg='white'
                        )
                    else:
                        button.configure(
                            bg=colors['background_tertiary'],
                            fg=colors['text_primary']
                        )
            
            logger.debug(f"Updated thumbnail selection for slide {self.current_edit_slide}")
            
        except Exception as e:
            logger.error(f"Error updating thumbnail selection: {e}")

    def update_slide_counter(self):
        """Обновляет счетчик слайдов"""
        try:
            if hasattr(self, 'slide_counter') and hasattr(self, 'thumbnail_buttons'):
                self.slide_counter.configure(
                    text=f"Demo-Folie {self.current_edit_slide} von {len(self.thumbnail_buttons)}"
                )
        except Exception as e:
            logger.error(f"Error updating slide counter: {e}")

    def auto_save_presentation(self):
        """Автоматически сохраняет презентацию"""
        try:
            self.save_current_slide_content()
            # Планирует следующее сохранение
            self.schedule_auto_save()
        except Exception as e:
            logger.error(f"Fehler beim Auto-Speichern: {e}")
            self.schedule_auto_save()  # Продолжаем попытки
        
    def create_creator_content(self):
        """Создает 3-колоночный Creator-Tab"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        # Главный контейнер
        self.container = tk.Frame(self.parent, bg=colors['background_primary'])
        
        # Header-Toolbar (сверху)
        self.create_header_toolbar()
        
        # 3-колоночный layout
        content_frame = tk.Frame(self.container, bg=colors['background_primary'])
        content_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Grid-Layout для 3 колонок
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=0, minsize=250)  # Folien-Übersicht (слева)
        content_frame.grid_columnconfigure(1, weight=1, minsize=800)  # Editor (по центру)
        content_frame.grid_columnconfigure(2, weight=0, minsize=300)  # Tool-Box (справа)
        
        # Колонка 1: Folien-Übersicht (слева)
        self.create_slides_overview_panel(content_frame)
        
        # Колонка 2: Haupt-Editor (по центру)
        self.create_main_editor_panel(content_frame)
        
        # Колонка 3: Tool-Box (справа)
        self.create_toolbox_panel(content_frame)
        
        # Status-Leiste (внизу)
        self.create_status_bar()
    
    def create_header_toolbar(self):
        """Создает Header-Toolbar"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        # Header-Frame (15% выше)
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
            text="🎨 Slide Creator",
            font=fonts['title'],
            fg=colors['accent_primary'],
            bg=colors['background_secondary']
        )
        title_label.pack(anchor='w', pady=(15, 0))
        
        subtitle_label = tk.Label(
            title_frame,
            text="Drag & Drop Editor",
            font=fonts['caption'],
            fg=colors['text_secondary'],
            bg=colors['background_secondary']
        )
        subtitle_label.pack(anchor='w')
        
        # Действия
        actions_frame = tk.Frame(header_frame, bg=colors['background_secondary'])
        actions_frame.pack(side='left', fill='y', padx=20)
        
        # Сохранить
        save_btn = tk.Button(
            actions_frame,
            text="💾 Speichern",
            font=fonts['button'],
            bg=colors['accent_primary'],
            fg='white',
            relief='flat',
            bd=0,
            padx=20,
            pady=10,
            cursor='hand2',
            command=self.manual_save_slide
        )
        save_btn.pack(side='left', padx=(0, 10), pady=15)
        
        # Предварительный просмотр
        preview_btn = tk.Button(
            actions_frame,
            text="👁 Vorschau",
            font=fonts['button'],
            bg=colors['accent_secondary'],
            fg='white',
            relief='flat',
            bd=0,
            padx=20,
            pady=10,
            cursor='hand2',
            command=self.preview_slide
        )
        preview_btn.pack(side='left', padx=(0, 10), pady=15)
        
        # Slide-Navigation
        nav_frame = tk.Frame(header_frame, bg=colors['background_secondary'])
        nav_frame.pack(side='right', fill='y', padx=(20, 15))
        
        # Slide-Счетчик
        self.slide_counter = tk.Label(
            nav_frame,
            text="Demo-Folie 1 von 10",
            font=fonts['subtitle'],
            fg=colors['text_primary'],
            bg=colors['background_secondary']
        )
        self.slide_counter.pack(pady=(20, 5))
        
        # Navigation-Buttons
        nav_buttons = tk.Frame(nav_frame, bg=colors['background_secondary'])
        nav_buttons.pack()
        
        prev_btn = tk.Button(
            nav_buttons,
            text="◀ Zurück",
            font=fonts['button'],
            bg=colors['background_tertiary'],
            fg=colors['text_primary'],
            relief='flat',
            bd=0,
            padx=15,
            pady=5,
            cursor='hand2',
            command=self.previous_slide
        )
        prev_btn.pack(side='left', padx=(0, 5))
        
        next_btn = tk.Button(
            nav_buttons,
            text="Weiter ▶",
            font=fonts['button'],
            bg=colors['background_tertiary'],
            fg=colors['text_primary'],
            relief='flat',
            bd=0,
            padx=15,
            pady=5,
            cursor='hand2',
            command=self.next_slide
        )
        next_btn.pack(side='left', padx=(5, 0))
    
    def create_slides_overview_panel(self, parent):
        """Создает Folien-Übersicht (слева) - Demo-Folien"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        # Panel Frame
        panel_frame = tk.Frame(
            parent,
            bg=colors['background_secondary'],
            relief='solid',
            bd=1,
            width=250
        )
        panel_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 5))
        panel_frame.grid_propagate(False)
        
        # Header
        header_frame = tk.Frame(panel_frame, bg=colors['background_secondary'])
        header_frame.pack(fill='x', padx=15, pady=(15, 10))
        
        header_label = tk.Label(
            header_frame,
            text="📋 Demo-Folien",
            font=fonts['title'],
            fg=colors['text_primary'],
            bg=colors['background_secondary']
        )
        header_label.pack(anchor='w')
        
        # Info-Label
        info_label = tk.Label(
            header_frame,
            text="Klicken zum Bearbeiten",
            font=fonts['caption'],
            fg=colors['text_secondary'],
            bg=colors['background_secondary']
        )
        info_label.pack(anchor='w', pady=(5, 0))
        
        # Scrollable Thumbnail List
        canvas = tk.Canvas(panel_frame, bg=colors['background_secondary'], highlightthickness=0)
        scrollbar = tk.Scrollbar(panel_frame, orient="vertical", command=canvas.yview)
        self.thumbnail_frame = tk.Frame(canvas, bg=colors['background_secondary'])
        
        self.thumbnail_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.thumbnail_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=(15, 0), pady=(0, 15))
        scrollbar.pack(side="right", fill="y", pady=(0, 15))
        
        # Создать thumbnails
        self.create_slide_thumbnails()
    
    def create_slide_thumbnails(self):
        """Создает Slide-Thumbnails из Demo-Folien"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        # Если thumbnails уже созданы, только обновить их
        if hasattr(self, 'thumbnail_buttons') and self.thumbnail_buttons:
            slides = content_manager.get_all_slides()
            for slide_id, slide in slides.items():
                if slide_id in self.thumbnail_buttons:
                    button = self.thumbnail_buttons[slide_id]
                    title = slide.title
                    display_title = title[:18] + "..." if len(title) > 18 else title
                    button.configure(text=f"Folie {slide_id}\n{display_title}")
            return
        
        self.thumbnail_buttons = {}
        
        # Content-Manager использовать (Demo-Folien)
        slides = content_manager.get_all_slides()
        
        if not slides:
            logger.warning("Keine Demo-Folien gefunden")
            return
        
        for slide_id, slide in slides.items():
            try:
                # Thumbnail-Container
                thumb_container = tk.Frame(
                    self.thumbnail_frame,
                    bg=colors['background_secondary']
                )
                thumb_container.pack(fill='x', padx=5, pady=3)
                
                # Thumbnail-Button
                is_active = slide_id == self.current_edit_slide
                bg_color = colors['accent_primary'] if is_active else colors['background_tertiary']
                
                title = slide.title
                display_title = title[:18] + "..." if len(title) > 18 else title
                
                thumb_btn = tk.Button(
                    thumb_container,
                    text=f"Folie {slide_id}\n{display_title}",
                    font=fonts['body'],
                    bg=bg_color,
                    fg='white' if is_active else colors['text_primary'],
                    relief='flat',
                    bd=0,
                    width=20,
                    height=3,
                    cursor='hand2',
                    command=lambda sid=slide_id: self.load_slide_to_editor(sid),
                    justify='left'
                )
                thumb_btn.pack(fill='x', ipady=5)
                
                self.thumbnail_buttons[slide_id] = thumb_btn
                
            except Exception as e:
                logger.error(f"Fehler beim Erstellen von Thumbnail für Slide {slide_id}: {e}")
    
    def create_main_editor_panel(self, parent):
        """Создает Haupt-Editor (по центру) - всегда белая Canvas"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        # Editor Frame
        editor_frame = tk.Frame(
            parent,
            bg=colors['background_secondary'],
            relief='solid',
            bd=1
        )
        editor_frame.grid(row=0, column=1, sticky='nsew', padx=5)
        
        # Header
        header_frame = tk.Frame(editor_frame, bg=colors['background_secondary'])
        header_frame.pack(fill='x', padx=20, pady=(15, 10))
        
        # Slide-Info
        self.slide_info_label = tk.Label(
            header_frame,
            text="Demo-Folie 1: Wählen Sie eine Folie zum Bearbeiten",
            font=fonts['display'],
            fg=colors['text_primary'],
            bg=colors['background_secondary']
        )
        self.slide_info_label.pack(anchor='w')
        
        # Canvas для Drag & Drop Editor - полная ширина и высота
        canvas_frame = tk.Frame(editor_frame, bg=colors['background_secondary'])
        canvas_frame.pack(fill='both', expand=True, padx=10, pady=(10, 10))
        
        # Canvas Container - использует полное доступное место
        canvas_container = tk.Frame(canvas_frame, bg=colors['background_secondary'])
        canvas_container.pack(fill='both', expand=True)
        
        # Создать Slide Canvas - с более темным фоном для лучшего контраста
        self.slide_canvas = tk.Canvas(
            canvas_container,
            bg='#E8E8E8',  # Немного темнее для лучшего контраста к белому слайду
            relief='flat',
            bd=0,
            highlightthickness=0
        )
        self.slide_canvas.pack(fill='both', expand=True)
        
        # Отслеживать размер Canvas и масштабировать слайд соответственно
        self.slide_canvas.bind('<Configure>', self.on_canvas_resize)
        
        # Кнопка Bearbeiten
        edit_button = tk.Button(
            canvas_container,
            text="Bearbeiten",
            font=fonts['button'],
            bg=colors['accent_secondary'],
            fg='white',
            relief='flat',
            bd=0,
            padx=20,
            pady=8,
            cursor='hand2',
            command=self.toggle_edit_mode
        )
        edit_button.place(relx=0.95, rely=0.05, anchor='ne')
        
        # Создать начальную Drop-Zone
        self.create_slide_content()
    
    def create_slide_content(self):
        """Создает Drop-Zone и начальный Slide-рамку"""
        # Невидимая Drop-Zone для распознавания Drop
        self.dropzone_rect = self.slide_canvas.create_rectangle(
            0, 0, self.slide_width, self.slide_height,
            outline='',  # Невидима
            width=0,
            fill='',
            tags='dropzone'
        )
        
        # Добавить начальную Slide-рамку
        self.slide_canvas.after(100, self.render_slide_preview)
    
    def on_canvas_resize(self, event):
        """Обработчик изменения размера canvas"""
        # Перерисовать предварительный просмотр при изменении размера
        self.main_window.root.after(100, self.render_slide_preview)

    def toggle_edit_mode(self):
        """Переключает между режимом предварительного просмотра и редактированием"""
        try:
            if not hasattr(self, 'edit_mode'):
                self.edit_mode = False
                
            self.edit_mode = not self.edit_mode
            
            if self.edit_mode:
                # Режим редактирования - добавить текстовые поля
                self.create_edit_widgets()
            else:
                # Режим предварительного просмотра - сохранить изменения и показать предварительный просмотр
                self.save_current_slide_content()
                self.clear_slide_canvas()
                self.render_slide_preview()
                
        except Exception as e:
            logger.error(f"Error toggling edit mode: {e}")

    def create_edit_widgets(self):
        """Создает виджеты для редактирования"""
        try:
            # Очистить canvas
            self.clear_slide_canvas()
            
            colors = theme_manager.get_colors()
            fonts = self.main_window.fonts
            
            # Получить данные текущего слайда
            slide = content_manager.get_slide(self.current_edit_slide)
            
            # Создать виджеты редактирования
            title_widget = tk.Text(
                self.slide_canvas,
                width=60,
                height=3,
                font=(fonts['title'][0], 24, 'bold'),
                bg='white',
                fg='#1E88E5',
                relief='flat',
                bd=1,
                wrap='word',
                insertbackground='#1E88E5'
            )
            
            content_widget = tk.Text(
                self.slide_canvas,
                width=70,
                height=15,
                font=(fonts['body'][0], 14),
                bg='white',
                fg='#2C3E50',
                relief='flat',
                bd=1,
                wrap='word',
                insertbackground='#2C3E50'
            )
            
            if slide:
                title_widget.insert('1.0', slide.title)
                content_widget.insert('1.0', slide.content)
            
            # Разместить виджеты на canvas
            self.slide_canvas.create_window(100, 50, window=title_widget, anchor='nw')
            self.slide_canvas.create_window(100, 150, window=content_widget, anchor='nw')
            
            # Сохранить ссылки для дальнейшего использования
            self.edit_widgets = {
                'title': title_widget,
                'content': content_widget
            }
            
            # Автосохранение при редактировании
            def on_edit(event=None):
                self.schedule_auto_save()
            
            title_widget.bind('<KeyRelease>', on_edit)
            content_widget.bind('<KeyRelease>', on_edit)
            
        except Exception as e:
            logger.error(f"Error creating edit widgets: {e}")
    
    def create_toolbox_panel(self, parent):
        """Создает Tool-Box (справа) с расширенными инструментами"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        # Panel Frame
        panel_frame = tk.Frame(
            parent,
            bg=colors['background_secondary'],
            relief='solid',
            bd=1,
            width=300
        )
        panel_frame.grid(row=0, column=2, sticky='nsew', padx=(5, 0))
        panel_frame.grid_propagate(False)
        
        # Header
        header_frame = tk.Frame(panel_frame, bg=colors['background_secondary'])
        header_frame.pack(fill='x', padx=15, pady=(15, 10))
        
        header_label = tk.Label(
            header_frame,
            text="🔧 Tool-Box",
            font=fonts['title'],
            fg=colors['text_primary'],
            bg=colors['background_secondary']
        )
        header_label.pack(anchor='w')
        
        # Scrollable Tools Frame
        tools_canvas = tk.Canvas(panel_frame, bg=colors['background_secondary'], highlightthickness=0)
        tools_scrollbar = tk.Scrollbar(panel_frame, orient="vertical", command=tools_canvas.yview)
        tools_frame = tk.Frame(tools_canvas, bg=colors['background_secondary'])
        
        tools_frame.bind(
            "<Configure>",
            lambda e: tools_canvas.configure(scrollregion=tools_canvas.bbox("all"))
        )
        
        tools_canvas.create_window((0, 0), window=tools_frame, anchor="nw")
        tools_canvas.configure(yscrollcommand=tools_scrollbar.set)
        
        tools_canvas.pack(side="left", fill="both", expand=True, padx=15, pady=10)
        tools_scrollbar.pack(side="right", fill="y", pady=10)
        
        # Основные инструменты
        main_tools_label = tk.Label(
            tools_frame,
            text="Hauptwerkzeuge",
            font=fonts['subtitle'],
            fg=colors['text_primary'],
            bg=colors['background_secondary']
        )
        main_tools_label.pack(anchor='w', pady=(0, 10))
        
        # Text-Tool
        text_btn = tk.Button(
            tools_frame,
            text="📝 Text hinzufügen",
            font=fonts['button'],
            bg=colors['background_tertiary'],
            fg=colors['text_primary'],
            relief='flat',
            bd=0,
            padx=20,
            pady=10,
            cursor='hand2',
            command=lambda: self.add_element('text')
        )
        text_btn.pack(fill='x', pady=5)
        
        # Image-Tool
        image_btn = tk.Button(
            tools_frame,
            text="🖼️ Bild hinzufügen",
            font=fonts['button'],
            bg=colors['background_tertiary'],
            fg=colors['text_primary'],
            relief='flat',
            bd=0,
            padx=20,
            pady=10,
            cursor='hand2',
            command=lambda: self.add_element('image')
        )
        image_btn.pack(fill='x', pady=5)
        
        # Separator
        separator1 = tk.Frame(tools_frame, bg=colors['border_medium'], height=2)
        separator1.pack(fill='x', pady=10)
        
        # Символы и спецзнаки
        symbols_label = tk.Label(
            tools_frame,
            text="Symbole & Zeichen",
            font=fonts['subtitle'],
            fg=colors['text_primary'],
            bg=colors['background_secondary']
        )
        symbols_label.pack(anchor='w', pady=(0, 10))
        
        # Панель спецсимволов
        symbols_frame = tk.Frame(tools_frame, bg=colors['background_secondary'])
        symbols_frame.pack(fill='x', pady=5)
        
        # Основные знаки препинания
        punctuation_symbols = ['.', ',', ';', ':', '!', '?', '-', '–', '—', '...']
        punct_frame = tk.Frame(symbols_frame, bg=colors['background_secondary'])
        punct_frame.pack(fill='x', pady=2)
        
        for i, symbol in enumerate(punctuation_symbols):
            btn = tk.Button(
                punct_frame,
                text=symbol,
                font=(fonts['body'][0], 12),
                bg=colors['background_tertiary'],
                fg=colors['text_primary'],
                relief='flat',
                bd=0,
                width=3,
                height=1,
                cursor='hand2',
                command=lambda s=symbol: self.add_symbol_element(s)
            )
            btn.grid(row=i//5, column=i%5, padx=2, pady=2)
        
        # Математические символы
        math_symbols = ['±', '×', '÷', '=', '≠', '≤', '≥', '∞', '∑', '√']
        math_frame = tk.Frame(symbols_frame, bg=colors['background_secondary'])
        math_frame.pack(fill='x', pady=2)
        
        for i, symbol in enumerate(math_symbols):
            btn = tk.Button(
                math_frame,
                text=symbol,
                font=(fonts['body'][0], 12),
                bg=colors['background_tertiary'],
                fg=colors['text_primary'],
                relief='flat',
                bd=0,
                width=3,
                height=1,
                cursor='hand2',
                command=lambda s=symbol: self.add_symbol_element(s)
            )
            btn.grid(row=i//5, column=i%5, padx=2, pady=2)
        
        # Separator
        separator2 = tk.Frame(tools_frame, bg=colors['border_medium'], height=2)
        separator2.pack(fill='x', pady=10)
        
        # Эмодзи
        emoji_label = tk.Label(
            tools_frame,
            text="Emojis",
            font=fonts['subtitle'],
            fg=colors['text_primary'],
            bg=colors['background_secondary']
        )
        emoji_label.pack(anchor='w', pady=(0, 10))
        
        # Панель эмодзи
        emoji_frame = tk.Frame(tools_frame, bg=colors['background_secondary'])
        emoji_frame.pack(fill='x', pady=5)
        
        # Часто используемые эмодзи
        common_emojis = ['😀', '😊', '👍', '❤️', '🎉', '🚗', '🏠', '💡', '📱', '⭐', '🔥', '✅', '❌', '➡️', '⬅️']
        
        for i, emoji in enumerate(common_emojis):
            btn = tk.Button(
                emoji_frame,
                text=emoji,
                font=(fonts['body'][0], 14),
                bg=colors['background_tertiary'],
                fg=colors['text_primary'],
                relief='flat',
                bd=0,
                width=3,
                height=1,
                cursor='hand2',
                command=lambda e=emoji: self.add_symbol_element(e)
            )
            btn.grid(row=i//5, column=i%5, padx=2, pady=2)
        
        # Separator
        separator3 = tk.Frame(tools_frame, bg=colors['border_medium'], height=2)
        separator3.pack(fill='x', pady=10)
        
        # Дополнительные инструменты
        extra_tools_label = tk.Label(
            tools_frame,
            text="Weitere Tools",
            font=fonts['subtitle'],
            fg=colors['text_primary'],
            bg=colors['background_secondary']
        )
        extra_tools_label.pack(anchor='w', pady=(0, 10))
        
        # Clear-Tool
        clear_btn = tk.Button(
            tools_frame,
            text="🗑️ Folie leeren",
            font=fonts['button'],
            bg=colors['accent_warning'],
            fg='white',
            relief='flat',
            bd=0,
            padx=20,
            pady=10,
            cursor='hand2',
            command=self.clear_slide
        )
        clear_btn.pack(fill='x', pady=5)
    
    def create_status_bar(self):
        """Создает Status-Leiste"""
        colors = theme_manager.get_colors()
        fonts = self.main_window.fonts
        
        status_frame = tk.Frame(
            self.container,
            bg=colors['background_secondary'],
            height=30
        )
        status_frame.pack(fill='x', padx=10, pady=5)
        status_frame.pack_propagate(False)
        
        # Status-Text
        self.status_label = tk.Label(
            status_frame,
            text="Bereit - Wählen Sie eine Folie zum Bearbeiten",
            font=fonts['caption'],
            fg=colors['text_secondary'],
            bg=colors['background_secondary']
        )
        self.status_label.pack(side='left', padx=15, pady=5)
        
        # Speicher-Status
        self.save_status_label = tk.Label(
            status_frame,
            text="Gespeichert",
            font=fonts['caption'],
            fg=colors['text_tertiary'],
            bg=colors['background_secondary']
        )
        self.save_status_label.pack(side='right', padx=15, pady=5)
    
    def add_element(self, element_type):
        """Добавляет элемент на слайд"""
        try:
            if element_type == 'image':
                self.add_image_element()
            elif element_type == 'text':
                self.add_text_element()
            else:
                logger.info(f"Adding {element_type} element to slide")
                messagebox.showinfo("Tool", f"{element_type.capitalize()} Tool wird implementiert")
        except Exception as e:
            logger.error(f"Error adding element: {e}")

    def make_canvas_item_movable(self, widget, canvas_item):
        """Делает элемент на canvas перемещаемым"""
        def start_move(event):
            widget.start_x = event.x
            widget.start_y = event.y
        
        def on_move(event):
            # Вычислить новую позицию
            delta_x = event.x - widget.start_x
            delta_y = event.y - widget.start_y
            
            # Переместить элемент
            self.slide_canvas.move(canvas_item, delta_x, delta_y)
        
        def end_move(event):
            # Сохранить изменения после перемещения
            self.schedule_auto_save()
        
        # Добавить обработчики событий
        widget.bind('<Button-1>', start_move)
        widget.bind('<B1-Motion>', on_move)
        widget.bind('<ButtonRelease-1>', end_move)
        
        # Изменить курсор при наведении
        widget.bind('<Enter>', lambda e: widget.configure(cursor='hand2'))
        widget.bind('<Leave>', lambda e: widget.configure(cursor=''))
    
    def clear_slide(self):
        """Очищает текущий слайд"""
        try:
            result = messagebox.askyesno("Folie leeren", "Möchten Sie wirklich die aktuelle Folie leeren?")
            if result:
                self.clear_slide_canvas()
                # Удалить сохраненные элементы
                slide = content_manager.get_slide(self.current_edit_slide)
                if slide and hasattr(slide, 'extra_data'):
                    slide.extra_data = None
                    content_manager.update_slide_content(
                        self.current_edit_slide,
                        slide.title,
                        slide.content,
                        None
                    )
                logger.info(f"Cleared slide {self.current_edit_slide}")
        except Exception as e:
            logger.error(f"Error clearing slide: {e}")
    
    def previous_slide(self):
        """Переходит к предыдущему слайду"""
        try:
            slides = content_manager.get_all_slides()
            slide_ids = sorted(slides.keys())
            
            if slide_ids:
                current_index = slide_ids.index(self.current_edit_slide) if self.current_edit_slide in slide_ids else 0
                prev_index = (current_index - 1) % len(slide_ids)
                self.load_slide_to_editor(slide_ids[prev_index])
        except Exception as e:
            logger.error(f"Error going to previous slide: {e}")
    
    def next_slide(self):
        """Переходит к следующему слайду"""
        try:
            slides = content_manager.get_all_slides()
            slide_ids = sorted(slides.keys())
            
            if slide_ids:
                current_index = slide_ids.index(self.current_edit_slide) if self.current_edit_slide in slide_ids else 0
                next_index = (current_index + 1) % len(slide_ids)
                self.load_slide_to_editor(slide_ids[next_index])
        except Exception as e:
            logger.error(f"Error going to next slide: {e}")
    
    def preview_slide(self):
        """Показывает предварительный просмотр текущего слайда"""
        try:
            # Сначала сохранить
            self.save_current_slide_content()
            
            # Затем показать предварительный просмотр
            if self.edit_mode:
                self.edit_mode = False
                self.clear_slide_canvas()
                self.render_slide_preview()
            
            logger.info(f"Previewing slide {self.current_edit_slide}")
        except Exception as e:
            logger.error(f"Error previewing slide: {e}")
    
    def refresh_thumbnails(self):
        """Обновляет отображение thumbnail после изменений"""
        try:
            self.create_slide_thumbnails()
            logger.debug("Thumbnails refreshed")
        except Exception as e:
            logger.error(f"Error refreshing thumbnails: {e}")
    
    def refresh_theme(self):
        """Обновляет тему для Creator-Tab"""
        try:
            # Theme-Updates для всех компонентов
            colors = theme_manager.get_colors()
            
            # Обновить фон контейнера
            if hasattr(self, 'container'):
                self.container.configure(bg=colors['background_primary'])
            
            # Дополнительные обновления темы можно добавить здесь
            logger.debug("Creator-Tab Theme обновлен")
        except Exception as e:
            logger.error(f"Error refreshing theme: {e}")
    
    def show(self):
        """Показывает Creator-Tab"""
        if not self.visible:
            self.container.pack(fill='both', expand=True)
            self.visible = True
            
            # Загрузить первый слайд если еще не загружен
            if not hasattr(self, 'current_slide') or not self.current_slide:
                self.load_slide_to_editor(1)
            
            logger.debug("Creator-Tab показан")
    
    def hide(self):
        """Скрывает Creator-Tab"""
        if self.visible:
            # Сохранить текущие изменения перед скрытием
            if hasattr(self, 'current_slide') and self.current_slide:
                self.save_current_slide_content()
            
            self.container.pack_forget()
            self.visible = False
            logger.debug("Creator-Tab скрыт")
            logger.debug("Creator-Tab versteckt")
