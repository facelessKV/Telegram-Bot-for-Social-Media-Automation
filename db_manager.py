import os
import logging
import sqlite3
import datetime
from typing import List, Tuple, Optional, Any

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Класс для работы с базой данных SQLite."""
    
    def __init__(self, db_path: str):
        """
        Инициализация менеджера базы данных.
        
        Args:
            db_path (str): Путь к файлу базы данных
        """
        self.db_path = db_path
        self.init_db()
    
    def init_db(self) -> None:
        """Инициализация базы данных и создание необходимых таблиц, если они не существуют."""
        # Проверяем существование директории
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        try:
            # Создаем соединение с базой данных
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Создаем таблицу для хранения опубликованных постов
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                platform TEXT NOT NULL,
                text TEXT NOT NULL,
                media_path TEXT,
                social_post_id TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Создаем таблицу для хранения запланированных постов
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                platform TEXT NOT NULL,
                text TEXT NOT NULL,
                media_path TEXT,
                media_type TEXT,
                scheduled_time TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            conn.commit()
            logger.info("База данных успешно инициализирована")
        except sqlite3.Error as e:
            logger.error(f"Ошибка при инициализации базы данных: {e}")
        finally:
            if conn:
                conn.close()
    
    def add_post(self, user_id: int, platform: str, text: str, media_path: Optional[str], 
                 social_post_id: str, status: str) -> int:
        """
        Добавление нового опубликованного поста в базу данных.
        
        Args:
            user_id (int): ID пользователя Telegram
            platform (str): Название платформы (twitter, instagram)
            text (str): Текст публикации
            media_path (Optional[str]): Путь к медиафайлу
            social_post_id (str): ID поста в социальной сети
            status (str): Статус публикации (published, error)
            
        Returns:
            int: ID добавленной записи
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                '''
                INSERT INTO posts (user_id, platform, text, media_path, social_post_id, status)
                VALUES (?, ?, ?, ?, ?, ?)
                ''',
                (user_id, platform, text, media_path, social_post_id, status)
            )
            
            post_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Пост успешно добавлен в базу данных, ID: {post_id}")
            
            return post_id
        except sqlite3.Error as e:
            logger.error(f"Ошибка при добавлении поста в базу данных: {e}")
            return -1
        finally:
            if conn:
                conn.close()
    
    def add_scheduled_post(self, user_id: int, platform: str, text: str, media_path: Optional[str],
                           media_type: Optional[str], scheduled_time: datetime.datetime) -> int:
        """
        Добавление запланированного поста в базу данных.
        
        Args:
            user_id (int): ID пользователя Telegram
            platform (str): Название платформы (twitter, instagram)
            text (str): Текст публикации
            media_path (Optional[str]): Путь к медиафайлу
            media_type (Optional[str]): Тип медиафайла (photo, video)
            scheduled_time (datetime.datetime): Запланированное время публикации
            
        Returns:
            int: ID добавленной записи
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                '''
                INSERT INTO scheduled_posts 
                (user_id, platform, text, media_path, media_type, scheduled_time)
                VALUES (?, ?, ?, ?, ?, ?)
                ''',
                (user_id, platform, text, media_path, media_type, scheduled_time)
            )
            
            post_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Запланированный пост успешно добавлен в базу данных, ID: {post_id}")
            
            return post_id
        except sqlite3.Error as e:
            logger.error(f"Ошибка при добавлении запланированного поста в базу данных: {e}")
            return -1
        finally:
            if conn:
                conn.close()
    
    def get_user_posts(self, user_id: int) -> List[Tuple]:
        """
        Получение всех постов пользователя.
        
        Args:
            user_id (int): ID пользователя Telegram
            
        Returns:
            List[Tuple]: Список кортежей с информацией о постах
        """
        try:
            conn = sqlite3.connect(self.db_path)
            # Устанавливаем row_factory для получения строк в виде кортежей
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                '''
                SELECT id, platform, text, media_path, social_post_id, status, created_at
                FROM posts
                WHERE user_id = ?
                ORDER BY created_at DESC
                ''',
                (user_id,)
            )
            
            posts = cursor.fetchall()
            return [tuple(row) for row in posts]
        except sqlite3.Error as e:
            logger.error(f"Ошибка при получении постов пользователя: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def get_scheduled_posts(self, user_id: int) -> List[Tuple]:
        """
        Получение всех запланированных постов пользователя.
        
        Args:
            user_id (int): ID пользователя Telegram
            
        Returns:
            List[Tuple]: Список кортежей с информацией о запланированных постах
        """
        try:
            conn = sqlite3.connect(self.db_path)
            # Настройка для возврата datetime вместо строк
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                '''
                SELECT id, platform, text, media_path, media_type, scheduled_time
                FROM scheduled_posts
                WHERE user_id = ? AND scheduled_time > datetime('now')
                ORDER BY scheduled_time ASC
                ''',
                (user_id,)
            )
            
            posts = cursor.fetchall()
            return [tuple(row) for row in posts]
        except sqlite3.Error as e:
            logger.error(f"Ошибка при получении запланированных постов пользователя: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def get_post_by_id(self, user_id: int, post_id: str) -> Optional[Tuple]:
        """
        Получение информации о посте по его ID.
        
        Args:
            user_id (int): ID пользователя Telegram
            post_id (str): ID поста
            
        Returns:
            Optional[Tuple]: Кортеж с информацией о посте или None, если пост не найден
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                '''
                SELECT id, platform, text, media_path, social_post_id, status, created_at
                FROM posts
                WHERE id = ? AND user_id = ?
                ''',
                (post_id, user_id)
            )
            
            post = cursor.fetchone()
            return post
        except sqlite3.Error as e:
            logger.error(f"Ошибка при получении информации о посте: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def get_scheduled_post_by_id(self, user_id: int, post_id: int) -> Optional[Tuple]:
        """
        Получение информации о запланированном посте по его ID.
        
        Args:
            user_id (int): ID пользователя Telegram
            post_id (int): ID запланированного поста
            
        Returns:
            Optional[Tuple]: Кортеж с информацией о запланированном посте или None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                '''
                SELECT id, platform, text, media_path, media_type, scheduled_time
                FROM scheduled_posts
                WHERE id = ? AND user_id = ?
                ''',
                (post_id, user_id)
            )
            
            post = cursor.fetchone()
            return post
        except sqlite3.Error as e:
            logger.error(f"Ошибка при получении информации о запланированном посте: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def delete_post(self, user_id: int, post_id: str) -> bool:
        """
        Удаление поста из базы данных.
        
        Args:
            user_id (int): ID пользователя Telegram
            post_id (str): ID поста
            
        Returns:
            bool: True если удаление успешно, иначе False
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Получаем информацию о посте для удаления медиафайла, если он есть
            cursor.execute(
                '''
                SELECT media_path FROM posts
                WHERE id = ? AND user_id = ?
                ''',
                (post_id, user_id)
            )
            
            post = cursor.fetchone()
            
            if post and post[0]:
                media_path = post[0]
                # Удаляем медиафайл, если он существует
                if os.path.exists(media_path):
                    os.remove(media_path)
            
            # Удаляем запись из базы данных
            cursor.execute(
                '''
                DELETE FROM posts
                WHERE id = ? AND user_id = ?
                ''',
                (post_id, user_id)
            )
            
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Ошибка при удалении поста: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def delete_scheduled_post(self, user_id: int, post_id: int) -> bool:
        """
        Удаление запланированного поста из базы данных.
        
        Args:
            user_id (int): ID пользователя Telegram
            post_id (int): ID запланированного поста
            
        Returns:
            bool: True если удаление успешно, иначе False
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Получаем информацию о посте для удаления медиафайла, если он есть
            cursor.execute(
                '''
                SELECT media_path FROM scheduled_posts
                WHERE id = ? AND user_id = ?
                ''',
                (post_id, user_id)
            )
            
            post = cursor.fetchone()
            
            if post and post[0]:
                media_path = post[0]
                # Удаляем медиафайл, если он существует
                if os.path.exists(media_path):
                    os.remove(media_path)
            
            # Удаляем запись из базы данных
            cursor.execute(
                '''
                DELETE FROM scheduled_posts
                WHERE id = ? AND user_id = ?
                ''',
                (post_id, user_id)
            )
            
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Ошибка при удалении запланированного поста: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_pending_scheduled_posts(self) -> List[Tuple]:
        """
        Получение запланированных постов, которые должны быть опубликованы.
        
        Returns:
            List[Tuple]: Список кортежей с информацией о запланированных постах
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Получаем посты, запланированные на период до текущего времени
            cursor.execute(
                '''
                SELECT id, user_id, platform, text, media_path, media_type
                FROM scheduled_posts
                WHERE scheduled_time <= datetime('now')
                ORDER BY scheduled_time ASC
                '''
            )
            
            posts = cursor.fetchall()
            return posts
        except sqlite3.Error as e:
            logger.error(f"Ошибка при получении запланированных постов: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def update_post_status(self, post_id: int, social_post_id: str, status: str) -> bool:
        """
        Обновление статуса поста.
        
        Args:
            post_id (int): ID поста в базе данных
            social_post_id (str): ID поста в социальной сети
            status (str): Новый статус поста
            
        Returns:
            bool: True если обновление успешно, иначе False
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                '''
                UPDATE posts
                SET social_post_id = ?, status = ?
                WHERE id = ?
                ''',
                (social_post_id, status, post_id)
            )
            
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Ошибка при обновлении статуса поста: {e}")
            return False
        finally:
            if conn:
                conn.close()