import os
import openai
import telebot
import time
from pymongo import MongoClient
import json

openai.api_key = os.getenv("OPENAI_API_KEY")
telegram_token = os.getenv("TELEGRAM_TOKEN")
mongo_db = os.getenv("MONGO_INITDB_DATABASE")
temperature = os.getenv("TEMPERATURE")

bot = telebot.TeleBot(telegram_token)

# Подключение к базе данных MongoDB
client = MongoClient("mongodb://mongo:27017/")
db = client[mongo_db]

# Создание коллекции для хранения диалогов
dialogues_collection = db["dialogues"]

# Функция для получения предыдущего диалога из базы данных
def get_previous_dialogue(user_id):
    previous_dialogue = dialogues_collection.find_one({"user_id": user_id})
    if previous_dialogue:
        return json.loads(previous_dialogue["dialogue"])
    else:
        return None

# Функция для сохранения текущего диалога в базе данных
def save_current_dialogue(user_id, dialogue):
    dialogues_collection.replace_one({"user_id": user_id}, {"user_id": user_id, "dialogue": dialogue}, upsert=True)


def log_message(user, message):
    if user == 'user':
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message.from_user.first_name} {message.from_user.last_name}: {message.text}")
    elif user == 'bot':
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] chatGPT-3:{message}")

@bot.message_handler(commands=['start'])
def start_message(message):
    log_message('user', message)
    bot.send_message(
        message.chat.id,
        "Здравствуйте! Чтобы испытать возможности chatGPT, просто задайте интересующий вас вопрос."
    )

@bot.message_handler(commands=['reset'])
def start_message(message):
    log_message('user', message)
    user_id = message.from_user.id
    previous_dialogue = get_previous_dialogue(user_id)
    if previous_dialogue:
        dialogues_collection.delete_one({"user_id": user_id})
    bot.send_message(
        message.chat.id,
        "История успешно очищена!"
    )

@bot.message_handler(content_types=['text'])
def handle(message):
    user_id = message.from_user.id
    previous_dialogue = get_previous_dialogue(user_id)
    prompt = "User: " + message.text + "\nBot: "
    if previous_dialogue:
        prompt = previous_dialogue + prompt

    log_message('user', message)
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=1024,
            n=1,
            stop=None,
            temperature=int(temperature)
        ).get("choices")[0].text
        dialog = prompt + response
        dialog = json.dumps(dialog[-2000:])
        save_current_dialogue(user_id, dialog)
        log_message('bot', response)
        bot.send_message(message.chat.id, response)
    except openai.error.ServiceUnavailableError as e:
        # Handle the exception
        print("Service Unavailable:", e)
        bot.send_message(message.chat.id, "OpenAI перегружен. Попробуйте повторить свой вопрос через несколько минут.")


print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Bot started!")
bot.polling(none_stop=True)
