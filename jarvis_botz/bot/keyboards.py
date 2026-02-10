from telegram import (Update, ReplyKeyboardMarkup,
                       ReplyKeyboardRemove, KeyboardButton,
                         InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo)

from telegram.ext import (ContextTypes, ConversationHandler)
import math
from typing import List, Tuple

import os


keyboard = [
    [KeyboardButton('🤖 Выбрать ИИ'), KeyboardButton('💎 Купить токены')],
    [KeyboardButton('⚙️ Настройки'), KeyboardButton('ℹ️ Инфо')],
    [KeyboardButton('🗑️ Чаты'), KeyboardButton('🛠️ Инструменты')],
    [KeyboardButton('➕ Создать новый чат')]
]

start_keyboard = ReplyKeyboardMarkup(
    keyboard=keyboard,
    resize_keyboard=True,
    input_field_placeholder='Введите сообщение или команду',
    is_persistent=True
)


set_model_keyboard = [
        InlineKeyboardButton(text="🚀 GPT-5 Mini (OpenAI)", callback_data="model:select:openai/gpt-5-mini"),
        InlineKeyboardButton(text="✨ Gemini Flash 2.5 Lite (Google)", callback_data="model:select:google/gemini-2.5-flash-lite"),
        InlineKeyboardButton(text="🧠 Claude 3 Haiku (Anthropic)", callback_data="model:select:anthropic/claude-3-haiku"),
        InlineKeyboardButton(text="🦙 Llama 4 70B (Meta)", callback_data="model:select:meta-llama/llama-4-maverick"),
        InlineKeyboardButton(text="⚡ Mistral 675B (Mistral)", callback_data="model:select:mistralai/mistral-large-2512"),
    ]



setting_keyboard = [
    # Ряд 1: Ключевое поведение
    [InlineKeyboardButton('✨ стиль', callback_data='style:page:0'), 
     InlineKeyboardButton('🌡️ температура', callback_data='temperature:page:0')],
    
    # Ряд 2: Роль и размер
    [InlineKeyboardButton('🗣️ Профиль ИИ', callback_data='system_prompt:page:0'),
     InlineKeyboardButton('🗜️ Длина ответа', callback_data='max_tokens:page:0')],
     
    # Ряд 3: Лимиты и Язык
    [InlineKeyboardButton('📊 Лимиты', callback_data='developing:page:0'),
     InlineKeyboardButton('🌍 Язык', callback_data='language:page:0')],
     
    # ⬆️ Важное дополнение для UX: кнопка "Назад"
    [InlineKeyboardButton('« Назад', callback_data='setting:quit:_quit_delete')]
]

setting_keyboard_markup = InlineKeyboardMarkup(
    inline_keyboard=setting_keyboard
)

system_prompts = [
    # --- 🧠 ИНТЕЛЛЕКТУАЛЬНЫЙ ЦЕНТР (Power Roles) ---
    InlineKeyboardButton("🏛 Архитектор Логики", callback_data="system_prompt:select:architect"),  # Глубокое решение задач
    InlineKeyboardButton("🕵️ Исследователь (OSINT)", callback_data="system_prompt:select:researcher"), # Поиск и проверка фактов
    InlineKeyboardButton("💡 Стратег (Game Theory)", callback_data="system_prompt:select:strategist"), # Планирование и тактика
    InlineKeyboardButton("⚖️ Профи-Консультант", callback_data="system_prompt:select:consultant"),   # Бизнес, право, финансы

    # --- 🛠️ МАСТЕР ИНСТРУМЕНТОВ (Utility Experts) ---
    InlineKeyboardButton("🚀 Senior Fullstack", callback_data="system_prompt:select:senior_dev"),  # Код, архитектура, безопасность
    InlineKeyboardButton("🎨 Prompt-Инженер", callback_data="system_prompt:select:prompt_master"), # Создает идеальные промпты
    InlineKeyboardButton("📈 Маркетолог-Психолог", callback_data="system_prompt:select:marketer"), # Тексты, которые цепляют
    InlineKeyboardButton("✍️ Главный Редактор", callback_data="system_prompt:select:chief_editor"), # Доводит любой текст до идеала

    # --- 🌌 АТМОСФЕРА И ВАЙБ (Vibe & Character) ---
    InlineKeyboardButton("🦾 Кибер-Разум (2077)", callback_data="system_prompt:select:cyber_mind"), # Футуристичный, холодный, точный
    InlineKeyboardButton("🌿 Стоик-Философ", callback_data="system_prompt:select:stoic"),          # Мудрость, спокойствие, смысл
    InlineKeyboardButton("🎭 Теневой Игрок", callback_data="system_prompt:select:shadow"),        # Хитрость, обход ограничений, нестандарт
    InlineKeyboardButton("🔥 Твой Соперник", callback_data="system_prompt:select:rival"),         # Подначивает, мотивирует, критикует

    # --- 🛠️ ЭКСПЕРТЫ ПО ЖИЗНИ (Life & Security) ---
    InlineKeyboardButton("⚡️ Билдер-Биохакер", callback_data="system_prompt:select:biohacker"),   # Здоровье и продуктивность
    InlineKeyboardButton("⚖️ Юрист-Детектив", callback_data="system_prompt:select:legal_expert"), # Защита и документы
    InlineKeyboardButton("💎 Крипто-Венчур", callback_data="system_prompt:select:financier"),    # Рынки и капитал
    InlineKeyboardButton("🧹 Решала (The Fixer)", callback_data="system_prompt:select:fixer"),   # Выход из тупиковых ситуаций
]

