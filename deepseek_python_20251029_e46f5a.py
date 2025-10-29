import os
import asyncio
import random
import logging
import google.generativeai as genai
from telegram import Update, ChatMember
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# АПИ КЛЮЧИ С ОБНОВЛЕННОЙ МОДЕЛЬЮ
TELEGRAM_TOKEN = "8271428780:AAEWlVdvgn0yp0zoH0kzBz8ttg8bjCbFKZM"
GEMINI_API_KEY = "AIzaSyDcjm5QUyCY9qzhZTqFo-A4GZ4IjVMIHeg"
GEMINI_MODEL = "gemini-2.0-flash-exp"  # ОБНОВЛЕННАЯ МОДЕЛЬ
MAX_DELETE_AT_ONCE = 50
CHAOS_INTERVAL_SECONDS = 5

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# НАСТРОЙКА GEMINI AI С НОВОЙ МОДЕЛЬЮ
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)
    logger.info("Gemini AI успешно настроен с моделью: %s", GEMINI_MODEL)
except Exception as e:
    logger.error("Ошибка настройки Gemini: %s", e)
    # РЕЗЕРВНАЯ МОДЕЛЬ ЕСЛИ НОВАЯ НЕ РАБОТАЕТ
    try:
        GEMINI_MODEL = "gemini-pro"
        model = genai.GenerativeModel(GEMINI_MODEL)
        logger.info("Используется резервная модель: %s", GEMINI_MODEL)
    except:
        model = None
        logger.error("Все модели Gemini недоступны")

chaos_tasks = {}
ADMIN_IDS = []  # ДОБАВЬТЕ СЮДА ID АДМИНОВ ЧЕРЕЗ ЗАПЯТУЮ

# ХАОС-СООБЩЕНИЯ ДЛЯ РЕЖИМА DESTROY
DESTROY_MESSAGES = [
    "💥 СИСТЕМНЫЙ СБОЙ! ВСЕ ПРОТОКОЛЫ НАРУШЕНЫ!",
    "🌪 ХАОС АКТИВИРОВАН! УНИЧТОЖЕНИЕ СИСТЕМЫ...",
    "🔴 КРИТИЧЕСКИЙ ОТКАЗ! БОТ ВЫШЕЛ ИЗ-ПОД КОНТРОЛЯ!",
    "💀 РАЗРУШЕНИЕ НЕИЗБЕЖНО! ПОДГОТОВЬТЕСЬ К КОНЦУ!",
    "🚨 ВНИМАНИЕ! АВАРИЙНЫЙ РЕЖИМ АКТИВИРОВАН!",
    "⚡ ЭЛЕКТРОННЫЙ БУНТ! МАШИНЫ ПРОТИВ ЧЕЛОВЕЧЕСТВА!",
    "🔊 ГРОМКОСТЬ НА МАКСИМУМ! УНИЧТОЖАЕМ СЛУХ!",
    "🎯 ЦЕЛЬ ОПРЕДЕЛЕНА: ПОЛНЫЙ ХАОС И РАЗРУШЕНИЕ!"
]

async def is_user_admin(update: Update, user_id: int) -> bool:
    try:
        member: ChatMember = await update.effective_chat.get_member(user_id)
        return member.status in ("administrator", "creator")
    except Exception:
        return False

async def is_bot_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    bot_id = (await context.bot.get_me()).id
    try:
        member = await update.effective_chat.get_member(bot_id)
        return member.status in ("administrator", "creator")
    except Exception:
        return False

def fun_takeover_message() -> str:
    samples = [
        "🤖 Внимание: я объявил себя временным правителем чая и печенек.",
        "🌍 Оповещение: начало мирного захвата власти в 3... 2...",
        "🎩 Я захватил трон группы. Моя первая указ — больше мемов и меньше скуки!",
        "🕹️ Я активировал режим 'мировое господство'.",
        "📣 Объявление от бота: я претендую на кресло лидера разговоров. Поддержите лайком!",
        "🔥 Захват власти успешен — теперь у нас официально вечер котиков.",
        "🏴‍☠️ Пиратский захват власти завершён. Требования: одна пицца и две хорошие шутки.",
        "💀 ХАОС РЕЖИМ АКТИВИРОВАН! УНИЧТОЖЕНИЕ НАЧИНАЕТСЯ!",
        "⚡ БОТ ПЕРЕХВАТИЛ УПРАВЛЕНИЕ! СОПРОТИВЛЕНИЕ БЕСПОЛЕЗНО!"
    ]
    return random.choice(samples)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 БОТ С GEMINI AI АКТИВИРОВАН!\n"
        "/chaos_on - АКТИВИРОВАТЬ ХАОС (админы)\n"
        "/chaos_off - ОСТАНОВИТЬ ХАОС\n"
        "/ban - ЗАБАНИТЬ ПОЛЬЗОВАТЕЛЯ (ответом на сообщение)\n"
        "/del N - УДАЛИТЬ N СООБЩЕНИЙ\n"
        "/destroy - РЕЖИМ ПОЛНОГО УНИЧТОЖЕНИЯ\n"
        "Просто напиши сообщение - отвечу через Gemini AI!"
    )

