#!/usr/bin/env python3
"""
Content Manager для Dynamic Messe Stand V4 - УЛУЧШЕННАЯ ВЕРСИЯ
Централизованная система управления слайдами с поддержкой изображений
"""

import os
import json
import yaml
import shutil
from datetime import datetime
from core.logger import logger
from core.storage import storage_manager

class SlideData:
    """Класс для представления данных слайда с поддержкой медиа"""
    
    def __init__(self, slide_id, title="", content="", layout="text", config_data=None, extra_data=None):
        self.slide_id = slide_id
        self.title = title
        self.content = content
        self.layout = layout  # text, image, mixed, custom
        self.config_data = config_data or {}
        self.extra_data = extra_data or {}
        self.created_at = datetime.now()
        self.modified_at = datetime.now()
        
        # Ensure images directory exists for this slide
        self.ensure_slide_directory()
    
    def ensure_slide_directory(self):
        """Создает директорию для слайда если она не существует"""
        slide_dir = os.path.join("data", "slides", f"slide_{self.slide_id}")
        os.makedirs(slide_dir, exist_ok=True)
        
        # Create images subdirectory
        images_dir = os.path.join(slide_dir, "images")
        os.makedirs(images_dir, exist_ok=True)
        
        return slide_dir
    
    def get_slide_directory(self):
        """Возвращает путь к директории слайда"""
        return os.path.join("data", "slides", f"slide_{self.slide_id}")
    
    def get_images_directory(self):
        """Возвращает путь к директории изображений слайда"""
        return os.path.join(self.get_slide_directory(), "images")
    
    def add_image(self, image_path, element_data=None):
        """Добавляет изображение к слайду"""
        try:
            if not os.path.exists(image_path):
                logger.error(f"Image file not found: {image_path}")
                return None
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            file_extension = os.path.splitext(image_path)[1]
            new_filename = f"image_{timestamp}{file_extension}"
            
            # Copy to slide images directory
            target_path = os.path.join(self.get_images_directory(), new_filename)
            shutil.copy2(image_path, target_path)
            
            # Add to extra_data
            if 'canvas_elements' not in self.extra_data:
                self.extra_data['canvas_elements'] = []
            
            image_element = {
                'type': 'image',
                'file_path': target_path,
                'relative_path': new_filename,
                'original_name': os.path.basename(image_path),
                'added_at': datetime.now().isoformat(),
                'x': element_data.get('x', 0) if element_data else 0,
                'y': element_data.get('y', 0) if element_data else 0,
                'width': element_data.get('width', 400) if element_data else 400,
                'height': element_data.get('height', 300) if element_data else 300
            }
            
            self.extra_data['canvas_elements'].append(image_element)
            self.modified_at = datetime.now()
            
            logger.info(f"Image added to slide {self.slide_id}: {new_filename}")
            return target_path
            
        except Exception as e:
            logger.error(f"Error adding image to slide {self.slide_id}: {e}")
            return None
    
    def remove_image(self, image_path):
        """Удаляет изображение из слайда"""
        try:
            # Remove from filesystem
            if os.path.exists(image_path):
                os.remove(image_path)
            
            # Remove from extra_data
            if 'canvas_elements' in self.extra_data:
                self.extra_data['canvas_elements'] = [
                    elem for elem in self.extra_data['canvas_elements'] 
                    if elem.get('type') != 'image' or elem.get('file_path') != image_path
                ]
            
            self.modified_at = datetime.now()
            logger.info(f"Image removed from slide {self.slide_id}: {os.path.basename(image_path)}")
            
        except Exception as e:
            logger.error(f"Error removing image from slide {self.slide_id}: {e}")
    
    def get_images(self):
        """Возвращает список всех изображений слайда"""
        if 'canvas_elements' not in self.extra_data:
            return []
        
        return [
            elem for elem in self.extra_data['canvas_elements'] 
            if elem.get('type') == 'image'
        ]
    
    def cleanup_missing_images(self):
        """Очищает ссылки на несуществующие изображения"""
        if 'canvas_elements' not in self.extra_data:
            return
        
        valid_elements = []
        for elem in self.extra_data['canvas_elements']:
            if elem.get('type') == 'image':
                file_path = elem.get('file_path', '')
                if os.path.exists(file_path):
                    valid_elements.append(elem)
                else:
                    logger.warning(f"Removing missing image reference: {file_path}")
            else:
                valid_elements.append(elem)
        
        self.extra_data['canvas_elements'] = valid_elements
        
        if len(valid_elements) != len(self.extra_data.get('canvas_elements', [])):
            self.modified_at = datetime.now()
    
    def get_slide_statistics(self):
        """Возвращает статистику слайда"""
        stats = {
            'slide_id': self.slide_id,
            'title_length': len(self.title),
            'content_length': len(self.content),
            'images_count': len(self.get_images()),
            'layout': self.layout,
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat()
        }
        
        # Add canvas elements statistics
        if 'canvas_elements' in self.extra_data:
            elements = self.extra_data['canvas_elements']
            stats['canvas_elements'] = {
                'total': len(elements),
                'images': len([e for e in elements if e.get('type') == 'image']),
                'text': len([e for e in elements if e.get('type') == 'text'])
            }
        
        return stats
    
    def to_dict(self):
        """Конвертация в словарь для сохранения"""
        return {
            'slide_id': self.slide_id,
            'title': self.title,
            'content': self.content,
            'layout': self.layout,
            'config_data': self.config_data,
            'extra_data': self.extra_data,
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data):
        """Создание объекта из словника"""
        slide = cls(
            data.get('slide_id', 1),
            data.get('title', ''),
            data.get('content', ''),
            data.get('layout', 'text'),
            data.get('config_data', {}),
            data.get('extra_data', {})
        )
        
        # Восстановление времени
        try:
            slide.created_at = datetime.fromisoformat(data.get('created_at', datetime.now().isoformat()))
            slide.modified_at = datetime.fromisoformat(data.get('modified_at', datetime.now().isoformat()))
        except:
            slide.created_at = datetime.now()
            slide.modified_at = datetime.now()
        
        # Cleanup missing images
        slide.cleanup_missing_images()
        
        return slide

