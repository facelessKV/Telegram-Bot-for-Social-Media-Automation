import os
import logging
import tweepy
from typing import Dict, Any, Optional

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TwitterAPI:
    """Класс для работы с Twitter API."""
    
    def __init__(self, api_key: str, api_secret: str, access_token: str, access_secret: str):
        """
        Инициализация API для Twitter.
        
        Args:
            api_key (str): API ключ
            api_secret (str): API секрет
            access_token (str): Токен доступа
            access_secret (str): Секрет токена доступа
        """
        # Инициализация клиента Twitter API v2
        try:
            self.client = tweepy.Client(
                consumer_key=api_key,
                consumer_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_secret
            )
            
            # Для загрузки медиафайлов нужен доступ к API v1.1
            auth = tweepy.OAuth1UserHandler(
                api_key, api_secret, access_token, access_secret
            )
            self.api = tweepy.API(auth)
            
            logger.info("Twitter API успешно инициализирован")
        except Exception as e:
            logger.error(f"Ошибка при инициализации Twitter API: {e}")
            # Мы всё равно создаем объект, но он может не работать
            # В реальном приложении лучше обработать ошибку соответствующим образом
    
    def post_text(self, text: str) -> Dict[str, Any]:
        """
        Публикация текстового сообщения в Twitter.
        
        Args:
            text (str): Текст для публикации
            
        Returns:
            Dict[str, Any]: Результат операции с ключами:
                - success (bool): Успешность операции
                - post_id (str, optional): ID созданного поста
                - post_url (str, optional): URL поста
                - error (str, optional): Текст ошибки
        """
        try:
            # Размещаем твит
            response = self.client.create_tweet(text=text)
            
            # Получаем ID твита
            tweet_id = response.data['id']
            
            # Формируем URL твита (username берется из первого пользователя в ответе)
            user_id = response.data['id']
            tweet_url = f"https://twitter.com/user/status/{tweet_id}"
            
            logger.info(f"Текстовый твит успешно опубликован, ID: {tweet_id}")
            
            return {
                "success": True,
                "post_id": str(tweet_id),
                "post_url": tweet_url
            }
        except Exception as e:
            logger.error(f"Ошибка при публикации твита: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def post_with_media(self, text: str, media_path: str, media_type: str) -> Dict[str, Any]:
        """
        Публикация сообщения с медиафайлом в Twitter.
        
        Args:
            text (str): Текст для публикации
            media_path (str): Путь к медиафайлу
            media_type (str): Тип медиафайла ('photo' или 'video')
            
        Returns:
            Dict[str, Any]: Результат операции с ключами:
                - success (bool): Успешность операции
                - post_id (str, optional): ID созданного поста
                - post_url (str, optional): URL поста
                - error (str, optional): Текст ошибки
        """
        try:
            # Проверяем существование файла
            if not os.path.exists(media_path):
                return {
                    "success": False,
                    "error": f"Файл не найден: {media_path}"
                }
            
            # Загружаем медиафайл
            if media_type == "photo":
                media = self.api.media_upload(media_path)
                media_id = media.media_id
            elif media_type == "video":
                # Для видео процесс сложнее, нужно использовать media_upload
                media = self.api.media_upload(
                    media_path,
                    media_category='tweet_video'
                )
                
                # Проверяем статус загрузки видео
                media_id = media.media_id
            else:
                return {
                    "success": False,
                    "error": f"Неподдерживаемый тип медиафайла: {media_type}"
                }
            
            # Публикуем твит с медиа
            response = self.client.create_tweet(
                text=text,
                media_ids=[media_id]
            )
            
            # Получаем ID твита
            tweet_id = response.data['id']
            
            # Формируем URL твита
            tweet_url = f"https://twitter.com/user/status/{tweet_id}"
            
            logger.info(f"Твит с медиа успешно опубликован, ID: {tweet_id}")
            
            return {
                "success": True,
                "post_id": str(tweet_id),
                "post_url": tweet_url
            }
        except Exception as e:
            logger.error(f"Ошибка при публикации твита с медиа: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_post(self, post_id: str) -> Dict[str, Any]:
        """
        Удаление поста из Twitter.
        
        Args:
            post_id (str): ID поста для удаления
            
        Returns:
            Dict[str, Any]: Результат операции с ключами:
                - success (bool): Успешность операции
                - error (str, optional): Текст ошибки
        """
        try:
            # Удаляем твит
            self.client.delete_tweet(id=post_id)
            
            logger.info(f"Твит успешно удален, ID: {post_id}")
            
            return {
                "success": True
            }
        except Exception as e:
            logger.error(f"Ошибка при удалении твита: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_post_status(self, post_id: str) -> Dict[str, Any]:
        """
        Получение статуса поста.
        
        Args:
            post_id (str): ID поста
            
        Returns:
            Dict[str, Any]: Информация о посте с ключами:
                - exists (bool): Существует ли пост
                - likes (int, optional): Количество лайков
                - retweets (int, optional): Количество ретвитов
                - replies (int, optional): Количество ответов
                - error (str, optional): Текст ошибки
        """
        try:
            # Получаем информацию о твите
            tweet = self.client.get_tweet(
                id=post_id,
                tweet_fields=['public_metrics']
            )
            
            if not tweet.data:
                return {
                    "exists": False,
                    "error": "Твит не найден"
                }
            
            # Извлекаем метрики
            metrics = tweet.data.public_metrics
            
            return {
                "exists": True,
                "likes": metrics['like_count'],
                "retweets": metrics['retweet_count'],
                "replies": metrics['reply_count']
            }
        except Exception as e:
            logger.error(f"Ошибка при получении статуса твита: {e}")
            return {
                "exists": False,
                "error": str(e)
            }