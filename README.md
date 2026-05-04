# 🎧 Discord Music Bot (Coursework Project)

##  Опис

Цей проєкт — це Discord-бот для відтворення музики у голосових каналах з підтримкою веб-панелі керування.

Бот дозволяє відтворювати музику з YouTube (через yt-dlp), керувати чергою треків, змінювати гучність, а також переглядати поточний стан через веб-інтерфейс.

У проєкті також реалізовані теми курсової роботи: генератори, memoization, priority queue, async функції, event system, proxy та logging decorator.

---

##  Функціонал

*  Відтворення музики (/play)
*  Пошук треків (/search)
*  Пауза / Продовження (/pause, /resume)
*  Пропуск (/skip)
*  Черга (/queue)
*  Пріоритетна черга (/priorityplay)
*  Регулювання гучності
*  Веб-панель керування

---

## 🛠 Використані технології

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
├── bot.py
├── README.md
├── requirements.txt
├── .gitignore
├── .env.example
├── templates/
└── static/
```

---

##  Встановлення

### 1. Клонування репозиторію

```bash
git clone https://github.com/removvi/-OP.git
cd -OP
```

---

### 2. Встановлення залежностей

```bash
pip install -r requirements.txt
```

---

##  Як отримати Discord Bot Token

1. Перейди на сайт:
   https://discord.com/developers/applications

2. Натисни **New Application**

3. Перейди у вкладку **Bot**

4. Натисни **Add Bot**

5. Скопіюйте **Token**
 

---

##  Налаштування .env

Створіть файл `.env` у корені проєкту:

```
TOKEN=YOUR_DISCORD_BOT_TOKEN
```

Файл `.env` не додається в Git (він у `.gitignore`).

---

##  Встановлення FFmpeg

Скачайте FFmpeg:
https://www.gyan.dev/ffmpeg/builds/

Після цього:

* або додайте його в PATH
* або вкажіть шлях у коді:

```python
FFMPEG_PATH = r"C:\path\to\ffmpeg.exe"
```

---

## Запуск

```bash
python bot.py
```

Після запуску:

* бот підключиться до Discord
* веб-панель буде доступна за адресою:

```
http://127.0.0.1:5000
```

---

##  Команди бота

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

## 🧠 Реалізовані теми курсової

* Task 1 — Generators & Iterators
* Task 3 — Memoization
* Task 4 — Priority Queue
* Task 5 — Async operations
* Task 6 — Stream processing
* Task 7 — EventEmitter
* Task 8 — Auth Proxy
* Task 9 — Logging decorator

---

##  Можливі проблеми

###  Бот не заходить у голосовий канал

Встановіть:

```bash
pip install PyNaCl
```

---

###  Музика не грає

Перевірте:

* чи встановлений FFmpeg
* чи бот має права у Discord
* чи ви знаходитесь у голосовому каналі

---

### Token не працює

Можливо Discord його скинув — створіть новий у Developer Portal.

---

## Висновок

У проєкті реалізовано Discord Music Bot з веб-панеллю та інтеграцією алгоритмічних структур і асинхронного програмування.

Проєкт демонструє роботу з Discord API, потоками даних, обробкою аудіо та сучасними підходами до розробки на Python.
