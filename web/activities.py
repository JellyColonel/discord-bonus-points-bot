"""
Activity definitions and lookup functions.
OPTIMIZED: Caching and O(1) lookups for better performance.
"""

from typing import Any, Dict, List, Optional

# Type alias for activity dictionary
Activity = Dict[str, Any]

# =============================================================================
# Category Definitions
# =============================================================================

CATEGORIES = {
    # Global fraction categories (for bulk hide/show)
    "all_crime": {
        "id": "all_crime",
        "name": "🔴 Все криминальные",
        "type": "fraction",
        "description": "Скрыть все активности для криминальных фракций",
    },
    "all_gov": {
        "id": "all_gov",
        "name": "🔵 Все гос. структуры",
        "type": "fraction",
        "description": "Скрыть все активности для гос. структур",
    },
    # Specific categories
    "smartphone": {
        "id": "smartphone",
        "name": "📱 Смартфон",
        "type": "specific",
        "description": "Активности через телефон",
    },
    "casino": {
        "id": "casino",
        "name": "🎰 Казино",
        "type": "specific",
        "description": "Активности в казино",
    },
    "pet": {
        "id": "pet",
        "name": "🐕 Питомец",
        "type": "specific",
        "description": "Активности с питомцем",
    },
    "sport": {
        "id": "sport",
        "name": "⚽ Спорт",
        "type": "specific",
        "description": "Спортивные игры",
    },
    "work": {
        "id": "work",
        "name": "🔨 Работы",
        "type": "specific",
        "description": "Рабочие активности",
    },
    "ems": {
        "id": "ems",
        "name": "🏥 EMS",
        "type": "specific",
        "description": "Активности для EMS",
    },
    "lspd": {
        "id": "lspd",
        "name": "🚔 LSPD",
        "type": "specific",
        "description": "Активности для LSPD",
    },
    "wn": {
        "id": "wn",
        "name": "📺 Weazel News",
        "type": "specific",
        "description": "Активности для Weazel News",
    },
    "gangs": {
        "id": "gangs",
        "name": "🔫 Банды",
        "type": "specific",
        "description": "Активности для банд",
    },
    "mafia": {
        "id": "mafia",
        "name": "🤵 Мафия",
        "type": "specific",
        "description": "Активности для мафии",
    },
}

# =============================================================================
# Activity Definitions
# =============================================================================

