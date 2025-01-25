QUALIFICATIONS = {
    'NONE': {
        'min_pv': 0,
        'min_go': 0,
        'min_partners': 0,
        'side_volume': 0
    },
    'M1': {
        'min_pv': 50,
        'min_go': 750,
        'min_partners': 2,
        'side_volume': 0
    },
    'M2': {
        'min_pv': 50,
        'min_go': 1500,
        'min_partners': 3,
        'side_volume': 0
    },
    'M3': {
        'min_pv': 50,
        'min_go': 3000,
        'min_partners': 4,
        'side_volume': 0
    },
    'B1': {
        'min_pv': 50,
        'min_go': 5500,
        'min_partners': 5,
        'side_volume': 2500,
        'required_m3': 1
    },
    'B2': {
        'min_pv': 50,
        'min_go': 8000,
        'min_partners': 6,
        'side_volume': 2000,
        'required_m3': 2
    },
    'B3': {
        'min_pv': 50,
        'min_go': 10000,
        'min_partners': 7,
        'side_volume': 1000,
        'required_m3': 3
    },
    'TOP': {
        'min_pv': 50,
        'min_go': 16000,
        'min_partners': 8,
        'side_volume': 1000,
        'required_m3': 5
    },
    'TOP1': {
        'min_pv': 50,
        'min_go': 23000,
        'min_partners': 9,
        'side_volume': 1000,
        'required_m3': 4,
        'required_b3': 1
    },
    'TOP2': {
        'min_pv': 50,
        'min_go': 30000,
        'min_partners': 10,
        'side_volume': 1000,
        'required_m3': 3,
        'required_b3': 2
    },
    'TOP3': {
        'min_pv': 50,
        'min_go': 37000,
        'min_partners': 11,
        'side_volume': 1000,
        'required_m3': 2,
        'required_b3': 3
    },
    'TOP4': {
        'min_pv': 50,
        'min_go': 44000,
        'min_partners': 12,
        'side_volume': 1000,
        'required_m3': 1,
        'required_b3': 4
    },
    'TOP5': {
        'min_pv': 50,
        'min_go': 51000,
        'min_partners': 13,
        'side_volume': 1000,
        'required_b3': 5
    },
    'AC1': {
        'min_pv': 50,
        'min_go': 200000,
        'min_partners': 15,
        'side_volume': 100000
    },
    'AC2': {
        'min_pv': 50,
        'min_go': 350000,
        'min_partners': 17,
        'side_volume': 100000
    },
    'AC3': {
        'min_pv': 50,
        'min_go': 500000,
        'min_partners': 20,
        'side_volume': 200000
    },
    'AC4': {
        'min_pv': 50,
        'min_go': 1000000,
        'min_partners': 25,
        'side_volume': 350000
    },
    'AC5': {
        'min_pv': 50,
        'min_go': 2500000,
        'min_partners': 30,
        'side_volume': 500000
    },
    'AC6': {
        'min_pv': 50,
        'min_go': 5000000,
        'min_partners': 35,
        'side_volume': 500000
    }
}

BONUS_RATES = {
    'PERSONAL': {
        70: 0.05,    # 5% for 70 PV
        200: 0.10    # 10% for 200 PV
    },
    'GROUP': {
        'M1': 0.05,  # 5%
        'M2': 0.10,  # 10%
        'M3': 0.15,  # 15%
        'B1': 0.20,  # 20%
        'B2': 0.25,  # 25%
        'B3': 0.30,  # 30%
        'TOP': 0.35,  # 35%
        'TOP1': 0.37, # 37%
        'TOP2': 0.39, # 39%
        'TOP3': 0.41, # 41%
        'TOP4': 0.43, # 43%
        'TOP5': 0.45, # 45%
        'AC1': 0.47,  # 47%
        'AC2': 0.49,  # 49%
        'AC3': 0.51,  # 51%
        'AC4': 0.53,  # 53%
        'AC5': 0.55,  # 55%
        'AC6': 0.57   # 57%
    },
    'CLUB': {
        'MIDDLE': 0.02,  # +2% from M3
        'BUSINESS': 0.04,  # +4% from B1
        'TRAVEL': 0.01,   # +1% from B1
        'TOP': 0.01       # +1% from B3
    }
}

