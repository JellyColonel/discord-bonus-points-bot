# bonus_points_bot/bot/data/activities.py
"""
Activity definitions and lookup functions.
OPTIMIZED: Caching and O(1) lookups for better performance.
"""

ACTIVITIES = {
    "📍 Одиночные": [
        {
            "id": "lottery",
            "name": "🎟️ Купить лотерейный билет",
            "bp": 1,
            "bp_vip": 2,
        },
        {
            "id": "browser",
            "name": "🌐 Посетить любой сайт в браузере",
            "bp": 1,
            "bp_vip": 2,
        },
        {
            "id": "match_like",
            "name": "❤️ Поставить лайк любой анкете в Match",
            "bp": 1,
            "bp_vip": 2,
        },
        {
            "id": "brawl",
            "name": "🎧 Зайти в любой канал в Brawl",
            "bp": 1,
            "bp_vip": 2,
        },
        {
            "id": "pet_ball",
            "name": "🐾 Кинуть мяч питомцу 15 раз",
            "bp": 2,
            "bp_vip": 4,
        },
        {
            "id": "pet_commands",
            "name": "🐶 15 выполненных питомцем команд",
            "bp": 2,
            "bp_vip": 4,
        },
        {
            "id": "darts",
            "name": "🎯 Победить в дартс",
            "bp": 1,
            "bp_vip": 2,
        },
        {
            "id": "casino_wheel",
            "name": "🎰 Ставка в колесе удачи в казино",
            "bp": 3,
            "bp_vip": 6,
        },
        {
            "id": "casino_zeros",
            "name": "💀 Нули в казино",
            "bp": 2,
            "bp_vip": 4,
        },
        {
            "id": "basketball",
            "name": "🏀 Забросить 2 мяча в баскетболе",
            "bp": 1,
            "bp_vip": 2,
        },
        {
            "id": "football",
            "name": "⚽ Забить 2 гола в футболе",
            "bp": 1,
            "bp_vip": 2,
        },
        {
            "id": "leasing",
            "name": "💳 Сделать платеж по лизингу",
            "bp": 1,
            "bp_vip": 2,
        },
        {
            "id": "shooting_range",
            "name": "🔫 Успешная тренировка в тире",
            "bp": 1,
            "bp_vip": 2,
        },
        {
            "id": "car_repair",
            "name": "🔧 Починить деталь в автосервисе",
            "bp": 1,
            "bp_vip": 2,
        },
        {
            "id": "cinema",
            "name": "🎬 Добавить 5 видео в кинотеатре",
            "bp": 1,
            "bp_vip": 2,
        },
        {
            "id": "film_studio",
            "name": "🎥 Арендовать киностудию",
            "bp": 2,
            "bp_vip": 4,
        },
        {
            "id": "metro",
            "name": "🚇 Проехать 1 станцию на метро",
            "bp": 2,
            "bp_vip": 4,
        },
        {
            "id": "volleyball",
            "name": "🏐 Поиграть 1 минуту в воллейбол",
            "bp": 1,
            "bp_vip": 2,
        },
        {
            "id": "table_tennis_solo",
            "name": "🏓 Поиграть 1 минуту в настольный теннис",
            "bp": 1,
            "bp_vip": 2,
        },
        {
            "id": "tennis_solo",
            "name": "🎾 Поиграть 1 минуту в большой теннис",
            "bp": 1,
            "bp_vip": 2,
        },
        {
            "id": "fishing",
            "name": "🎣 Поймать 20 рыб",
            "bp": 4,
            "bp_vip": 8,
        },
        {
            "id": "bus",
            "name": "🚌 2 круга на любом маршруте автобусника",
            "bp": 2,
            "bp_vip": 4,
        },
        {
            "id": "port",
            "name": "⚙️ 25 действий в порту",
            "bp": 2,
            "bp_vip": 4,
        },
        {
            "id": "construction",
            "name": "⚙️ 25 действий на стройке",
            "bp": 2,
            "bp_vip": 4,
        },
        {
            "id": "mine",
            "name": "⚙️ 25 действий в шахте",
            "bp": 2,
            "bp_vip": 4,
        },
        {
            "id": "farm",
            "name": "🌾 10 действий на ферме",
            "bp": 1,
            "bp_vip": 2,
        },
        {
            "id": "firefighter",
            "name": '🔥 Потушить 25 "огоньков" пожарным',
            "bp": 1,
            "bp_vip": 2,
        },
        {
            "id": "trucker",
            "name": "🚛 Выполнить 3 заказа дальнобойщиком",
            "bp": 2,
            "bp_vip": 4,
        },
        {
            "id": "gym",
            "name": "💪 20 подходов в тренажерном зале",
            "bp": 1,
            "bp_vip": 2,
        },
        {
            "id": "club_quests",
            "name": "🎫 Выполнить 2 квеста любых клубов",
            "bp": 4,
            "bp_vip": 8,
        },
        {
            "id": "hunting",
            "name": "🐻 5 раз снять 100% шкуру с животных",
            "bp": 2,
            "bp_vip": 4,
        },
        {
            "id": "dp_case",
            "name": "💎 Прокрутить за DP серебрянный или золотой кейс",
            "bp": 10,
            "bp_vip": 20,
        },
        {
            "id": "treasure",
            "name": "🏺 Выкопать 1 сокровище(не мусор)",
            "bp": 1,
            "bp_vip": 2,
        },
        {
            "id": "post_office",
            "name": "📦 10 посылок на почте",
            "bp": 1,
            "bp_vip": 2,
        },
        {
            "id": "surgeon",
            "name": "💉 Два раза оплатить смену внешности у хирурга в EMS",
            "bp": 2,
            "bp_vip": 4,
        },
        {
            "id": "online_3h",
            "name": "🕒 3 часа в онлайне",
            "bp": 2,
            "bp_vip": 4,
        },
    ],
    "🤝 Парные": [
        {
            "id": "armwrestling",
            "name": "💪 Победить в армрестлинге",
            "bp": 1,
            "bp_vip": 2,
        },
        {
            "id": "karting_pair",
            "name": "🏎️ Выиграть гонку в картинге",
            "bp": 1,
            "bp_vip": 2,
        },
        {
            "id": "mafia",
            "name": "🎭 Сыграть в мафию в казино",
            "bp": 3,
            "bp_vip": 6,
        },
        {
            "id": "training_complex",
            "name": "🏋️ Выиграть 5 игр в тренировочном комплексе (ставка от $100)",
            "bp": 1,
            "bp_vip": 2,
        },
        {
            "id": "street_race",
            "name": "🏁 Проехать 1 уличную гонку (ставка ≥ $1000)",
            "bp": 1,
            "bp_vip": 2,
        },
        {
            "id": "arena",
            "name": "🎮 Выиграть 3 любых игры на арене (ставка от $100)",
            "bp": 1,
            "bp_vip": 2,
        },
        {
            "id": "dance_battle",
            "name": "💃 3 победы в Дэнс Баттлах",
            "bp": 2,
            "bp_vip": 4,
        },
    ],
}

