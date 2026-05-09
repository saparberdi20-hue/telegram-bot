
import os
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from PIL import Image
from rembg import remove
import asyncio
import io
import re

TOKEN = "8743646770:AAHLdAzyxmXugXPpJh2CjXCB65SU5FAoi3E"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ===================== DOMINO O'YINI =====================

games = {}  # Foydalanuvchilar o'yinlari

def create_domino_set():
    tiles = []
    for i in range(7):
        for j in range(i, 7):
            tiles.append((i, j))
    random.shuffle(tiles)
    return tiles

def tile_str(tile):
    return f"[{tile[0]}|{tile[1]}]"

def bot_move(game):
    board_left = game['board'][0][0]
    board_right = game['board'][-1][1]
    for tile in game['bot_hand']:
        if tile[0] == board_right:
            game['bot_hand'].remove(tile)
            game['board'].append(tile)
            return f"Bot {tile_str(tile)} qo'ydi ➡️"
        elif tile[1] == board_right:
            game['bot_hand'].remove(tile)
            game['board'].append((tile[1], tile[0]))
            return f"Bot {tile_str(tile)} qo'ydi ➡️"
        elif tile[1] == board_left:
            game['bot_hand'].remove(tile)
            game['board'].insert(0, tile)
            return f"Bot {tile_str(tile)} qo'ydi ⬅️"
        elif tile[0] == board_left:
            game['bot_hand'].remove(tile)
            game['board'].insert(0, (tile[1], tile[0]))
            return f"Bot {tile_str(tile)} qo'ydi ⬅️"
    if game['pile']:
        drawn = game['pile'].pop()
        game['bot_hand'].append(drawn)
        return f"Bot tortdi 🎴"
    return "Bot o'tkizdi ⏭"

def game_board_text(game, user_id):
    board_str = " ".join(tile_str(t) for t in game['board'][-5:])
    hand = game['player_hand'] if game['mode'] == 'bot' else game['hands'][user_id]
    hand_str = " ".join(tile_str(t) for t in hand)
    left = game['board'][0][0]
    right = game['board'][-1][1]
    text = (
        f"🎲 DOMINO O'YINI\n\n"
        f"📋 Taxta: ...{board_str}\n"
        f"⬅️ Chap: {left} | O'ng: {right} ➡️\n\n"
        f"🃏 Sizning qo'lingiz:\n{hand_str}\n\n"
    )
    if game['mode'] == 'bot':
        text += f"🤖 Bot qo'lida: {len(game['bot_hand'])} ta tosh\n"
        text += f"🎴 Uyumda: {len(game['pile'])} ta tosh"
    return text

def player_keyboard(game, user_id):
    hand = game['player_hand'] if game['mode'] == 'bot' else game['hands'][user_id]
    left = game['board'][0][0]
    right = game['board'][-1][1]
    buttons = []
    for i, tile in enumerate(hand):
        can_play = (tile[0] == left or tile[1] == left or
                    tile[0] == right or tile[1] == right)
        if can_play:
            buttons.append([InlineKeyboardButton(
                text=f"✅ {tile_str(tile)}",
                callback_data=f"play_{i}"
            )])
    buttons.append([InlineKeyboardButton(text="🎴 Tortib olish", callback_data="draw")])
    buttons.append([InlineKeyboardButton(text="⏭ O'tkazib yuborish", callback_data="skip")])
    buttons.append([InlineKeyboardButton(text="🚪 O'yindan chiqish", callback_data="quit_game")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ===================== RASM FUNKSIYALARI =====================

def parse_request(text):
    if not text:
        return None
    match = re.match(r'(\d+)x(\d+)\s+(\w+)', text.lower())
    if match:
        width = int(match.group(1))
        height = int(match.group(2))
        color_name = match.group(3)
        return width, height, color_name
    return None

COLORS = {
    "sariq": "yellow", "qizil": "red", "yashil": "green",
    "kok": "blue", "oq": "white", "qora": "black",
    "sariq2": "orange", "binafsha": "purple",
    "pushti": "pink", "kulrang": "gray",
}

# ===================== HANDLERLAR =====================

@dp.message(Command("start"))
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎨 Rasm yaratish", callback_data="rasm_yaratish")],
        [InlineKeyboardButton(text="🖼 Rasm fonini o'chirish", callback_data="fon_ochirish")],
        [InlineKeyboardButton(text="🎲 O'yin", callback_data="oyin")]
    ])
    await message.answer(
        "Salom! 👋\n\nQuyidagi bo'limlardan birini tanlang:",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "oyin")