ACTIVE_PARTNER_BONUSES = {
    5: 100,   # 5 partners: +100 у.е.
    7: 200,   # 7 partners: +200 у.е.
    9: 300,   # 9 partners: +300 у.е.
    12: 400,  # 12 partners: +400 у.е.
    15: 500   # 15 partners: +500 у.е.
}

# Настройки быстрого старта
QUICK_START_BONUSES = {
    'M1': {'bonus': 50, 'period': 1},  # 50 у.е. в первый месяц
    'M2': {'bonus': 100, 'period': 2}, # 100 у.е. во второй месяц
    'M3': {'bonus': 200, 'period': 3}  # 200 у.е. в третий месяц
}

# Стартовые наборы
STARTER_KITS = {
    'START': {
        'price': 100,
        'pv': 70,
        'privileges': ['personal_discount']
    },
    'START_PLUS': {
        'price': 200,
        'pv': 140,
        'privileges': ['personal_discount', 'training_access']
    },
    'BUSINESS': {
        'price': 500,
        'pv': 200,
        'privileges': ['personal_discount', 'training_access', 'business_tools']
    },
    'VIP': {
        'price': 1000,
        'pv': 300,
        'privileges': ['personal_discount', 'training_access', 'business_tools', 'mentorship']
    }
}

# Привилегии стартовых наборов
STARTER_KIT_PRIVILEGES = {
    'personal_discount': {
        'name': 'Персональная скидка',
        'value': 0.20  # 20% скидка
    },
    'training_access': {
        'name': 'Доступ к обучению',
        'duration': 30  # дней
    },
    'business_tools': {
        'name': 'Бизнес-инструменты',
        'tools': ['marketing_materials', 'business_planner', 'presentation_templates']
    },
    'mentorship': {
        'name': 'Персональное наставничество',
        'duration': 90,  # дней
        'sessions': 12   # количество сессий
    }
}

# Клубная система
CLUB_LEVELS = {
    'MIDDLE': {
        'qualification': 'M3',
        'maintenance_period': 3,  # месяца
        'benefits': [
            'middle_events',
            'middle_training',
            'middle_bonus'
        ]
    },
    'BUSINESS': {
        'qualification': 'B1',
        'maintenance_period': 6,  # месяцев
        'benefits': [
            'business_events',
            'business_training',
            'business_bonus',
            'travel_bonus'
        ]
    },
    'TOP': {
        'qualification': 'B3',
        'maintenance_period': 6,  # месяцев
        'benefits': [
            'top_events',
            'top_training',
            'top_bonus',
            'leadership_program'
        ]
    }
}

CLUB_BENEFITS = {
    'middle_events': {
        'name': 'Мероприятия Middle Club',
        'events_per_year': 4,
        'discount': 0.50  # 50% скидка на мероприятия
    },
    'middle_training': {
        'name': 'Тренинги Middle Club',
        'sessions_per_month': 2,
        'materials_included': True
    },
    'middle_bonus': {
        'name': 'Бонус Middle Club',
        'rate': 0.02  # +2% к групповому бонусу
    },
    'business_events': {
        'name': 'Мероприятия Business Club',
        'events_per_year': 6,
        'discount': 0.75  # 75% скидка на мероприятия
    },
    'business_training': {
        'name': 'Тренинги Business Club',
        'sessions_per_month': 4,
        'materials_included': True,
        'personal_mentor': True
    },
    'business_bonus': {
        'name': 'Бонус Business Club',
        'rate': 0.04  # +4% к групповому бонусу
    },
    'travel_bonus': {
        'name': 'Travel Bonus',
        'rate': 0.01,  # +1% к групповому бонусу
        'min_go': 5500  # минимальный GO для получения
    },
    'top_events': {
        'name': 'Мероприятия TOP Club',
        'events_per_year': 8,
        'discount': 1.00,  # 100% скидка на мероприятия
        'vip_access': True
    },
    'top_training': {
        'name': 'Тренинги TOP Club',
        'sessions_per_month': 6,
        'materials_included': True,
        'personal_mentor': True,
        'strategy_sessions': True
    },
    'top_bonus': {
        'name': 'Бонус TOP Club',
        'rate': 0.01  # +1% к групповому бонусу
    },
    'leadership_program': {
        'name': 'Программа лидерства',
        'duration': 12,  # месяцев
        'mentoring_bonus': 1000  # бонус за менторство новых партнеров
    }
}

