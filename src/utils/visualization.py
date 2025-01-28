import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
import numpy as np
from typing import Dict, List
from models.structure import NetworkStructure
from utils.constants import QUALIFICATION_NAMES
import streamlit as st

# Цвета для квалификаций
QUALIFICATION_COLORS = {
    'NONE': '#808080',  # Серый
    'M1': '#90EE90',    # Светло-зеленый
    'M2': '#3CB371',    # Средне-зеленый
    'M3': '#228B22',    # Темно-зеленый
    'B1': '#ADD8E6',    # Светло-синий
    'B2': '#4169E1',    # Средне-синий
    'B3': '#000080',    # Темно-синий
    'TOP': '#FFD700',   # Золотой
    'TOP1': '#FFA500',  # Оранжевый
    'TOP2': '#FF8C00',  # Темно-оранжевый
    'TOP3': '#FF7F50',  # Коралловый
    'TOP4': '#FF6347',  # Томатный
    'TOP5': '#FF4500',  # Оранжево-красный
    'AC1': '#8B0000',   # Темно-красный
    'AC2': '#800080',   # Пурпурный
    'AC3': '#4B0082',   # Индиго
    'AC4': '#483D8B',   # Темно-синий сланец
    'AC5': '#2F4F4F',   # Темно-синий серый
    'AC6': '#000000'    # Черный
}

def plot_network(structure: NetworkStructure, key: str = None) -> go.Figure:
    """
    Визуализирует структуру сети
    Args:
        structure: Структура сети для визуализации
        key: Уникальный ключ для графика
    Returns:
        go.Figure: Объект фигуры Plotly
    """
    G = nx.Graph()
    
    # Добавляем узлы и ребра
    for partner_id, partner in structure.partners.items():
        G.add_node(partner_id, 
                  pv=partner.pv,
                  qualification=partner.qualification)
        if partner.upline_id is not None:
            G.add_edge(partner.upline_id, partner_id)
    
    # Если сеть слишком большая, используем упрощенную визуализацию
    if len(G.nodes()) > 100:
        # Создаем круговой layout
        radius = 1
        num_nodes = len(G.nodes())
        pos = {}
        nodes = list(G.nodes())
        
        # Размещаем корневой узел в центре
        root_id = structure.root_id
        pos[root_id] = np.array([0, 0])
        nodes.remove(root_id)
        
        # Размещаем остальные узлы по кругу
        for i, node in enumerate(nodes):
            angle = 2 * np.pi * i / (num_nodes - 1)
            pos[node] = np.array([radius * np.cos(angle), radius * np.sin(angle)])
    else:
        try:
            pos = nx.spring_layout(G, k=1/np.sqrt(len(G.nodes())), iterations=50)
        except:
            # Если spring_layout не работает, используем круговой layout
            pos = nx.circular_layout(G)
    
    # Создаем узлы
    node_trace = go.Scatter(
        x=[pos[k][0] for k in G.nodes()],
        y=[pos[k][1] for k in G.nodes()],
        mode='markers+text',
        hoverinfo='text',
        marker=dict(
            size=20,
            color=['blue' if n == structure.root_id else 'lightblue' for n in G.nodes()],
            line=dict(width=2)
        ),
        text=[f"ID: {n}\nPV: {G.nodes[n]['pv']}\nQual: {G.nodes[n]['qualification']}"
              for n in G.nodes()],
        textposition="top center"
    )
    
    # Создаем ребра
    edge_trace = go.Scatter(
        x=[],
        y=[],
        line=dict(width=1, color='#888'),
        hoverinfo='none',
        mode='lines'
    )
    
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_trace['x'] += (x0, x1, None)
        edge_trace['y'] += (y0, y1, None)
    
    # Создаем фигуру
    fig = go.Figure(data=[edge_trace, node_trace],
                   layout=go.Layout(
                       showlegend=False,
                       hovermode='closest',
                       margin=dict(b=20,l=5,r=5,t=40),
                       xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                       yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                   ))
    
    return fig

