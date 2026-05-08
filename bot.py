import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from PIL import Image, ImageDraw
import asyncio
import io
import re

TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

def parse_request(text):
    match = re.match(r'(\d+)x(\d+)\s+(\w+)', text.lower())
    if match:
        width = int(match.group(1))
        height = int(match.group(2))
        color_name = match.group(3)
        return width, height, color_name
    return None

COLORS = {
    "sariq": "yellow",
    "qizil": "red",
    "yashil": "green",
    "ko'k": "blue",
    "oq": "white",
    "qora": "black",
    "to'q sariq": "orange",
    "binafsha": "purple",
    "pushti": "pink",
    "kulrang": "gray",
}

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Salom! 👋\nMenga rasm o'lchamini va rangini yozing!\nMasalan: 800x800 sariq")

@dp.message()
async def generate_image(message: types.Message):
    result = parse_request(message.text)
    if result:
        width, height, color_name = result
        color = COLORS.get(color_name, color_name)
        img = Image.new("RGB", (width, height), color=color)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        await message.answer_document(
            types.BufferedInputFile(buf.read(), filename=f"{width}x{height}_{color_name}.png")
        )
    else:
        await message.answer("Noto'g'ri format!\nMasalan: 800x800 sariq")

async def main():
    await dp.start_polling(bot)

asyncio.run(main())