ACTIVITIES: List[Activity] = [
    # -------------------------------------------------------------------------
    # Neutral - Low Time - Solo
    # -------------------------------------------------------------------------
    {
        "id": "lottery",
        "name": "🎟️ Купить лотерейный билет",
        "bp": 1,
        "bp_vip": 2,
        "type": "solo",
        "time": "low",
        "fraction": ["neutral"],
        "categories": ["smartphone"],
    },
    {
        "id": "browser",
        "name": "🌐 Посетить любой сайт в браузере",
        "bp": 1,
        "bp_vip": 2,
        "type": "solo",
        "time": "low",
        "fraction": ["neutral"],
        "categories": ["smartphone"],
    },
    {
        "id": "brawl",
        "name": "🎧 Зайти в любой канал в Brawl",
        "bp": 1,
        "bp_vip": 2,
        "type": "solo",
        "time": "low",
        "fraction": ["neutral"],
        "categories": ["smartphone"],
    },
    {
        "id": "match_like",
        "name": "❤️ Поставить лайк любой анкете в Match",
        "bp": 1,
        "bp_vip": 2,
        "type": "solo",
        "time": "low",
        "fraction": ["neutral"],
        "categories": ["smartphone"],
    },
    {
        "id": "business_materials",
        "name": "📦 Заказ материалов для бизнеса вручную",
        "bp": 1,
        "bp_vip": 2,
        "type": "solo",
        "time": "low",
        "fraction": ["neutral"],
        "categories": [],
    },
    {
        "id": "shooting_range",
        "name": "🔫 Успешная тренировка в тире",
        "bp": 1,
        "bp_vip": 2,
        "type": "solo",
        "time": "low",
        "fraction": ["neutral"],
        "categories": [],
    },
    {
        "id": "film_studio",
        "name": "🎥 Арендовать киностудию",
        "bp": 2,
        "bp_vip": 4,
        "type": "solo",
        "time": "low",
        "fraction": ["neutral"],
        "categories": [],
    },
    {
        "id": "cinema",
        "name": "🎬 Добавить 5 видео в кинотеатре",
        "bp": 1,
        "bp_vip": 2,
        "type": "solo",
        "time": "low",
        "fraction": ["neutral"],
        "categories": [],
    },
    {
        "id": "surgeon",
        "name": "💉 Два раза оплатить смену внешности у хирурга",
        "bp": 2,
        "bp_vip": 4,
        "type": "solo",
        "time": "low",
        "fraction": ["neutral"],
        "categories": [],
    },
    {
        "id": "dp_case",
        "name": "💎 Прокрутить за DP кейс",
        "bp": 10,
        "bp_vip": 20,
        "type": "solo",
        "time": "low",
        "fraction": ["neutral"],
        "categories": [],
    },
    {
        "id": "pet_ball",
        "name": "🐾 Кинуть мяч питомцу 15 раз",
        "bp": 2,
        "bp_vip": 4,
        "type": "solo",
        "time": "low",
        "fraction": ["neutral"],
        "categories": ["pet"],
    },
    {
        "id": "pet_commands",
        "name": "🐶 15 выполненных питомцем команд",
        "bp": 2,
        "bp_vip": 4,
        "type": "solo",
        "time": "low",
        "fraction": ["neutral"],
        "categories": ["pet"],
    },
    {
        "id": "casino_wheel",
        "name": "🎰 Ставка в колесе удачи в казино",
        "bp": 3,
        "bp_vip": 6,
        "type": "solo",
        "time": "low",
        "fraction": ["neutral"],
        "categories": ["casino"],
    },
    {
        "id": "metro",
        "name": "🚇 Проехать 1 станцию на метро",
        "bp": 2,
        "bp_vip": 4,
        "type": "solo",
        "time": "low",
        "fraction": ["neutral"],
        "categories": [],
    },
    {
        "id": "fishing",
        "name": "🎣 Поймать 20 рыб",
        "bp": 4,
        "bp_vip": 8,
        "type": "solo",
        "time": "low",
        "fraction": ["neutral"],
        "categories": [],
    },
    {
        "id": "car_repair",
        "name": "🔧 Починить деталь в автосервисе",
        "bp": 1,
        "bp_vip": 2,
        "type": "solo",
        "time": "low",
        "fraction": ["neutral"],
        "categories": [],
    },
    {
        "id": "basketball",
        "name": "🏀 Забросить 2 мяча в баскетболе",
        "bp": 1,
        "bp_vip": 2,
        "type": "solo",
        "time": "low",
        "fraction": ["neutral"],
        "categories": ["sport"],
    },
    {
        "id": "football",
        "name": "⚽ Забить 2 гола в футболе",
        "bp": 1,
        "bp_vip": 2,
        "type": "solo",
        "time": "low",
        "fraction": ["neutral"],
        "categories": ["sport"],
    },
    {
        "id": "darts",
        "name": "🎯 Победить в дартс",
        "bp": 1,
        "bp_vip": 2,
        "type": "solo",
        "time": "low",
        "fraction": ["neutral"],
        "categories": ["sport"],
    },
    {
        "id": "volleyball",
        "name": "🏐 Поиграть 1 минуту в волейбол",
        "bp": 1,
        "bp_vip": 2,
        "type": "solo",
        "time": "low",
        "fraction": ["neutral"],
        "categories": ["sport"],
    },
    {
        "id": "table_tennis",
        "name": "🏓 Поиграть 1 минуту в настольный теннис",
        "bp": 1,
        "bp_vip": 2,
        "type": "solo",
        "time": "low",
        "fraction": ["neutral"],
        "categories": ["sport"],
    },
    {
        "id": "tennis",
        "name": "🎾 Поиграть 1 минуту в большой теннис",
        "bp": 1,
        "bp_vip": 2,
        "type": "solo",
        "time": "low",
        "fraction": ["neutral"],
        "categories": ["sport"],
    },
    {
        "id": "leasing",
        "name": "💳 Сделать платеж по лизингу",
        "bp": 1,
        "bp_vip": 2,
        "type": "solo",
        "time": "low",
        "fraction": ["neutral"],
        "categories": [],
    },
    # -------------------------------------------------------------------------
    # Neutral - Low Time - Pair
    # -------------------------------------------------------------------------
    {
        "id": "karting",
        "name": "🏎️ Выиграть гонку в картинге",
        "bp": 1,
        "bp_vip": 2,
        "type": "pair",
        "time": "low",
        "fraction": ["neutral"],
        "categories": [],
    },
    {
        "id": "street_race",
        "name": "🏁 Проехать 1 уличную гонку",
        "bp": 1,
        "bp_vip": 2,
        "type": "pair",
        "time": "low",
        "fraction": ["neutral"],
        "categories": [],
    },
    {
        "id": "arena",
        "name": "🎮 Выиграть 3 любых игры на арене",
        "bp": 1,
        "bp_vip": 2,
        "type": "pair",
        "time": "low",
        "fraction": ["neutral"],
        "categories": [],
    },
    {
        "id": "armwrestling",
        "name": "💪 Победить в армрестлинге",
        "bp": 1,
        "bp_vip": 2,
        "type": "pair",
        "time": "low",
        "fraction": ["neutral"],
        "categories": [],
    },
    {
        "id": "casino_mafia",
        "name": "🎭 Сыграть в мафию в казино",
        "bp": 3,
        "bp_vip": 6,
        "type": "pair",
        "time": "low",
        "fraction": ["neutral"],
        "categories": ["casino"],
    },
    {
        "id": "car_repair_other",
        "name": "🔧 Починить деталь авто другого игрока",
        "bp": 4,
        "bp_vip": 8,
        "type": "pair",
        "time": "low",
        "fraction": ["neutral"],
        "categories": [],
    },
    # -------------------------------------------------------------------------
    # Neutral - Medium Time - Solo
    # -------------------------------------------------------------------------
    {
        "id": "casino_zeros",
        "name": "💀 Нули в казино",
        "bp": 2,
        "bp_vip": 4,
        "type": "solo",
        "time": "medium",
        "fraction": ["neutral"],
        "categories": ["casino"],
    },
    {
        "id": "construction",
        "name": "🏗️ 25 действий на стройке",
        "bp": 2,
        "bp_vip": 4,
        "type": "solo",
        "time": "medium",
        "fraction": ["neutral"],
        "categories": ["work"],
    },
    {
        "id": "port",
        "name": "⚓ 25 действий в порту",
        "bp": 2,
        "bp_vip": 4,
        "type": "solo",
        "time": "medium",
        "fraction": ["neutral"],
        "categories": ["work"],
    },
    {
        "id": "mine",
        "name": "⛏️ 25 действий в шахте",
        "bp": 2,
        "bp_vip": 4,
        "type": "solo",
        "time": "medium",
        "fraction": ["neutral"],
        "categories": ["work"],
    },
    {
        "id": "gym",
        "name": "💪 20 подходов в тренажерном зале",
        "bp": 1,
        "bp_vip": 2,
        "type": "solo",
        "time": "medium",
        "fraction": ["neutral"],
        "categories": [],
    },
    {
        "id": "post_office",
        "name": "📦 10 посылок на почте",
        "bp": 1,
        "bp_vip": 2,
        "type": "solo",
        "time": "medium",
        "fraction": ["neutral"],
        "categories": [],
    },
    {
        "id": "farm",
        "name": "🌾 10 действий на ферме",
        "bp": 1,
        "bp_vip": 2,
        "type": "solo",
        "time": "medium",
        "fraction": ["neutral"],
        "categories": ["work"],
    },
    {
        "id": "trucker",
        "name": "🚛 Выполнить 3 заказа дальнобойщиком",
        "bp": 2,
        "bp_vip": 4,
        "type": "solo",
        "time": "medium",
        "fraction": ["neutral"],
        "categories": ["work"],
    },
    {
        "id": "club_quests",
        "name": "🎫 Выполнить 2 квеста любых клубов",
        "bp": 4,
        "bp_vip": 8,
        "type": "solo",
        "time": "medium",
        "fraction": ["neutral"],
        "categories": [],
    },
    {
        "id": "bus",
        "name": "🚌 2 круга на любом маршруте автобусника",
        "bp": 2,
        "bp_vip": 4,
        "type": "solo",
        "time": "medium",
        "fraction": ["neutral"],
        "categories": ["work"],
    },
    # -------------------------------------------------------------------------
    # Neutral - Medium Time - Pair
    # -------------------------------------------------------------------------
    {
        "id": "dance_battle",
        "name": "💃 3 победы в Дэнс Баттлах",
        "bp": 2,
        "bp_vip": 4,
        "type": "pair",
        "time": "medium",
        "fraction": ["neutral"],
        "categories": [],
    },
    {
        "id": "training_complex",
        "name": "🏋️ Выиграть 5 игр в тренировочном комплексе",
        "bp": 1,
        "bp_vip": 2,
        "type": "pair",
        "time": "medium",
        "fraction": ["neutral"],
        "categories": [],
    },
    # -------------------------------------------------------------------------
    # Neutral - High Time - Solo
    # -------------------------------------------------------------------------
    {
        "id": "online_3h",
        "name": "🕒 3 часа в онлайне",
        "bp": 2,
        "bp_vip": 4,
        "type": "solo",
        "time": "high",
        "fraction": ["neutral"],
        "categories": [],
    },
    {
        "id": "firefighter",
        "name": '🔥 Потушить 25 "огоньков" пожарным',
        "bp": 1,
        "bp_vip": 2,
        "type": "solo",
        "time": "high",
        "fraction": ["neutral"],
        "categories": ["work"],
    },
    {
        "id": "treasure",
        "name": "🏺 Выкопать 1 сокровище (не хлам)",
        "bp": 1,
        "bp_vip": 2,
        "type": "solo",
        "time": "high",
        "fraction": ["neutral"],
        "categories": [],
    },
    # -------------------------------------------------------------------------
    # Neutral - High Time - Pair
    # -------------------------------------------------------------------------
    {
        "id": "hunting",
        "name": "🐻 5 раз снять 100% шкуру с животных",
        "bp": 2,
        "bp_vip": 4,
        "type": "pair",
        "time": "high",
        "fraction": ["neutral"],
        "categories": [],
    },
    # -------------------------------------------------------------------------
    # Crime - Low Time - Solo
    # -------------------------------------------------------------------------
    {
        "id": "greenhouse",
        "name": "🌿 Посадить траву в теплице",
        "bp": 4,
        "bp_vip": 8,
        "type": "solo",
        "time": "low",
        "fraction": ["crime"],
        "categories": ["gangs"],
    },
    {
        "id": "painkiller_lab",
        "name": "💊 Запустить переработку обезболивающих",
        "bp": 4,
        "bp_vip": 8,
        "type": "solo",
        "time": "low",
        "fraction": ["crime"],
        "categories": ["mafia"],
    },
    # -------------------------------------------------------------------------
    # Crime - Medium Time - Solo
    # -------------------------------------------------------------------------
    {
        "id": "graffiti",
        "name": "🎨 7 закрашенных граффити",
        "bp": 1,
        "bp_vip": 2,
        "type": "solo",
        "time": "medium",
        "fraction": ["crime"],
        "categories": ["gangs"],
    },
    {
        "id": "contraband",
        "name": "📦 Сдать 5 контрабанды",
        "bp": 2,
        "bp_vip": 4,
        "type": "solo",
        "time": "medium",
        "fraction": ["crime"],
        "categories": ["mafia"],
    },
    # -------------------------------------------------------------------------
    # Crime - High Time - Solo
    # -------------------------------------------------------------------------
    {
        "id": "lockpicking",
        "name": "🔓 Взломать 15 замков",
        "bp": 2,
        "bp_vip": 4,
        "type": "solo",
        "time": "high",
        "fraction": ["crime"],
        "categories": ["gangs", "mafia"],
    },
    # -------------------------------------------------------------------------
    # Crime + Gov - High Time - Solo
    # -------------------------------------------------------------------------
    {
        "id": "airdrops",
        "name": "🪂 Принять участие в двух Airdrop",
        "bp": 4,
        "bp_vip": 8,
        "type": "solo",
        "time": "high",
        "fraction": ["crime", "gov"],
        "categories": [],
    },
    # -------------------------------------------------------------------------
    # Crime - High Time - Pair
    # -------------------------------------------------------------------------
    {
        "id": "capts_bizwars",
        "name": "⚔️ Участие в каптах/бизварах",
        "bp": 1,
        "bp_vip": 2,
        "type": "pair",
        "time": "high",
        "fraction": ["crime"],
        "categories": [],
    },
    {
        "id": "hummer_vzh",
        "name": "🚙 Сдать Хаммер с ВЗХ",
        "bp": 3,
        "bp_vip": 6,
        "type": "pair",
        "time": "high",
        "fraction": ["crime"],
        "categories": [],
    },
    # -------------------------------------------------------------------------
    # Gov - High Time - Solo
    # -------------------------------------------------------------------------
    {
        "id": "vehicle_registration",
        "name": "🚗 Поставить на учет 2 автомобиля",
        "bp": 1,
        "bp_vip": 2,
        "type": "solo",
        "time": "high",
        "fraction": ["gov"],
        "categories": ["lspd"],
    },
    {
        "id": "arrest",
        "name": "👮 Произвести 1 арест в КПЗ",
        "bp": 1,
        "bp_vip": 2,
        "type": "solo",
        "time": "high",
        "fraction": ["gov"],
        "categories": ["lspd"],
    },
    {
        "id": "bail_out",
        "name": "⚖️ Выкупить двух человек из КПЗ",
        "bp": 2,
        "bp_vip": 4,
        "type": "solo",
        "time": "high",
        "fraction": ["gov"],
        "categories": [],
    },
    {
        "id": "medcards",
        "name": "💳 5 выданных медкарт в EMS",
        "bp": 2,
        "bp_vip": 4,
        "type": "solo",
        "time": "high",
        "fraction": ["gov"],
        "categories": ["ems"],
    },
    {
        "id": "ems_calls",
        "name": "🚑 Закрыть 15 вызовов в EMS",
        "bp": 2,
        "bp_vip": 4,
        "type": "solo",
        "time": "high",
        "fraction": ["gov"],
        "categories": ["ems"],
    },
    {
        "id": "wn_ads",
        "name": "📰 Отредактировать 40 объявлений в WN",
        "bp": 2,
        "bp_vip": 4,
        "type": "solo",
        "time": "high",
        "fraction": ["gov"],
        "categories": ["wn"],
    },
    {
        "id": "codes",
        "name": "🚨 Закрыть 5 кодов в силовых структурах",
        "bp": 2,
        "bp_vip": 4,
        "type": "solo",
        "time": "high",
        "fraction": ["gov"],
        "categories": [],
    },
]

