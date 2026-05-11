import threading

from bot.client import create_client
from config import DISCORD_TOKEN
from web.routes import create_web_app


def run_web(app):
    app.run(host="127.0.0.1", port=5000, debug=False)


def main():
    if not DISCORD_TOKEN:
        raise RuntimeError("Не знайдено DISCORD_TOKEN у .env")

    client = create_client()
    web_app = create_web_app(client)

    threading.Thread(target=run_web, args=(web_app,), daemon=True).start()
    client.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