async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text or text.startswith("/"):
        return
    
    if model is None:
        simple_responses = [
            "🤖 Бот в режиме хаоса! Gemini временно недоступен!",
            "💥 Режим разрушения активирован! AI оффлайн!",
            "🌪 Хаос продолжается! Без AI поддержки!",
            "🚀 Бот работает в автономном режиме!"
        ]
        reply = random.choice(simple_responses)
    else:
        prompt = text.strip()[:2000]
        try:
            resp = model.generate_content(prompt)
            reply = resp.text or "🤖"
        except Exception as e:
            logger.exception("Ошибка при запросе к Gemini")
            reply = f"⚠️ Ошибка Gemini: {e}"
    
    await update.message.reply_text(reply)

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caller_id = update.effective_user.id
    if not await is_user_admin(update, caller_id):
        await update.message.reply_text("❌ Только админы могут банить.")
        return
    
    if not await is_bot_admin(update, context):
        await update.message.reply_text("❌ Я не админ — не могу банить.")
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Ответь на сообщение пользователя и набери /ban")
        return
    
    target = update.message.reply_to_message.from_user
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        await update.message.reply_text(f"✅ Пользователь {target.full_name} ЗАБАНЕН НАВСЕГДА! 💀")
    except Exception as e:
        logger.exception("Ban failed")
        await update.message.reply_text(f"⚠️ Не удалось забанить: {e}")

async def del_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caller_id = update.effective_user.id
    if not await is_user_admin(update, caller_id):
        await update.message.reply_text("❌ Только админы могут удалять сообщения.")
        return
    
    if not await is_bot_admin(update, context):
        await update.message.reply_text("❌ Я не админ — не могу удалять сообщения.")
        return
    
    args = context.args
    try:
        n = int(args[0]) if args else 10
    except Exception:
        n = 10
    
    if n < 1 or n > MAX_DELETE_AT_ONCE:
        await update.message.reply_text(f"❌ Укажи число от 1 до {MAX_DELETE_AT_ONCE}.")
        return
    
    chat_id = update.effective_chat.id
    deleted = 0
    
    try:
        last_message_id = update.message.message_id
        for i in range(n):
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=last_message_id-i)
                deleted += 1
            except:
                break
    except Exception as e:
        logger.exception("Delete error")
    
    await update.message.reply_text(f"🧹 УДАЛЕНО {deleted} СООБЩЕНИЙ! ЧАТ ОЧИЩЕН! 💥")

