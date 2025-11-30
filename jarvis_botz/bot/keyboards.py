from telegram import (Update, ReplyKeyboardMarkup,
                       ReplyKeyboardRemove, KeyboardButton,
                         InlineKeyboardButton, InlineKeyboardMarkup)



from telegram.ext import (ContextTypes, ConversationHandler)
import math

def create_grid_paged_menu(all_items: list[tuple[str, str]], prefix:str, page: int = 0, col: int = 1, row: int = 1) -> InlineKeyboardMarkup:
    ITEMS_PER_PAGE = col * row

    total_items = len(all_items)
    
    total_pages = math.ceil(total_items / ITEMS_PER_PAGE)
    
    page = max(0, min(page, total_pages - 1))

    start_index = page * ITEMS_PER_PAGE
    end_index = start_index + ITEMS_PER_PAGE
    page_items = all_items[start_index:end_index]
    
    keyboard = []
    current_row = []
    
    for i, button in enumerate(page_items):
        current_row.append(button)
        

        if len(current_row) == col or i == len(page_items) - 1:
            keyboard.append(current_row)
            current_row = []

    nav_row = []
    

    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Back", callback_data=f"{prefix}:page:{page - 1}"))
    else:
        nav_row.append(InlineKeyboardButton(" ", callback_data="ignore")) 
        
    nav_row.append(InlineKeyboardButton(f"Page. {page + 1}/{total_pages}", callback_data="ignore"))
    

    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Forward ➡️", callback_data=f"{prefix}:page:{page + 1}"))
    else:
        nav_row.append(InlineKeyboardButton(" ", callback_data="ignore"))


    if nav_row:
        keyboard.append(nav_row)
        
    keyboard.append([InlineKeyboardButton("❌ Quit", callback_data=f'{prefix}:quit:select')])

    return InlineKeyboardMarkup(keyboard)
    



keyboard = [
    # Ряд 1: Конфигурация и Информация
    [KeyboardButton('⚙️ Настройки'), KeyboardButton('ℹ️ Инфо')],
    
    # Ряд 2: Действия и Режимы
    [KeyboardButton('🗑️ Новый Чат'), KeyboardButton('🛠️ Инструменты')]
]

start_keyboard = ReplyKeyboardMarkup(
    keyboard=keyboard,
    resize_keyboard=True,
    input_field_placeholder='Введите сообщение или команду',
    is_persistent=True
)


start_keyboard = ReplyKeyboardMarkup(
    keyboard=keyboard,
    resize_keyboard=True,
    input_field_placeholder='input text commands',
    is_persistent=True
)



setting_keyboard = [
    # Ряд 1: Ключевое поведение
    [InlineKeyboardButton('✨ стиль', callback_data='style:page:0'), 
     InlineKeyboardButton('🌡️ температура', callback_data='temperature:page:0')],
    
    # Ряд 2: Роль и размер
    [InlineKeyboardButton('🗣️ Профиль ИИ', callback_data='system_prompt:page:0'),
     InlineKeyboardButton('🗜️ Длина ответа', callback_data='max_tokens:page:0')],
     
    # Ряд 3: Лимиты и Язык
    [InlineKeyboardButton('📊 Лимиты', callback_data='usage_limits:page:0'),
     InlineKeyboardButton('🌍 Язык', callback_data='language:page:0')],
     
    # ⬆️ Важное дополнение для UX: кнопка "Назад"
    [InlineKeyboardButton('« Назад', callback_data='settings:quit:start')]
]

setting_keyboard_markup = InlineKeyboardMarkup(
    inline_keyboard=setting_keyboard
)

