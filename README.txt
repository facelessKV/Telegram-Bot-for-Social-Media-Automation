# РУКОВОДСТВО ПО УСТАНОВКЕ И ЗАПУСКУ TELEGRAM-БОТА
# ДЛЯ АВТОМАТИЗАЦИИ ПУБЛИКАЦИЙ В TWITTER

==================================================

## ЧТО НУЖНО ПЕРЕД НАЧАЛОМ:

1. Доступ к интернету
2. Учетная запись в Twitter
3. Учетная запись в Telegram

==================================================

## УСТАНОВКА НА WINDOWS:

1. УСТАНОВИТЕ PYTHON:
   * Скачайте Python 3.9.7 (РЕКОМЕНДУЕМАЯ ВЕРСИЯ) с официального сайта:
     https://www.python.org/downloads/release/python-397/
   * Выберите "Windows installer (64-bit)" или "Windows installer (32-bit)" в зависимости от вашей системы
   * ВАЖНО: Во время установки ОБЯЗАТЕЛЬНО отметьте галочку "Add Python to PATH"
   * Нажмите "Install Now"

2. ПРОВЕРЬТЕ УСТАНОВКУ:
   * Откройте Командную строку (нажмите Win+R, введите cmd, нажмите Enter)
   * Введите: python --version
   * Должно появиться что-то вроде: Python 3.9.7

3. СКАЧАЙТЕ ФАЙЛЫ БОТА:
   * Создайте новую папку на рабочем столе с названием "twitter-bot"
   * Скопируйте все файлы бота в эту папку

4. УСТАНОВИТЕ ЗАВИСИМОСТИ:
   * Откройте Командную строку
   * Перейдите в папку с ботом, например:
     cd C:\Users\ИМЯ_ПОЛЬЗОВАТЕЛЯ\Desktop\twitter-bot
   * Введите:
     pip install -r requirements.txt

5. ПОЛУЧИТЕ API КЛЮЧИ:
   * Для Telegram:
     - Откройте Telegram и найдите @BotFather
     - Отправьте команду /newbot
     - Следуйте инструкциям, чтобы создать бота
     - Сохраните полученный токен

   * Для Twitter:
     - Перейдите на https://developer.twitter.com/
     - Зарегистрируйтесь как разработчик
     - Создайте новый проект и приложение
     - Получите API Key, API Secret, Access Token и Access Secret

6. НАСТРОЙТЕ БОТА:
   * Откройте файл main.py в Блокноте или другом текстовом редакторе
   * Найдите следующие строки (примерно в начале файла):
     ```
     TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_TOKEN")
     TWITTER_API_KEY = os.environ.get("TWITTER_API_KEY", "YOUR_TWITTER_API_KEY")
     TWITTER_API_SECRET = os.environ.get("TWITTER_API_SECRET", "YOUR_TWITTER_SECRET")
     TWITTER_ACCESS_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN", "YOUR_TWITTER_ACCESS_TOKEN")
     TWITTER_ACCESS_SECRET = os.environ.get("TWITTER_ACCESS_SECRET", "YOUR_TWITTER_ACCESS_SECRET")
     ```
   * Замените текст в кавычках на ваши реальные ключи, например:
     ```
     TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "1234567890:AAEzLfSgHiRtAQ_9u8hOFa-QWer321Adlm")
     ```
   * Сохраните файл

7. ЗАПУСТИТЕ БОТА:
   * Откройте Командную строку
   * Перейдите в папку с ботом, например:
     cd C:\Users\ИМЯ_ПОЛЬЗОВАТЕЛЯ\Desktop\twitter-bot
   * Введите:
     python main.py
   * Должно появиться сообщение о том, что бот запущен

==================================================

## УСТАНОВКА НА LINUX:

1. УСТАНОВИТЕ PYTHON:
   * Откройте Терминал (Ctrl+Alt+T в большинстве дистрибутивов)
   * Введите следующие команды:
     ```
     sudo apt update
     sudo apt install python3.9
     sudo apt install python3-pip
     sudo apt install python3.9-venv
     ```

