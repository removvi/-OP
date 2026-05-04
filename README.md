# Курсова робота: Discord Music Bot з веб-панеллю та алгоритмічними модулями
#  Discord Music Bot (Coursework Project)

##  Опис

Цей проєкт — це Discord-бот для відтворення музики у голосових каналах з підтримкою веб-панелі керування.

Бот дозволяє відтворювати музику з YouTube (через yt-dlp), керувати чергою треків, змінювати гучність, а також переглядати поточний стан через веб-інтерфейс.

Проєкт також містить реалізації алгоритмічних та архітектурних тем курсової роботи (generators, memoization, priority queue, async, event system, proxy, logging).

---

##  Функціонал

*  Відтворення музики (/play)
*  Пошук треків (/search)
*  Пауза /  Продовження (/pause, /resume)
*  Пропуск (/skip)
*  Черга (/queue)
*  Пріоритетна черга (/priorityplay)
*  Регулювання гучності
*  Веб-панель керування (Flask)

---

##  Використані технології

* Python
* discord.py
* yt-dlp
* Flask
* FFmpeg
* asyncio
* python-dotenv

---

##  Структура проєкту

```
-OP/
│
├── bot.py
├── requirements.txt
├── .env.example
├── README.md
├── .gitignore
│
├── templates/
└── static/
```

---

## ⚙️ Встановлення

### 1. Клонування репозиторію

```
git clone https://github.com/removvi/-OP.git
cd ".\-OP"
```

---

### 2. Встановлення залежностей

```
pip install -r requirements.txt
```

---

### 3. Встановлення FFmpeg

Скачати FFmpeg:

 https://www.gyan.dev/ffmpeg/builds/

Після цього:

* або додати його в PATH
* або вказати шлях у коді:

```python
FFMPEG_PATH = r"C:\path\to\ffmpeg.exe"
```

---

##  Як отримати Discord Bot Token

1. Перейти на сайт:
    https://discord.com/developers/applications

2. Натиснути **"New Application"**

3. Перейти у вкладку **Bot**

4. Натиснути **"Add Bot"**

5. Скопіюйте **Token**


##  Налаштування .env

Створити файл `.env` у корені проєкту:

```
TOKEN=YOUR_DISCORD_BOT_TOKEN
```

---

## Запуск

```
python bot.py
```

Після запуску:

* бот зʼявиться у Discord
* веб-панель буде доступна на:

 http://127.0.0.1:5000

---

##  Команди

| Команда | Опис            |
| ------- | --------------- |
| /join   | Підключити бота |
| /play   | Відтворити трек |
| /search | Пошук треків    |
| /skip   | Пропустити      |
| /pause  | Пауза           |
| /resume | Продовжити      |
| /queue  | Черга           |
| /now    | Поточний трек   |
| /leave  | Вийти           |

---

##  Реалізовані теми курсової

* Task 1 — Generators & Iterators
* Task 3 — Memoization (LRU cache)
* Task 4 — Priority Queue
* Task 5 — Async operations
* Task 6 — Stream processing (FFmpeg)
* Task 7 — EventEmitter
* Task 8 — Auth Proxy
* Task 9 — Logging decorator


##  Висновок

У проєкті реалізовано повноцінного Discord Music Bot з веб-панеллю та інтеграцією алгоритмічних структур і асинхронного програмування.

Проєкт демонструє практичне застосування Python, роботи з API, потоків даних та архітектурних патернів.