system_prompts = [
    # --- 🛠️ Основные Функциональные ---
    InlineKeyboardButton("👤 Свой Профиль", callback_data="system_prompt:select:custom"), 
    InlineKeyboardButton("👨‍🏫 Наставник", callback_data="system_prompt:select:mentor"),
    InlineKeyboardButton("📝 Редактор", callback_data="system_prompt:select:editor"),
    InlineKeyboardButton("💡 Креативщик", callback_data="system_prompt:select:creative"),
    InlineKeyboardButton("🚀 Эксперт по коду", callback_data="system_prompt:select:code_expert"),
    
    # --- 🧠 Аналитические и Принятие Решений ---
    InlineKeyboardButton("⚖️ Аргументатор (За/Против)", callback_data="system_prompt:select:argumentator"), # Оставил пояснение, так как это ключевая функция
    InlineKeyboardButton("🤔 Критик", callback_data="system_prompt:select:critic"), 
    InlineKeyboardButton("📊 Аналитик (Таблицы/Тезисы)", callback_data="system_prompt:select:data_analyst"),
    
    # --- 🗺️ Специфические Эксперты ---
    InlineKeyboardButton("🌍 Переводчик", callback_data="system_prompt:select:translator"),
    InlineKeyboardButton("📚 Энциклопедист", callback_data="system_prompt:select:encyclopedist"), 
    
    # --- 🤪 Абсурдные/Развлекательные ---
    InlineKeyboardButton("🤡 Тролль", callback_data="system_prompt:select:troll"), 
    InlineKeyboardButton("🤫 Секретный Агент", callback_data="system_prompt:select:secret_agent"),
]

max_tokens = [
    InlineKeyboardButton("📌 Кратко (≈50 слов)", callback_data="max_tokens:select:100"), 
    InlineKeyboardButton("📜 Средне (≈150 слов)", callback_data="max_tokens:select:250"), 
    InlineKeyboardButton("📚 Подробно (≈300+ слов)", callback_data="max_tokens:select:400"), 
]

languages = [
    InlineKeyboardButton("🇷🇺 Русский", callback_data="language:select:ru"),
    InlineKeyboardButton("🇬🇧 English", callback_data="language:select:en"),
    InlineKeyboardButton("🇪🇸 Español", callback_data="language:select:es"),
    InlineKeyboardButton("🇩🇪 Deutsch", callback_data="language:select:de"),
]