# =============================================================================
# Caching and Lookup Functions
# =============================================================================

_ACTIVITIES_BY_ID_CACHE: Dict[str, Activity] = {}
_ACTIVITIES_BY_CATEGORY_CACHE: Dict[str, List[Activity]] = {}
_ACTIVITIES_BY_FRACTION_CACHE: Dict[str, List[Activity]] = {}


def _initialize_caches() -> None:
    """Initialize caches for fast activity lookups."""
    global \
        _ACTIVITIES_BY_ID_CACHE, \
        _ACTIVITIES_BY_CATEGORY_CACHE, \
        _ACTIVITIES_BY_FRACTION_CACHE

    _ACTIVITIES_BY_ID_CACHE = {activity["id"]: activity for activity in ACTIVITIES}

    # Build category cache
    _ACTIVITIES_BY_CATEGORY_CACHE = {}
    for activity in ACTIVITIES:
        for category in activity.get("categories", []):
            if category not in _ACTIVITIES_BY_CATEGORY_CACHE:
                _ACTIVITIES_BY_CATEGORY_CACHE[category] = []
            _ACTIVITIES_BY_CATEGORY_CACHE[category].append(activity)

    # Build fraction cache
    _ACTIVITIES_BY_FRACTION_CACHE = {"neutral": [], "crime": [], "gov": []}
    for activity in ACTIVITIES:
        for fraction in activity.get("fraction", ["neutral"]):
            if fraction in _ACTIVITIES_BY_FRACTION_CACHE:
                _ACTIVITIES_BY_FRACTION_CACHE[fraction].append(activity)


_initialize_caches()

TOTAL_ACTIVITIES = len(ACTIVITIES)


def get_all_activities() -> List[Activity]:
    """Get list of all activities. O(1)"""
    return ACTIVITIES


def get_activity_by_id(activity_id: str) -> Optional[Activity]:
    """Find activity by ID. O(1) dictionary lookup."""
    return _ACTIVITIES_BY_ID_CACHE.get(activity_id)


def get_activities_by_category(category_id: str) -> List[Activity]:
    """Get all activities in a specific category. O(1)"""
    return _ACTIVITIES_BY_CATEGORY_CACHE.get(category_id, [])


def get_activities_by_fraction(fraction: str) -> List[Activity]:
    """Get all activities for a specific fraction. O(1)"""
    return _ACTIVITIES_BY_FRACTION_CACHE.get(fraction, [])


def get_category_info(category_id: str) -> Optional[Dict[str, Any]]:
    """Get category metadata. O(1)"""
    return CATEGORIES.get(category_id)


def get_all_categories() -> Dict[str, Dict[str, Any]]:
    """Get all category definitions."""
    return CATEGORIES
