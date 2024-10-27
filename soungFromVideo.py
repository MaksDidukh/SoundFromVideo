import telebot
import moviepy.editor as mp
import os
import time
from queue import Queue
from threading import Thread

# Вставь сюда токен, который ты получил от BotFather
TOKEN = '7964257155:AAHNo1RMT65aTtEEcGk98FT6HivS2qtSskk'
bot = telebot.TeleBot(TOKEN)

# Очередь для обработки видео
video_queue = Queue()

# Функция для извлечения аудио
def extract_audio(video_path, audio_path):
    video = mp.VideoFileClip(video_path)
    video.audio.write_audiofile(audio_path)
    video.close()

# Функция для обновления сообщения о статусе обработки
def update_status(chat_id, message_id, text):
    bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text)

# Функция обработки видео в очереди
def process_video_queue():
    while True:
        # Извлекаем элемент из очереди
        message, chat_id, message_id = video_queue.get()

        try:
            # Обновляем статус — загружаем видео
            update_status(chat_id, message_id, "🔄 Видео загружается...")

            # Скачиваем видеофайл
            file_info = bot.get_file(message.video.file_id)
            downloaded_file = bot.download_file(file_info.file_path)

            video_filename = f'input_{message.video.file_id}.mp4'
            with open(video_filename, 'wb') as new_file:
                new_file.write(downloaded_file)

            # Обновляем статус — извлекаем звук
            update_status(chat_id, message_id, "🔄 Извлечение аудио...")

            # Извлекаем аудио
            audio_filename = f'output_{message.video.file_id}.mp3'
            extract_audio(video_filename, audio_filename)

            # Обновляем статус — отправка аудио
            update_status(chat_id, message_id, "🔄 Отправка аудио...")

            # Отправляем аудиофайл пользователю
            with open(audio_filename, 'rb') as audio_file:
                bot.send_audio(chat_id, audio_file)

            # Обновляем статус — завершение
            update_status(chat_id, message_id, "✅ Обработка завершена!")

        except Exception as e:
            bot.send_message(chat_id, f'Произошла ошибка при обработке видео: {str(e)}')

        finally:
            # Удаляем временные файлы после обработки
            if os.path.exists(video_filename):
                os.remove(video_filename)
            if os.path.exists(audio_filename):
                os.remove(audio_filename)

            # Сообщаем очереди, что задача выполнена
            video_queue.task_done()

# Запускаем обработчик очереди в отдельном потоке
Thread(target=process_video_queue, daemon=True).start()

# Хендлер на получение видеофайла
@bot.message_handler(content_types=['video'])
def handle_video(message):
    chat_id = message.chat.id

    # Создаем сообщение с информацией о статусе
    status_message = bot.send_message(chat_id, "⏳ Ваша очередь на обработку...")

    # Добавляем видео в очередь для обработки
    video_queue.put((message, chat_id, status_message.message_id))

# Запуск бота
bot.polling()