CLUB_EVENTS = {
    'MIDDLE': [
        {
            'name': 'Квартальная встреча Middle Club',
            'duration': 1,  # дней
            'base_price': 100,
            'frequency': 'quarterly'
        },
        {
            'name': 'Тренинг личностного роста',
            'duration': 2,
            'base_price': 200,
            'frequency': 'semi_annual'
        }
    ],
    'BUSINESS': [
        {
            'name': 'Бизнес-конференция',
            'duration': 2,
            'base_price': 300,
            'frequency': 'quarterly'
        },
        {
            'name': 'Выездной интенсив',
            'duration': 3,
            'base_price': 500,
            'frequency': 'annual'
        }
    ],
    'TOP': [
        {
            'name': 'Саммит лидеров',
            'duration': 3,
            'base_price': 1000,
            'frequency': 'semi_annual'
        },
        {
            'name': 'VIP мастермайнд',
            'duration': 2,
            'base_price': 800,
            'frequency': 'quarterly'
        }
    ]
}

# Региональные настройки
REGIONS = {
    'RU': {
        'name': 'Россия',
        'currency': 'RUB',
        'min_pv_threshold': 50,
        'compression_threshold': 50,
        'grace_period': 2,  # месяца
        'qualification_adjustments': {
            'M1': {'min_go': 600},  # Снижение требований для M1
            'M2': {'min_go': 1200},  # Снижение требований для M2
            'M3': {'min_go': 2400}   # Снижение требований для M3
        }
    },
    'KZ': {
        'name': 'Казахстан',
        'currency': 'KZT',
        'min_pv_threshold': 50,
        'compression_threshold': 50,
        'grace_period': 2,
        'qualification_adjustments': {
            'M1': {'min_go': 650},
            'M2': {'min_go': 1300},
            'M3': {'min_go': 2600}
        }
    },
    'UZ': {
        'name': 'Узбекистан',
        'currency': 'UZS',
        'min_pv_threshold': 40,  # Сниженный порог
        'compression_threshold': 40,
        'grace_period': 3,  # Увеличенный период
        'qualification_adjustments': {
            'M1': {'min_go': 500},  # Значительное снижение требований
            'M2': {'min_go': 1000},
            'M3': {'min_go': 2000}
        }
    },
    'KG': {
        'name': 'Кыргызстан',
        'currency': 'KGS',
        'min_pv_threshold': 40,
        'compression_threshold': 40,
        'grace_period': 3,
        'qualification_adjustments': {
            'M1': {'min_go': 500},
            'M2': {'min_go': 1000},
            'M3': {'min_go': 2000}
        }
    }
}

# Расширенные настройки компрессии
COMPRESSION_RULES = {
    'STANDARD': {
        'threshold': 50,
        'grace_period': 1,
        'warning_period': 1,  # месяц до компрессии
        'recovery_period': 3,  # месяца на восстановление
        'min_recovery_pv': 70  # PV для восстановления
    },
    'SOFT': {  # Для новых регионов
        'threshold': 40,
        'grace_period': 3,
        'warning_period': 2,
        'recovery_period': 4,
        'min_recovery_pv': 50
    },
    'STRICT': {  # Для развитых регионов
        'threshold': 50,
        'grace_period': 1,
        'warning_period': 1,
        'recovery_period': 2,
        'min_recovery_pv': 100
    }
}

