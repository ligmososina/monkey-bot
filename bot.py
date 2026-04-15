import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import WebAppInfo, MenuButtonWebApp

TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    raise RuntimeError("Встанови змінну середовища TOKEN")

WEBAPP_URL = "https://ligmososina.github.io/monkey-bot/"

bot = Bot(token=TOKEN)
dp = Dispatcher()

DB_FILE = "db.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f)

def get_player(db, user_id):
    uid = str(user_id)
    if uid not in db:
        db[uid] = {
            "beneny": 0,
            "ryja_mavpy": 0,
            "narkotyczna_mavpy": 0,
            "gattouz_bradar": 0,
            "mavpa_tap": 1
            "last_update": asyncio.get_event_loop().time()
        }
    return db[uid]

def collect_passive(player):
    now = asyncio.get_event_loop().time()
    elapsed = now - player.get("last_update", now)
    player["beneny"] += player.get("ryja_mavpy", 0) * 0.1 * elapsed + player.get("narkotyczna_mavpy", 0) * 0.5 * elapsed + player.get("gattouz_bradar", 0) * 10 * elapsed 
    player["last_update"] = now

@dp.message(Command("start"))
async def start(message: types.Message):
    db = load_db()
    get_player(db, message.from_user.id)
    save_db(db)
    await bot.set_chat_menu_button(
        chat_id=message.chat.id,
        menu_button=MenuButtonWebApp(text="🐵 Макакє", web_app=WebAppInfo(url=WEBAPP_URL))
    )
    await message.answer("🐵 Натисни кнопку нижче щоб грати!")

@dp.message(F.web_app_data)
async def web_app_handler(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        action = data.get("action")
        uid = str(message.from_user.id)
        db = load_db()
        player = get_player(db, uid)
        collect_passive(player)

        if action == "get_state":
            save_db(db)
            await message.answer(json.dumps({
                "beneny": player["beneny"],
                "ryja_mavpy": player["ryja_mavpy"],
                "gattouz_bradar": player["gattouz_bradar"]
            }))

        elif action == "click":
            player["beneny"] += player.get("mavpa_tap", 1)
            save_db(db)
            await message.answer(json.dumps({
                "beneny": player["beneny"],
                "ryja_mavpy": player["ryja_mavpy"],
                "gattouz_bradar": player["gattouz_bradar"],
                "mavpa_tap": player["mavpa_tap"]
            }))

        elif action == "buy_trump":
            trump_price = 10 + player["ryja_mavpy"] * 10
            if player["beneny"] >= trump_price:
                player["beneny"] -= trump_price
                player["ryja_mavpy"] += 1
                save_db(db)
                await message.answer(json.dumps({
                    "success": True,
                    "beneny": player["beneny"],
                    "ryja_mavpy": player["ryja_mavpy"]
                }))
            else:
                await message.answer(json.dumps({
                    "success": False,
                    "need": trump_price,
                    "beneny": player["beneny"]
                }))

    except Exception as e:
        await message.answer(json.dumps({"error": str(e)}))

@dp.message(F.text & ~F.text.startswith("/"))
async def unknown(message: types.Message):
    await message.answer("🐵 Натисни кнопку Макакє щоб грати!")

async def main():
    print("Бот запущено!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())