# Caches initialized once at module load
_ALL_ACTIVITIES_CACHE = None
_ACTIVITIES_BY_ID_CACHE = None


def _initialize_caches():
    """Initialize caches and pre-compute search fields."""
    global _ALL_ACTIVITIES_CACHE, _ACTIVITIES_BY_ID_CACHE

    _ALL_ACTIVITIES_CACHE = []
    for category_activities in ACTIVITIES.values():
        _ALL_ACTIVITIES_CACHE.extend(category_activities)

    # Pre-lowercase for faster autocomplete
    for activity in _ALL_ACTIVITIES_CACHE:
        activity["_name_lower"] = activity["name"].lower()
        activity["_id_lower"] = activity["id"].lower()

    # O(1) lookup dictionary
    _ACTIVITIES_BY_ID_CACHE = {
        activity["id"]: activity for activity in _ALL_ACTIVITIES_CACHE
    }


_initialize_caches()

TOTAL_ACTIVITIES = len(_ALL_ACTIVITIES_CACHE)


def get_all_activities():
    """Get flat list of all activities (cached). O(1)"""
    return _ALL_ACTIVITIES_CACHE


def get_activity_by_id(activity_id):
    """Find activity by ID. O(1) dictionary lookup."""
    return _ACTIVITIES_BY_ID_CACHE.get(activity_id)


def search_activities(query, max_results=25):
    """Search activities by name or ID (uses pre-lowercased fields)."""
    if not query:
        return _ALL_ACTIVITIES_CACHE[:max_results]

    query_lower = query.lower()
    results = []

    for activity in _ALL_ACTIVITIES_CACHE:
        if len(results) >= max_results:
            break
        if (
            query_lower in activity["_name_lower"]
            or query_lower in activity["_id_lower"]
        ):
            results.append(activity)

    return results
