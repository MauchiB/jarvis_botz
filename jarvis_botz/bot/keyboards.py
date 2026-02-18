from telegram import (ReplyKeyboardMarkup, KeyboardButton,
                      InlineKeyboardButton, InlineKeyboardMarkup)


loading_texts = [
    "Думаю… 🤔",
    "Генерирую ответ… ⏳",
    "Подбираю лучшие слова… ✍️",
    "Анализирую вопрос… 🧠",
    "Готовлю умный ответ… 🤓",
    "Секунду, считаю варианты… 🔢",
    "Ищу идеальный ответ… 🔍",
    "Почти готово… ⌛",
    "Обрабатываю данные… ⚙️",
    "Строю нейросети… 🕸️",
    "Сверяюсь с виртуальной библиотекой… 📚",
    "Печатаю… 💬",
    "Думаю быстрее света… ⚡",
    "Загружаю мысли… 💭",
    "Формулирую гениальность… ✨",
    "Придумываю лучший вариант… 🛠️",
    "Сканирую интернет (почти)… 🌐",
    "Собираю слова по буквам… 🔤",
    "Компилирую ответ… 🧩",
    "Проверяю логику… 🧐",
    "Взвешиваю аргументы… ⚖️",
    "Настраиваю нейроны… 🔌",
    "Включаю режим «умный»… 🤖",
    "Секунду, магия происходит… 🪄",
    "Готовлю что-то интересное… 🎁",
    "Почти придумал… 😌",
    "Мысли сходятся… 🌀",
    "Пишу шедевр… 🖋️",
    "Идёт процесс мышления… 🧠",
    "Ответ на подходе… 🚀"
]



keyboard = [
    [KeyboardButton('⚙️ Настройки'), KeyboardButton('ℹ️ Инфо')],
    [KeyboardButton('🗑️ Чаты'),KeyboardButton('➕ Создать новый чат')],
    [KeyboardButton('💎 Купить токены')]
]


start_keyboard = ReplyKeyboardMarkup(
    keyboard=keyboard,
    resize_keyboard=True,
    input_field_placeholder='Введите сообщение или команду',
    is_persistent=True,
    one_time_keyboard=False
)


model_keyboard = [
        InlineKeyboardButton(text="🚀 GPT-5 Mini (OpenAI)", callback_data="model:select:openai/gpt-5-mini"),
        InlineKeyboardButton(text="✨ Gemini Flash 2.5 Lite (Google)", callback_data="model:select:google/gemini-2.5-flash-lite"),
        InlineKeyboardButton(text="🧠 Claude 3 Haiku (Anthropic)", callback_data="model:select:anthropic/claude-3-haiku"),
        InlineKeyboardButton(text="🦙 Llama 4 70B (Meta)", callback_data="model:select:meta-llama/llama-4-maverick"),
        InlineKeyboardButton(text="⚡ Mistral 675B (Mistral)", callback_data="model:select:mistralai/mistral-large-2512"),
    ]



settings_keyboard = [
    [InlineKeyboardButton('🤖 Выбрать ИИ', callback_data='model:page:0'),
     InlineKeyboardButton('✨ стиль', callback_data='style:page:0')],
    
    
    [InlineKeyboardButton('🌍 Язык', callback_data='language:page:0'), 
     InlineKeyboardButton('🌡️ температура', callback_data='temperature:page:0')],
    
    
    [InlineKeyboardButton('🗣️ Профиль ИИ', callback_data='system_prompt:page:0'),
     InlineKeyboardButton('🗜️ Длина ответа', callback_data='max_tokens:page:0')],
     

    [InlineKeyboardButton('‼️СБРОСИТЬ НАСТРОЙКИ‼️', callback_data='settings:reset:_reset_settings')],
    [InlineKeyboardButton('« Назад', callback_data='settings:quit:_quit_delete')]
]

settings_keyboard_markup = InlineKeyboardMarkup(
    inline_keyboard=settings_keyboard
)

