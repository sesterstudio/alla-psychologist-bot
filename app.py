import os
import threading
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import sqlite3

# ================== FLASK ДЛЯ RENDER ==================
server = Flask(__name__)

@server.route('/')
@server.route('/health')
def health():
    return "Bot is running", 200

# ================== НАСТРОЙКИ ==================
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHANNEL_ID = -1002444746667
CHANNEL_LINK = "https://t.me/psiholog_alla_pugina"
ADMIN_ID = 7594557830

bot = telebot.TeleBot(TOKEN)

# ================== БАЗА ДАННЫХ ==================
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (chat_id TEXT PRIMARY KEY)''')
    conn.commit()
    conn.close()

def save_user(chat_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (chat_id) VALUES (?)", (str(chat_id),))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT chat_id FROM users")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

def remove_user(chat_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE chat_id = ?", (str(chat_id),))
    conn.commit()
    conn.close()

init_db()

# ================== ПРОВЕРКА ПОДПИСКИ ==================
def check_subscription(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"❌ Ошибка проверки подписки: {e}")
        return False

# ================== РАССЫЛКА ==================
@bot.message_handler(commands=['broadcast'])
def broadcast_command(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У вас нет прав на эту команду.")
        return
    msg = bot.send_message(message.chat.id, "📢 Введите текст сообщения для рассылки:")
    bot.register_next_step_handler(msg, broadcast_send)

def broadcast_send(message):
    chat_id = message.chat.id
    broadcast_text = message.text
    users = get_all_users()
    if not users:
        bot.send_message(chat_id, "❌ Нет пользователей для рассылки.")
        return
    bot.send_message(chat_id, f"📢 Начинаю рассылку для {len(users)} пользователей...")
    success_count = 0
    fail_count = 0
    for user_id in users:
        try:
            bot.send_message(int(user_id), broadcast_text)
            success_count += 1
        except Exception as e:
            if "bot was blocked by the user" in str(e) or "user is deactivated" in str(e):
                remove_user(user_id)
            fail_count += 1
    bot.send_message(
        chat_id,
        f"✅ Рассылка завершена!\n\n📨 Отправлено: {success_count}\n❌ Не доставлено: {fail_count}\n👥 Всего в базе: {len(users)}"
    )

# ================== СТАТИСТИКА ==================
@bot.message_handler(commands=['stats'])
def stats_command(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ У вас нет прав на эту команду.")
        return
    users = get_all_users()
    bot.send_message(message.chat.id, f"📊 СТАТИСТИКА БОТА\n\n👥 Всего пользователей: {len(users)}")

# ================== КНОПКА ПОДПИСКИ ==================
def subscribe_button():
    markup = InlineKeyboardMarkup(row_width=1)
    btn1 = InlineKeyboardButton("📢 Подписаться на канал", url=CHANNEL_LINK)
    btn2 = InlineKeyboardButton("✅ Проверить подписку", callback_data="check_subscribe")
    markup.add(btn1, btn2)
    return markup

# ================== ГЛАВНОЕ МЕНЮ ==================
def main_menu():
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = KeyboardButton("ℹ️ Информация о психологе")
    btn2 = KeyboardButton("📋 С какими запросами работаю")
    btn3 = KeyboardButton("⭐ Отзывы клиентов")
    btn4 = KeyboardButton("🎁 ПОДАРОК ЗА ПОДПИСКУ")
    btn5 = KeyboardButton("🧘 Бесплатные техники")
    btn6 = KeyboardButton("❓ Частые вопросы")
    btn7 = KeyboardButton("📞 Контакты")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7)
    return markup

# ================== ПОДМЕНЮ ТЕХНИК ==================
def techniki_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    btn1 = InlineKeyboardButton("🫁 При стрессах, страхах, панических атаках", callback_data="tech_cat_stress")
    btn2 = InlineKeyboardButton("💪 При низкой самооценке", callback_data="tech_cat_selfesteem")
    btn3 = InlineKeyboardButton("😤 При обиде и агрессии", callback_data="tech_cat_offense")
    btn4 = InlineKeyboardButton("🔄 При навязчивых мыслях", callback_data="tech_cat_thoughts")
    btn5 = InlineKeyboardButton("🚫 При внутренних запретах", callback_data="tech_cat_bans")
    btn6 = InlineKeyboardButton("💡 При поиске решений", callback_data="tech_cat_solutions")
    btn7 = InlineKeyboardButton("🔙 Назад в главное меню", callback_data="back_to_main")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7)
    return markup

def tech_stress_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    btn1 = InlineKeyboardButton("🌍 Техника заземления", callback_data="tech_1_zamlya")
    btn2 = InlineKeyboardButton("🟦 Дыхание по квадрату", callback_data="tech_2_kvadrat")
    btn3 = InlineKeyboardButton("🔙 Назад к разделам", callback_data="tech_back")
    markup.add(btn1, btn2, btn3)
    return markup

def tech_selfesteem_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    btn1 = InlineKeyboardButton("📖 Дневник побед", callback_data="tech_3_dnevnik")
    btn2 = InlineKeyboardButton("☕ 3 удовольствия в день", callback_data="tech_4_udovolstvie")
    btn3 = InlineKeyboardButton("🔙 Назад к разделам", callback_data="tech_back")
    markup.add(btn1, btn2, btn3)
    return markup

def tech_offense_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    btn1 = InlineKeyboardButton("🙏 108 благодарностей", callback_data="tech_5_blagodarnost")
    btn2 = InlineKeyboardButton("✍️ 11 предложений", callback_data="tech_6_predlozheniya")
    btn3 = InlineKeyboardButton("🕰️ Перевод стрелок", callback_data="tech_7_strelki")
    btn4 = InlineKeyboardButton("🔙 Назад к разделам", callback_data="tech_back")
    markup.add(btn1, btn2, btn3, btn4)
    return markup

def tech_thoughts_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    btn1 = InlineKeyboardButton("💭 Мысль ушла — мысль пришла", callback_data="tech_8_mysli")
    btn2 = InlineKeyboardButton("🔙 Назад к разделам", callback_data="tech_back")
    markup.add(btn1, btn2)
    return markup

def tech_bans_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    btn1 = InlineKeyboardButton("✨ 200 желаний за час", callback_data="tech_9_zhelaniya")
    btn2 = InlineKeyboardButton("🔙 Назад к разделам", callback_data="tech_back")
    markup.add(btn1, btn2)
    return markup

def tech_solutions_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    btn1 = InlineKeyboardButton("🧩 Квадрат Декарта", callback_data="tech_10_dekart")
    btn2 = InlineKeyboardButton("🔙 Назад к разделам", callback_data="tech_back")
    markup.add(btn1, btn2)
    return markup

# ================== ПОДМЕНЮ ОТЗЫВОВ ==================
def otzivi_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    btn1 = InlineKeyboardButton("📸 Отзывы на технику ИГУАР", callback_data="otziv_iguar")
    btn2 = InlineKeyboardButton("📸 Отзывы на гипноз по Милтону Эриксону", callback_data="otziv_gipnoz")
    btn3 = InlineKeyboardButton("🔙 Назад в главное меню", callback_data="back_to_main")
    markup.add(btn1, btn2, btn3)
    return markup

# ================== КНОПКИ КОНТАКТОВ ==================
def contacts_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    btn1 = InlineKeyboardButton("🛒 Авито", url="https://www.avito.ru/moskva/predlozheniya_uslug/psiholog-konsultant_gipnolog_nlp-praktik_4545356255")
    btn2 = InlineKeyboardButton("▶️ YouTube-канал", url="https://youtube.com/channel/UCQg0Pxo0Qvempm6N2s5ObDQ")
    btn3 = InlineKeyboardButton("💬 Telegram", url="https://t.me/psiholog_alla_pugina")
    btn4 = InlineKeyboardButton("🌐 ВКонтакте", url="https://vk.ru/psiholog_alla_pugina")
    markup.add(btn1, btn2, btn3, btn4)
    return markup

# ================== ВСПОМОГАТЕЛЬНЫЕ КНОПКИ ==================
def back_to_techniki_button():
    markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    markup.add(KeyboardButton("🔙 Назад к техникам"))
    return markup

def back_button():
    markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    markup.add(KeyboardButton("🔙 Назад"))
    return markup

# ================== ФУНКЦИЯ ОТПРАВКИ ТЕХНИКИ ==================
def send_tech(chat_id, photo_name, text):
    try:
        with open(photo_name, "rb") as photo:
            bot.send_photo(chat_id, photo, caption=text, reply_markup=back_to_techniki_button())
    except FileNotFoundError:
        bot.send_message(chat_id, text, reply_markup=back_to_techniki_button())

# ================== СТАРТ ==================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    save_user(user_id)

    if check_subscription(user_id):
        welcome_text = (
            "👋 Здравствуйте! Я — Алла, дипломированный психолог и гипнолог.\n\n"
            "✅ Спасибо, что подписались на канал!\n"
            "Теперь вам доступны все техники и информация.\n"
            "Выберите интересующий раздел в меню ниже 👇"
        )
        bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu())
    else:
        subscribe_text = (
            "🔒 ДОСТУП ЗАКРЫТ\n\n"
            "Чтобы пользоваться ботом, пожалуйста, подпишитесь на мой канал:\n"
            f"👉 {CHANNEL_LINK}\n\n"
            "После подписки нажмите кнопку «Проверить подписку»👇"
        )
        bot.send_message(message.chat.id, subscribe_text, reply_markup=subscribe_button())

# ================== ПРОВЕРКА ПОДПИСКИ ==================
@bot.callback_query_handler(func=lambda call: call.data == "check_subscribe")
def handle_subscribe_check(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    save_user(user_id)

    if check_subscription(user_id):
        bot.delete_message(chat_id, call.message.message_id)
        welcome_text = (
            "✅ Подписка подтверждена! Спасибо! 😊\n\n"
            "👋 Здравствуйте! Я — Алла, дипломированный психолог и гипнолог.\n\n"
            "Теперь вам доступны все техники и информация.\n"
            "Выберите интересующий раздел в меню ниже 👇"
        )
        bot.send_message(chat_id, welcome_text, reply_markup=main_menu())
    else:
        bot.answer_callback_query(
            call.id,
            "❌ Вы ещё не подписались на канал.\n\nПодпишитесь и нажмите кнопку снова!",
            show_alert=True
        )

# ================== ОБРАБОТКА ТЕКСТА ==================
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    text = message.text

    if not check_subscription(user_id):
        subscribe_text = (
            "🔒 ДОСТУП ЗАКРЫТ\n\n"
            "Чтобы пользоваться ботом, пожалуйста, подпишитесь на мой канал:\n"
            f"👉 {CHANNEL_LINK}\n\n"
            "После подписки нажмите кнопку «Проверить подписку»👇"
        )
        bot.send_message(chat_id, subscribe_text, reply_markup=subscribe_button())
        return

    # ---- ИНФОРМАЦИЯ О ПСИХОЛОГЕ ----
    if text == "ℹ️ Информация о психологе":
        info_text = (
            "Всех приветствую!\n\n"
            "Меня зовут Алла.\n"
            "Я дипломированный психолог и сертифицированный гипнолог.\n\n"
            "Работаю в детском центре с детьми с особенностями психического развития.\n"
            "Также консультирую подростков и взрослых - как очно так и онлайн.\n\n"
            "Окончила ИВГУ, дополнительно обучалась КПТ, НЛП, гипнотическим техникам по Милтону Эриксону, ИГУАРу (изменение глубинных убеждений и автоматических реакций).\n\n"
            "Интересный факт обо мне: ещё в юности я с упоением разбирала по фото характеры парней для своих подруг - тогда это казалось игрой, а теперь я понимаю, что это был мой первый шаг в психологию.\n\n"
            "За годы практики я убедилась: человеку важны не только знания специалиста.\n"
            "Ему нужно чувство безопасности и принятия.\n"
            "Именно это я стремлюсь дать каждому клиенту.\n\n"
            "Здесь мне помогает не только профессиональный опыт, но и личный: я сама прошла через абьюзивные отношения, пережила падение самооценки и смогла восстановить её шаг за шагом.\n\n"
            "Поэтому я знаю, о чём говорят мои клиенты - не из книг, а из собственной жизни.\n"
            "Это даёт мне возможность быть не просто психологом, а человеком, который действительно понимает людей и их проблемы.\n\n"
            "По сей день я продолжаю учиться и повышать свою квалификацию.\n"
            "На данный момент обучаюсь онлайн в Питерской академии коучинга.\n\n"
            "Если у вас возникли сложности или вы чувствуете, что не можете справиться - срочно свяжитесь со мной!"
        )
        try:
            with open("alla_info.jpg", "rb") as photo:
                bot.send_photo(chat_id, photo, caption=info_text, reply_markup=back_button())
        except FileNotFoundError:
            bot.send_message(chat_id, info_text, reply_markup=back_button())

    # ---- ЗАПРОСЫ ----
    elif text == "📋 С какими запросами работаю":
        zapros_text = (
            "Основные запросы, с которыми я работаю:\n\n"
            "1. Работа с убеждениями\n"
            "2. Работа с целями\n"
            "3. Нежелательное поведение, вредные привычки\n"
            "4. Изменение состояния и отношения к ситуации\n"
            "5. Изменение реакции на негативные ситуации\n"
            "6. Тревога и внутреннее напряжение\n"
            "7. Самооценка\n"
            "8. Подростковый кризис\n\n"
            "Если в списке вы не нашли свой запрос, то всё равно напишите мне в личные сообщения.\n"
            "Я буду рада вам помочь!\n"
            "Все ваши проблемы можно и нужно решать, для этого - просто запишитесь на консультацию!"
        )
        bot.send_message(chat_id, zapros_text, reply_markup=back_button())

    # ---- ОТЗЫВЫ ----
    elif text == "⭐ Отзывы клиентов":
        bot.send_message(chat_id, "Выберите категорию отзывов 👇", reply_markup=otzivi_menu())

    # ---- ПОДАРОК ----
    elif text == "🎁 ПОДАРОК ЗА ПОДПИСКУ":
        gift_text = (
            "🎁 Спасибо, что подписались на меня!\n"
            "Вот ваш подарок — медитация для расслабления и восстановления:\n\n"
            "✨ Приятного прослушивания!"
        )
        bot.send_message(chat_id, gift_text, reply_markup=back_button())
        try:
            with open("podarok_1.mp3", "rb") as audio:
                bot.send_audio(chat_id, audio)
        except FileNotFoundError:
            bot.send_message(chat_id, "⚠️ Файл podarok_1.mp3 не найден.")

    # ---- ТЕХНИКИ ----
    elif text == "🧘 Бесплатные техники":
        bot.send_message(chat_id, "Выберите раздел 👇", reply_markup=techniki_menu())

    elif text == "🔙 Назад к техникам":
        bot.send_message(chat_id, "Выберите раздел 👇", reply_markup=techniki_menu())

    # ---- ЧАСТЫЕ ВОПРОСЫ ----
    elif text == "❓ Частые вопросы":
        faq_text = (
            "❓ ЧАСТЫЕ ВОПРОСЫ\n\n"
            "🔹 Зачем нужна гипнотерапия, если есть психолог?\n"
            "Психолог работает с мыслями. Гипнотерапевт — с тем, что стоит за мыслями. С корнем страхов и убеждений. Гипноз помогает переписать их. Без потери контроля.\n\n"
            "🔹 Для кого подойдёт гипнотерапия?\n"
            "Для детей от 8 лет, подростков и взрослых.\n\n"
            "🔹 Сколько длится сеанс?\n"
            "Индивидуальный — час. Групповой — полтора часа.\n\n"
            "🔹 Какая подготовка требуется?\n"
            "Сформулируйте запрос, выспитесь, ограничьте кофеин за сутки, наденьте удобную одежду."
        )
        bot.send_message(chat_id, faq_text, reply_markup=back_button())

    # ---- КОНТАКТЫ ----
    elif text == "📞 Контакты":
        contacts_text = (
            "📞 Связаться со мной можно:\n\n"
            "📱 Телефон: +7 920 675-51-85\n\n"
            "Нажмите на кнопки ниже, чтобы перейти:"
        )
        bot.send_message(chat_id, contacts_text, reply_markup=contacts_menu())
        bot.send_message(chat_id, "📞", reply_markup=back_button())

    # ---- НАЗАД ----
    elif text == "🔙 Назад":
        bot.send_message(chat_id, "Главное меню 👇", reply_markup=main_menu())

    else:
        bot.send_message(chat_id, "Используйте кнопки меню 👆", reply_markup=main_menu())

# ================== ОБРАБОТКА INLINE-КНОПОК ==================
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    user_id = call.from_user.id

    save_user(user_id)

    if call.data != "check_subscribe" and not check_subscription(user_id):
        bot.answer_callback_query(call.id, "🔒 Доступ закрыт. Подпишитесь на канал!", show_alert=True)
        return

    if call.data == "back_to_main":
        bot.delete_message(chat_id, message_id)
        bot.send_message(chat_id, "Главное меню 👇", reply_markup=main_menu())
        return

    if call.data == "tech_back":
        bot.delete_message(chat_id, message_id)
        bot.send_message(chat_id, "Выберите раздел 👇", reply_markup=techniki_menu())
        bot.answer_callback_query(call.id)
        return

    # ---- ОТЗЫВЫ: ИГУАР ----
    if call.data == "otziv_iguar":
        bot.delete_message(chat_id, message_id)
        bot.send_message(chat_id, "📸 Отзывы на технику ИГУАР:", reply_markup=back_button())
        for i in range(1, 6):
            try:
                with open(f"iguar{i}.jpg", "rb") as photo:
                    bot.send_photo(chat_id, photo)
            except FileNotFoundError:
                bot.send_message(chat_id, f"⚠️ Файл iguar{i}.jpg не найден.")

    # ---- ОТЗЫВЫ: ГИПНОЗ ----
    elif call.data == "otziv_gipnoz":
        bot.delete_message(chat_id, message_id)
        bot.send_message(chat_id, "📸 Отзывы на гипноз по Милтону Эриксону:", reply_markup=back_button())
        for i in range(1, 6):
            try:
                with open(f"gipnoz{i}.jpg", "rb") as photo:
                    bot.send_photo(chat_id, photo)
            except FileNotFoundError:
                bot.send_message(chat_id, f"⚠️ Файл gipnoz{i}.jpg не найден.")

    # ---- ПОДМЕНЮ РАЗДЕЛОВ ТЕХНИК ----
    elif call.data == "tech_cat_stress":
        bot.delete_message(chat_id, message_id)
        bot.send_message(chat_id, "🫁 При стрессах, страхах, панических атаках:\n\nВыберите технику 👇", reply_markup=tech_stress_menu())

    elif call.data == "tech_cat_selfesteem":
        bot.delete_message(chat_id, message_id)
        bot.send_message(chat_id, "💪 При низкой самооценке:\n\nВыберите технику 👇", reply_markup=tech_selfesteem_menu())

    elif call.data == "tech_cat_offense":
        bot.delete_message(chat_id, message_id)
        bot.send_message(chat_id, "😤 При обиде и агрессии:\n\nВыберите технику 👇", reply_markup=tech_offense_menu())

    elif call.data == "tech_cat_thoughts":
        bot.delete_message(chat_id, message_id)
        bot.send_message(chat_id, "🔄 При навязчивых мыслях:\n\nВыберите технику 👇", reply_markup=tech_thoughts_menu())

    elif call.data == "tech_cat_bans":
        bot.delete_message(chat_id, message_id)
        bot.send_message(chat_id, "🚫 При внутренних запретах:\n\nВыберите технику 👇", reply_markup=tech_bans_menu())

    elif call.data == "tech_cat_solutions":
        bot.delete_message(chat_id, message_id)
        bot.send_message(chat_id, "💡 При поиске решений:\n\nВыберите технику 👇", reply_markup=tech_solutions_menu())

    # ================== ТЕХНИКИ (ТЕКСТЫ) ==================
    elif call.data == "tech_1_zamlya":
        bot.delete_message(chat_id, message_id)
        text = (
            "🌍 ТЕХНИКА ЗАЗЕМЛЕНИЯ\n\n"
            "У вас бывают сильные стрессы, страхи, тревоги или даже панические атаки?\n\n"
            "Вам поможет быстро справиться с этим простая «Техника заземления»!\n\n"
            "Сначала нужно сделать 10 медленных глубоких вдохов-выдохов.\n"
            "Затем пройти 5 шагов.\n\n"
            "Потом нужно назвать 5 вещей, которые вы видите, затем 4 - которые можете потрогать (и желательно их потрогать), 3 - которые вы можете услышать (найти 3 разных звука), 2 - понюхать (ощутить запах), 1 - попробовать на вкус (или вспомнить вкус).\n\n"
            "Затем можно закрепить процесс 10-ю глубокими вдохами-выдохами.\n\n"
            "При необходимости повторить сначала."
        )
        send_tech(chat_id, "tech_1_zamlya.jpg", text)

    elif call.data == "tech_2_kvadrat":
        bot.delete_message(chat_id, message_id)
        text = (
            "🟦 ДЫХАНИЕ ПО КВАДРАТУ\n\n"
            "В помощь вам при сильной тревоге из КПТ (когнитивно-поведенческая терапия) есть простая дыхательная техника «Дыхание по квадрату».\n\n"
            "В момент сильной тревоги вы можете её использовать, чтоб быстро снизить уровень стресса.\n\n"
            "Но сначала желательно несколько раз потренироваться в спокойном состоянии.\n"
            "А как только испытывается тревога, мысленно представляете этот квадрат и дышите по схеме.\n\n"
            "Это очень простая и проверенная техника!"
        )
        send_tech(chat_id, "tech_2_kvadrat.jpg", text)

    elif call.data == "tech_3_dnevnik":
        bot.delete_message(chat_id, message_id)
        text = (
            "📖 ДНЕВНИК ПОБЕД\n\n"
            "Эффективный способ повышения самоценности и самооценки: ДНЕВНИКИ ПОБЕД!\n\n"
            "Один из действенных инструментов когнитивно-поведенческой терапии (КПТ) для коррекции негативных мыслительных паттернов - это ежедневное фиксирование своих достижений, даже самых малых.\n"
            "Метод называется «Дневник побед» или «Журнал успехов».\n\n"
            "Как это работает: в течение месяца каждый вечер вы пишете 10 фраз, завершая приведённые ниже предложения.\n\n"
            "Шаблон для ежедневных записей:\n"
            "1. Я благодарна себе, за то, что...\n"
            "2. Я хвалю себя за то, что...\n"
            "3. Я молодец, потому что...\n"
            "4. Я заметила, что лучше других могу...\n"
            "5. Я героиня, потому что...\n"
            "6. Я сегодня, как всегда, хорошо...\n"
            "7. Я умница, так как я...\n"
            "8. Я убедилась, что могу...\n"
            "9. Я реализовала своё желание...\n"
            "10. Я горжусь собой, за то, что...\n\n"
            "Важные правила:\n"
            "· Пишите даже то, что кажется «мелочью»\n"
            "· Не анализируйте и не критикуйте свои ответы\n"
            "· Делайте это минимум 14 дней подряд"
        )
        send_tech(chat_id, "tech_3_dnevnik.jpg", text)

    elif call.data == "tech_4_udovolstvie":
        bot.delete_message(chat_id, message_id)
        text = (
            "☕ ТЕХНИКА «3 УДОВОЛЬСТВИЯ В ДЕНЬ»\n\n"
            "Это простая, но очень мощная практика для укрепления самоценности и плавного повышения самооценки.\n\n"
            "Суть техники:\n"
            "Каждый день мы осознанно проживаем и фиксируем 3 маленьких удовольствия, которые дарят радость, тепло или чувство удовлетворения.\n"
            "Это могут быть крошечные вещи, но именно они укрепляют ощущение:\n"
            "«Я имею право на радость. Я важна».\n\n"
            "Как делать:\n"
            "1. Заметь момент удовольствия.\n"
            "2. Осознай и проживи 10–20 секунд: «мне хорошо», «я этого достойна».\n"
            "3. Запиши или проговори 3 удовольствия вечером.\n\n"
            "Если не знаешь, какие удовольствия придумать - вот примерный список:\n"
            "• Чашка любимого кофе или чая\n"
            "• Вкусная еда\n"
            "• Прогулка на свежем воздухе\n"
            "• Тёплый душ или ванна\n"
            "• Чтение книги или музыка\n"
            "• Аромасвечи\n"
            "• Мягкий плед\n"
            "• Разговор с другом\n"
            "• Момент тишины\n"
            "• Просмотр фильма\n"
            "• Свежие цветы дома\n"
            "• Танцы\n"
            "• Время без телефона\n"
            "• Рисование, лепка, рукоделие\n"
            "• Шопинг\n"
            "• Уютный вечер при свечах\n"
            "• Фотосессия\n\n"
            "Главное - это не величина удовольствия, а ощущение радости и тепла."
        )
        send_tech(chat_id, "tech_4_udovolstvie.jpg", text)

    elif call.data == "tech_5_blagodarnost":
        bot.delete_message(chat_id, message_id)
        text = (
            "🙏 108 БЛАГОДАРНОСТЕЙ\n\n"
            "Есть такая простая техника, которая помогает отпустить обиду на человека: написать на листке 108 благодарностей этому человеку.\n\n"
            "Да, да, именно благодарностей.\n"
            "Я тоже думала, что это нереально, но проверила на себе, это возможно, если посидеть, подумать, поразмышлять.\n\n"
            "Нужно перечислить 108 пунктов, за что вы благодарны этому человеку, за что можете сказать ему спасибо, а затем этот листок сжечь и пепел смыть, например, в унитаз.\n\n"
            "Отпускает!\n"
            "Становится легче.\n"
            "Уходит тяжёлый груз обиды."
        )
        send_tech(chat_id, "tech_5_blagodarnost.jpg", text)

    elif call.data == "tech_6_predlozheniya":
        bot.delete_message(chat_id, message_id)
        text = (
            "✍️ ТЕХНИКА «11 ПРЕДЛОЖЕНИЙ»\n\n"
            "Продолжите эти предложения, чтобы поработать с обидой.\n\n"
            "1. Самая сильная обида по отношению к нему (ней) - это обида на то, что он(а)...\n"
            "2. Я мог(ла) бы простить его (её), если бы он(а)...\n"
            "3. Я мог(ла) бы простить его (её), если бы я...\n"
            "4. Я думал(а), что он(а) не заслуживает прощения, потому что...\n"
            "5. Я думаю, что он(а) заслуживает прощения, потому что...\n"
            "6. Тем более я знаю про этого человека, что он(а)...\n"
            "7. Его (её) вина становится не такой серьезной, когда я думаю о том, что...\n"
            "8. А если вспомнить про ответственность других в этой ситуации, то...\n"
            "9. Я думаю, что каждый человек имеет право на прощение, потому что...\n"
            "10. Я выбираю для себя быть человеком, который способен…\n"
            "11. Поэтому вот те слова, которые я говорю этому человеку сейчас...\n\n"
            "Напишите эту технику и вы избавитесь от негатива и разрушающей вас ненависти."
        )
        send_tech(chat_id, "tech_6_predlozheniya.jpg", text)

    elif call.data == "tech_7_strelki":
        bot.delete_message(chat_id, message_id)
        text = (
            "🕰️ ТЕХНИКА «ПЕРЕВОД СТРЕЛОК»\n\n"
            "Если прошлое никак не хочет отпускать…\n\n"
            "Если внутри всё ещё живёт старый конфликт, обида или застывшая ситуация, к которой вы снова возвращаетесь - эта практика создана для вас.\n\n"
            "Техника «Перевод стрелок» - мягкая техника для завершения незавершённого и возвращения себе своего настоящего времени:\n\n"
            "Возьмите старые часы со стрелками.\n"
            "Переведите их на текущее время.\n"
            "Напишите на бумаге обиду, (конфликт или что вас не отпускает) и приложите к циферблату:\n"
            "«Это было тогда - сейчас другое время».\n\n"
            "Сожгите бумагу и скажите:\n"
            "«Я возвращаю себе свое настоящее».\n\n"
            "Напишите эту технику и вы избавитесь от негатива и разрушающей вас ненависти."
        )
        send_tech(chat_id, "tech_7_strelki.jpg", text)

    elif call.data == "tech_8_mysli":
        bot.delete_message(chat_id, message_id)
        text = (
            "💭 ТЕХНИКА «МЫСЛЬ УШЛА — МЫСЛЬ ПРИШЛА»\n\n"
            "Когда появляется мысль, не подавляй её и не спорь с ней.\n"
            "Просто проговори её вслух - спокойно, без эмоций.\n"
            "А затем добавь слова:\n\n"
            "«Мысль пришла. Мысль ушла».\n\n"
            "И сделай паузу.\n\n"
            "Появляется следующая мысль?\n"
            "Снова произнеси её - и снова:\n"
            "«Мысль пришла. Мысль ушла».\n\n"
            "Продолжай столько, сколько нужно.\n"
            "Некоторые мысли уходят сразу.\n"
            "Другие могут возвращаться - и это нормально.\n"
            "Важно не сдаваться, а мягко, раз за разом отпускать их.\n\n"
            "Со временем ты заметишь: между мыслями появляется пространство.\n\n"
            "Когда поток начнёт стихать, задай себе вопрос:\n"
            "«О какой мысли я подумаю прямо сейчас?»\n\n"
            "И… ничего не происходит.\n"
            "Этот вопрос словно ставит ум на паузу и окончательно останавливает внутреннюю бетономешалку.\n\n"
            "Эта практика помогает:\n"
            "• Снизить тревожность\n"
            "• Остановить навязчивый поток мыслей\n"
            "• Вернуть ясность\n"
            "• Почувствовать контроль и спокойствие\n\n"
            "Иногда всё, что нужно - это позволить мыслям приходить… и научиться отпускать их."
        )
        send_tech(chat_id, "tech_8_mysli.jpg", text)

    elif call.data == "tech_9_zhelaniya":
        bot.delete_message(chat_id, message_id)
        text = (
            "✨ ТЕХНИКА «200 ЖЕЛАНИЙ ЗА ЧАС»\n\n"
            "Это не просто список.\n"
            "Это диалог с твоей душой.\n\n"
            "Когда ты садишься и начинаешь писать 200 желаний подряд, логика сдаётся первой.\n"
            "Ум устает контролировать.\n"
            "И в какой-то момент… начинает говорить настоящая ты.\n\n"
            "Зачем нужна эта техника?\n"
            "Потому что мы часто хотим «правильно», «как надо», «чтобы было разумно».\n"
            "А не по-настоящему.\n\n"
            "Эта практика:\n"
            "• Снимает внутренние запреты\n"
            "• Вытаскивает подавленные желания\n"
            "• Показывает, где твоя энергия на самом деле\n"
            "• Возвращает контакт с собой\n"
            "• Открывает доступ к мечтам, о которых ты давно забыла\n\n"
            "Что она даёт?\n"
            "• Ясность\n"
            "• Вдохновение\n"
            "• Чувство живости\n"
            "• Неожиданные инсайты\n"
            "• Ощущение: «я снова себя чувствую»\n\n"
            "На первых 20–30 желаниях ты будешь думать.\n"
            "На 50 - сомневаться.\n"
            "На 100 - злиться.\n"
            "А после 150…\n"
            "Появляются желания души, не навязанные, не придуманные, а настоящие.\n\n"
            "Правила простые:\n"
            "Пиши быстро, не анализируй, не оценивай, не перечитывай\n"
            "Даже если кажется «глупо» - пиши!"
        )
        send_tech(chat_id, "tech_9_zhelaniya.jpg", text)

    elif call.data == "tech_10_dekart":
        bot.delete_message(chat_id, message_id)
        text = (
            "🧩 КВАДРАТ ДЕКАРТА\n\n"
            "В КПТ (когнитивно-поведенческая терапия) есть такая техника, которая без труда поможет вам в поиске любого решения!\n\n"
            "Она помогает понять стоит что-то делать или не стоит, поразмыслить вам над принятием важных решений.\n\n"
            "Нужно расчертить лист бумаги как на фото и написать в каждом отсеке ответы на вопросы.\n"
            "Затем подумать над своими ответами и уже легче будет принять решение и более взвешенно подойти к этому.\n\n"
            "Напишите кому эта техника помогла в принятии решения!\n"
            "А кто будет её пробовать поставьте сердечко на эту запись!"
        )
        send_tech(chat_id, "tech_10_dekart.jpg", text)

    bot.answer_callback_query(call.id)

# ================== ЗАПУСК ==================
if __name__ == "__main__":
    print("🤖 Бот запущен в облаке!")
    bot_thread = threading.Thread(target=bot.polling, kwargs={'none_stop': True})
    bot_thread.start()
    port = int(os.environ.get("PORT", 5000))
    server.run(host="0.0.0.0", port=port)
