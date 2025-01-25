# Оптимизатор структуры NL

Инструмент для оптимизации и анализа структуры партнерской сети NL International.

## Возможности

- Оптимизация структуры для максимальной прибыли
- Анализ уязвимостей и рисков
- Визуализация сети и метрик
- Пошаговое построение структуры
- Расчет всех видов бонусов
- Учет квалификационных требований

## Требования

- Python 3.8+
- Зависимости из файла requirements.txt

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/ваш-пользователь/nl-network-optimizer.git
cd nl-network-optimizer
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
# Для Windows:
venv\Scripts\activate
# Для Linux/Mac:
source venv/bin/activate
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

## Использование

1. Запустите приложение:
```bash
streamlit run src/app.py
```

2. Откройте браузер по адресу http://localhost:8501

3. В интерфейсе:
   - Укажите общий объем PV для распределения
   - Выберите режим оптимизации (максимальная прибыль или анализ уязвимостей)
   - Исследуйте результаты через интерактивные визуализации

## Структура проекта

```
nl-network-optimizer/
├── src/
│   ├── app.py                  # Основное приложение Streamlit
│   ├── models/
│   │   ├── optimizer.py        # Алгоритмы оптимизации
│   │   └── structure.py        # Модель структуры сети
│   └── utils/
│       ├── constants.py        # Константы и конфигурация
│       └── visualization.py    # Функции визуализации
├── requirements.txt            # Зависимости проекта
└── README.md                  # Документация
```

## Особенности реализации

1. **Прозрачность расчетов**
   - Все формулы и коэффициенты документированы
   - Возможность проверки промежуточных результатов
   - Подробная визуализация структуры

2. **Точность расчетов**
   - Учет всех видов бонусов (личный, групповой, клубный)
   - Проверка квалификационных требований
   - Оптимизация с учетом компрессии

3. **Анализ рисков**
   - Оценка зависимости от крупных партнеров
   - Анализ стабильности структуры
   - Выявление потенциальных уязвимостей

## Функциональность

1. **Оптимизация структуры**
   - Распределение заданного объема PV
   - Построение оптимальной структуры
   - Максимизация дохода

2. **Визуализация**
   - Интерактивная карта структуры
   - Графики распределения квалификаций
   - Диаграммы доходов
   - Анализ рисков

3. **Расчеты**
   - Все виды бонусов
   - Квалификационные требования
   - Компрессия
   - Прогноз доходности

## Лицензия

MIT License 