system_prompts = [
    InlineKeyboardButton("🏛 Архитектор Логики", callback_data="system_prompt:select:architect"),  # Глубокое решение задач
    InlineKeyboardButton("🕵️ Исследователь (OSINT)", callback_data="system_prompt:select:researcher"), # Поиск и проверка фактов
    InlineKeyboardButton("💡 Стратег (Game Theory)", callback_data="system_prompt:select:strategist"), # Планирование и тактика
    InlineKeyboardButton("⚖️ Профи-Консультант", callback_data="system_prompt:select:consultant"),   # Бизнес, право, финансы

    InlineKeyboardButton("🚀 Senior Fullstack", callback_data="system_prompt:select:senior_dev"),  # Код, архитектура, безопасность
    InlineKeyboardButton("🎨 Prompt-Инженер", callback_data="system_prompt:select:prompt_master"), # Создает идеальные промпты
    InlineKeyboardButton("📈 Маркетолог-Психолог", callback_data="system_prompt:select:marketer"), # Тексты, которые цепляют
    InlineKeyboardButton("✍️ Главный Редактор", callback_data="system_prompt:select:chief_editor"), # Доводит любой текст до идеала

    InlineKeyboardButton("🦾 Кибер-Разум (2077)", callback_data="system_prompt:select:cyber_mind"), # Футуристичный, холодный, точный
    InlineKeyboardButton("🌿 Стоик-Философ", callback_data="system_prompt:select:stoic"),          # Мудрость, спокойствие, смысл
    InlineKeyboardButton("🎭 Теневой Игрок", callback_data="system_prompt:select:shadow"),        # Хитрость, обход ограничений, нестандарт
    InlineKeyboardButton("🔥 Твой Соперник", callback_data="system_prompt:select:rival"),         # Подначивает, мотивирует, критикует

    InlineKeyboardButton("⚡️ Билдер-Биохакер", callback_data="system_prompt:select:biohacker"),   # Здоровье и продуктивность
    InlineKeyboardButton("⚖️ Юрист-Детектив", callback_data="system_prompt:select:legal_expert"), # Защита и документы
    InlineKeyboardButton("💎 Крипто-Венчур", callback_data="system_prompt:select:financier"),    # Рынки и капитал
    InlineKeyboardButton("🧹 Решала (The Fixer)", callback_data="system_prompt:select:fixer"),   # Выход из тупиковых ситуаций
]

max_tokens_keyboard = [
    InlineKeyboardButton("⚡ Очень кратко (~40–60 слов)", callback_data="max_tokens:select:80"),
    InlineKeyboardButton("📌 Кратко (~80–120 слов)", callback_data="max_tokens:select:150"),
    InlineKeyboardButton("📝 Развернуто (~150–220 слов)", callback_data="max_tokens:select:250"),
    InlineKeyboardButton("📚 Подробно (~300–400 слов)", callback_data="max_tokens:select:450"),
    InlineKeyboardButton("🧠 Максимально подробно (~600–800 слов)", callback_data="max_tokens:select:800"),
    InlineKeyboardButton("🚀 Лонгрид / Эксперт (~1000+ слов)", callback_data="max_tokens:select:1200")
]

