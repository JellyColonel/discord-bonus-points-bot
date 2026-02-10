"""
Activity definitions and lookup functions.
OPTIMIZED: Caching and O(1) lookups for better performance.
"""

from typing import Any, Dict, List, Optional

# Type alias for activity dictionary
Activity = Dict[str, Any]

# =============================================================================
# Activity Definitions
# =============================================================================

ACTIVITIES: List[Activity] = [
    # =========================================================================
    # SOLO ACTIVITIES
    # =========================================================================
    # -------------------------------------------------------------------------
    # Solo - Low Time
    # -------------------------------------------------------------------------
    {
        "id": "lottery",
        "name": "🎟️ Купить лотерейный билет",
        "bp": 1,
        "type": "solo",
        "time": "low",
        "description": "Купите один лотерейный билет у NPC",
    },
    {
        "id": "browser",
        "name": "🌐 Посетить любой сайт в браузере",
        "bp": 1,
        "type": "solo",
        "time": "low",
        "description": "Откройте внутриигровой браузер и зайдите на любой сайт",
    },
    {
        "id": "brawl",
        "name": "🎧 Зайти в любой канал в Brawl",
        "bp": 1,
        "type": "solo",
        "time": "low",
    },
    {
        "id": "match_like",
        "name": "❤️ Поставить лайк любой анкете в Match",
        "bp": 1,
        "type": "solo",
        "time": "low",
    },
    {
        "id": "business_materials",
        "name": "📦 Заказ материалов для бизнеса вручную",
        "bp": 1,
        "type": "solo",
        "time": "low",
        "description": "Закажите материалы для бизнеса вручную (не автозаказ)",
    },
    {
        "id": "shooting_range",
        "name": "🔫 Успешная тренировка в тире",
        "bp": 1,
        "type": "solo",
        "time": "low",
        "description": "Пройдите тренировку в тире и наберите минимальный балл",
    },
    {
        "id": "film_studio",
        "name": "🎥 Арендовать киностудию",
        "bp": 2,
        "type": "solo",
        "time": "low",
    },
    {
        "id": "cinema",
        "name": "🎬 Добавить 5 видео в кинотеатре",
        "bp": 1,
        "type": "solo",
        "time": "low",
        "description": "Загрузите 5 видео в кинотеатр через меню управления",
    },
    {
        "id": "surgeon",
        "name": "💉 Два раза оплатить смену внешности у хирурга",
        "bp": 2,
        "type": "solo",
        "time": "low",
    },
    {
        "id": "dp_case",
        "name": "💎 Прокрутить за DP кейс",
        "bp": 10,
        "type": "solo",
        "time": "low",
        "description": "Откройте один кейс за донат-валюту (DP)",
    },
    {
        "id": "pet_ball",
        "name": "🐾 Кинуть мяч питомцу 15 раз",
        "bp": 2,
        "type": "solo",
        "time": "low",
    },
    {
        "id": "pet_commands",
        "name": "🐶 15 выполненных питомцем команд",
        "bp": 2,
        "type": "solo",
        "time": "low",
    },
    {
        "id": "casino_wheel",
        "name": "🎰 Ставка в колесе удачи в казино",
        "bp": 3,
        "type": "solo",
        "time": "low",
        "description": "Сделайте одну ставку в колесе удачи внутри казино",
    },
    {
        "id": "metro",
        "name": "🚇 Проехать 1 станцию на метро",
        "bp": 2,
        "type": "solo",
        "time": "low",
    },
    {
        "id": "fishing",
        "name": "🎣 Поймать 20 рыб",
        "bp": 4,
        "type": "solo",
        "time": "low",
        "description": "Поймайте 20 рыб на рыбалке за один день",
    },
    {
        "id": "car_repair",
        "name": "🔧 Починить деталь в автосервисе",
        "bp": 1,
        "type": "solo",
        "time": "low",
    },
    {
        "id": "basketball",
        "name": "🏀 Забросить 2 мяча в баскетболе",
        "bp": 1,
        "type": "solo",
        "time": "low",
    },
    {
        "id": "football",
        "name": "⚽ Забить 2 гола в футболе",
        "bp": 1,
        "type": "solo",
        "time": "low",
    },
    {
        "id": "darts",
        "name": "🎯 Победить в дартс",
        "bp": 1,
        "type": "solo",
        "time": "low",
    },
    {
        "id": "volleyball",
        "name": "🏐 Поиграть 1 минуту в волейбол",
        "bp": 1,
        "type": "solo",
        "time": "low",
    },
    {
        "id": "table_tennis",
        "name": "🏓 Поиграть 1 минуту в настольный теннис",
        "bp": 1,
        "type": "solo",
        "time": "low",
    },
    {
        "id": "tennis",
        "name": "🎾 Поиграть 1 минуту в большой теннис",
        "bp": 1,
        "type": "solo",
        "time": "low",
    },
    {
        "id": "leasing",
        "name": "💳 Сделать платеж по лизингу",
        "bp": 1,
        "type": "solo",
        "time": "low",
    },
    {
        "id": "greenhouse",
        "name": "🌿 Посадить траву в теплице",
        "bp": 4,
        "type": "solo",
        "time": "low",
    },
    {
        "id": "painkiller_lab",
        "name": "💊 Запустить переработку обезболивающих",
        "bp": 4,
        "type": "solo",
        "time": "low",
    },
    # -------------------------------------------------------------------------
    # Solo - Medium Time
    # -------------------------------------------------------------------------
    {
        "id": "casino_zeros",
        "name": "👀 Нули в казино",
        "bp": 2,
        "type": "solo",
        "time": "medium",
        "description": "Дождитесь выпадения нулей на рулетке в казино",
    },
    {
        "id": "construction",
        "name": "🏗️ 25 действий на стройке",
        "bp": 2,
        "type": "solo",
        "time": "medium",
        "description": "Выполните 25 действий на работе строителя",
    },
    {
        "id": "port",
        "name": "⚓ 25 действий в порту",
        "bp": 2,
        "type": "solo",
        "time": "medium",
    },
    {
        "id": "mine",
        "name": "⛏️ 25 действий в шахте",
        "bp": 2,
        "type": "solo",
        "time": "medium",
    },
    {
        "id": "gym",
        "name": "💪 20 подходов в тренажерном зале",
        "bp": 1,
        "type": "solo",
        "time": "medium",
    },
    {
        "id": "post_office",
        "name": "📦 10 посылок на почте",
        "bp": 1,
        "type": "solo",
        "time": "medium",
    },
    {
        "id": "farm",
        "name": "🌾 10 действий на ферме",
        "bp": 1,
        "type": "solo",
        "time": "medium",
    },
    {
        "id": "trucker",
        "name": "🚛 Выполнить 3 заказа дальнобойщиком",
        "bp": 2,
        "type": "solo",
        "time": "medium",
    },
    {
        "id": "club_quests",
        "name": "🎫 Выполнить 2 квеста любых клубов",
        "bp": 4,
        "type": "solo",
        "time": "medium",
        "description": "Завершите 2 квеста от любых клубов на сервере",
    },
    {
        "id": "bus",
        "name": "🚌 2 круга на любом маршруте автобусника",
        "bp": 2,
        "type": "solo",
        "time": "medium",
    },
    {
        "id": "graffiti",
        "name": "🎨 7 закрашенных граффити",
        "bp": 1,
        "type": "solo",
        "time": "medium",
    },
    {
        "id": "contraband",
        "name": "📦 Сдать 5 контрабанды",
        "bp": 2,
        "type": "solo",
        "time": "medium",
    },
    # -------------------------------------------------------------------------
    # Solo - High Time
    # -------------------------------------------------------------------------
    {
        "id": "online_3h",
        "name": "🕒 3 часа в онлайне",
        "bp": 2,
        "type": "solo",
        "time": "high",
        "repeatable": True,
        "description": "Провести 3 часа в онлайне на сервере. Можно выполнять несколько раз",
    },
    {
        "id": "firefighter",
        "name": '🔥 Потушить 25 "огоньков" пожарным',
        "bp": 1,
        "type": "solo",
        "time": "high",
    },
    {
        "id": "treasure",
        "name": "🏺 Выкопать 1 сокровище (не хлам)",
        "bp": 1,
        "type": "solo",
        "time": "high",
    },
    {
        "id": "lockpicking",
        "name": "🔓 Взломать 15 замков",
        "bp": 2,
        "type": "solo",
        "time": "high",
    },
    {
        "id": "airdrops",
        "name": "🪂 Принять участие в двух Airdrop",
        "bp": 4,
        "type": "solo",
        "time": "high",
        "description": "Примите участие в двух событиях Airdrop (сброс груза)",
    },
    {
        "id": "vehicle_registration",
        "name": "🚗 Поставить на учет 2 автомобиля",
        "bp": 1,
        "type": "solo",
        "time": "high",
    },
    {
        "id": "arrest",
        "name": "👮 Произвести 1 арест в КПЗ",
        "bp": 1,
        "type": "solo",
        "time": "high",
    },
    {
        "id": "bail_out",
        "name": "⚖️ Выкупить двух человек из КПЗ",
        "bp": 2,
        "type": "solo",
        "time": "high",
    },
    {
        "id": "medcards",
        "name": "💳 5 выданных медкарт в EMS",
        "bp": 2,
        "type": "solo",
        "time": "high",
    },
    {
        "id": "ems_calls",
        "name": "🚑 Закрыть 15 вызовов в EMS",
        "bp": 2,
        "type": "solo",
        "time": "high",
    },
    {
        "id": "wn_ads",
        "name": "📰 Отредактировать 40 объявлений в WN",
        "bp": 2,
        "type": "solo",
        "time": "high",
    },
    {
        "id": "codes",
        "name": "🚨 Закрыть 5 кодов в силовых структурах",
        "bp": 2,
        "type": "solo",
        "time": "high",
    },
    {
        "id": "hunting",
        "name": "🐻 5 раз снять 100% шкуру с животных",
        "bp": 2,
        "type": "solo",
        "time": "high",
    },
    # =========================================================================
    # PAIR ACTIVITIES
    # =========================================================================
    # -------------------------------------------------------------------------
    # Pair - Low Time
    # -------------------------------------------------------------------------
    {
        "id": "karting",
        "name": "🏎️ Выиграть гонку в картинге",
        "bp": 1,
        "type": "pair",
        "time": "low",
    },
    {
        "id": "street_race",
        "name": "🏁 Проехать 1 уличную гонку",
        "bp": 1,
        "type": "pair",
        "time": "low",
    },
    {
        "id": "arena",
        "name": "🎮 Выиграть 3 любых игры на арене",
        "bp": 1,
        "type": "pair",
        "time": "low",
    },
    {
        "id": "armwrestling",
        "name": "💪 Победить в армрестлинге",
        "bp": 1,
        "type": "pair",
        "time": "low",
    },
    {
        "id": "casino_mafia",
        "name": "🎭 Сыграть в мафию в казино",
        "bp": 3,
        "type": "pair",
        "time": "low",
    },
    {
        "id": "car_repair_other",
        "name": "🔧 Починить деталь авто другого игрока",
        "bp": 4,
        "type": "pair",
        "time": "low",
    },
    # -------------------------------------------------------------------------
    # Pair - Medium Time
    # -------------------------------------------------------------------------
    {
        "id": "dance_battle",
        "name": "💃 3 победы в Дэнс Баттлах",
        "bp": 2,
        "type": "pair",
        "time": "medium",
    },
    {
        "id": "training_complex",
        "name": "🏋️ Выиграть 5 игр в тренировочном комплексе",
        "bp": 1,
        "type": "pair",
        "time": "medium",
    },
    # -------------------------------------------------------------------------
    # Pair - High Time
    # -------------------------------------------------------------------------
    {
        "id": "capts_bizwars",
        "name": "⚔️ Участие в каптах/бизварах",
        "bp": 1,
        "type": "pair",
        "time": "high",
    },
    {
        "id": "hummer_vzh",
        "name": "🚙 Сдать Хаммер с ВЗХ",
        "bp": 3,
        "type": "pair",
        "time": "high",
    },
]

# =============================================================================
# Caching and Lookup Functions
# =============================================================================

_ACTIVITIES_BY_ID_CACHE: Dict[str, Activity] = {}


def _initialize_caches() -> None:
    """Initialize caches for fast activity lookups."""
    global _ACTIVITIES_BY_ID_CACHE
    _ACTIVITIES_BY_ID_CACHE = {activity["id"]: activity for activity in ACTIVITIES}


_initialize_caches()

TOTAL_ACTIVITIES = len(ACTIVITIES)


def get_all_activities() -> List[Activity]:
    """Get list of all activities. O(1)"""
    return ACTIVITIES


def get_activity_by_id(activity_id: str) -> Optional[Activity]:
    """Find activity by ID. O(1) dictionary lookup."""
    return _ACTIVITIES_BY_ID_CACHE.get(activity_id)


def is_repeatable(activity_id: str) -> bool:
    """Check if an activity is repeatable. O(1) dictionary lookup."""
    activity = _ACTIVITIES_BY_ID_CACHE.get(activity_id)
    return bool(activity and activity.get("repeatable", False))
