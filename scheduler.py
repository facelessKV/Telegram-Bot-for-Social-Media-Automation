import logging
import datetime
import threading
import time
from typing import Dict, Any, Optional

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class PostScheduler:
    """Класс для планирования и выполнения отложенных публикаций."""
    
    def __init__(self, db_manager, twitter_api):
        """
        Инициализация планировщика.
        
        Args:
            db_manager: Менеджер базы данных
            twitter_api: API для работы с Twitter
        """
        self.db_manager = db_manager
        self.twitter_api = twitter_api
        self.scheduled_posts = {}  # Словарь для хранения запланированных задач
        self.running = False
        self.scheduler_thread = None
        self.check_interval = 60  # Интервал проверки в секундах (1 минута)
    
    def start(self) -> None:
        """Запуск планировщика в отдельном потоке."""
        if self.running:
            logger.warning("Планировщик уже запущен")
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop)
        self.scheduler_thread.daemon = True  # Поток демон завершится вместе с основным процессом
        self.scheduler_thread.start()
        logger.info("Планировщик публикаций запущен")
    
    def stop(self) -> None:
        """Остановка планировщика."""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join()
            logger.info("Планировщик публикаций остановлен")
    
    def _scheduler_loop(self) -> None:
        """Основной цикл планировщика, который проверяет и публикует запланированные посты."""
        while self.running:
            try:
                # Получаем все запланированные посты, которые должны быть опубликованы
                pending_posts = self.db_manager.get_pending_scheduled_posts()
                
                for post in pending_posts:
                    post_id, user_id, platform, text, media_path, media_type = post
                    
                    # Публикуем пост
                    result = self._publish_post(platform, text, media_path, media_type)
                    
                    if result["success"]:
                        # Сохраняем успешную публикацию в базу данных
                        self.db_manager.add_post(
                            user_id,
                            platform,
                            text,
                            media_path,
                            result["post_id"],
                            "published"
                        )
                        
                        # Удаляем запланированный пост из базы данных
                        self.db_manager.delete_scheduled_post(user_id, post_id)
                        
                        logger.info(f"Запланированный пост {post_id} успешно опубликован")
                    else:
                        logger.error(f"Ошибка при публикации запланированного поста {post_id}: {result['error']}")
                        # Можно обновить статус запланированного поста на "failed" или оставить для повторной попытки
                
                # Спим до следующей проверки
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Ошибка в цикле планировщика: {e}")
                time.sleep(self.check_interval)
    
    def _publish_post(self, platform: str, text: str, media_path: Optional[str], 
                     media_type: Optional[str]) -> Dict[str, Any]:
        """
        Публикация поста в социальную сеть.
        
        Args:
            platform (str): Платформа для публикации
            text (str): Текст публикации
            media_path (Optional[str]): Путь к медиафайлу
            media_type (Optional[str]): Тип медиафайла
            
        Returns:
            Dict[str, Any]: Результат публикации
        """
        if platform == "twitter":
            if media_path and media_type:
                return self.twitter_api.post_with_media(text, media_path, media_type)
            else:
                return self.twitter_api.post_text(text)
        else:
            return {
                "success": False,
                "error": f"Неподдерживаемая платформа: {platform}"
            }
    
    def schedule_post(self, post_id: int, scheduled_time: datetime.datetime) -> None:
        """
        Добавление поста в планировщик.
        
        Args:
            post_id (int): ID запланированного поста в базе данных
            scheduled_time (datetime.datetime): Запланированное время публикации
        """
        # В текущей реализации нам не нужно хранить отдельно запланированные задачи в памяти,
        # т.к. мы регулярно проверяем базу данных на наличие постов для публикации.
        # Но мы можем расширить функционал, например, для уведомлений пользователя.
        self.scheduled_posts[post_id] = scheduled_time
        logger.info(f"Пост {post_id} запланирован на {scheduled_time}")
    
    def cancel_scheduled_post(self, post_id: int) -> None:
        """
        Отмена запланированного поста.
        
        Args:
            post_id (int): ID запланированного поста
        """
        if post_id in self.scheduled_posts:
            del self.scheduled_posts[post_id]
            logger.info(f"Запланированный пост {post_id} отменен")

    def get_scheduled_posts(self) -> Dict[int, datetime.datetime]:
        """
        Получение списка запланированных постов.
        
        Returns:
            Dict[int, datetime.datetime]: Словарь с ID постов и временем публикации
        """
        return self.scheduled_posts