# Условия восстановления после компрессии
RECOVERY_CONDITIONS = {
    'QUICK': {
        'period': 1,  # месяц
        'required_pv': 100,
        'bonus_rate': 0.05  # +5% к бонусам на 3 месяца
    },
    'STANDARD': {
        'period': 2,  # месяца
        'required_pv': 70,
        'bonus_rate': 0.03  # +3% к бонусам на 2 месяца
    },
    'GRADUAL': {
        'period': 3,  # месяца
        'required_pv': 50,
        'bonus_rate': 0.02  # +2% к бонусам на 1 месяц
    }
}

# Предупреждения о компрессии
COMPRESSION_WARNINGS = {
    'CRITICAL': {
        'threshold': 0,  # Текущий PV
        'message': 'Критическое предупреждение: структура будет сжата в следующем месяце',
        'notification_type': 'immediate'
    },
    'WARNING': {
        'threshold': 30,
        'message': 'Предупреждение: низкий PV, риск компрессии',
        'notification_type': 'weekly'
    },
    'NOTICE': {
        'threshold': 40,
        'message': 'Уведомление: PV ниже рекомендуемого уровня',
        'notification_type': 'monthly'
    }
}

# Настройки компрессии
COMPRESSION_THRESHOLD = 50  # Обновляем в зависимости от региона
COMPRESSION_GRACE_PERIOD = 1  # Обновляем в зависимости от региона

# Веса для оценки рисков
RISK_WEIGHTS = {
    'dependency': 0.4,
    'compression': 0.3,
    'stability': 0.3
}

# Словарь для перевода квалификаций
QUALIFICATION_NAMES = {
    'NONE': 'Нет',
    'M1': 'М1',
    'M2': 'М2',
    'M3': 'М3',
    'B1': 'Б1',
    'B2': 'Б2',
    'B3': 'Б3',
    'TOP': 'ТОП',
    'TOP1': 'ТОП1',
    'TOP2': 'ТОП2',
    'TOP3': 'ТОП3',
    'TOP4': 'ТОП4',
    'TOP5': 'ТОП5',
    'AC1': 'АК1',
    'AC2': 'АК2',
    'AC3': 'АК3',
    'AC4': 'АК4',
    'AC5': 'АК5',
    'AC6': 'АК6'
}

# Курсы валют
CURRENCY_RATES = {
    'RUB': 35,
    'KZT': 175,
    'KGS': 35,
    'BYN': 0.98,
    'UZS': 3850,
    'GEL': 1.45,
    'TRY': 4.5,
    'MDL': 8,
    'TJS': 3.5,
    'AED': 1.42
}

# Бонусы за динамику роста GO
DYNAMIC_GO_BONUS_RATES = {
    0.20: 0.005,  # +0.5% при росте 20%
    0.30: 0.010,  # +1.0% при росте 30%
    0.50: 0.015,  # +1.5% при росте 50%
    1.00: 0.020   # +2.0% при росте 100%
}

# Бонусы программы наставничества
MENTORSHIP_BONUSES = {
    'M3': 100,    # +100 у.е. за достижение M3
    'B1': 200,    # +200 у.е. за достижение B1
    'B3': 500,    # +500 у.е. за достижение B3
    'TOP': 1000   # +1000 у.е. за достижение TOP
}

# Периоды для расчета динамики
DYNAMICS_CALCULATION_PERIODS = {
    'monthly': 1,      # Ежемесячный рост
    'quarterly': 3,    # Квартальный рост
    'yearly': 12       # Годовой рост
}

# Минимальные периоды поддержания квалификации для бонусов
QUALIFICATION_MAINTENANCE_PERIODS = {
    'M3': 3,  # 3 месяца для Middle Club
    'B1': 6,  # 6 месяцев для Business Club
    'B3': 6,  # 6 месяцев для TOP Club
    'TOP': 6  # 6 месяцев для высших квалификаций
} 