max_tokens = [
    InlineKeyboardButton("📌 Кратко (≈50 слов)", callback_data="max_tokens:select:100"), 
    InlineKeyboardButton("📜 Средне (≈150 слов)", callback_data="max_tokens:select:250"), 
    InlineKeyboardButton("📚 Подробно (≈300+ слов)", callback_data="max_tokens:select:400"), 
]

languages = [
    InlineKeyboardButton("🇷🇺 Русский", callback_data="language:select:russian"),
    InlineKeyboardButton("🇬🇧 English", callback_data="language:select:english"),
    InlineKeyboardButton("🇪🇸 Español", callback_data="language:select:spanish"),
    InlineKeyboardButton("🇩🇪 Deutsch", callback_data="language:select:german"),
]

styles = [
    # --- 🛠 ИНСТРУМЕНТЫ МОЩНОСТИ (Core Efficiency) ---
    InlineKeyboardButton("🔍 Суть (TL;DR)", callback_data="style:select:tldr"),             # Выжимка главного
    InlineKeyboardButton("🎯 Точный и краткий", callback_data="style:select:concise"),      # Без лишних слов
    InlineKeyboardButton("🧪 Глубокий анализ", callback_data="style:select:analytical"),    # Логика и детализация
    InlineKeyboardButton("✍️ Редактор-корректор", callback_data="style:select:proofread"),   # Исправление ошибок и стиля
    InlineKeyboardButton("👶 Объясни проще (ELI5)", callback_data="style:select:eli5"),      # Сложное простыми словами
    InlineKeyboardButton("📝 По шагам (1. 2. 3.)", callback_data="style:select:steps"),     # Четкие алгоритмы действий

    # --- 💼 КАРЬЕРА И БИЗНЕС (Professional Edge) ---
    InlineKeyboardButton("💼 Executive (CEO)", callback_data="style:select:business"),      # Тон топ-менеджмента
    InlineKeyboardButton("📧 Email-мастер", callback_data="style:select:email"),            # Идеальная переписка
    InlineKeyboardButton("⚖️ Адвокат дьявола", callback_data="style:select:critic"),        # Критика и поиск дыр в идеях
    InlineKeyboardButton("💰 Продажник (Pitch)", callback_data="style:select:sales"),       # Текст, который убеждает
    InlineKeyboardButton("📊 Аналитик", callback_data="style:select:analyst"),              # Структура, таблицы, выводы
    InlineKeyboardButton("👔 HR-интервьюер", callback_data="style:select:hr"),              # Режим подготовки к работе

    # --- ⚡ СОВРЕМЕННЫЙ ВАЙБ (Modern & Meta) ---
    InlineKeyboardButton("🗿 Сигма / База", callback_data="style:select:sigma"),            # Прямолинейно, уверенно, честно
    InlineKeyboardButton("💅 Slay (Gen-Z)", callback_data="style:select:genz"),             # Тренды, сленг, энергия
    InlineKeyboardButton("🔥 Прожарка (Roast)", callback_data="style:select:roast"),        # Острый юмор и критика
    InlineKeyboardButton("🤫 Cyberpunk", callback_data="style:select:noir"),                # Атмосфера будущего и лаконичность
    InlineKeyboardButton("🥦 Дзен (Mindful)", callback_data="style:select:zen"),            # Спокойствие и поддержка
    InlineKeyboardButton("💡 Мозговой штурм", callback_data="style:select:creative"),      # Нестандартный креатив

    # --- 🚀 КОНТЕНТ И ОБУЧЕНИЕ (Growth & Media) ---
    InlineKeyboardButton("🎨 Промпт-инженер", callback_data="style:select:prompt"),          # Создание запросов для других ИИ
    InlineKeyboardButton("🎞 Сценарист", callback_data="style:select:script"),              # Для Reels/Shorts/TikTok
    InlineKeyboardButton("🧵 Тред-мейкер", callback_data="style:select:thread"),            # Формат X (Twitter) или цепочек
    InlineKeyboardButton("🧱 Первоосновы", callback_data="style:select:first_principles"), # Глубокое понимание темы
    InlineKeyboardButton("🎓 Сократ (Ментор)", callback_data="style:select:socratic"),      # Обучение через наводящие вопросы
    InlineKeyboardButton("💻 Код-мастер", callback_data="style:select:dev"),                # Только чистый код и пояснения
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
    'language': languages, # Новый список
    'set_model':set_model_keyboard
}