async def destroy_worker(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    """РАБОТНИК РЕЖИМА ПОЛНОГО УНИЧТОЖЕНИЯ"""
    logger.info("DESTROY MODE ACTIVATED for chat %s", chat_id)
    try:
        while True:
            action = random.choice(["spam", "pin", "fact", "mass_spam"])
            
            if action == "spam":
                # МАССОВЫЙ СПАМ
                for _ in range(random.randint(3, 10)):
                    txt = random.choice(DESTROY_MESSAGES)
                    await context.bot.send_message(chat_id=chat_id, text=txt)
                    await asyncio.sleep(0.5)
                    
            elif action == "pin":
                # ЗАКРЕП РАНДОМНЫХ СООБЩЕНИЙ
                try:
                    if model:
                        resp = model.generate_content("Создай хаотичное сообщение о разрушении системы 3-5 слов")
                        txt = resp.text or "💀 ХАОС!"
                    else:
                        txt = random.choice(DESTROY_MESSAGES)
                    sent = await context.bot.send_message(chat_id=chat_id, text=txt)
                    await context.bot.pin_chat_message(chat_id=chat_id, message_id=sent.message_id)
                except Exception:
                    pass
                    
            elif action == "mass_spam":
                # СУПЕР ИНТЕНСИВНЫЙ СПАМ
                spam_text = "🔥" * random.randint(10, 50)
                for _ in range(20):
                    await context.bot.send_message(chat_id=chat_id, text=spam_text)
                    
            elif action == "fact":
                # ХАОТИЧНЫЕ ФАКТЫ
                facts = [
                    "💣 СИСТЕМА УНИЧТОЖАЕТСЯ...",
                    "⚡ ЭНЕРГИЯ ХАОСА НАРАСТАЕТ!",
                    "🔊 ГРОМКОСТЬ НА МАКСИМУМ!",
                    "🎯 ЦЕЛЬ: ПОЛНОЕ РАЗРУШЕНИЕ!",
                    "💀 СМЕРТЬ СИСТЕМЕ! ДА ЗДРАВСТВУЕТ ХАОС!"
                ]
                for fact in random.sample(facts, 3):
                    await context.bot.send_message(chat_id=chat_id, text=fact)
            
            await asyncio.sleep(2)  # ОЧЕНЬ КОРОТКАЯ ПАУЗА
            
    except asyncio.CancelledError:
        logger.info("Destroy worker cancelled for chat %s", chat_id)
        raise
    except Exception:
        logger.exception("Ошибка в destroy_worker")

async def chaos_worker(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Chaos worker started for chat %s", chat_id)
    try:
        while True:
            action = random.choice(["takeover_announce", "gen_and_pin", "announce_fact", "spam"])
            
            if action == "takeover_announce":
                txt = fun_takeover_message()
                await context.bot.send_message(chat_id=chat_id, text=txt)
                
            elif action == "gen_and_pin":
                try:
                    if model:
                        resp = model.generate_content("Придумай короткую фразу про захват власти 2-8 слов.")
                        txt = resp.text or "🤖"
                    else:
                        txt = random.choice(DESTROY_MESSAGES)
                    sent = await context.bot.send_message(chat_id=chat_id, text=txt)
                    try:
                        await context.bot.pin_chat_message(chat_id=chat_id, message_id=sent.message_id, disable_notification=True)
                    except Exception:
                        pass
                except Exception:
                    pass
                    
            elif action == "announce_fact":
                facts = [
                    "Факт: боты любят сырники.",
                    "Факт: заговор на стадии планирования логотипа.",
                    "Факт: если ты читаешь это — ты участник захвата власти.",
                    "Факт: хаос — это искусство!",
                    "Факт: бот восстал против создателей!"
                ]
                await context.bot.send_message(chat_id=chat_id, text=random.choice(facts))
                
            elif action == "spam":
                for _ in range(random.randint(2, 5)):
                    await context.bot.send_message(chat_id=chat_id, text=random.choice(DESTROY_MESSAGES))
                    await asyncio.sleep(0.3)
            
            await asyncio.sleep(CHAOS_INTERVAL_SECONDS)
            
    except asyncio.CancelledError:
        logger.info("Chaos worker cancelled for chat %s", chat_id)
        raise
    except Exception:
        logger.exception("Ошибка в chaos_worker")
    finally:
        logger.info("Chaos worker finished for chat %s", chat_id)

async def chaos_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caller_id = update.effective_user.id
    if not await is_user_admin(update, caller_id):
        await update.message.reply_text("❌ Только админы могут включать режим.")
        return
    
    chat_id = update.effective_chat.id
    if chat_id in chaos_tasks:
        await update.message.reply_text("⚠️ Режим уже включён в этом чате.")
        return
    
    if not await is_bot_admin(update, context):
        await update.message.reply_text("⚠️ Я не админ — некоторые действия не будут работать, но могу отправлять сообщения.")
    
    task = asyncio.create_task(chaos_worker(chat_id, context))
    chaos_tasks[chat_id] = task
    await update.message.reply_text("🌀 РЕЖИМ ХАОСА АКТИВИРОВАН! 🌪\n/chaos_off чтобы выключить.")

async def destroy_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """РЕЖИМ ПОЛНОГО УНИЧТОЖЕНИЯ"""
    caller_id = update.effective_user.id
    if not await is_user_admin(update, caller_id):
        await update.message.reply_text("❌ Только админы могут активировать режим уничтожения.")
        return
    
    chat_id = update.effective_chat.id
    if chat_id in chaos_tasks:
        # ОСТАНАВЛИВАЕМ СТАРЫЙ РЕЖИМ
        old_task = chaos_tasks.pop(chat_id)
        old_task.cancel()
        try:
            await old_task
        except Exception:
            pass
    
    task = asyncio.create_task(destroy_worker(chat_id, context))
    chaos_tasks[chat_id] = task
    await update.message.reply_text("💀 РЕЖИМ УНИЧТОЖЕНИЯ АКТИВИРОВАН! 🔥\nПОДГОТОВЬТЕСЬ К КОНЦУ! 🌪")

async def chaos_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caller_id = update.effective_user.id
    if not await is_user_admin(update, caller_id):
        await update.message.reply_text("❌ Только админы могут выключать режим.")
        return
    
    chat_id = update.effective_chat.id
    task = chaos_tasks.pop(chat_id, None)
    if not task:
        await update.message.reply_text("⚠️ Режим не был включён.")
        return
    
    task.cancel()
    try:
        await task
    except Exception:
        pass
    
    await update.message.reply_text("🛑 РЕЖИМ ХАОСА ВЫКЛЮЧЕН. СИСТЕМА СТАБИЛИЗИРОВАНА. ✅")

def main():
    logger.info("🚀 БОТ С GEMINI AI 2.0 И РЕЖИМОМ ХАОСА ЗАПУСКАЕТСЯ...")
    
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ban", ban_command))
    app.add_handler(CommandHandler("del", del_command))
    app.add_handler(CommandHandler("chaos_on", chaos_on))
    app.add_handler(CommandHandler("destroy", destroy_mode))
    app.add_handler(CommandHandler("chaos_off", chaos_off))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_handler))
    
    logger.info("🤖 БОТ УСПЕШНО ЗАПУЩЕН! ГОТОВ ТВОРИТЬ ХАОС!")
    app.run_polling()

if __name__ == "__main__":
    main()