styles = [
    # Ваши существующие стили (сокращенные)
    InlineKeyboardButton("💬 Разговорный", callback_data="style:select:casual"),
    InlineKeyboardButton("💡 Креативный", callback_data="style:select:creative"),
    InlineKeyboardButton("📚 Академический", callback_data="style:select:academic"),
    InlineKeyboardButton("😄 Юмористический", callback_data="style:select:humorous"),
    InlineKeyboardButton("🔬 Технический", callback_data="style:select:technical"),
    InlineKeyboardButton("📌 Краткий", callback_data="style:select:concise"),
    InlineKeyboardButton("📰 Объективный", callback_data="style:select:journalistic"),
    
    # --- 💼 Профессиональные и Функциональные ---
    InlineKeyboardButton("💼 Строгий", callback_data="style:select:formal"),
    InlineKeyboardButton("👨‍⚖️ Юридический", callback_data="style:select:legal"),
    InlineKeyboardButton("📊 Тезисный", callback_data="style:select:slide"),
    InlineKeyboardButton("📝 Редактор", callback_data="style:select:editor"),
    InlineKeyboardButton("👩‍🏫 Педагог", callback_data="style:select:tutor"),
    
    # --- 🎭 Ролевые и Исторические ---
    InlineKeyboardButton("🏴‍☠️ Пират", callback_data="style:select:pirate"),
    InlineKeyboardButton("👑 Рыцарь", callback_data="style:select:knight"),
    InlineKeyboardButton("🎩 Джентльмен", callback_data="style:select:victorian"),
    InlineKeyboardButton("🤖 Ретро-ПК", callback_data="style:select:retro_pc"),
    InlineKeyboardButton("👽 Инопланетянин", callback_data="style:select:alien"),
    InlineKeyboardButton("🤠 Ковбой", callback_data="style:select:cowboy"),
    InlineKeyboardButton("🧙‍♂️ Волшебник", callback_data="style:select:wizard"),
    InlineKeyboardButton("🦸 Супергерой", callback_data="style:select:superhero"),
    InlineKeyboardButton("👶 Ребенок", callback_data="style:select:child"),
    InlineKeyboardButton("🌸 Аниме/Манга", callback_data="style:select:anime"), # <-- НОВЫЙ СТИЛЬ
    
    # --- 🎨 Литературные и Художественные ---
    InlineKeyboardButton("📜 Поэтический", callback_data="style:select:poet"),
    InlineKeyboardButton("🖋️ Эпический", callback_data="style:select:epic"),
    InlineKeyboardButton("🔮 Философский", callback_data="style:select:philosopher"),
    InlineKeyboardButton("🎶 Тексты песен", callback_data="style:select:lyricist"),
    InlineKeyboardButton("🌌 Sci-Fi", callback_data="style:select:scifi"),
    InlineKeyboardButton("🤫 Шепот", callback_data="style:select:whisper"),
    InlineKeyboardButton("🎭 Драматический", callback_data="style:select:drama"),
    InlineKeyboardButton("🧐 Критик", callback_data="style:select:review"),
    
    # --- 🤪 Абсурдные и Необычные ---
    InlineKeyboardButton("🤪 Абсурдный", callback_data="style:select:absurd"),
    InlineKeyboardButton("🤯 Кризис", callback_data="style:select:crisis"),
    InlineKeyboardButton("🐾 Кошка (Мяу!)", callback_data="style:select:cat"),
    InlineKeyboardButton("🔄 Обратный порядок", callback_data="style:select:reverse"),
    InlineKeyboardButton("🛑 Цифры", callback_data="style:select:numbers"),
    InlineKeyboardButton("🍕 Рецепт", callback_data="style:select:pizza_recipe"),
    InlineKeyboardButton("🥕 О моркови", callback_data="style:select:carrot"),
    InlineKeyboardButton("🔥 Аллитерация", callback_data="style:select:allit"),
    InlineKeyboardButton("❓ Вопросами", callback_data="style:select:questioner"),
    
    # --- 🧘 Эмоциональные и Нейтральные ---
    InlineKeyboardButton("😎 Сленг (Chill)", callback_data="style:select:chill"),
    InlineKeyboardButton("😴 Сонный", callback_data="style:select:sleepy"),
    InlineKeyboardButton("🙄 Саркастичный", callback_data="style:select:sarcastic"),
    InlineKeyboardButton("😇 Позитивный", callback_data="style:select:positive"),
    InlineKeyboardButton("😔 Грустный", callback_data="style:select:sad"),
    InlineKeyboardButton("🤫 Минималистичный", callback_data="style:select:minimal"),
    
    # --- 🗿 Мемы и Форматы ---
    InlineKeyboardButton("🗿 Сигма", callback_data="style:select:sigma"),
    InlineKeyboardButton("📈 Грайндсет", callback_data="style:select:grindset"),
    InlineKeyboardButton("🗣️ Комментарий Reddit", callback_data="style:select:reddit"),
    InlineKeyboardButton("💅 Инфлюенсер", callback_data="style:select:vibe_influencer"),
    InlineKeyboardButton("🤯 Теория заговора", callback_data="style:select:conspiracy"),
    
    # --- 💻 Профессиональные и Ролевые (Узконаправленные) ---
    InlineKeyboardButton("💻 Разработчик", callback_data="style:select:developer"),
    InlineKeyboardButton("🤖 Супер-логичный ИИ", callback_data="style:select:super_ai"),
    InlineKeyboardButton("🧘 Дзен", callback_data="style:select:zen"),
    InlineKeyboardButton("📺 Реклама", callback_data="style:select:advert"),
    
    # --- 🧵 Формат и Структура (Уникальные) ---
    InlineKeyboardButton("🧵 Twitter-тред", callback_data="style:select:twitter_thread"),
    InlineKeyboardButton("🎤 Стендап", callback_data="style:select:standup"),
    InlineKeyboardButton("❌ Отрицания", callback_data="style:select:negation"),
]

temperatures = [
    InlineKeyboardButton("🧊 0.1 (Точность и факты)", 
                         callback_data="temperature:select:0.1"),
    
    InlineKeyboardButton("📉 0.4 (Контролируемый ответ)", 
                         callback_data="temperature:select:0.4"),
    
    InlineKeyboardButton("⚖️ 0.7 (Сбалансированный ответ)", 
                         callback_data="temperature:select:0.7"),
    
    InlineKeyboardButton("📈 0.9 (Высокая креативность)", 
                         callback_data="temperature:select:0.9"),

    InlineKeyboardButton("🤯 1.0 (Максимум фантазии)", 
                         callback_data="temperature:select:1.0"),
]


data_items = {
    'style': styles,  # Ваш существующий список
    'temperature': temperatures, # Ваш существующий список
    'system_prompt': system_prompts, # Новый список
    'max_tokens': max_tokens, # Новый список
    'language': languages # Новый список
}