def plot_metrics(metrics: Dict) -> go.Figure:
    """Создание визуализации метрик сети"""
    fig = go.Figure()
    
    # Распределение квалификаций
    if 'qualification_counts' in metrics:
        quals = [QUALIFICATION_NAMES[q] for q in metrics['qualification_counts'].keys()]
        counts = list(metrics['qualification_counts'].values())
        
        fig.add_trace(go.Bar(
            name='Квалификации',
            x=quals,
            y=counts,
            marker_color='#4169E1'
        ))
        
    # Структура дохода
    if 'income_breakdown' in metrics:
        income_types_ru = {
            'personal_bonus': 'Личный бонус',
            'group_bonus': 'Групповой бонус',
            'club_bonus': 'Клубный бонус',
            'mentorship_bonus': 'Бонус наставника',
            'dynamic_bonus': 'Динамический бонус',
            'recovery_bonus': 'Бонус восстановления',
            'total': 'Общий доход'
        }
        income_types = [income_types_ru[k] for k in metrics['income_breakdown'].keys()]
        income_values = list(metrics['income_breakdown'].values())
        
        fig.add_trace(go.Bar(
            name='Доход',
            x=income_types,
            y=income_values,
            marker_color='#228B22',
            visible=False
        ))
        
    # Анализ рисков
    if 'risk_analysis' in metrics:
        risk_types_ru = {
            'dependency_risk': 'Риск зависимости',
            'compression_risk': 'Риск компрессии',
            'stability_risk': 'Риск стабильности'
        }
        risk_types = [risk_types_ru[k] for k in metrics['risk_analysis'].keys()]
        risk_values = list(metrics['risk_analysis'].values())
        
        fig.add_trace(go.Bar(
            name='Риски',
            x=risk_types,
            y=risk_values,
            marker_color='#DC143C',
            visible=False
        ))
        
    # Динамика роста
    if 'growth_metrics' in metrics:
        growth_types_ru = {
            'monthly_growth': 'Месячный рост',
            'quarterly_growth': 'Квартальный рост',
            'yearly_growth': 'Годовой рост'
        }
        growth_types = [growth_types_ru[k] for k in metrics['growth_metrics'].keys()]
        growth_values = [v * 100 for v in metrics['growth_metrics'].values()]  # Конвертируем в проценты
        
        fig.add_trace(go.Bar(
            name='Динамика роста',
            x=growth_types,
            y=growth_values,
            marker_color='#FFD700',
            visible=False,
            text=[f'{v:.1f}%' for v in growth_values],
            textposition='auto'
        ))
        
    # Добавление кнопок переключения
    fig.update_layout(
        updatemenus=[{
            'buttons': [
                {
                    'args': [{'visible': [True, False, False, False]}],
                    'label': 'Квалификации',
                    'method': 'update'
                },
                {
                    'args': [{'visible': [False, True, False, False]}],
                    'label': 'Доход',
                    'method': 'update'
                },
                {
                    'args': [{'visible': [False, False, True, False]}],
                    'label': 'Риски',
                    'method': 'update'
                },
                {
                    'args': [{'visible': [False, False, False, True]}],
                    'label': 'Динамика роста',
                    'method': 'update'
                }
            ],
            'direction': 'down',
            'showactive': True,
            'x': 0.1,
            'y': 1.15
        }],
        title='Метрики сети',
        height=500
    )
    
    return fig

def create_sankey_diagram(structure: NetworkStructure) -> go.Figure:
    """Создание диаграммы Сэнки для потоков PV в сети"""
    nodes = []
    links = []
    node_ids = {}
    current_id = 0
    
    # Добавление корневого узла
    nodes.append(QUALIFICATION_NAMES[structure.partners[structure.root_id].qualification])
    node_ids[structure.root_id] = current_id
    current_id += 1
    
    # Добавление остальных узлов и связей
    for partner_id, partner in structure.partners.items():
        if partner_id != structure.root_id:
            if partner_id not in node_ids:
                nodes.append(QUALIFICATION_NAMES[partner.qualification])
                node_ids[partner_id] = current_id
                current_id += 1
            
            if partner.upline_id is not None:
                links.append({
                    'source': node_ids[partner.upline_id],
                    'target': node_ids[partner_id],
                    'value': partner.pv
                })
                
    # Создание диаграммы
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=nodes,
            color="blue"
        ),
        link=dict(
            source=[link['source'] for link in links],
            target=[link['target'] for link in links],
            value=[link['value'] for link in links]
        )
    )])
    
    fig.update_layout(
        title_text="Поток PV в сети",
        font_size=10,
        height=600
    )
    
    return fig 