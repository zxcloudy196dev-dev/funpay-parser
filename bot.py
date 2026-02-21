import telebot
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
import sys
from telebot import types

# ===== ЛОГИРОВАНИЕ =====
def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")
    sys.stdout.flush()

log("🚀 Бот запускается...")

# ===== ХРАНИЛИЩА =====
user_filters = {}
user_search_results = {}

# ===== ТВОИ ДАННЫЕ =====
BOT_TOKEN = '8561754542:AAF4gbVvemiagKv_L5QXU6bjHWJH36fPE_c'
ADMIN_ID = 7015434265
log(f"✅ Токен: {BOT_TOKEN[:10]}...")
# =======================

bot = telebot.TeleBot(BOT_TOKEN)

# ===== КАТЕГОРИИ =====
CATEGORIES = {
    'telegram_stars': ('⭐ Telegram Звёзды', 'https://funpay.com/lots/2418/', 100),
    'discord_nitro': ('💬 Discord Нитро', 'https://funpay.com/lots/923/', 100),
    'dota_boost': ('📈 Буст MMR Dota 2', 'https://funpay.com/lots/82/', 100),
    'cs2_prime': ('🔫 CS2 Прайм', 'https://funpay.com/lots/1907/', 100),
    'anno_accounts': ('🏝️ Аккаунты Anno', 'https://funpay.com/lots/3341/', 100),
    'arknights_accounts': ('📱 Аккаунты Arknights', 'https://funpay.com/lots/1141/', 100),
    'gta_money': ('💰 Деньги GTA 5 Online', 'https://funpay.com/chips/158/', 100),
    'fortnite_vbucks': ('🦴 V-Bucks Fortnite', 'https://funpay.com/lots/928/', 100),
    'dbd_accounts': ('🔪 Аккаунты Dead by Daylight', 'https://funpay.com/lots/460/', 100)
}

# ===== ДРАЙВЕР =====
def create_driver():
    log("🔄 Создание драйвера...")
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        log("✅ Драйвер готов")
        return driver
    except Exception as e:
        log(f"❌ Ошибка драйвера: {e}")
        return None

# ===== ПАРСЕР =====
def parse_category(url, limit=100, chat_id=None):
    log(f"🔍 Парсинг: {url}")
    
    driver = None
    try:
        driver = create_driver()
        if not driver:
            return []
        
        driver.get(url)
        log("🌐 Страница загружена")
        
        # Ждём товары
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "tc-item"))
            )
        except:
            log("⏱️ Товары не загрузились")
            return []
        
        # Берём ТОЛЬКО ПЕРВЫЕ 500 товаров (остальное не нужно)
        all_items = driver.find_elements(By.CLASS_NAME, "tc-item")
        items = all_items[:500]  # ← вот это главное изменение
        log(f"🔎 Всего на странице: {len(all_items)}, берём первые {len(items)}")
        
        filters = user_filters.get(chat_id, {'max_reviews': 999999, 'max_days': 999999})
        log(f"⚙️ Фильтры: отзывы ≤{filters['max_reviews']}, дни ≤{filters['max_days']}")
        
        seen_sellers = set()
        results = []
        
        for i, item in enumerate(items):
            if len(results) >= limit:
                log(f"🛑 Достигнут лимит {limit}")
                break
            
            # Показываем прогресс каждые 50 товаров
            if i % 50 == 0 and i > 0:
                log(f"⏳ Обработано {i}/{len(items)} товаров, найдено {len(results)}")
                
            try:
                seller = item.find_element(By.CLASS_NAME, "media-user-name").text.strip()
                
                if seller in seen_sellers:
                    continue
                
                title = item.find_element(By.CLASS_NAME, "tc-desc-text").text.strip()
                price = item.find_element(By.CLASS_NAME, "tc-price").text.strip().replace('\n', ' ')
                
                reviews_text = item.find_element(By.CLASS_NAME, "media-user-reviews").text.strip()
                reviews = int(re.search(r'\d+', reviews_text).group()) if re.search(r'\d+', reviews_text) else 0
                
                days_text = item.find_element(By.CLASS_NAME, "media-user-info").text.strip()
                days_match = re.search(r'\d+', days_text)
                days = int(days_match.group()) if days_match else 0
                
                if reviews <= filters['max_reviews'] and days <= filters['max_days']:
                    results.append({
                        'title': title[:100],
                        'price': price,
                        'seller': seller,
                        'reviews': reviews,
                        'days': days,
                        'link': item.get_attribute("href")
                    })
                    seen_sellers.add(seller)
                    
            except Exception as e:
                continue
        
        log(f"✅ Готово! Найдено {len(results)} товаров")
        return results
        
    except Exception as e:
        log(f"❌ Ошибка парсинга: {e}")
        return []
    finally:
        if driver:
            driver.quit()