2. ПРОВЕРЬТЕ УСТАНОВКУ:
   * В Терминале введите:
     python3.9 --version
   * Должно появиться что-то вроде: Python 3.9.X

3. СКАЧАЙТЕ ФАЙЛЫ БОТА:
   * Создайте новую папку в домашнем каталоге:
     ```
     mkdir ~/twitter-bot
     cd ~/twitter-bot
     ```
   * Скопируйте все файлы бота в эту папку

4. СОЗДАЙТЕ ВИРТУАЛЬНОЕ ОКРУЖЕНИЕ:
   * В Терминале, находясь в папке twitter-bot, введите:
     ```
     python3.9 -m venv venv
     source venv/bin/activate
     ```
   * В начале строки должно появиться (venv)

5. УСТАНОВИТЕ ЗАВИСИМОСТИ:
   * Введите:
     ```
     pip install -r requirements.txt
     ```

6. ПОЛУЧИТЕ API КЛЮЧИ:
   * Для Telegram:
     - Откройте Telegram и найдите @BotFather
     - Отправьте команду /newbot
     - Следуйте инструкциям, чтобы создать бота
     - Сохраните полученный токен

   * Для Twitter:
     - Перейдите на https://developer.twitter.com/
     - Зарегистрируйтесь как разработчик
     - Создайте новый проект и приложение
     - Получите API Key, API Secret, Access Token и Access Secret

7. НАСТРОЙТЕ БОТА:
   * Откройте файл main.py в текстовом редакторе:
     ```
     nano main.py
     ```
   * Найдите следующие строки (примерно в начале файла):
     ```
     TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_TOKEN")
     TWITTER_API_KEY = os.environ.get("TWITTER_API_KEY", "YOUR_TWITTER_API_KEY")
     TWITTER_API_SECRET = os.environ.get("TWITTER_API_SECRET", "YOUR_TWITTER_SECRET")
     TWITTER_ACCESS_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN", "YOUR_TWITTER_ACCESS_TOKEN")
     TWITTER_ACCESS_SECRET = os.environ.get("TWITTER_ACCESS_SECRET", "YOUR_TWITTER_ACCESS_SECRET")
     ```
   * Замените текст в кавычках на ваши реальные ключи
   * Сохраните файл: Ctrl+O, затем Enter, затем Ctrl+X

8. ЗАПУСТИТЕ БОТА:
   * В Терминале, находясь в папке twitter-bot, введите:
     ```
     python main.py
     ```
   * Должно появиться сообщение о том, что бот запущен

==================================================

## КАК ПОЛЬЗОВАТЬСЯ БОТОМ:

1. Откройте Telegram
2. Найдите вашего бота по имени, которое вы указали при создании
3. Нажмите "Начать" или отправьте команду /start
4. Доступные команды:
   * /start - начало работы с ботом
   * /help - справка по командам
   * /new_post - создание новой публикации
   * /schedule - запланировать публикацию
   * /scheduled - показать список запланированных публикаций
   * /history - посмотреть историю публикаций
   * /delete_post - удалить публикацию
   * /cancel - отменить текущую операцию

==================================================

## УСТРАНЕНИЕ ПРОБЛЕМ:

1. "Python не найден" или "python не является внутренней командой...":
   * Убедитесь, что вы отметили галочку "Add Python to PATH" при установке
   * Попробуйте использовать команду python3 вместо python

2. "Не удалось установить зависимости" или ошибки при установке:
   * Попробуйте установить каждую зависимость отдельно:
     ```
     pip install python-telegram-bot
     pip install tweepy
     ```

3. "Бот не отвечает":
   * Убедитесь, что скрипт бота запущен (командная строка открыта и в ней работает скрипт)
   * Проверьте токен Telegram бота на правильность

4. "Ошибка при публикации в Twitter":
   * Проверьте правильность всех ключей Twitter API
   * Убедитесь, что ваша учетная запись Twitter активна и не заблокирована

==================================================

Если у вас возникли другие проблемы, пожалуйста, обратитесь к разработчику.