async def oyin_menu(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Botga qarshi", callback_data="start_bot_game")],
        [InlineKeyboardButton(text="👥 2 kishi birga", callback_data="start_multi_game")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_main")]
    ])
    await callback.message.edit_text(
        "🎲 DOMINO O'YINI\n\nQanday o'ynaysiz?",
        reply_markup=keyboard
    )
    await callback.answer()

@dp.callback_query(F.data == "start_bot_game")
async def start_bot_game(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    tiles = create_domino_set()
    player_hand = tiles[:7]
    bot_hand = tiles[7:14]
    pile = tiles[14:]
    first_tile = player_hand.pop(0)
    games[user_id] = {
        'mode': 'bot',
        'board': [first_tile],
        'player_hand': player_hand,
        'bot_hand': bot_hand,
        'pile': pile,
        'turn': 'player'
    }
    game = games[user_id]
    text = game_board_text(game, user_id)
    await callback.message.edit_text(
        text + "\n\n🟢 Sizning navbatingiz!",
        reply_markup=player_keyboard(game, user_id)
    )
    await callback.answer()

@dp.callback_query(F.data == "start_multi_game")
async def start_multi_game(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "👥 2 kishilik o'yin\n\n"
        "Do'stingizga shu buyruqni yuboring:\n"
        f"/join_{callback.from_user.id}\n\n"
        "Do'stingiz qo'shilishini kuting... ⏳"
    )
    user_id = callback.from_user.id
    tiles = create_domino_set()
    games[f"wait_{user_id}"] = {
        'mode': 'multi',
        'host': user_id,
        'tiles': tiles
    }
    await callback.answer()

@dp.message(lambda m: m.text and m.text.startswith("/join_"))
async def join_game(message: types.Message):
    try:
        host_id = int(message.text.split("_")[1])
        wait_key = f"wait_{host_id}"
        if wait_key not in games:
            await message.answer("O'yin topilmadi! ❌")
            return
        guest_id = message.from_user.id
        if guest_id == host_id:
            await message.answer("O'z o'yiningizga qo'shila olmaysiz! ❌")
            return
        tiles = games[wait_key]['tiles']
        hand1 = tiles[:7]
        hand2 = tiles[7:14]
        pile = tiles[14:]
        first_tile = hand1.pop(0)
        game_id = f"multi_{host_id}_{guest_id}"
        game = {
            'mode': 'multi',
            'board': [first_tile],
            'hands': {host_id: hand1, guest_id: hand2},
            'pile': pile,
            'turn': host_id,
            'players': [host_id, guest_id]
        }
        games[host_id] = game
        games[guest_id] = game
        del games[wait_key]
        text = game_board_text(game, host_id)
        await bot.send_message(
            host_id,
            text + "\n\n🟢 Sizning navbatingiz!",
            reply_markup=player_keyboard(game, host_id)
        )
        await message.answer(
            game_board_text(game, guest_id) + "\n\n⏳ Raqibingiz navbati..."
        )
    except Exception as e:
        await message.answer("Xato yuz berdi! ❌")

@dp.callback_query(F.data.startswith("play_"))
async def play_tile(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in games:
        await callback.answer("O'yin topilmadi!")
        return
    game = games[user_id]
    if game['mode'] == 'multi' and game['turn'] != user_id:
        await callback.answer("Hozir sizning navbatingiz emas! ⏳")
        return
    tile_idx = int(callback.data.split("_")[1])
    hand = game['player_hand'] if game['mode'] == 'bot' else game['hands'][user_id]
    if tile_idx >= len(hand):
        await callback.answer("Noto'g'ri tosh!")
        return
    tile = hand[tile_idx]
    left = game['board'][0][0]
    right = game['board'][-1][1]
    placed = False
    if tile[0] == right:
        game['board'].append(tile)
        placed = True
    elif tile[1] == right:
        game['board'].append((tile[1], tile[0]))
        placed = True
    elif tile[1] == left:
        game['board'].insert(0, tile)
        placed = True
    elif tile[0] == left:
        game['board'].insert(0, (tile[1], tile[0]))
        placed = True
    if not placed:
        await callback.answer("Bu toshni qo'yib bo'lmaydi! ❌")
        return
    hand.pop(tile_idx)
    if not hand:
        await callback.message.edit_text("🏆 TABRIKLAYMAN! Siz yutdingiz! 🎉")
        del games[user_id]
        await callback.answer()
        return
    if game['mode'] == 'bot':
        bot_result = bot_move(game)
        if not game['bot_hand']:
            await callback.message.edit_text("😔 Bot yutdi! Keyingi safar omad!")
            del games[user_id]
            await callback.answer()
            return
        text = game_board_text(game, user_id)
        await callback.message.edit_text(
            text + f"\n\n🤖 {bot_result}\n\n🟢 Sizning navbatingiz!",
            reply_markup=player_keyboard(game, user_id)
        )
    else:
        players = game['players']
        next_player = players[1] if players[0] == user_id else players[0]
        game['turn'] = next_player
        await callback.message.edit_text(
            game_board_text(game, user_id) + "\n\n⏳ Raqibingiz navbati..."
        )
        await bot.send_message(
            next_player,
            game_board_text(game, next_player) + "\n\n🟢 Sizning navbatingiz!",
            reply_markup=player_keyboard(game, next_player)
        )
    await callback.answer()

@dp.callback_query(F.data == "draw")
async def draw_tile(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in games:
        await callback.answer("O'yin topilmadi!")
        return
    game = games[user_id]
    if not game['pile']:
        await callback.answer("Uyumda tosh qolmadi! ❌")
        return
    hand = game['player_hand'] if game['mode'] == 'bot' else game['hands'][user_id]
    drawn = game['pile'].pop()
    hand.append(drawn)
    text = game_board_text(game, user_id)
    await callback.message.edit_text(
        text + f"\n\n🎴 {tile_str(drawn)} tortib oldingiz!\n\n🟢 Sizning navbatingiz!",
        reply_markup=player_keyboard(game, user_id)
    )
    await callback.answer()

@dp.callback_query(F.data == "skip")
async def skip_turn(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in games:
        await callback.answer("O'yin topilmadi!")
        return
    game = games[user_id]
    if game['mode'] == 'bot':
        bot_result = bot_move(game)
        text = game_board_text(game, user_id)
        await callback.message.edit_text(
            text + f"\n\n🤖 {bot_result}\n\n🟢 Sizning navbatingiz!",
            reply_markup=player_keyboard(game, user_id)
        )
    else:
        players = game['players']
        next_player = players[1] if players[0] == user_id else players[0]
        game['turn'] = next_player
        await callback.message.edit_text(
            game_board_text(game, user_id) + "\n\n⏭ O'tkazdingiz. Raqibingiz navbati..."
        )
        await bot.send_message(
            next_player,
            game_board_text(game, next_player) + "\n\n🟢 Sizning navbatingiz!",
            reply_markup=player_keyboard(game, next_player)
        )
    await callback.answer()

@dp.callback_query(F.data == "quit_game")
async def quit_game(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id in games:
        del games[user_id]
    await callback.message.edit_text("🚪 O'yindan chiqdingiz!")
    await callback.answer()

@dp.callback_query(F.data == "rasm_yaratish")
async def rasm_yaratish(callback: types.CallbackQuery):
    await callback.message.answer("🎨 Rasm o'lchamini va rangini yozing!\nMasalan: 800x800 sariq")
    await callback.answer()

@dp.callback_query(F.data == "fon_ochirish")
async def fon_ochirish(callback: types.CallbackQuery):
    await callback.message.answer("🖼 Menga rasm yuboring — fonini o'chirib PNG qilib beraman!")
    await callback.answer()

@dp.callback_query(F.data == "back_main")
async def back_main(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎨 Rasm yaratish", callback_data="rasm_yaratish")],
        [InlineKeyboardButton(text="🖼 Rasm fonini o'chirish", callback_data="fon_ochirish")],
        [InlineKeyboardButton(text="🎲 O'yin", callback_data="oyin")]
    ])
    await callback.message.edit_text(
        "Salom! 👋\n\nQuyidagi bo'limlardan birini tanlang:",
        reply_markup=keyboard
    )
    await callback.answer()

@dp.message()
async def handle_message(message: types.Message):
    if message.photo:
        await message.answer("⏳ Fon o'chirilmoqda, kuting...")
        file = await bot.get_file(message.photo[-1].file_id)
        file_bytes = await bot.download_file(file.file_path)
        output = remove(file_bytes.read())
        await message.answer_document(
            types.BufferedInputFile(output, filename="result.png")
        )
    elif message.text:
        result = parse_request(message.text)
        if result:
            width, height, color_name = result
            color = COLORS.get(color_name, color_name)
            img = Image.new("RGB", (width, height), color=color)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            await message.answer_document(
                types.BufferedInputFile(buf.read(), filename="result.png")
            )
        else:
            await message.answer("Notogri format! Masalan: 800x800 sariq")

async def main():
    await dp.start_polling(bot)

asyncio.run(main())