# ===== ФОРМАТИРОВАНИЕ =====
def format_page(results, page, page_size=5):
    start = (page - 1) * page_size
    end = start + page_size
    page_items = results[start:end]
    
    if not page_items:
        return None
    
    total_pages = (len(results) + page_size - 1) // page_size
    
    text = f"📄 Стр {page}/{total_pages} | Всего: {len(results)}\n\n"
    
    for i, item in enumerate(page_items, start=start+1):
        text += f"{i}. **{item['title']}**\n"
        text += f"   💰 {item['price']}\n"
        text += f"   👤 {item['seller']} | 📊 {item['reviews']} отз | 📅 {item['days']} дн\n"
        text += f"   🔗 {item['link']}\n\n"
    
    return text

def send_page(chat_id, message_id, page, results):
    text = format_page(results, page, 5)
    if not text:
        return
    
    markup = types.InlineKeyboardMarkup(row_width=3)
    total_pages = (len(results) + 4) // 5
    
    if total_pages > 1:
        nav = []
        if page > 1:
            nav.append(types.InlineKeyboardButton("◀️", callback_data=f"page_{page-1}"))
        nav.append(types.InlineKeyboardButton(f"{page}/{total_pages}", callback_data="current"))
        if page < total_pages:
            nav.append(types.InlineKeyboardButton("▶️", callback_data=f"page_{page+1}"))
        markup.add(*nav)
    
    if message_id:
        bot.edit_message_text(text, chat_id, message_id, parse_mode='Markdown', reply_markup=markup)
    else:
        bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=markup)

# ===== НАСТРОЙКИ =====
def filters_menu(chat_id):
    filters = user_filters.get(chat_id, {'max_reviews': 999999, 'max_days': 999999})
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(f"📊 Отзывы ≤ {filters['max_reviews']}", callback_data="set_reviews"),
        types.InlineKeyboardButton(f"📅 Дни ≤ {filters['max_days']}", callback_data="set_days")
    )
    markup.add(types.InlineKeyboardButton("🔄 Сбросить", callback_data="reset_filters"))
    
    bot.send_message(
        chat_id,
        "⚙️ **Настройки фильтров**\n\n"
        "Ищем **новичков** — чем меньше отзывов и дней, тем свежее аккаунт.\n\n"
        f"📊 Отзывов ≤ {filters['max_reviews']}\n"
        f"📅 Дней ≤ {filters['max_days']}",
        parse_mode='Markdown',
        reply_markup=markup
    )

# ===== ОБРАБОТЧИКИ =====
@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.type == 'private':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        buttons = []
        for key, (name, url, limit) in CATEGORIES.items():
            buttons.append(types.KeyboardButton(name))
        markup.add(*buttons)
        markup.add(types.KeyboardButton('⚙️ Настройки'), types.KeyboardButton('ℹ️ Помощь'))
        
        bot.send_message(
            message.chat.id,
            "👋 **Привет!**\n\nВыбери категорию:",
            parse_mode='Markdown',
            reply_markup=markup
        )
    else:
        bot.reply_to(message, "👋 Бот работает. Используй /search <категория>")

@bot.message_handler(commands=['search'])
def search_command(message):
    """Команда для поиска в группах"""
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "❌ Используй: /search <категория>\nДоступны: telegram, discord, cs2, gta, fortnite, dbd")
        return
    
    query = parts[1].lower()
    
    category_map = {
        'telegram': '⭐ Telegram Звёзды',
        'discord': '💬 Discord Нитро',
        'cs2': '🔫 CS2 Прайм',
        'gta': '💰 Деньги GTA 5 Online',
        'fortnite': '🦴 V-Bucks Fortnite',
        'dbd': '🔪 Аккаунты Dead by Daylight'
    }
    
    if query not in category_map:
        bot.reply_to(message, "❌ Доступны: " + ', '.join(category_map.keys()))
        return
    
    category_name = category_map[query]
    selected_category = None
    for key, (name, url, limit) in CATEGORIES.items():
        if name == category_name:
            selected_category = (name, url, limit)
            break
    
    if not selected_category:
        bot.reply_to(message, "❌ Ошибка")
        return
    
    name, url, limit = selected_category
    sent = bot.reply_to(message, f"🔍 Ищу **{name}**...", parse_mode='Markdown')
    
    results = parse_category(url, limit, message.chat.id)
    
    if not results:
        bot.edit_message_text("❌ Ничего не найдено", message.chat.id, sent.message_id)
        return
    
    user_search_results[message.chat.id] = results
    bot.delete_message(message.chat.id, sent.message_id)
    send_page(message.chat.id, None, 1, results)