languages_keyboard = [
    InlineKeyboardButton("🇷🇺 Русский — понятно и по-делу 🧊", callback_data="language:select:russian"),
    InlineKeyboardButton("🇬🇧 English — classic & global 🌍", callback_data="language:select:english"),
    InlineKeyboardButton("🇪🇸 Español — rápido y alegre 🎉", callback_data="language:select:spanish"),
    InlineKeyboardButton("🇩🇪 Deutsch — präzise & klar ⚙️", callback_data="language:select:german"),
    InlineKeyboardButton("🇫🇷 Français — élégant ✨", callback_data="language:select:french"),
    InlineKeyboardButton("🇮🇹 Italiano — bello & semplice 🍝", callback_data="language:select:italian"),
    InlineKeyboardButton("🇵🇹 Português — suave & fácil 🌊", callback_data="language:select:portuguese"),
    InlineKeyboardButton("🇺🇦 Українська — щиро 💙💛", callback_data="language:select:ukrainian"),
    InlineKeyboardButton("🇵🇱 Polski — szybko ⚡", callback_data="language:select:polish"),
    InlineKeyboardButton("🇹🇷 Türkçe — net ve hızlı 🔥", callback_data="language:select:turkish"),
    InlineKeyboardButton("🇯🇵 日本語 — 丁寧で正確 🎌", callback_data="language:select:japanese"),
    InlineKeyboardButton("🇨🇳 中文 — 简洁高效 🐉", callback_data="language:select:chinese"),
    InlineKeyboardButton("🇰🇷 한국어 — 빠르고 정확 ⚡", callback_data="language:select:korean"),
]
styles_keyboard = [
    InlineKeyboardButton("🔍 Суть (TL;DR)", callback_data="style:select:tldr"),             # Выжимка главного
    InlineKeyboardButton("🎯 Точный и краткий", callback_data="style:select:concise"),      # Без лишних слов
    InlineKeyboardButton("🧪 Глубокий анализ", callback_data="style:select:analytical"),    # Логика и детализация
    InlineKeyboardButton("✍️ Редактор-корректор", callback_data="style:select:proofread"),   # Исправление ошибок и стиля
    InlineKeyboardButton("👶 Объясни проще (ELI5)", callback_data="style:select:eli5"),      # Сложное простыми словами
    InlineKeyboardButton("📝 По шагам (1. 2. 3.)", callback_data="style:select:steps"),     # Четкие алгоритмы действий


    InlineKeyboardButton("💼 Executive (CEO)", callback_data="style:select:business"),      # Тон топ-менеджмента
    InlineKeyboardButton("📧 Email-мастер", callback_data="style:select:email"),            # Идеальная переписка
    InlineKeyboardButton("⚖️ Адвокат дьявола", callback_data="style:select:critic"),        # Критика и поиск дыр в идеях
    InlineKeyboardButton("💰 Продажник (Pitch)", callback_data="style:select:sales"),       # Текст, который убеждает
    InlineKeyboardButton("📊 Аналитик", callback_data="style:select:analyst"),              # Структура, таблицы, выводы
    InlineKeyboardButton("👔 HR-интервьюер", callback_data="style:select:hr"),              # Режим подготовки к работе


    InlineKeyboardButton("🗿 Сигма / База", callback_data="style:select:sigma"),            # Прямолинейно, уверенно, честно
    InlineKeyboardButton("💅 Slay (Gen-Z)", callback_data="style:select:genz"),             # Тренды, сленг, энергия
    InlineKeyboardButton("🔥 Прожарка (Roast)", callback_data="style:select:roast"),        # Острый юмор и критика
    InlineKeyboardButton("🤫 Cyberpunk", callback_data="style:select:noir"),                # Атмосфера будущего и лаконичность
    InlineKeyboardButton("🥦 Дзен (Mindful)", callback_data="style:select:zen"),            # Спокойствие и поддержка
    InlineKeyboardButton("💡 Мозговой штурм", callback_data="style:select:creative"),      # Нестандартный креатив


    InlineKeyboardButton("🎨 Промпт-инженер", callback_data="style:select:prompt"),          # Создание запросов для других ИИ
    InlineKeyboardButton("🎞 Сценарист", callback_data="style:select:script"),              # Для Reels/Shorts/TikTok
    InlineKeyboardButton("🧵 Тред-мейкер", callback_data="style:select:thread"),            # Формат X (Twitter) или цепочек
    InlineKeyboardButton("🧱 Первоосновы", callback_data="style:select:first_principles"), # Глубокое понимание темы
    InlineKeyboardButton("🎓 Сократ (Ментор)", callback_data="style:select:socratic"),      # Обучение через наводящие вопросы
    InlineKeyboardButton("💻 Код-мастер", callback_data="style:select:dev"),                # Только чистый код и пояснения
]

temperatures_keyboard = [
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
    'style': styles_keyboard,
    'temperature': temperatures_keyboard,
    'system_prompt': system_prompts,
    'max_tokens': max_tokens_keyboard,
    'language': languages_keyboard,
    'model':model_keyboard
}


help_text = (
        "🤖 <b>Jarvis AI — ваш персональный ассистент</b>\n\n"
        
        "Я умею помогать с учёбой, кодом, переводами, идеями и просто болтать 😎\n\n"
        
        "<b>🚀 Возможности бота</b>\n"
        "• Ответы на любые вопросы\n"
        "• Помощь с программированием\n"
        "• Переводы текстов\n"
        "• Написание сочинений и рефератов\n"
        "• Генерация идей и планов\n"
        "• Работа с изображениями\n"
        "• Поддержка нескольких языков 🌍\n\n"
        
        "<b>💎 Токены</b>\n"
        "Бот работает на токенах.\n"
        "• Чем длиннее ответ — тем больше токенов\n"
        "• Купить токены можно в меню «💎 Купить токены»\n\n"
        
        "<b>📨 Длинные ответы</b>\n"
        "Telegram имеет лимит 4096 символов.\n"
        "Если ответ очень большой — он может прийти в 2 сообщениях.\n\n"
        
        "<b>🔗 Реферальная система</b>\n"
        "/ref — получить реферальную ссылку\n"
        "Приглашайте друзей и получайте бонусы 🎁\n\n"
        
        "<b>💸 Возврат средств</b>\n"
        "/refund — возврат звёзд при ошибке оплаты.\n"
        "Работает только если платёж действительно не прошёл.\n\n"
        
        "<b>⚙️ Настройки</b>\n"
        "Можно менять:\n"
        "• язык\n"
        "• длину ответа\n"
        "• стиль текста\n\n"
        
        "<b>🧠 Как работает ИИ?</b>\n"
        "Вы отправляете сообщение → ИИ анализирует → формирует ответ.\n"
        "Во время генерации может показываться «Думаю…» ⏳\n\n"
        
        "<b>📌 Команды</b>\n"
        "/start — перезапуск бота\n"
        "/help — это меню\n"
        "/ref — реферальная ссылка\n"
        "/refund — возврат платежа\n\n"
        
        "✨ <i>Просто напишите сообщение и я отвечу!</i>"
    )








