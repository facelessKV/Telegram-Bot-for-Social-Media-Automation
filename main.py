import os
import logging
import datetime
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    filters
)
from social_api import TwitterAPI
from scheduler import PostScheduler
from db_manager import DatabaseManager

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния разговора
CHOOSING_PLATFORM, TYPING_MESSAGE, UPLOADING_MEDIA, SCHEDULING = range(4)

# Токен телеграм бота
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_TOKEN")

# Токены для Twitter API
TWITTER_API_KEY = os.environ.get("TWITTER_API_KEY", "YOUR_TWITTER_API_KEY")
TWITTER_API_SECRET = os.environ.get("TWITTER_API_SECRET", "YOUR_TWITTER_SECRET")
TWITTER_ACCESS_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN", "YOUR_TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = os.environ.get("TWITTER_ACCESS_SECRET", "YOUR_TWITTER_ACCESS_SECRET")

class SocialMediaBot:
    """Основной класс для Telegram-бота, управляющего публикациями в социальных сетях."""
    
    def __init__(self):
        """Инициализация бота, API социальных сетей и базы данных."""
        # Настраиваем соединение с базой данных
        self.db_manager = DatabaseManager("social_posts.db")
        
        # Инициализируем API для Twitter
        self.twitter_api = TwitterAPI(
            TWITTER_API_KEY,
            TWITTER_API_SECRET,
            TWITTER_ACCESS_TOKEN,
            TWITTER_ACCESS_SECRET
        )
        
        # Инициализируем планировщик задач
        self.scheduler = PostScheduler(self.db_manager, self.twitter_api)
        
        # Словарь для хранения данных пользователей во время разговора
        self.user_data = {}

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /start."""
        user = update.effective_user
        await update.message.reply_text(
            f"Привет, {user.first_name}! Я бот для автоматизации публикаций в социальных сетях.\n\n"
            "Вот что я умею:\n"
            "/new_post - Создать новую публикацию\n"
            "/schedule - Запланировать публикацию\n"
            "/history - Посмотреть историю публикаций\n"
            "/delete_post - Удалить публикацию\n"
            "/help - Справка по командам"
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /help."""
        await update.message.reply_text(
            "📱 *Автоматизация публикаций в социальных сетях* 📱\n\n"
            "*Доступные команды:*\n"
            "/new_post - Создать и опубликовать новый пост\n"
            "/schedule - Запланировать публикацию на определенное время\n"
            "/scheduled - Показать список запланированных публикаций\n"
            "/history - Посмотреть историю ваших публикаций\n"
            "/delete_post - Удалить опубликованный пост\n"
            "/cancel - Отменить текущую операцию\n\n"
            "*Поддерживаемые платформы:*\n"
            "- Twitter (текст, изображения, видео)\n\n"
            "*Планирование публикаций:*\n"
            "Вы можете запланировать посты на конкретную дату и время.\n"
            "Формат времени: ДД.ММ.ГГГГ ЧЧ:ММ",
            parse_mode="Markdown"
        )

    async def new_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Начало создания новой публикации."""
        # Создаем клавиатуру для выбора платформы
        keyboard = [
            [InlineKeyboardButton("Twitter", callback_data="platform_twitter")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Выберите платформу для публикации:",
            reply_markup=reply_markup
        )
        
        # Инициализируем данные для нового поста
        user_id = update.effective_user.id
        self.user_data[user_id] = {
            "platform": None,
            "text": None,
            "media_path": None,
            "media_type": None
        }
        
        return CHOOSING_PLATFORM

    async def platform_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка выбора платформы."""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        chosen_platform = query.data.split("_")[1]
        
        self.user_data[user_id]["platform"] = chosen_platform
        
        await query.edit_message_text(
            f"Вы выбрали {chosen_platform.capitalize()}. Теперь отправьте текст вашей публикации:"
        )
        
        return TYPING_MESSAGE

    async def receive_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Получение текста публикации."""
        user_id = update.effective_user.id
        message_text = update.message.text
        
        # Сохраняем текст публикации
        self.user_data[user_id]["text"] = message_text
        
        # Спрашиваем о медиафайле
        keyboard = [
            [InlineKeyboardButton("Пропустить", callback_data="skip_media")],
            [InlineKeyboardButton("Добавить изображение/видео", callback_data="add_media")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Хотите добавить изображение или видео к вашей публикации?",
            reply_markup=reply_markup
        )
        
        return UPLOADING_MEDIA

    async def media_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка решения о добавлении медиафайла."""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        if query.data == "skip_media":
            # Переходим к планированию или публикации
            keyboard = [
                [InlineKeyboardButton("Опубликовать сейчас", callback_data="publish_now")],
                [InlineKeyboardButton("Запланировать", callback_data="schedule_post")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "Опубликовать сейчас или запланировать на будущее?",
                reply_markup=reply_markup
            )
            return SCHEDULING
        else:
            await query.edit_message_text(
                "Пожалуйста, отправьте изображение или видео (отправьте файл):"
            )
            return UPLOADING_MEDIA

    async def receive_media(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Получение медиафайла."""
        user_id = update.effective_user.id
        
        # Определяем тип медиафайла
        if update.message.photo:
            # Для фото берем самое большое изображение
            file_id = update.message.photo[-1].file_id
            media_type = "photo"
        elif update.message.video:
            file_id = update.message.video.file_id
            media_type = "video"
        elif update.message.document:
            file_id = update.message.document.file_id
            # Для документов проверяем MIME-тип
            mime_type = update.message.document.mime_type
            if mime_type and mime_type.startswith("image"):
                media_type = "photo"
            elif mime_type and mime_type.startswith("video"):
                media_type = "video"
            else:
                await update.message.reply_text(
                    "Извините, этот формат файла не поддерживается. "
                    "Пожалуйста, отправьте изображение или видео."
                )
                return UPLOADING_MEDIA
        else:
            await update.message.reply_text(
                "Извините, я не смог распознать этот тип медиафайла. "
                "Пожалуйста, отправьте изображение или видео."
            )
            return UPLOADING_MEDIA
        
        # Скачиваем файл
        file = await context.bot.get_file(file_id)
        file_path = f"media/user_{user_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Создаем папку, если не существует
        os.makedirs("media", exist_ok=True)
        
        if media_type == "photo":
            file_path += ".jpg"
        else:
            file_path += ".mp4"
        
        await file.download_to_drive(file_path)
        
        # Сохраняем путь к файлу и тип
        self.user_data[user_id]["media_path"] = file_path
        self.user_data[user_id]["media_type"] = media_type
        
        # Переходим к планированию или публикации
        keyboard = [
            [InlineKeyboardButton("Опубликовать сейчас", callback_data="publish_now")],
            [InlineKeyboardButton("Запланировать", callback_data="schedule_post")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Медиафайл успешно загружен! Опубликовать сейчас или запланировать на будущее?",
            reply_markup=reply_markup
        )
        
        return SCHEDULING

    async def schedule_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка выбора между немедленной публикацией и планированием."""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        if query.data == "publish_now":
            # Публикуем сейчас
            post_data = self.user_data[user_id]
            platform = post_data["platform"]
            text = post_data["text"]
            media_path = post_data["media_path"]
            media_type = post_data["media_type"]
            
            await query.edit_message_text("Публикую ваш пост...")
            
            # Публикация в зависимости от платформы
            if platform == "twitter":
                if media_path:
                    # Публикация с медиафайлом
                    result = self.twitter_api.post_with_media(text, media_path, media_type)
                else:
                    # Текстовая публикация
                    result = self.twitter_api.post_text(text)
                
                # Проверяем результат
                if result["success"]:
                    # Сохраняем в базу данных
                    self.db_manager.add_post(
                        user_id,
                        platform,
                        text,
                        media_path,
                        result["post_id"],
                        "published"
                    )
                    
                    await query.edit_message_text(
                        f"✅ Успешно опубликовано в {platform.capitalize()}!\n\n"
                        f"ID поста: {result['post_id']}\n"
                        f"Ссылка: {result.get('post_url', 'Недоступно')}"
                    )
                else:
                    await query.edit_message_text(
                        f"❌ Ошибка при публикации в {platform.capitalize()}:\n"
                        f"{result['error']}"
                    )
            
            # Очищаем данные пользователя
            del self.user_data[user_id]
            return ConversationHandler.END
        else:
            # Планируем на будущее
            await query.edit_message_text(
                "Пожалуйста, укажите дату и время для публикации в формате:\n"
                "ДД.ММ.ГГГГ ЧЧ:ММ\n\n"
                "Например: 25.12.2023 15:30"
            )
            return SCHEDULING

    async def receive_schedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Получение даты и времени для запланированной публикации."""
        user_id = update.effective_user.id
        schedule_text = update.message.text
        
        try:
            # Парсим дату и время
            schedule_datetime = datetime.datetime.strptime(schedule_text, "%d.%m.%Y %H:%M")
            
            # Проверяем, что дата в будущем
            if schedule_datetime <= datetime.datetime.now():
                await update.message.reply_text(
                    "❌ Дата должна быть в будущем. Пожалуйста, укажите корректную дату и время:"
                )
                return SCHEDULING
            
            # Получаем данные поста
            post_data = self.user_data[user_id]
            platform = post_data["platform"]
            text = post_data["text"]
            media_path = post_data["media_path"]
            media_type = post_data["media_type"]
            
            # Сохраняем запланированную публикацию в базу данных
            post_id = self.db_manager.add_scheduled_post(
                user_id,
                platform,
                text,
                media_path,
                media_type,
                schedule_datetime
            )
            
            # Добавляем задачу в планировщик
            self.scheduler.schedule_post(post_id, schedule_datetime)
            
            # Форматируем дату и время для отображения
            formatted_datetime = schedule_datetime.strftime("%d.%m.%Y в %H:%M")
            
            await update.message.reply_text(
                f"✅ Публикация успешно запланирована на {formatted_datetime}!\n\n"
                f"Платформа: {platform.capitalize()}\n"
                f"ID запланированной публикации: {post_id}\n\n"
                "Вы можете просмотреть все запланированные публикации с помощью команды /scheduled"
            )
            
            # Очищаем данные пользователя
            del self.user_data[user_id]
            return ConversationHandler.END
            
        except ValueError:
            await update.message.reply_text(
                "❌ Неверный формат даты и времени. Пожалуйста, используйте формат ДД.ММ.ГГГГ ЧЧ:ММ\n"
                "Например: 25.12.2023 15:30"
            )
            return SCHEDULING

    async def show_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показать историю публикаций."""
        user_id = update.effective_user.id
        
        # Получаем историю публикаций из базы данных
        posts = self.db_manager.get_user_posts(user_id)
        
        if not posts:
            await update.message.reply_text(
                "У вас пока нет опубликованных постов."
            )
            return
        
        # Формируем сообщение с историей
        history_text = "📜 *История ваших публикаций:*\n\n"
        
        for i, post in enumerate(posts, 1):
            post_id, platform, text, media_path, social_post_id, status, created_at = post
            
            # Ограничиваем длину текста
            if len(text) > 50:
                text = text[:47] + "..."
            
            # Формируем сообщение о посте
            post_info = (
                f"*{i}. Платформа:* {platform.capitalize()}\n"
                f"*ID:* {social_post_id}\n"
                f"*Статус:* {status}\n"
                f"*Дата:* {created_at}\n"
                f"*Текст:* {text}\n\n"
            )
            
            history_text += post_info
        
        # Добавляем инструкцию по удалению
        history_text += (
            "Чтобы удалить пост, используйте команду:\n"
            "/delete_post [ID поста]"
        )
        
        await update.message.reply_text(
            history_text,
            parse_mode="Markdown"
        )

    async def show_scheduled(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Показать запланированные публикации."""
        user_id = update.effective_user.id
        
        # Получаем запланированные публикации из базы данных
        scheduled_posts = self.db_manager.get_scheduled_posts(user_id)
        
        if not scheduled_posts:
            await update.message.reply_text(
                "У вас нет запланированных публикаций."
            )
            return
        
        # Формируем сообщение с запланированными публикациями
        scheduled_text = "📅 *Запланированные публикации:*\n\n"
        
        for i, post in enumerate(scheduled_posts, 1):
            post_id, platform, text, media_path, media_type, scheduled_time = post
            
            # Ограничиваем длину текста
            if len(text) > 50:
                text = text[:47] + "..."
            
            # Форматируем дату и время
            formatted_time = scheduled_time.strftime("%d.%m.%Y в %H:%M")
            
            # Формируем сообщение о запланированном посте
            post_info = (
                f"*{i}. Платформа:* {platform.capitalize()}\n"
                f"*ID:* {post_id}\n"
                f"*Запланировано на:* {formatted_time}\n"
                f"*Текст:* {text}\n\n"
            )
            
            scheduled_text += post_info
        
        # Добавляем инструкцию по отмене запланированной публикации
        scheduled_text += (
            "Чтобы отменить запланированную публикацию, используйте команду:\n"
            "/cancel_scheduled [ID публикации]"
        )
        
        await update.message.reply_text(
            scheduled_text,
            parse_mode="Markdown"
        )

    async def delete_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Удаление опубликованного поста."""
        if not context.args:
            await update.message.reply_text(
                "❌ Пожалуйста, укажите ID поста для удаления.\n"
                "Например: /delete_post 123456789"
            )
            return
        
        user_id = update.effective_user.id
        post_id = context.args[0]
        
        # Проверяем, существует ли пост с таким ID у пользователя
        post = self.db_manager.get_post_by_id(user_id, post_id)
        
        if not post:
            await update.message.reply_text(
                f"❌ Пост с ID {post_id} не найден или не принадлежит вам."
            )
            return
        
        # Удаляем пост из социальной сети
        platform = post[1]
        social_post_id = post[4]
        
        if platform == "twitter":
            result = self.twitter_api.delete_post(social_post_id)
            
            if result["success"]:
                # Удаляем пост из базы данных
                self.db_manager.delete_post(user_id, post_id)
                
                await update.message.reply_text(
                    f"✅ Пост успешно удален из {platform.capitalize()}!"
                )
            else:
                await update.message.reply_text(
                    f"❌ Ошибка при удалении поста из {platform.capitalize()}:\n"
                    f"{result['error']}"
                )
        else:
            await update.message.reply_text(
                f"❌ Удаление для платформы {platform} не поддерживается."
            )

    async def cancel_scheduled(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Отмена запланированной публикации."""
        if not context.args:
            await update.message.reply_text(
                "❌ Пожалуйста, укажите ID запланированной публикации для отмены.\n"
                "Например: /cancel_scheduled 123"
            )
            return
        
        user_id = update.effective_user.id
        post_id = int(context.args[0])
        
        # Проверяем, существует ли запланированная публикация с таким ID у пользователя
        post = self.db_manager.get_scheduled_post_by_id(user_id, post_id)
        
        if not post:
            await update.message.reply_text(
                f"❌ Запланированная публикация с ID {post_id} не найдена или не принадлежит вам."
            )
            return
        
        # Отменяем публикацию в планировщике
        self.scheduler.cancel_scheduled_post(post_id)
        
        # Удаляем запланированную публикацию из базы данных
        self.db_manager.delete_scheduled_post(user_id, post_id)
        
        await update.message.reply_text(
            "✅ Запланированная публикация успешно отменена!"
        )

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Отмена текущей операции."""
        user_id = update.effective_user.id
        
        # Очищаем данные пользователя, если они существуют
        if user_id in self.user_data:
            del self.user_data[user_id]
        
        await update.message.reply_text(
            "🚫 Операция отменена. Что бы вы хотели сделать дальше?\n\n"
            "Используйте /new_post для создания новой публикации или "
            "/help для просмотра доступных команд."
        )
        
        return ConversationHandler.END

def main():
    """Запуск бота."""
    # Создаем бота
    bot = SocialMediaBot()
    
    # Создаем обработчик разговора для создания публикации
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("new_post", bot.new_post)],
        states={
            CHOOSING_PLATFORM: [
                CallbackQueryHandler(bot.platform_choice, pattern=r"^platform_")
            ],
            TYPING_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_text)
            ],
            UPLOADING_MEDIA: [
                CallbackQueryHandler(bot.media_choice, pattern=r"^(skip_media|add_media)$"),
                MessageHandler(
                    filters.PHOTO | filters.VIDEO | filters.Document.ALL,
                    bot.receive_media
                )
            ],
            SCHEDULING: [
                CallbackQueryHandler(bot.schedule_choice, pattern=r"^(publish_now|schedule_post)$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.receive_schedule)
            ]
        },
        fallbacks=[CommandHandler("cancel", bot.cancel)]
    )
    
    # Создаем приложение и добавляем обработчики
    application = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчик разговора
    application.add_handler(conv_handler)
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CommandHandler("history", bot.show_history))
    application.add_handler(CommandHandler("scheduled", bot.show_scheduled))
    application.add_handler(CommandHandler("delete_post", bot.delete_post))
    application.add_handler(CommandHandler("cancel_scheduled", bot.cancel_scheduled))
    
    # Запускаем планировщик заданий для бота
    bot.scheduler.start()
    
    # Запускаем бота
    application.run_polling()

if __name__ == "__main__":
    main()