import random
import webbrowser
import pyttsx3
import speech_recognition as sr
import json
import os
from vosk import Model, KaldiRecognizer
import wave

# Глобальные переменные для хранения текущих языков
current_recognition_language = "ru-RU"  # По умолчанию русский
current_speech_language = "ru"  # По умолчанию русский

# Глобальные переменные
recognizer = sr.Recognizer()
microphone = sr.Microphone()
ttsEngine = pyttsx3.init()

# Загрузка команд из JSON
def load_commands_from_json():
    try:
        with open("commands.json", "r", encoding="utf-8") as f:
            commands = json.load(f)
            print("Команды успешно загружены из файла.")
            return commands
    except FileNotFoundError:
        print("Ошибка: файл 'commands.json' не найден.")
        return {}
    except json.JSONDecodeError:
        print("Ошибка: не удается декодировать JSON в файле 'commands.json'.")
        return {}
    except Exception as e:
        print(f"Неизвестная ошибка при загрузке команд: {e}")
        return {}

# Загрузка команд
commands = load_commands_from_json()

# Настройка голоса
def setup_assistant_voice(language="ru"):
    voices = ttsEngine.getProperty("voices")
    print("Доступные голоса:")
    for voice in voices:
        print(f"ID: {voice.id}, Name: {voice.name}")

    # Меняем голос в зависимости от языка
    if language == "en":
        ttsEngine.setProperty("voice", voices[1].id)  # English voice
    else:
        ttsEngine.setProperty("voice", voices[0].id)  # Russian voice

# Проигрывание речи
def play_voice_assistant_speech(text_to_speech):
    ttsEngine.say(str(text_to_speech))
    ttsEngine.runAndWait()

# Смена языка распознавания и синтеза речи
def change_language(new_language="ru"):
    global current_recognition_language, current_speech_language
    
    if new_language == "en":
        current_recognition_language = "en-US"
        current_speech_language = "en"
    else:
        current_recognition_language = "ru-RU"
        current_speech_language = "ru"
    
    # Настройка голоса на новый язык
    setup_assistant_voice(language=current_speech_language)
    
    # Приветствие на новом языке
    if new_language == "en":
        play_voice_assistant_speech("I am changing the language to English.")
    else:
        play_voice_assistant_speech("Я меняю язык на русский.")

    print(f"Язык изменен на: {new_language}")

# Приветствие
def play_greetings(*args):
    play_voice_assistant_speech("Привет! Как я могу помочь?")

# Прощание и выход
def play_farewell_and_quit(*args):
    play_voice_assistant_speech("До свидания! Хорошего дня")
    exit()

# Поиск в Google
def search_for_term_on_google(*args):
    search_term = " ".join(args)
    url = f"https://www.google.com/search?q={search_term}"
    webbrowser.get().open(url)
    play_voice_assistant_speech(f"Я ищу {search_term} в Google.")

# Подбросить монетку
def drop_coin(*args):
    result = "Орел" if random.choice([True, False]) else "Решка"
    play_voice_assistant_speech(f"Выпало: {result}")

# Запись и распознавание аудио
def record_and_recognize_audio(*args: tuple):
    with microphone:
        recognized_data = ""
        recognizer.adjust_for_ambient_noise(microphone, duration=2)

        try:
            print("Listening...")
            audio = recognizer.listen(microphone, 5, 5)

            with open("microphone-results.wav", "wb") as file:
                file.write(audio.get_wav_data())
        except sr.WaitTimeoutError:
            print("Can you check if your microphone is on, please?")
            return ""
        
        try:
            print("Started recognition...")
            recognized_data = recognizer.recognize_google(audio, language=current_recognition_language).lower()
            print(f"Распознано: {recognized_data}")
        except sr.UnknownValueError:
            pass
        except sr.RequestError:
            print("Trying to use offline recognition...")
            recognized_data = use_offline_recognition()

        return recognized_data.strip()

# Оффлайн распознавание
def use_offline_recognition():
    recognized_data = ""
    try:
        if not os.path.exists("models/vosk-model-small-ru-0.4"):
            print("Please download the model from the specified URL and unpack it in the 'models' folder.")
            exit(1)

        wave_audio_file = wave.open("microphone-results.wav", "rb")
        model = Model("models/vosk-model-small-ru-0.4")
        offline_recognizer = KaldiRecognizer(model, wave_audio_file.getframerate())

        data = wave_audio_file.readframes(wave_audio_file.getnframes())
        if len(data) > 0:
            if offline_recognizer.AcceptWaveform(data):
                recognized_data = offline_recognizer.Result()
                recognized_data = json.loads(recognized_data)
                recognized_data = recognized_data["text"]
    except Exception as e:
        print(f"Error with offline speech recognition: {e}")
    return recognized_data

# Выполнение команды по имени
def execute_command_with_name(command_name: str, *args: list):
    print(f"Ищем команду: {command_name}")
    for key, command in commands.items():
        if any(command_name in example for example in command["examples"]):
            print(f"Команда {command_name} найдена, выполняем {command['responses']}")
            function_name = command["responses"]
            if function_name in globals():
                globals()[function_name](*args)
            break
    else:
        print("Команда не найдена.")
        play_voice_assistant_speech("Извините, я вас не понял")

# Главная часть программы
if __name__ == "__main__":
    setup_assistant_voice(language="ru")  # По умолчанию русский язык

    while True:
        voice_input = record_and_recognize_audio()
        
        # Check if the file exists before deleting it
        if os.path.exists("microphone-results.wav"):
            os.remove("microphone-results.wav")
        
        print(f"Вы сказали: {voice_input}")

        if not voice_input:
            continue

        voice_input = voice_input.split(" ")
        command = voice_input[0]
        command_options = voice_input[1:]

        # Обработка команды смены языка
        if "сменить" in voice_input or "поменяй" in voice_input or "переключить" in voice_input:
            if "английский" in voice_input:
                change_language("en")
            elif "русский" in voice_input:
                change_language("ru")
            else:
                play_voice_assistant_speech("Не могу понять, на какой язык нужно переключиться.")
        else:
            execute_command_with_name(command, *command_options)