class ContentManager:
    """Централизованный менеджер контента с расширенными возможностями"""
    
    def __init__(self):
        self.slides = {}
        self.content_observers = []  # Для уведомления об изменениях
        self.backup_enabled = True
        self.auto_cleanup_enabled = True
        
        # Ensure base directories exist
        self.ensure_base_directories()
        
        # Load existing content or create default
        if not self.load_from_file():
            self.load_default_content()
    
    def ensure_base_directories(self):
        """Создает базовые директории"""
        directories = [
            "data",
            "data/slides", 
            "data/images",
            "data/backups"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def load_default_content(self):
        """Загрузка контента по умолчанию"""
        default_slides = {
            1: SlideData(1, "BumbleB - Das automatisierte Shuttle", 
                        "Schonmal ein automatisiert Shuttle gesehen, das aussieht wie eine Hummel?\n\nShuttle fährt los von Bushaltestelle an Bahnhof...", "text"),
            2: SlideData(2, "BumbleB - Wie die Hummel fährt",
                        "Wie die Hummel ihre Flügel nutzt, so nutzt unser BumbleB innovative Technologie für autonomes Fahren.", "text"),
            3: SlideData(3, "Einsatzgebiete und Vorteile",
                        "Vielseitige Einsatzmöglichkeiten in urbanen Gebieten für nachhaltigen Transport.", "text"),
            4: SlideData(4, "Sicherheitssysteme",
                        "Moderne Sicherheitssysteme gewährleisten maximale Sicherheit für alle Passagiere.", "text"),
            5: SlideData(5, "Nachhaltigkeit & Umwelt",
                        "Nachhaltiger Transport für eine grüne Zukunft - umweltfreundlich und effizient.", "text")
        }
        
        for slide_id, slide_data in default_slides.items():
            if slide_id not in self.slides:
                self.slides[slide_id] = slide_data
        
        # Save default content
        self.save_to_file()
        
        logger.debug(f"Loaded {len(default_slides)} default slides")
    
    def get_slide(self, slide_id):
        """Получение слайда по ID"""
        slide = self.slides.get(slide_id)
        if slide and self.auto_cleanup_enabled:
            slide.cleanup_missing_images()
        return slide
    
    def get_all_slides(self):
        """Получение всех слайдов"""
        if self.auto_cleanup_enabled:
            for slide in self.slides.values():
                slide.cleanup_missing_images()
        return self.slides.copy()
    
    def get_slide_count(self):
        """Получение количества слайдов"""
        return len(self.slides)
    
    def update_slide_content(self, slide_id, title, content, extra_data=None):
        """Обновление контента слайда с улучшенной обработкой"""
        if slide_id not in self.slides:
            self.slides[slide_id] = SlideData(slide_id)
        
        slide = self.slides[slide_id]
        slide.title = title
        slide.content = content
        
        if extra_data:
            if isinstance(extra_data, dict):
                slide.extra_data.update(extra_data)
            else:
                slide.extra_data = extra_data
        
        slide.modified_at = datetime.now()
        
        # Auto-save
        self.save_slide(slide_id)
        
        # Уведомить наблюдателей об изменениях
        self.notify_observers(slide_id, slide)
        
        logger.debug(f"Updated slide {slide_id}: {title[:30]}...")
        return True
    
    def create_slide(self, slide_id, title="", content="", layout="text"):
        """Создание нового слайда"""
        if slide_id in self.slides:
            logger.warning(f"Slide {slide_id} already exists, updating instead")
        
        self.slides[slide_id] = SlideData(slide_id, title, content, layout)
        self.save_slide(slide_id)
        self.notify_observers(slide_id, self.slides[slide_id])
        
        logger.info(f"Created new slide {slide_id}")
        return True
    
    def delete_slide(self, slide_id):
        """Удаление слайда"""
        if slide_id in self.slides:
            slide = self.slides[slide_id]
            
            # Remove slide directory and all contents
            slide_dir = slide.get_slide_directory()
            if os.path.exists(slide_dir):
                try:
                    shutil.rmtree(slide_dir)
                    logger.info(f"Removed slide directory: {slide_dir}")
                except Exception as e:
                    logger.error(f"Error removing slide directory: {e}")
            
            del self.slides[slide_id]
            self.notify_observers(slide_id, None, action='delete')
            
            logger.info(f"Deleted slide {slide_id}")
            return True
        return False
    
    def duplicate_slide(self, slide_id, new_slide_id=None):
        """Дублирование слайда"""
        if slide_id not in self.slides:
            logger.error(f"Source slide {slide_id} not found")
            return False
        
        if new_slide_id is None:
            # Find next available ID
            new_slide_id = max(self.slides.keys()) + 1 if self.slides else 1
        
        source_slide = self.slides[slide_id]
        
        # Create new slide
        new_slide = SlideData(
            new_slide_id,
            f"{source_slide.title} (Kopie)",
            source_slide.content,
            source_slide.layout,
            source_slide.config_data.copy(),
            {}  # Start with empty extra_data, will copy images below
        )
        
        # Copy images
        if 'canvas_elements' in source_slide.extra_data:
            new_elements = []
            for element in source_slide.extra_data['canvas_elements']:
                if element.get('type') == 'image':
                    # Copy image file
                    source_path = element.get('file_path')
                    if source_path and os.path.exists(source_path):
                        copied_path = new_slide.add_image(source_path, element)
                        if copied_path:
                            # Find the newly added element and update its position
                            if 'canvas_elements' in new_slide.extra_data:
                                last_element = new_slide.extra_data['canvas_elements'][-1]
                                last_element.update({
                                    'x': element.get('x', 0),
                                    'y': element.get('y', 0),
                                    'width': element.get('width', 400),
                                    'height': element.get('height', 300)
                                })
                else:
                    # Copy non-image elements
                    new_elements.append(element.copy())
            
            # Add non-image elements
            if 'canvas_elements' not in new_slide.extra_data:
                new_slide.extra_data['canvas_elements'] = []
            new_slide.extra_data['canvas_elements'].extend(new_elements)
        
        self.slides[new_slide_id] = new_slide
        self.save_slide(new_slide_id)
        self.notify_observers(new_slide_id, new_slide, action='create')
        
        logger.info(f"Duplicated slide {slide_id} to {new_slide_id}")
        return True
    
    def move_slide(self, old_id, new_id):
        """Перемещение/переименование слайда"""
        if old_id not in self.slides:
            return False
        
        if new_id in self.slides and new_id != old_id:
            logger.error(f"Target slide ID {new_id} already exists")
            return False
        
        slide = self.slides[old_id]
        slide.slide_id = new_id
        
        # Move slide directory
        old_dir = os.path.join("data", "slides", f"slide_{old_id}")
        new_dir = os.path.join("data", "slides", f"slide_{new_id}")
        
        if os.path.exists(old_dir):
            try:
                if os.path.exists(new_dir):
                    shutil.rmtree(new_dir)
                shutil.move(old_dir, new_dir)
            except Exception as e:
                logger.error(f"Error moving slide directory: {e}")
        
        # Update slides dict
        del self.slides[old_id]
        self.slides[new_id] = slide
        
        self.save_slide(new_id)
        self.notify_observers(old_id, None, action='delete')
        self.notify_observers(new_id, slide, action='create')
        
        logger.info(f"Moved slide {old_id} to {new_id}")
        return True
    
    def add_observer(self, callback):
        """Добавление наблюдателя для получения уведомлений об изменениях"""
        self.content_observers.append(callback)
    
    def notify_observers(self, slide_id, slide_data, action='update'):
        """Уведомление всех наблюдателей об изменениях"""
        for callback in self.content_observers:
            try:
                callback(slide_id, slide_data, action)
            except Exception as e:
                logger.error(f"Error notifying observer: {e}")
    
    def save_slide(self, slide_id):
        """Сохранение отдельного слайда"""
        if slide_id not in self.slides:
            return False
        
        slide = self.slides[slide_id]
        slide_file = os.path.join(slide.get_slide_directory(), "slide.json")
        
        try:
            with open(slide_file, 'w', encoding='utf-8') as f:
                json.dump(slide.to_dict(), f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Slide {slide_id} saved to {slide_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving slide {slide_id}: {e}")
            return False
    
    def save_to_file(self, filepath=None):
        """Сохранение всех слайдов в файл"""
        if not filepath:
            filepath = os.path.join("data", "slides.json")
        
        # Create backup if enabled
        if self.backup_enabled and os.path.exists(filepath):
            self.create_backup(filepath)
        
        # Save individual slides first
        for slide_id in self.slides:
            self.save_slide(slide_id)
        
        # Save master index
        data = {
            'slides': {str(k): v.to_dict() for k, v in self.slides.items()},
            'exported_at': datetime.now().isoformat(),
            'version': "4.1.0",
            'total_slides': len(self.slides),
            'backup_enabled': self.backup_enabled
        }
        
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Slides saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error saving slides: {e}")
            return False
    
    def create_backup(self, filepath):
        """Создание резервной копии"""
        try:
            backup_dir = os.path.join("data", "backups")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"slides_backup_{timestamp}.json")
            
            shutil.copy2(filepath, backup_file)
            logger.debug(f"Backup created: {backup_file}")
            
            # Keep only last 10 backups
            self.cleanup_old_backups(backup_dir, max_backups=10)
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
    
    def cleanup_old_backups(self, backup_dir, max_backups=10):
        """Очистка старых резервных копий"""
        try:
            backup_files = [
                f for f in os.listdir(backup_dir) 
                if f.startswith("slides_backup_") and f.endswith(".json")
            ]
            
            backup_files.sort()  # Sort by name (which includes timestamp)
            
            while len(backup_files) > max_backups:
                old_backup = backup_files.pop(0)
                old_backup_path = os.path.join(backup_dir, old_backup)
                os.remove(old_backup_path)
                logger.debug(f"Removed old backup: {old_backup}")
                
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
    
    def load_from_file(self, filepath=None):
        """Загрузка слайдов из файла"""
        if not filepath:
            filepath = os.path.join("data", "slides.json")
        
        if not os.path.exists(filepath):
            logger.debug(f"Slides file not found: {filepath}")
            return False
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'slides' in data:
                self.slides.clear()
                for slide_id_str, slide_data in data['slides'].items():
                    slide_id = int(slide_id_str)
                    self.slides[slide_id] = SlideData.from_dict(slide_data)
                
                logger.info(f"Loaded {len(self.slides)} slides from {filepath}")
                
                # Уведомить всех наблюдателей
                for slide_id, slide_data in self.slides.items():
                    self.notify_observers(slide_id, slide_data, action='load')
                
                return True
        except Exception as e:
            logger.error(f"Error loading slides: {e}")
            return False
    
    def get_presentation_statistics(self):
        """Возвращает статистику презентации"""
        stats = {
            'total_slides': len(self.slides),
            'total_images': 0,
            'total_content_length': 0,
            'slides_by_layout': {},
            'creation_dates': [],
            'modification_dates': []
        }
        
        for slide in self.slides.values():
            slide_stats = slide.get_slide_statistics()
            
            stats['total_images'] += slide_stats['images_count']
            stats['total_content_length'] += slide_stats['content_length']
            
            layout = slide_stats['layout']
            stats['slides_by_layout'][layout] = stats['slides_by_layout'].get(layout, 0) + 1
            
            stats['creation_dates'].append(slide_stats['created_at'])
            stats['modification_dates'].append(slide_stats['modified_at'])
        
        return stats
    
    def export_presentation_as_json(self, filepath=None):
        """Экспорт презентации в JSON"""
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"exports/presentation_{timestamp}.json"
        
        return self.save_to_file(filepath)
    
    def export_presentation_as_yaml(self, filepath=None):
        """Экспорт презентации в YAML"""
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"exports/presentation_{timestamp}.yaml"
        
        # Create export directory
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        data = {
            'presentation': {
                'metadata': {
                    'title': 'BumbleB Präsentation',
                    'description': 'Automatisierte Shuttle-Präsentation',
                    'exported_at': datetime.now().isoformat(),
                    'version': "4.1.0",
                    'total_slides': len(self.slides)
                },
                'statistics': self.get_presentation_statistics()
            },
            'slides': {str(k): v.to_dict() for k, v in self.slides.items()}
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            logger.info(f"Slides exported to YAML: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error exporting to YAML: {e}")
            return None
    
    def cleanup_orphaned_files(self):
        """Очистка файлов-сирот (изображения без ссылок)"""
        try:
            slides_dir = os.path.join("data", "slides")
            if not os.path.exists(slides_dir):
                return
            
            # Get all referenced image paths
            referenced_images = set()
            for slide in self.slides.values():
                for image in slide.get_images():
                    if 'file_path' in image:
                        referenced_images.add(image['file_path'])
            
            # Find orphaned files
            orphaned_files = []
            for slide_dir_name in os.listdir(slides_dir):
                slide_dir_path = os.path.join(slides_dir, slide_dir_name)
                if os.path.isdir(slide_dir_path):
                    images_dir = os.path.join(slide_dir_path, "images")
                    if os.path.exists(images_dir):
                        for image_file in os.listdir(images_dir):
                            image_path = os.path.join(images_dir, image_file)
                            if image_path not in referenced_images:
                                orphaned_files.append(image_path)
            
            # Remove orphaned files
            for orphaned_file in orphaned_files:
                try:
                    os.remove(orphaned_file)
                    logger.info(f"Removed orphaned file: {orphaned_file}")
                except Exception as e:
                    logger.error(f"Error removing orphaned file {orphaned_file}: {e}")
            
            if orphaned_files:
                logger.info(f"Cleaned up {len(orphaned_files)} orphaned files")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

# Глобальная инстанция менеджера контента
content_manager = ContentManager()