@bot.message_handler(commands=['settings'])
def settings_command(message):
    """Открыть настройки в группе"""
    log(f"👥 Групповая команда /settings от {message.chat.id}")
    filters_menu(message.chat.id)

@bot.message_handler(func=lambda message: True)
def handle_private(message):
    """Только для личных сообщений"""
    # В группах игнорируем всё, кроме команд (они обрабатываются выше)
    if message.chat.type != 'private':
        return
    
    if message.text == '⚙️ Настройки':
        filters_menu(message.chat.id)
        return
    
    if message.text == 'ℹ️ Помощь':
        bot.send_message(
            message.chat.id,
            "📚 **Помощь**\n\n"
            "• Выбери категорию из меню\n"
            "• ⚙️ Настройки — фильтры\n"
            "• В группах используй /search и /settings",
            parse_mode='Markdown'
        )
        return
    
    # Поиск категории
    category_name = message.text
    selected_category = None
    for key, (name, url, limit) in CATEGORIES.items():
        if name == category_name:
            selected_category = (name, url, limit)
            break
    
    if not selected_category:
        bot.send_message(message.chat.id, "❌ Используй кнопки меню")
        return
    
    name, url, limit = selected_category
    sent = bot.send_message(message.chat.id, f"🔍 Ищу **{name}**...", parse_mode='Markdown')
    
    results = parse_category(url, limit, message.chat.id)
    
    if not results:
        bot.edit_message_text("❌ Товары не найдены", message.chat.id, sent.message_id)
        return
    
    user_search_results[message.chat.id] = results
    bot.delete_message(message.chat.id, sent.message_id)
    send_page(message.chat.id, None, 1, results)
# ===== КНОПКИ =====
@bot.callback_query_handler(func=lambda call: call.data.startswith('page_'))
def page_callback(call):
    page = int(call.data.split('_')[1])
    chat_id = call.message.chat.id
    results = user_search_results.get(chat_id)
    
    if results:
        send_page(chat_id, call.message.message_id, page, results)
    else:
        bot.answer_callback_query(call.id, "❌ Результаты устарели")

@bot.callback_query_handler(func=lambda call: call.data == 'current')
def current_callback(call):
    bot.answer_callback_query(call.id, "📍 Ты здесь")

@bot.callback_query_handler(func=lambda call: call.data in ["set_reviews", "set_days", "reset_filters"])
def settings_callback(call):
    chat_id = call.message.chat.id
    
    if call.data == "set_reviews":
        msg = bot.send_message(chat_id, "📊 Введи **максимум** отзывов:")
        bot.register_next_step_handler(msg, process_reviews)
    
    elif call.data == "set_days":
        msg = bot.send_message(chat_id, "📅 Введи **максимум** дней:")
        bot.register_next_step_handler(msg, process_days)
    
    elif call.data == "reset_filters":
        user_filters[chat_id] = {'max_reviews': 999999, 'max_days': 999999}
        bot.answer_callback_query(call.id, "🔄 Фильтры сброшены")
        filters_menu(chat_id)

def process_reviews(message):
    try:
        val = int(message.text)
        if val < 0:
            raise ValueError
        chat_id = message.chat.id
        if chat_id not in user_filters:
            user_filters[chat_id] = {'max_reviews': 999999, 'max_days': 999999}
        user_filters[chat_id]['max_reviews'] = val
        bot.send_message(chat_id, f"✅ Максимум отзывов: {val}")
        filters_menu(chat_id)
    except:
        bot.send_message(message.chat.id, "❌ Введи число")

def process_days(message):
    try:
        val = int(message.text)
        if val < 0:
            raise ValueError
        chat_id = message.chat.id
        if chat_id not in user_filters:
            user_filters[chat_id] = {'max_reviews': 999999, 'max_days': 999999}
        user_filters[chat_id]['max_days'] = val
        bot.send_message(chat_id, f"✅ Максимум дней: {val}")
        filters_menu(chat_id)
    except:
        bot.send_message(message.chat.id, "❌ Введи число")

# ===== ЗАПУСК =====
if __name__ == "__main__":
    log("🚀 Бот готов к работе")
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=20)
        except Exception as e:
            log(f"❌ Ошибка: {e}")
            time.sleep(5)
