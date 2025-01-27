import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import networkx as nx
from models.optimizer import UserOptimizer, ScenarioAnalyzer
from models.structure import NetworkStructure
from utils.constants import QUALIFICATIONS, BONUS_RATES, STARTER_KITS, STARTER_KIT_PRIVILEGES, CLUB_BENEFITS, CLUB_EVENTS, CLUB_LEVELS, REGIONS, COMPRESSION_WARNINGS, RECOVERY_CONDITIONS, QUALIFICATION_NAMES
from utils.visualization import plot_network, plot_metrics

st.set_page_config(
    page_title="Оптимизатор структуры NL",
    page_icon="📊",
    layout="wide"
)

def analyze_scenarios():
    st.header("Анализ сценариев распределения PV")
    
    total_pv = st.number_input(
        "Введите общий объем PV для анализа",
        min_value=100,
        max_value=1000000,
        value=10000,
        step=100
    )
    
    if st.button("Анализировать сценарии"):
        analyzer = ScenarioAnalyzer()
        scenarios = analyzer.generate_scenarios(total_pv)
        
        st.subheader("Результаты анализа")
        st.write("Сценарии отсортированы по общей эффективности (с учетом дохода и рисков)")
        
        for i, scenario in enumerate(scenarios, 1):
            metrics = scenario['metrics']
            
            with st.expander(f"{i}. {scenario['name']} (Скор: {metrics['total_score']:.2f})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("### Основные метрики")
                    st.write(f"- Квалификация: {metrics['qualification']}")
                    st.write(f"- Общий доход: {metrics['total_income']:.2f} у.е.")
                    st.write(f"- Активных партнеров: {metrics['active_partners']}")
                    st.write(f"- Групповой объем: {metrics['group_volume']:.0f} PV")
                    st.write(f"- Боковой объем: {metrics['side_volume']:.0f} PV")
                    st.write(f"- Эффективность: {metrics['efficiency']:.2%}")
                    st.write(f"- Оценка риска: {metrics['risk_score']:.2%}")
                
                with col2:
                    st.write("### Структура бонусов")
                    bonus_data = {
                        'Тип бонуса': [
                            'Личный бонус (LO)',
                            'Партнерский бонус (PB)',
                            'Групповой бонус (GO)',
                            'Клубный бонус'
                        ],
                        'Сумма': [
                            metrics['personal_bonus'],
                            metrics['partner_bonus'],
                            metrics['group_bonus'],
                            metrics['club_bonus']
                        ]
                    }
                    bonus_df = pd.DataFrame(bonus_data)
                    bonus_df = bonus_df[bonus_df['Сумма'] > 0]  # Показываем только ненулевые бонусы
                    
                    fig = go.Figure(data=[
                        go.Bar(
                            x=bonus_df['Тип бонуса'],
                            y=bonus_df['Сумма'],
                            text=bonus_df['Сумма'].round(2),
                            textposition='auto',
                        )
                    ])
                    fig.update_layout(
                        title='Структура бонусов',
                        xaxis_title='Тип бонуса',
                        yaxis_title='Сумма (у.е.)'
                    )
                    st.plotly_chart(fig, key=f"bonus_chart_{i}")
                
                # Визуализация структуры
                st.write("### Визуализация структуры")
                fig = plot_network(scenario['structure'])
                st.plotly_chart(fig, key=f"network_plot_{i}", use_container_width=True)

def main():
    st.title("Оптимизатор структуры NL")
    
    # Боковая панель конфигурации
    st.sidebar.header("Параметры")
    
    # Выбор режима работы
    mode = st.sidebar.radio(
        "Режим работы",
        ["Оптимизация структуры", "Анализ сценариев"]
    )
    
    if mode == "Анализ сценариев":
        analyze_scenarios()
    else:
        # Выбор региона
        selected_region = st.sidebar.selectbox(
            "Регион",
            list(REGIONS.keys()),
            format_func=lambda x: REGIONS[x]['name']
        )
        
        region_info = REGIONS[selected_region]
        st.sidebar.write(f"Валюта: {region_info['currency']}")
        st.sidebar.write(f"Мин. PV: {region_info['min_pv_threshold']}")
        
        # Выбор стартового набора
        st.sidebar.subheader("Стартовый набор")
        starter_kit = st.sidebar.selectbox(
            "Выберите стартовый набор",
            ["Нет"] + list(STARTER_KITS.keys()),
            format_func=lambda x: {
                'START': 'Старт (100 у.е.)',
                'START_PLUS': 'Старт+ (200 у.е.)',
                'BUSINESS': 'Бизнес (500 у.е.)',
                'VIP': 'VIP (1000 у.е.)',
                'Нет': 'Без набора'
            }.get(x, x)
        )
        
        if starter_kit != "Нет":
            st.sidebar.write("### Привилегии набора")
            kit = STARTER_KITS[starter_kit]
            for privilege in kit['privileges']:
                priv_info = STARTER_KIT_PRIVILEGES[privilege]
                st.sidebar.write(f"- {priv_info['name']}")
                if 'duration' in priv_info:
                    st.sidebar.write(f"  _{priv_info['duration']} дней_")
        
        total_pv = st.sidebar.number_input(
            "Общий объем PV для распределения",
            min_value=1000,
            max_value=1000000,
            value=10000,
            step=1000
        )
        
        optimization_mode = st.sidebar.selectbox(
            "Режим оптимизации",
            ["Максимальная прибыль", "Анализ уязвимостей"]
        )
        
        # Основной контент
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Структура сети")
            optimizer = UserOptimizer()
            structure = NetworkStructure(total_pv)
            
            # Устанавливаем регион для корневого партнера
            root_partner = structure.partners[structure.root_id]
            root_partner.region = selected_region
            
            # Применяем стартовый набор если выбран
            if starter_kit != "Нет":
                structure.partners[structure.root_id].purchase_starter_kit(starter_kit)
            
            if optimization_mode == "Максимальная прибыль":
                result = optimizer.optimize_for_profit(structure)
            else:
                result = optimizer.analyze_vulnerabilities(structure)
                
            # История изменений
            st.write("### История построения сети")
            history = result.get_history()
            
            # Создаем вкладки для каждого этапа
            if history:
                tabs = st.tabs([snapshot['stage_name'] for snapshot in history])
                
                for i, (tab, snapshot) in enumerate(zip(tabs, history)):
                    with tab:
                        metrics = snapshot['metrics']
                        
                        # Основные метрики этапа
                        st.write("#### Основные показатели")
                        stage_metrics = pd.DataFrame({
                            "Показатель": [
                                "Всего партнеров",
                                "Активных партнеров",
                                "Общий PV",
                                "Ожидаемый доход"
                            ],
                            "Значение": [
                                metrics["total_partners"],
                                metrics["active_partners"],
                                f"{metrics['total_pv']:,.0f}",
                                f"{metrics['expected_income']:,.2f} у.е."
                            ]
                        })
                        st.table(stage_metrics)
                        
                        # Квалификации на этапе
                        if 'qualification_counts' in metrics:
                            st.write("#### Распределение квалификаций")
                            qual_data = []
                            for qual, count in metrics['qualification_counts'].items():
                                qual_data.append({
                                    "Квалификация": QUALIFICATION_NAMES[qual],
                                    "Количество": count
                                })
                            qual_df = pd.DataFrame(qual_data)
                            st.table(qual_df)
                        
                        # Структура дохода
                        if 'income_breakdown' in metrics:
                            st.write("#### Структура дохода")
                            income_df = pd.DataFrame({
                                "Тип бонуса": [
                                    "Личный бонус",
                                    "Групповой бонус",
                                    "Клубный бонус",
                                    "Бонус наставника",
                                    "Динамический бонус",
                                    "Бонус восстановления",
                                    "Общий доход"
                                ],
                                "Сумма": [
                                    f"{metrics['income_breakdown']['personal_bonus']:,.2f}",
                                    f"{metrics['income_breakdown']['group_bonus']:,.2f}",
                                    f"{metrics['income_breakdown']['club_bonus']:,.2f}",
                                    f"{metrics['income_breakdown']['mentorship_bonus']:,.2f}",
                                    f"{metrics['income_breakdown']['dynamic_bonus']:,.2f}",
                                    f"{metrics['income_breakdown'].get('recovery_bonus', 0):,.2f}",
                                    f"{metrics['income_breakdown']['total']:,.2f}"
                                ]
                            })
                            st.table(income_df)
                            
                        # Визуализация сети для этого этапа
                        if i < len(history) - 1:  # Показываем изменения до следующего этапа
                            next_snapshot = history[i + 1]
                            st.write("#### Изменения на следующем этапе")
                            changes = {
                                "PV": next_snapshot['metrics']['total_pv'] - metrics['total_pv'],
                                "Доход": next_snapshot['metrics']['expected_income'] - metrics['expected_income'],
                                "Партнеры": next_snapshot['metrics']['total_partners'] - metrics['total_partners']
                            }
                            changes_df = pd.DataFrame({
                                "Показатель": ["Изменение PV", "Изменение дохода", "Новых партнеров"],
                                "Значение": [
                                    f"{changes['PV']:+,.0f}",
                                    f"{changes['Доход']:+,.2f} у.е.",
                                    f"{changes['Партнеры']:+d}"
                                ]
                            })
                            st.table(changes_df)
            
            # Визуализация сети
            fig = plot_network(result.network)
            st.plotly_chart(fig, use_container_width=True)
            
            # Информация о компрессии
            st.write("### Статус компрессии")
            is_compressed, warning_level = root_partner.check_compression_status()
            
            if is_compressed:
                st.error(f"⚠️ {COMPRESSION_WARNINGS[warning_level]['message']}")
                
                # Показываем условия восстановления
                st.write("#### Условия восстановления:")
                for recovery_type, conditions in RECOVERY_CONDITIONS.items():
                    st.write(f"**{recovery_type}:**")
                    st.write(f"- Период: {conditions['period']} мес.")
                    st.write(f"- Требуемый PV: {conditions['required_pv']}")
                    st.write(f"- Бонус: +{conditions['bonus_rate']:.1%}")
            else:
                compression_rule = root_partner.get_compression_rule()
                st.success("✅ Структура активна")
                st.write(f"Порог компрессии: {compression_rule['threshold']} PV")
                st.write(f"Льготный период: {compression_rule['grace_period']} мес.")
                
            # История компрессий
            if root_partner.compression_history:
                st.write("#### История компрессий:")
                compression_df = pd.DataFrame(
                    root_partner.compression_history,
                    columns=["Дата", "PV"]
                )
                st.table(compression_df)
            
            # Клубная информация
            st.write("### Клубная система")
            root_partner = structure.partners[structure.root_id]
            
            # Обновляем клубное членство
            root_partner.update_club_membership()
            current_club = root_partner.get_club_level()
            
            if current_club:
                st.write(f"**Текущий клубный уровень:** {current_club}")
                
                # Активные привилегии
                st.write("#### Активные привилегии")
                benefits = root_partner.get_club_benefits()
                for benefit in benefits:
                    if benefit in CLUB_BENEFITS:
                        benefit_info = CLUB_BENEFITS[benefit]
                        st.write(f"- {benefit_info['name']}")
                        
                # Доступные мероприятия
                st.write("#### Доступные мероприятия")
                for club_level in root_partner.club_memberships:
                    if club_level in CLUB_EVENTS:
                        st.write(f"**{club_level} Club:**")
                        for event in CLUB_EVENTS[club_level]:
                            discount = root_partner.get_event_discount(club_level)
                            final_price = event['base_price'] * (1 - discount)
                            st.write(
                                f"- {event['name']}\n"
                                f"  * Длительность: {event['duration']} дней\n"
                                f"  * Базовая цена: {event['base_price']} у.е.\n"
                                f"  * Скидка: {discount:.0%}\n"
                                f"  * Итоговая цена: {final_price:.0f} у.е."
                            )
            else:
                st.write("_Партнер пока не является участником клубной системы_")
                # Показываем требования для вступления в клубы
                st.write("#### Требования для вступления:")
                for level, requirements in CLUB_LEVELS.items():
                    st.write(f"**{level} Club:**")
                    qual_req = requirements['qualification']
                    months_req = requirements['maintenance_period']
                    st.write(
                        f"- Квалификация: {qual_req}\n"
                        f"- Поддержание квалификации: {months_req} мес."
                    )
            
        with col2:
            st.subheader("Результаты анализа")
            metrics = result.get_metrics()
            fig = plot_metrics(metrics)
            st.plotly_chart(fig, use_container_width=True)
            
            # Добавляем информацию о восстановлении
            if root_partner.recovery_status:
                recovery_info = RECOVERY_CONDITIONS[root_partner.recovery_status]
                st.warning(
                    f"🔄 Статус восстановления: {root_partner.recovery_status}\n"
                    f"Бонус: +{recovery_info['bonus_rate']:.1%}"
                )
            
            # Детальная статистика
            st.write("### Статистика сети")
            
            # Добавляем информацию о стартовом наборе
            root_partner = structure.partners[structure.root_id]
            metrics_data = {
                "Метрика": [
                    "Всего партнеров",
                    "Активных партнеров",
                    "Общий PV",
                    "Ожидаемый доход"
                ],
                "Значение": [
                    metrics["total_partners"],
                    metrics["active_partners"],
                    f"{metrics['total_pv']:,.0f}",
                    f"{metrics['expected_income']:,.2f} у.е."
                ]
            }
            
            if root_partner.starter_kit:
                kit = STARTER_KITS[root_partner.starter_kit]
                metrics_data["Метрика"].extend([
                    "Стартовый набор",
                    "Активные привилегии"
                ])
                
                active_privileges = [
                    STARTER_KIT_PRIVILEGES[p]['name']
                    for p in root_partner.privileges
                    if root_partner.has_privilege(p)
                ]
                
                metrics_data["Значение"].extend([
                    f"{root_partner.starter_kit} ({kit['price']} у.е.)",
                    ", ".join(active_privileges) if active_privileges else "Нет активных привилегий"
                ])
            
            stats_df = pd.DataFrame(metrics_data)
            st.table(stats_df)
            
            # Обновляем структуру дохода с учетом региональных особенностей
            income_df = pd.DataFrame({
                "Тип бонуса": [
                    "Личный бонус",
                    "Групповой бонус",
                    "Клубный бонус",
                    "Бонус наставника",
                    "Динамический бонус",
                    "Быстрый старт",
                    "Бонус лидерства",
                    "Бонус восстановления",
                    "Общий доход"
                ],
                "Сумма": [
                    f"{metrics['income_breakdown']['personal_bonus']:,.2f}",
                    f"{metrics['income_breakdown']['group_bonus']:,.2f}",
                    f"{metrics['income_breakdown']['club_bonus']:,.2f}",
                    f"{metrics['income_breakdown']['mentorship_bonus']:,.2f}",
                    f"{metrics['income_breakdown']['dynamic_bonus']:,.2f}",
                    f"{root_partner.get_quick_start_bonus():,.2f}",
                    f"{root_partner.get_leadership_bonus():,.2f}",
                    f"{metrics['income_breakdown'].get('recovery_bonus', 0):,.2f}",
                    f"{metrics['income_breakdown']['total']:,.2f}"
                ]
            })
            st.table(income_df)
            
            # Добавляем информацию о региональных особенностях
            st.write("### Региональные условия")
            
            # Основная информация о регионе
            region_df = pd.DataFrame({
                "Параметр": [
                    "Регион",
                    "Валюта",
                    "Минимальный PV",
                    "Порог компрессии",
                    "Льготный период"
                ],
                "Значение": [
                    region_info['name'],
                    region_info['currency'],
                    f"{region_info['min_pv_threshold']} PV",
                    f"{region_info['compression_threshold']} PV",
                    f"{region_info['grace_period']} мес."
                ]
            })
            st.table(region_df)
            
            # Корректировки квалификаций
            if 'qualification_adjustments' in region_info:
                st.write("#### Корректировки квалификаций")
                
                # Создаем DataFrame для корректировок
                adjustments_data = []
                for qual, adjustments in region_info['qualification_adjustments'].items():
                    for param, value in adjustments.items():
                        if param == 'min_go':
                            param_name = 'Минимальный GO'
                            value_str = f"{value:,} PV"
                        else:
                            param_name = param
                            value_str = str(value)
                            
                        adjustments_data.append({
                            "Квалификация": QUALIFICATION_NAMES[qual],
                            "Параметр": param_name,
                            "Значение": value_str,
                            "Стандартное значение": f"{QUALIFICATIONS[qual]['min_go']:,} PV"
                        })
                
                if adjustments_data:
                    adjustments_df = pd.DataFrame(adjustments_data)
                    st.table(adjustments_df)
                    
            # Добавляем информацию о клубных бонусах в структуру дохода
            club_bonus_rate = root_partner.get_club_bonus_rate()
            leadership_bonus = root_partner.get_leadership_bonus()
            
            income_df = pd.DataFrame({
                "Тип бонуса": [
                    "Личный бонус",
                    "Групповой бонус",
                    "Клубный бонус",
                    "Бонус наставника",
                    "Динамический бонус",
                    "Быстрый старт",
                    "Бонус лидерства",
                    "Бонус восстановления",
                    "Общий доход"
                ],
                "Сумма": [
                    f"{metrics['income_breakdown']['personal_bonus']:,.2f}",
                    f"{metrics['income_breakdown']['group_bonus']:,.2f}",
                    f"{metrics['income_breakdown']['club_bonus']:,.2f}",
                    f"{metrics['income_breakdown']['mentorship_bonus']:,.2f}",
                    f"{metrics['income_breakdown']['dynamic_bonus']:,.2f}",
                    f"{root_partner.get_quick_start_bonus():,.2f}",
                    f"{leadership_bonus:,.2f}",
                    f"{metrics['income_breakdown'].get('recovery_bonus', 0):,.2f}",
                    f"{metrics['income_breakdown']['total']:,.2f}"
                ]
            })
            st.table(income_df)
            
            if club_bonus_rate > 0:
                st.write(f"**Дополнительная ставка клубного бонуса:** +{club_bonus_rate:.1%}")
            
            # Динамика роста
            st.write("### Динамика роста")
            growth_df = pd.DataFrame({
                "Период": [
                    "Месячный рост",
                    "Квартальный рост",
                    "Годовой рост"
                ],
                "Значение": [
                    f"{metrics['growth_metrics']['monthly_growth']:.1%}",
                    f"{metrics['growth_metrics']['quarterly_growth']:.1%}",
                    f"{metrics['growth_metrics']['yearly_growth']:.1%}"
                ]
            })
            st.table(growth_df)
            
            # Если есть анализ рисков
            if 'risk_analysis' in metrics:
                st.write("### Анализ рисков")
                risk_df = pd.DataFrame({
                    "Тип риска": [
                        "Зависимость от крупных партнеров",
                        "Риск компрессии",
                        "Стабильность структуры"
                    ],
                    "Значение": [
                        f"{metrics['risk_analysis']['dependency_risk']:.2%}",
                        f"{metrics['risk_analysis']['compression_risk']:.2%}",
                        f"{metrics['risk_analysis']['stability_risk']:.2%}"
                    ]
                })
                st.table(risk_df)
                
                if 'vulnerability_score' in metrics:
                    st.write(f"**Общий показатель уязвимости:** {metrics['vulnerability_score']:.2%}")

            # Если есть анализ рисков
            if 'vulnerabilities' in metrics:
                st.write("### Анализ уязвимостей")
                
                # Общий показатель уязвимости
                vulnerability_score = metrics['vulnerability_score']
                score_color = (
                    "red" if vulnerability_score > 0.7
                    else "orange" if vulnerability_score > 0.4
                    else "green"
                )
                st.markdown(
                    f"**Общий показатель уязвимости:** "
                    f"<span style='color: {score_color}'>{vulnerability_score:.1%}</span>",
                    unsafe_allow_html=True
                )
                
                # Создаем вкладки для разных типов уязвимостей
                vuln_types = {
                    'compression_abuse': 'Компрессия',
                    'qualification_abuse': 'Квалификации',
                    'volume_distribution': 'Объемы',
                    'structure_manipulation': 'Структура',
                    'bonus_exploitation': 'Бонусы'
                }
                
                vuln_tabs = st.tabs(list(vuln_types.values()))
                
                for (vuln_type, tab_name), tab in zip(vuln_types.items(), vuln_tabs):
                    with tab:
                        vuln_data = metrics['vulnerabilities'][vuln_type]
                        
                        # Показатель риска для данного типа
                        risk_color = (
                            "red" if vuln_data['risk_level'] > 0.7
                            else "orange" if vuln_data['risk_level'] > 0.4
                            else "green"
                        )
                        st.markdown(
                            f"**Уровень риска:** "
                            f"<span style='color: {risk_color}'>{vuln_data['risk_level']:.1%}</span>",
                            unsafe_allow_html=True
                        )
                        
                        # Найденные проблемы
                        if vuln_data['issues']:
                            st.write("#### Обнаруженные проблемы")
                            for issue in vuln_data['issues']:
                                with st.expander(issue['description']):
                                    if 'partner_id' in issue:
                                        st.write(f"Партнер ID: {issue['partner_id']}")
                                    if 'pattern' in issue:
                                        st.write(f"Паттерн: {issue['pattern']}")
                                    if 'frequency' in issue:
                                        st.write(f"Частота: {issue['frequency']}")
                                    if 'changes' in issue:
                                        st.write("Изменения:")
                                        changes_df = pd.DataFrame(issue['changes'])
                                        st.table(changes_df)
                        else:
                            st.success("Проблем не обнаружено")
                            
                # Рекомендации
                if 'recommendations' in metrics:
                    st.write("### Рекомендации по улучшению")
                    for rec in metrics['recommendations']:
                        with st.expander(f"🔍 {rec['description']} (Приоритет: {rec['priority']})"):
                            st.write(rec['details'])
                            
            # Добавляем график изменения выплат
            if history:
                st.write("### История изменения выплат")
                payments_data = []
                for snapshot in history:
                    if 'income_breakdown' in snapshot['metrics']:
                        payments_data.append({
                            'Этап': snapshot['stage_name'],
                            'Выплаты': snapshot['metrics']['income_breakdown']['total']
                        })
                
                if payments_data:
                    payments_df = pd.DataFrame(payments_data)
                    fig = go.Figure(data=[
                        go.Bar(
                            x=payments_df['Этап'],
                            y=payments_df['Выплаты'],
                            text=[f"{x:,.2f}" for x in payments_df['Выплаты']],
                            textposition='auto',
                        )
                    ])
                    fig.update_layout(
                        title="Динамика выплат по этапам",
                        xaxis_title="Этап построения",
                        yaxis_title="Сумма выплат",
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main() 