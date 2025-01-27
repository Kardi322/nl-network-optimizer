import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from utils.constants import QUALIFICATIONS, RISK_WEIGHTS
from models.structure import NetworkStructure
from models.partner import Partner

class OptimizationResult:
    def __init__(self, network: NetworkStructure, metrics: Dict):
        self.network = network
        self.metrics = metrics
        
    def get_metrics(self) -> Dict:
        return self.metrics
        
    def get_history(self) -> List[Dict]:
        """Получить историю изменений сети"""
        return self.network.get_history()

class UserOptimizer:
    def __init__(self):
        self.min_partner_pv = 50
        self.optimal_personal_pv = 200
        
    def optimize_for_profit(self, structure: NetworkStructure, 
                           target_qualification: str = 'B3',    # Целевая квалификация
                           min_partners: int = None,            # Минимальное количество партнеров
                           max_partners: int = None,            # Максимальное количество партнеров
                           strategy: str = 'balanced'           # Стратегия распределения
                           ) -> OptimizationResult:
        """
        Оптимизация структуры с гибкими параметрами
        Args:
            structure: Структура сети
            target_qualification: Целевая квалификация ('M3', 'B3', 'TOP' и т.д.)
            min_partners: Минимальное количество партнеров
            max_partners: Максимальное количество партнеров
            strategy: Стратегия распределения ('balanced', 'aggressive', 'conservative')
        """
        # Этап 1: Начальное состояние (личные продажи)
        initial_metrics = {
            'stage': 'Личные продажи',
            'total_pv': structure.total_pv,
            'personal_pv': structure.partners[structure.root_id].pv,
            'payout': structure.calculate_income(structure.root_id)['total'],
            'strategy': strategy,
            'target_qualification': target_qualification
        }
        structure.create_snapshot({
            'name': "Этап 1: Личные продажи",
            'metrics': initial_metrics
        })
        
        remaining_pv = structure.total_pv - structure.partners[structure.root_id].pv
        
        # Определяем параметры в зависимости от стратегии
        if strategy == 'aggressive':
            initial_partners = min(3, remaining_pv // (self.min_partner_pv * 2))
            pv_per_partner = self.min_partner_pv * 2
        elif strategy == 'conservative':
            initial_partners = min(7, remaining_pv // (self.min_partner_pv // 2))
            pv_per_partner = self.min_partner_pv // 2
        else:  # balanced
            initial_partners = min(5, remaining_pv // self.min_partner_pv)
            pv_per_partner = self.min_partner_pv
        
        # Применяем ограничения по количеству партнеров
        if min_partners is not None:
            initial_partners = max(initial_partners, min_partners)
        if max_partners is not None:
            initial_partners = min(initial_partners, max_partners)
        
        # Этап 2: Добавление партнеров без квалификации
        for _ in range(initial_partners):
            structure.add_partner(pv_per_partner, structure.root_id)
            remaining_pv -= pv_per_partner
        
        structure.update_qualifications()
        basic_metrics = {
            'stage': 'Базовая структура',
            'partners_added': initial_partners,
            'pv_per_partner': pv_per_partner,
            'level_analysis': self.analyze_level_progression(structure),
            'payout': structure.calculate_income(structure.root_id)['total']
        }
        structure.create_snapshot({
            'name': "Этап 2: Базовая структура",
            'metrics': basic_metrics
        })
        
        # Этап 3-4: Построение структуры в зависимости от целевой квалификации
        if target_qualification in QUALIFICATIONS:
            requirements = QUALIFICATIONS[target_qualification]
            if remaining_pv >= requirements['min_go']:
                # Этап 3: Построение промежуточной квалификации (M3)
                if target_qualification in ['B3', 'TOP']:
                    self._build_target_structure(structure, structure.root_id, 'M3', strategy)
                    remaining_pv -= QUALIFICATIONS['M3']['min_go']
                    structure.update_qualifications()
                    m3_metrics = {
                        'stage': 'Достижение M3',
                        'qualification_changes': structure.get_qualification_changes(),
                        'level_analysis': self.analyze_level_progression(structure),
                        'payout_increase': structure.calculate_income(structure.root_id)['total'] - basic_metrics['payout']
                    }
                    structure.create_snapshot({
                        'name': "Этап 3: Достижение M3",
                        'metrics': m3_metrics
                    })
                    
                    # Этап 4: Построение целевой квалификации
                    self._build_target_structure(structure, structure.root_id, target_qualification, strategy)
                    remaining_pv -= (requirements['min_go'] - QUALIFICATIONS['M3']['min_go'])
                    structure.update_qualifications()
                    target_metrics = {
                        'stage': f'Достижение {target_qualification}',
                        'qualification_changes': structure.get_qualification_changes(),
                        'level_analysis': self.analyze_level_progression(structure),
                        'payout_increase': structure.calculate_income(structure.root_id)['total'] - 
                                         (m3_metrics['payout_increase'] + basic_metrics['payout'])
                    }
                    structure.create_snapshot({
                        'name': f"Этап 4: Достижение {target_qualification}",
                        'metrics': target_metrics
                    })
                else:
                    # Для других квалификаций строим напрямую
                    self._build_target_structure(structure, structure.root_id, target_qualification, strategy)
                    remaining_pv -= requirements['min_go']
                    structure.update_qualifications()
                    target_metrics = {
                        'stage': f'Достижение {target_qualification}',
                        'qualification_changes': structure.get_qualification_changes(),
                        'level_analysis': self.analyze_level_progression(structure),
                        'payout_increase': structure.calculate_income(structure.root_id)['total'] - basic_metrics['payout']
                    }
                    structure.create_snapshot({
                        'name': f"Этап 3: Достижение {target_qualification}",
                        'metrics': target_metrics
                    })
        
        # Этап 5: Оптимальное распределение оставшегося PV
        if remaining_pv > 0:
            self._distribute_remaining_pv(structure, structure.root_id, remaining_pv, strategy)
            structure.update_qualifications()
            final_metrics = {
                'stage': 'Финальная оптимизация',
                'remaining_pv_distributed': remaining_pv,
                'level_analysis': self.analyze_level_progression(structure),
                'final_payout': structure.calculate_income(structure.root_id)['total']
            }
            structure.create_snapshot({
                'name': "Этап 5: Финальная оптимизация",
                'metrics': final_metrics
            })
            
        metrics = structure.get_metrics()
        return OptimizationResult(structure, metrics)
        
    def analyze_vulnerabilities(self, structure: NetworkStructure) -> OptimizationResult:
        """Анализ уязвимостей и поиск "лазеек" в системе"""
        # Сначала создаем оптимальную структуру
        result = self.optimize_for_profit(structure)
        
        # Анализируем различные типы уязвимостей
        vulnerabilities = {
            'compression_abuse': self._analyze_compression_abuse(result.network),
            'qualification_abuse': self._analyze_qualification_abuse(result.network),
            'volume_distribution': self._analyze_volume_distribution(result.network),
            'structure_manipulation': self._analyze_structure_manipulation(result.network),
            'bonus_exploitation': self._analyze_bonus_exploitation(result.network),
            'nonstandard_configurations': self._analyze_nonstandard_configurations(result.network)
        }
        
        # Добавляем рекомендации по устранению
        recommendations = self._generate_recommendations(vulnerabilities)
        
        # Обновляем метрики
        result.metrics.update({
            'vulnerabilities': vulnerabilities,
            'recommendations': recommendations,
            'risk_analysis': self._calculate_risk_metrics(result.network),
            'vulnerability_score': self._calculate_vulnerability_score(vulnerabilities)
        })
        
        # Создаем снимок с результатами анализа
        structure.create_snapshot({
            'name': "Анализ уязвимостей и рекомендации",
            'metrics': result.metrics
        })
        
        return result
        
    def _build_target_structure(self, structure: NetworkStructure, upline_id: int, target_qual: str, strategy: str):
        """Построение структуры для достижения целевой квалификации"""
        requirements = QUALIFICATIONS[target_qual]
        
        if strategy == 'aggressive':
            # Концентрируем объемы в меньшем количестве партнеров
            partner_count = max(3, requirements['min_partners'] - 1)
            pv_per_partner = requirements['min_go'] / partner_count
            for _ in range(partner_count):
                structure.add_partner(pv_per_partner, upline_id)
            
        elif strategy == 'conservative':
            # Распределяем объемы между большим количеством партнеров
            partner_count = requirements['min_partners'] + 2
            pv_per_partner = requirements['min_go'] / partner_count
            for _ in range(partner_count):
                structure.add_partner(pv_per_partner, upline_id)
            
        else:  # balanced
            # Используем стандартное распределение
            if target_qual == 'M3':
                self._build_m3_structure(structure, upline_id)
            elif target_qual == 'B3':
                self._build_b3_structure(structure, upline_id)
            else:
                self._build_minimal_structure(structure, upline_id, target_qual)

    def _distribute_remaining_pv(self, structure: NetworkStructure, root_id: int, remaining_pv: float, strategy: str = 'balanced'):
        """Распределение оставшегося PV согласно выбранной стратегии"""
        partners = list(structure.partners.values())
        partners.sort(key=lambda p: self._calculate_partner_potential(structure, p.id))
        
        if strategy == 'aggressive':
            # Распределяем между топ-3 партнерами
            top_partners = min(len(partners), 3)
            pv_per_partner = remaining_pv / top_partners
        elif strategy == 'conservative':
            # Распределяем между большим количеством партнеров
            top_partners = min(len(partners), 7)
            pv_per_partner = remaining_pv / top_partners
        else:  # balanced
            # Стандартное распределение между топ-5
            top_partners = min(len(partners), 5)
            pv_per_partner = remaining_pv / top_partners
        
        for i, partner in enumerate(partners[:top_partners]):
            if i == top_partners - 1:
                partner.pv += remaining_pv  # Добавляем весь оставшийся PV последнему партнеру
            else:
                partner.pv += pv_per_partner
                remaining_pv -= pv_per_partner
                
    def _calculate_partner_potential(self, structure: NetworkStructure, partner_id: int) -> float:
        """Calculate partner's potential for additional PV"""
        partner = structure.partners[partner_id]
        current_income = structure.calculate_income(partner_id)['total']
        
        # Simulate adding more PV
        partner.pv += 1000
        potential_income = structure.calculate_income(partner_id)['total']
        partner.pv -= 1000  # Restore original PV
        
        return potential_income - current_income
        
    def _calculate_risk_metrics(self, structure: NetworkStructure) -> Dict:
        """Calculate various risk metrics for the network"""
        # Dependency risk
        max_branch_volume = max(
            structure.calculate_group_volume(pid)
            for pid in structure.partners[structure.root_id].downline_ids
        ) if structure.partners[structure.root_id].downline_ids else 0
        
        total_volume = structure.calculate_group_volume(structure.root_id)
        dependency_risk = max_branch_volume / total_volume if total_volume > 0 else 0
        
        # Compression risk
        total_partners = len(structure.partners)
        compressed_partners = sum(
            1 for p in structure.partners.values()
            if p.is_compressed()
        )
        compression_risk = compressed_partners / total_partners if total_partners > 0 else 0
        
        # Stability risk
        qualified_partners = sum(
            1 for p in structure.partners.values()
            if p.qualification in ['M3', 'B1', 'B2', 'B3']
        )
        stability_risk = 1 - (qualified_partners / total_partners if total_partners > 0 else 0)
        
        return {
            'dependency_risk': dependency_risk,
            'compression_risk': compression_risk,
            'stability_risk': stability_risk
        }
        
    def _analyze_compression_abuse(self, structure: NetworkStructure) -> Dict:
        """Анализ возможных злоупотреблений системой компрессии"""
        issues = []
        risk_level = 0.0
        
        # Проверяем циклическое восстановление/компрессию
        for partner in structure.partners.values():
            if partner.compression_history:
                cycles = self._detect_compression_cycles(partner)
                if cycles:
                    issues.append({
                        'type': 'compression_cycling',
                        'description': 'Обнаружено циклическое восстановление после компрессии',
                        'partner_id': partner.id,
                        'cycles': cycles
                    })
                    risk_level += 0.3
                    
        # Проверяем манипуляции с льготным периодом
        grace_period_abuse = self._check_grace_period_abuse(structure)
        if grace_period_abuse:
            issues.append({
                'type': 'grace_period_abuse',
                'description': 'Выявлены манипуляции с льготным периодом',
                'cases': grace_period_abuse
            })
            risk_level += 0.2
            
        return {
            'issues': issues,
            'risk_level': min(risk_level, 1.0),
            'recommendations': self._get_compression_recommendations(issues)
        }
        
    def _analyze_qualification_abuse(self, structure: NetworkStructure) -> Dict:
        """Анализ манипуляций с квалификациями"""
        issues = []
        risk_level = 0.0
        
        # Проверяем быстрые изменения квалификаций
        for partner in structure.partners.values():
            qualification_changes = self._analyze_qualification_changes(partner)
            if qualification_changes['suspicious']:
                issues.append({
                    'type': 'rapid_qualification_change',
                    'description': 'Подозрительно быстрое изменение квалификаций',
                    'partner_id': partner.id,
                    'changes': qualification_changes['changes']
                })
                risk_level += 0.25
                
        # Проверяем нестандартные структуры квалификаций
        unusual_structures = self._detect_unusual_structures(structure)
        if unusual_structures:
            issues.append({
                'type': 'unusual_structure',
                'description': 'Обнаружены нестандартные структуры квалификаций',
                'cases': unusual_structures
            })
            risk_level += 0.2
            
        return {
            'issues': issues,
            'risk_level': min(risk_level, 1.0),
            'recommendations': self._get_qualification_recommendations(issues)
        }
        
    def _analyze_volume_distribution(self, structure: NetworkStructure) -> Dict:
        """Анализ распределения объемов"""
        issues = []
        risk_level = 0.0
        
        # Проверяем распределение объемов
        distribution = self._calculate_volume_distribution(structure)
        
        # Проверяем коэффициент Джини
        if distribution['gini_coefficient'] > 0.6:
            issues.append({
                'type': 'high_inequality',
                'description': 'Высокое неравенство в распределении объемов',
                'gini': distribution['gini_coefficient']
            })
            risk_level += 0.3
            
        # Проверяем концентрацию
        if distribution['concentration_ratio'] > 0.8:
            issues.append({
                'type': 'high_concentration',
                'description': 'Чрезмерная концентрация объемов',
                'ratio': distribution['concentration_ratio']
            })
            risk_level += 0.3
            
        # Проверяем личные объемы
        personal_volume_issues = self._check_personal_volume_manipulation(structure)
        if personal_volume_issues:
            issues.append({
                'type': 'personal_volume_manipulation',
                'description': 'Обнаружены манипуляции с личными объемами',
                'cases': personal_volume_issues
            })
            risk_level += 0.2
            
        return {
            'issues': issues,
            'risk_level': min(risk_level, 1.0),
            'recommendations': self._get_volume_recommendations(issues)
        }
        
    def _calculate_volume_distribution(self, structure: NetworkStructure) -> Dict:
        """Расчет распределения объемов в структуре"""
        volumes = []
        for partner in structure.partners.values():
            if partner.pv > 0:
                volumes.append(partner.pv)
                
        if not volumes:
            return {
                'gini_coefficient': 0.0,
                'concentration_ratio': 0.0
            }
            
        # Расчет коэффициента Джини
        n = len(volumes)
        volumes.sort()
        cumsum = np.cumsum(volumes)
        total = cumsum[-1]
        
        if total == 0:
            return {
                'gini_coefficient': 0.0,
                'concentration_ratio': 0.0
            }
            
        # Расчет коэффициента Джини
        gini = (n + 1 - 2 * np.sum(cumsum) / total) / n
        
        # Расчет коэффициента концентрации (доля объема у топ-20% партнеров)
        top_20_percent = volumes[int(0.8 * n):]
        concentration_ratio = sum(top_20_percent) / total
        
        return {
            'gini_coefficient': float(gini),
            'concentration_ratio': float(concentration_ratio)
        }
        
    def _check_volume_concentration(self, structure: NetworkStructure) -> Optional[Dict]:
        """Проверка концентрации объемов"""
        distribution = self._calculate_volume_distribution(structure)
        
        if distribution['concentration_ratio'] > 0.8:  # Высокая концентрация
            return {
                'type': 'high_concentration',
                'concentration_ratio': distribution['concentration_ratio'],
                'description': 'Чрезмерная концентрация объемов у небольшой группы партнеров'
            }
            
        return None
        
    def _analyze_structure_manipulation(self, structure: NetworkStructure) -> Dict:
        """Анализ манипуляций со структурой"""
        issues = []
        risk_level = 0.0
        
        # Проверяем искусственное создание глубины
        depth_issues = self._analyze_depth_manipulation(structure)
        if depth_issues:
            issues.append({
                'type': 'artificial_depth',
                'description': 'Выявлено искусственное создание глубины',
                'cases': depth_issues
            })
            risk_level += 0.25
            
        # Проверяем дублирование партнеров
        duplicate_issues = self._check_partner_duplication(structure)
        if duplicate_issues:
            issues.append({
                'type': 'partner_duplication',
                'description': 'Обнаружены признаки дублирования партнеров',
                'cases': duplicate_issues
            })
            risk_level += 0.3
            
        return {
            'issues': issues,
            'risk_level': min(risk_level, 1.0),
            'recommendations': self._get_structure_recommendations(issues)
        }
        
    def _analyze_bonus_exploitation(self, structure: NetworkStructure) -> Dict:
        """Анализ злоупотреблений бонусной системой"""
        issues = []
        risk_level = 0.0
        
        # Проверяем манипуляции с быстрым стартом
        quick_start_issues = self._analyze_quick_start_abuse(structure)
        if quick_start_issues:
            issues.append({
                'type': 'quick_start_abuse',
                'description': 'Выявлены манипуляции с бонусами быстрого старта',
                'cases': quick_start_issues
            })
            risk_level += 0.2
            
        # Проверяем злоупотребления клубной системой
        club_issues = self._analyze_club_system_abuse(structure)
        if club_issues:
            issues.append({
                'type': 'club_system_abuse',
                'description': 'Обнаружены злоупотребления клубной системой',
                'cases': club_issues
            })
            risk_level += 0.25
            
        return {
            'issues': issues,
            'risk_level': min(risk_level, 1.0),
            'recommendations': self._get_bonus_recommendations(issues)
        }
        
    def _generate_recommendations(self, vulnerabilities: Dict) -> List[Dict]:
        """Генерация рекомендаций по устранению уязвимостей"""
        recommendations = []
        
        for vuln_type, data in vulnerabilities.items():
            if data['risk_level'] > 0:
                recommendations.extend(data['recommendations'])
                
        # Сортируем по приоритету
        recommendations.sort(key=lambda x: x['priority'], reverse=True)
        return recommendations
        
    def _calculate_vulnerability_score(self, vulnerabilities: Dict) -> float:
        """Расчет общего показателя уязвимости"""
        weights = {
            'compression_abuse': 0.2,
            'qualification_abuse': 0.2,
            'volume_distribution': 0.15,
            'structure_manipulation': 0.15,
            'bonus_exploitation': 0.15,
            'nonstandard_configurations': 0.15
        }
        
        total_score = sum(
            data['risk_level'] * weights[vuln_type]
            for vuln_type, data in vulnerabilities.items()
        )
        
        return min(total_score, 1.0)

    def _detect_compression_cycles(self, partner: Partner) -> List[Dict]:
        """Поиск циклических паттернов компрессии/восстановления"""
        cycles = []
        history = partner.compression_history
        
        if len(history) < 2:
            return cycles
            
        # Ищем повторяющиеся паттерны
        for i in range(len(history) - 1):
            current_date, current_pv = history[i]
            next_date, next_pv = history[i + 1]
            days_between = (next_date - current_date).days
            
            if days_between <= 60:  # Подозрительно короткий цикл
                cycles.append({
                    'start_date': current_date.isoformat(),
                    'end_date': next_date.isoformat(),
                    'pv_change': next_pv - current_pv,
                    'days': days_between
                })
                
        return cycles
        
    def _check_grace_period_abuse(self, structure: NetworkStructure) -> List[Dict]:
        """Проверка злоупотреблений льготным периодом"""
        abuse_cases = []
        
        for partner in structure.partners.values():
            if partner.compression_history:
                grace_periods = self._analyze_grace_periods(partner)
                if grace_periods['suspicious']:
                    abuse_cases.append({
                        'partner_id': partner.id,
                        'pattern': grace_periods['pattern'],
                        'frequency': grace_periods['frequency']
                    })
                    
        return abuse_cases
        
    def _analyze_qualification_changes(self, partner: Partner) -> Dict:
        """Анализ изменений квалификаций"""
        changes = []
        suspicious = False
        
        if len(partner.qualification_history) < 2:
            return {'suspicious': False, 'changes': []}
            
        for i in range(len(partner.qualification_history) - 1):
            current_date, current_qual = partner.qualification_history[i]
            next_date, next_qual = partner.qualification_history[i + 1]
            days_between = (next_date - current_date).days
            
            # Проверяем быстрые повышения квалификации
            if self._is_rapid_qualification_increase(current_qual, next_qual, days_between):
                suspicious = True
                changes.append({
                    'from_qual': current_qual,
                    'to_qual': next_qual,
                    'days': days_between,
                    'date': next_date.isoformat()
                })
                
        return {
            'suspicious': suspicious,
            'changes': changes
        }
        
    def _is_rapid_qualification_increase(self, from_qual: str, to_qual: str, days: int) -> bool:
        """Проверка подозрительно быстрого повышения квалификации"""
        qual_ranks = {
            'NONE': 0, 'M1': 1, 'M2': 2, 'M3': 3,
            'B1': 4, 'B2': 5, 'B3': 6, 'TOP': 7
        }
        
        if from_qual not in qual_ranks or to_qual not in qual_ranks:
            return False
            
        rank_difference = qual_ranks[to_qual] - qual_ranks[from_qual]
        min_expected_days = rank_difference * 30  # Ожидаем минимум 30 дней на ранг
        
        return days < min_expected_days
        
    def _detect_unusual_structures(self, structure: NetworkStructure) -> List[Dict]:
        """Поиск нестандартных структур квалификаций"""
        unusual_cases = []
        
        # Проверяем несбалансированные ветви
        for partner_id in structure.partners:
            if unusual_branch := self._check_branch_balance(structure, partner_id):
                unusual_cases.append(unusual_branch)
                
        # Проверяем неестественное распределение квалификаций
        if unusual_dist := self._check_qualification_distribution(structure):
            unusual_cases.extend(unusual_dist)
            
        return unusual_cases
        
    def _analyze_volume_patterns(self, structure: NetworkStructure) -> Dict:
        """Анализ паттернов распределения объемов"""
        patterns = []
        suspicious = False
        
        # Проверяем равномерность распределения
        distribution = self._calculate_volume_distribution(structure)
        if distribution['suspicious']:
            issues.append({
                'type': 'high_inequality',
                'gini': distribution['gini_coefficient'],
                'description': 'Слишком неравномерное распределение объемов'
            })
            
        # Проверяем концентрацию объемов
        if concentration := self._check_volume_concentration(structure):
            suspicious = True
            patterns.append(concentration)
            
        return {
            'suspicious': suspicious,
            'patterns': patterns
        }
        
    def _check_personal_volume_manipulation(self, structure: NetworkStructure) -> List[Dict]:
        """Проверка манипуляций с личными объемами"""
        suspicious_cases = []
        
        for partner in structure.partners.values():
            if partner.volume_history:
                volume_changes = self._analyze_personal_volume_changes(partner)
                if volume_changes['suspicious']:
                    suspicious_cases.append({
                        'partner_id': partner.id,
                        'pattern': volume_changes['pattern'],
                        'frequency': volume_changes['frequency']
                    })
                    
        return suspicious_cases
        
    def _get_compression_recommendations(self, issues: List[Dict]) -> List[Dict]:
        """Генерация рекомендаций по устранению проблем с компрессией"""
        recommendations = []
        
        for issue in issues:
            if issue['type'] == 'compression_cycling':
                recommendations.append({
                    'priority': 1,
                    'description': 'Внедрить минимальный период между восстановлениями',
                    'details': 'Установить ограничение на количество восстановлений в год'
                })
            elif issue['type'] == 'grace_period_abuse':
                recommendations.append({
                    'priority': 2,
                    'description': 'Пересмотреть условия льготного периода',
                    'details': 'Ввести доп. требования для получения льготного периода'
                })
                
        return recommendations
        
    def _get_qualification_recommendations(self, issues: List[Dict]) -> List[Dict]:
        """Генерация рекомендаций по устранению проблем с квалификациями"""
        recommendations = []
        
        for issue in issues:
            if issue['type'] == 'rapid_qualification_change':
                recommendations.append({
                    'priority': 1,
                    'description': 'Ввести минимальные периоды между повышениями квалификации',
                    'details': 'Установить проверку истории квалификаций'
                })
            elif issue['type'] == 'unusual_structure':
                recommendations.append({
                    'priority': 2,
                    'description': 'Внедрить проверку баланса структуры',
                    'details': 'Добавить требования к распределению квалификаций'
                })
                
        return recommendations
        
    def _get_volume_recommendations(self, issues: List[Dict]) -> List[Dict]:
        """Генерация рекомендаций по устранению проблем с объемами"""
        recommendations = []
        
        for issue in issues:
            if issue['type'] == 'uneven_distribution':
                recommendations.append({
                    'priority': 2,
                    'description': 'Внедрить проверку равномерности распределения объемов',
                    'details': 'Установить максимальную разницу между ветвями'
                })
            elif issue['type'] == 'personal_volume_manipulation':
                recommendations.append({
                    'priority': 1,
                    'description': 'Ввести контроль изменений личных объемов',
                    'details': 'Добавить проверку истории изменений PV'
                })
                
        return recommendations
        
    def _get_structure_recommendations(self, issues: List[Dict]) -> List[Dict]:
        """Генерация рекомендаций по устранению проблем со структурой"""
        recommendations = []
        
        for issue in issues:
            if issue['type'] == 'artificial_depth':
                recommendations.append({
                    'priority': 1,
                    'description': 'Внедрить проверку естественности структуры',
                    'details': 'Добавить анализ глубины и ширины структуры'
                })
            elif issue['type'] == 'partner_duplication':
                recommendations.append({
                    'priority': 1,
                    'description': 'Усилить контроль регистрации партнеров',
                    'details': 'Внедрить проверку на дубликаты'
                })
                
        return recommendations
        
    def _get_bonus_recommendations(self, issues: List[Dict]) -> List[Dict]:
        """Генерация рекомендаций по устранению проблем с бонусами"""
        recommendations = []
        
        for issue in issues:
            if issue['type'] == 'quick_start_abuse':
                recommendations.append({
                    'priority': 2,
                    'description': 'Пересмотреть условия программы быстрого старта',
                    'details': 'Добавить доп. требования для получения бонусов'
                })
            elif issue['type'] == 'club_system_abuse':
                recommendations.append({
                    'priority': 1,
                    'description': 'Усилить контроль клубного членства',
                    'details': 'Внедрить проверку активности в клубе'
                })
                
        return recommendations

    def _check_branch_balance(self, structure: NetworkStructure, partner_id: int) -> Optional[Dict]:
        """Проверка баланса ветвей структуры"""
        partner = structure.partners[partner_id]
        if not partner.downline_ids:
            return None
            
        # Рассчитываем объемы ветвей
        branch_volumes = [
            structure.calculate_group_volume(downline_id)
            for downline_id in partner.downline_ids
        ]
        
        if not branch_volumes:
            return None
            
        max_volume = max(branch_volumes)
        min_volume = min(branch_volumes)
        total_volume = sum(branch_volumes)
        
        # Проверяем дисбаланс
        if total_volume > 0:
            imbalance = (max_volume - min_volume) / total_volume
            if imbalance > 0.7:  # Критический дисбаланс
                return {
                    'type': 'branch_imbalance',
                    'partner_id': partner_id,
                    'max_volume': max_volume,
                    'min_volume': min_volume,
                    'imbalance': imbalance
                }
        return None
        
    def _check_qualification_distribution(self, structure: NetworkStructure) -> List[Dict]:
        """Проверка распределения квалификаций"""
        issues = []
        
        # Считаем количество партнеров по квалификациям
        qualification_counts = {}
        for partner in structure.partners.values():
            qualification_counts[partner.qualification] = \
                qualification_counts.get(partner.qualification, 0) + 1
                
        total_partners = len(structure.partners)
        if total_partners == 0:
            return issues
            
        # Проверяем неестественное распределение
        for qual, count in qualification_counts.items():
            ratio = count / total_partners
            
            # Проверяем аномалии в распределении
            if qual in ['B1', 'B2', 'B3'] and ratio > 0.4:
                issues.append({
                    'type': 'high_qualification_concentration',
                    'qualification': qual,
                    'count': count,
                    'ratio': ratio
                })
            elif qual == 'NONE' and ratio > 0.6:
                issues.append({
                    'type': 'high_unqualified_ratio',
                    'count': count,
                    'ratio': ratio
                })
                
        return issues
        
    def _analyze_grace_periods(self, partner: Partner) -> Dict:
        """Анализ использования льготных периодов"""
        if not partner.compression_history:
            return {'suspicious': False}
            
        grace_periods = []
        pattern = None
        frequency = 0
        
        for i in range(len(partner.compression_history) - 1):
            current_date, _ = partner.compression_history[i]
            next_date, _ = partner.compression_history[i + 1]
            days_between = (next_date - current_date).days
            
            if days_between <= 90:  # Подозрительно короткий интервал
                grace_periods.append(days_between)
                frequency += 1
                
        if grace_periods:
            avg_period = sum(grace_periods) / len(grace_periods)
            if avg_period < 45:  # Слишком частое использование
                pattern = 'frequent_short_periods'
            elif len(grace_periods) > 3:  # Слишком много периодов
                pattern = 'multiple_periods'
                
        return {
            'suspicious': pattern is not None,
            'pattern': pattern,
            'frequency': frequency
        }
        
    def _analyze_depth_manipulation(self, structure: NetworkStructure) -> List[Dict]:
        """Анализ манипуляций с глубиной структуры"""
        issues = []
        
        for partner_id in structure.partners:
            depth = self._calculate_branch_depth(structure, partner_id)
            if depth > 7:  # Подозрительно глубокая структура
                active_partners = self._count_active_partners_in_branch(structure, partner_id)
                if active_partners < depth * 2:  # Мало активных партнеров для такой глубины
                    issues.append({
                        'type': 'artificial_depth',
                        'partner_id': partner_id,
                        'depth': depth,
                        'active_partners': active_partners
                    })
                    
        return issues
        
    def _calculate_branch_depth(self, structure: NetworkStructure, partner_id: int, depth: int = 0) -> int:
        """Расчет глубины ветви"""
        partner = structure.partners[partner_id]
        if not partner.downline_ids:
            return depth
            
        return max(
            self._calculate_branch_depth(structure, downline_id, depth + 1)
            for downline_id in partner.downline_ids
        )
        
    def _count_active_partners_in_branch(self, structure: NetworkStructure, partner_id: int) -> int:
        """Подсчет активных партнеров в ветви"""
        partner = structure.partners[partner_id]
        count = 1 if partner.pv >= self.min_partner_pv else 0
        
        for downline_id in partner.downline_ids:
            count += self._count_active_partners_in_branch(structure, downline_id)
            
        return count
        
    def _check_partner_duplication(self, structure: NetworkStructure) -> List[Dict]:
        """Проверка признаков дублирования партнеров"""
        issues = []
        
        # Группируем партнеров по объемам и квалификациям
        volume_groups = {}
        for partner in structure.partners.values():
            key = (partner.pv, partner.qualification)
            if key in volume_groups:
                volume_groups[key].append(partner.id)
            else:
                volume_groups[key] = [partner.id]
                
        # Проверяем подозрительные группы
        for (pv, qual), partner_ids in volume_groups.items():
            if len(partner_ids) > 3 and pv > 0:  # Подозрительное количество одинаковых партнеров
                issues.append({
                    'type': 'duplicate_pattern',
                    'pv': pv,
                    'qualification': qual,
                    'count': len(partner_ids),
                    'partner_ids': partner_ids
                })
                
        return issues
        
    def _analyze_quick_start_abuse(self, structure: NetworkStructure) -> List[Dict]:
        """Анализ злоупотреблений программой быстрого старта"""
        issues = []
        
        for partner in structure.partners.values():
            if 'quick_start' in partner.privileges:
                # Проверяем историю объемов
                if partner.volume_history:
                    volumes = [vol for _, vol in partner.volume_history]
                    if len(volumes) >= 2:
                        volume_changes = [
                            (volumes[i+1] - volumes[i]) / volumes[i]
                            for i in range(len(volumes)-1)
                        ]
                        
                        # Проверяем резкие изменения объемов
                        if any(abs(change) > 2.0 for change in volume_changes):  # Изменение более чем в 2 раза
                            issues.append({
                                'type': 'quick_start_volume_manipulation',
                                'partner_id': partner.id,
                                'changes': volume_changes
                            })
                            
        return issues
        
    def _analyze_club_system_abuse(self, structure: NetworkStructure) -> List[Dict]:
        """Анализ злоупотреблений клубной системой"""
        issues = []
        
        for partner in structure.partners.values():
            if partner.club_memberships:
                # Проверяем историю квалификаций
                if len(partner.qualification_history) >= 2:
                    qual_changes = []
                    for i in range(len(partner.qualification_history) - 1):
                        date1, qual1 = partner.qualification_history[i]
                        date2, qual2 = partner.qualification_history[i + 1]
                        days_between = (date2 - date1).days
                        qual_changes.append((qual1, qual2, days_between))
                        
                    # Ищем подозрительные паттерны
                    for qual1, qual2, days in qual_changes:
                        if days < 30 and self._is_significant_qualification_change(qual1, qual2):
                            issues.append({
                                'type': 'club_qualification_manipulation',
                                'partner_id': partner.id,
                                'from_qual': qual1,
                                'to_qual': qual2,
                                'days': days
                            })
                            
        return issues
        
    def _is_significant_qualification_change(self, qual1: str, qual2: str) -> bool:
        """Проверка значимости изменения квалификации"""
        qual_ranks = {
            'NONE': 0, 'M1': 1, 'M2': 2, 'M3': 3,
            'B1': 4, 'B2': 5, 'B3': 6, 'TOP': 7
        }
        
        if qual1 not in qual_ranks or qual2 not in qual_ranks:
            return False
            
        return abs(qual_ranks[qual2] - qual_ranks[qual1]) > 1

    def _analyze_personal_volume_changes(self, partner: Partner) -> Dict:
        """Анализ изменений личных объемов партнера"""
        if not partner.volume_history:
            return {
                'suspicious': False,
                'pattern': None,
                'frequency': 0
            }
            
        changes = []
        pattern = None
        frequency = 0
        
        # Анализируем историю изменений
        volumes = []
        for record in partner.volume_history:
            if isinstance(record, tuple) and len(record) == 2:
                _, vol = record
                volumes.append(vol)
            elif isinstance(record, (int, float)):
                volumes.append(record)
                
        if len(volumes) < 2:
            return {
                'suspicious': False,
                'pattern': None,
                'frequency': 0
            }
            
        for i in range(len(volumes) - 1):
            if volumes[i] > 0:
                change = (volumes[i+1] - volumes[i]) / volumes[i]
            else:
                change = 0
            changes.append(change)
            
            # Проверяем резкие изменения
            if abs(change) > 1.0:  # Изменение более чем в 2 раза
                frequency += 1
                
        if changes:
            # Определяем паттерн изменений
            if frequency > 2:
                pattern = 'frequent_large_changes'
            elif any(abs(change) > 2.0 for change in changes):
                pattern = 'extreme_changes'
            elif all(change < -0.5 for change in changes):
                pattern = 'consistent_decrease'
            elif all(change > 0.5 for change in changes):
                pattern = 'consistent_increase'
                
        return {
            'suspicious': pattern is not None,
            'pattern': pattern,
            'frequency': frequency
        }

    def _analyze_nonstandard_configurations(self, structure: NetworkStructure) -> Dict:
        """Глубокий анализ нестандартных конфигураций сети"""
        issues = []
        risk_level = 0.0
        
        # Анализ структурных аномалий
        structural_issues = self._check_structural_anomalies(structure)
        if structural_issues:
            issues.extend(structural_issues)
            risk_level += 0.2
            
        # Анализ квалификационных цепочек
        qualification_chains = self._analyze_qualification_chains(structure)
        if qualification_chains['suspicious']:
            issues.extend(qualification_chains['issues'])
            risk_level += 0.25
            
        # Анализ распределения объемов по уровням
        level_distribution = self._analyze_level_volume_distribution(structure)
        if level_distribution['suspicious']:
            issues.extend(level_distribution['issues'])
            risk_level += 0.2
            
        # Анализ временных паттернов
        temporal_patterns = self._analyze_temporal_patterns(structure)
        if temporal_patterns['suspicious']:
            issues.extend(temporal_patterns['issues'])
            risk_level += 0.15
            
        return {
            'issues': issues,
            'risk_level': min(risk_level, 1.0),
            'recommendations': self._get_nonstandard_recommendations(issues)
        }
        
    def _check_structural_anomalies(self, structure: NetworkStructure) -> List[Dict]:
        """Проверка структурных аномалий"""
        issues = []
        
        # Проверка "пустых" веток
        empty_branches = self._find_empty_branches(structure)
        if empty_branches:
            issues.append({
                'type': 'empty_branches',
                'description': 'Обнаружены пустые ветки в структуре',
                'branches': empty_branches
            })
            
        # Проверка несбалансированных квалификаций
        unbalanced_quals = self._check_qualification_balance(structure)
        if unbalanced_quals:
            issues.append({
                'type': 'unbalanced_qualifications',
                'description': 'Неестественное распределение квалификаций',
                'details': unbalanced_quals
            })
            
        # Проверка изолированных групп
        isolated_groups = self._find_isolated_groups(structure)
        if isolated_groups:
            issues.append({
                'type': 'isolated_groups',
                'description': 'Обнаружены изолированные группы партнеров',
                'groups': isolated_groups
            })
            
        return issues
        
    def _analyze_qualification_chains(self, structure: NetworkStructure) -> Dict:
        """Анализ цепочек квалификаций"""
        issues = []
        suspicious = False
        
        # Анализ последовательностей квалификаций
        for partner_id in structure.partners:
            chain = self._get_qualification_chain(structure, partner_id)
            if anomaly := self._check_chain_anomaly(chain):
                suspicious = True
                issues.append({
                    'type': 'qualification_chain_anomaly',
                    'partner_id': partner_id,
                    'chain': chain,
                    'anomaly': anomaly
                })
                
        return {
            'suspicious': suspicious,
            'issues': issues
        }
        
    def _analyze_level_volume_distribution(self, structure: NetworkStructure) -> Dict:
        """Анализ распределения объемов по уровням"""
        issues = []
        suspicious = False
        
        # Получаем объемы по уровням
        level_volumes = self._calculate_level_volumes(structure)
        
        # Проверяем аномалии в распределении
        for level, volume in level_volumes.items():
            if anomaly := self._check_level_anomaly(level, volume, level_volumes):
                suspicious = True
                issues.append({
                    'type': 'level_volume_anomaly',
                    'level': level,
                    'volume': volume,
                    'anomaly': anomaly
                })
                
        return {
            'suspicious': suspicious,
            'issues': issues
        }
        
    def _analyze_temporal_patterns(self, structure: NetworkStructure) -> Dict:
        """Анализ временных паттернов в структуре"""
        issues = []
        suspicious = False
        
        # Анализ паттернов роста
        growth_patterns = self._analyze_growth_patterns(structure)
        if growth_patterns['suspicious']:
            suspicious = True
            issues.extend(growth_patterns['issues'])
            
        # Анализ сезонности
        seasonality = self._check_seasonality(structure)
        if seasonality['suspicious']:
            suspicious = True
            issues.extend(seasonality['issues'])
            
        return {
            'suspicious': suspicious,
            'issues': issues
        }
        
    def _find_empty_branches(self, structure: NetworkStructure) -> List[Dict]:
        """Поиск пустых веток в структуре"""
        empty_branches = []
        
        for partner_id in structure.partners:
            partner = structure.partners[partner_id]
            if partner.downline_ids:
                branch_volume = structure.calculate_group_volume(partner_id)
                active_partners = self._count_active_partners_in_branch(structure, partner_id)
                
                if branch_volume < self.min_partner_pv * 2 and active_partners < 2:
                    empty_branches.append({
                        'partner_id': partner_id,
                        'volume': branch_volume,
                        'active_partners': active_partners
                    })
                    
        return empty_branches
        
    def _check_qualification_balance(self, structure: NetworkStructure) -> List[Dict]:
        """Проверка баланса квалификаций"""
        imbalances = []
        
        # Считаем квалификации по уровням
        level_qualifications = {}
        for partner_id in structure.partners:
            level = self._get_partner_level(structure, partner_id)
            qual = structure.partners[partner_id].qualification
            
            if level not in level_qualifications:
                level_qualifications[level] = {}
            if qual not in level_qualifications[level]:
                level_qualifications[level][qual] = 0
            level_qualifications[level][qual] += 1
            
        # Проверяем дисбаланс
        for level, quals in level_qualifications.items():
            total = sum(quals.values())
            for qual, count in quals.items():
                ratio = count / total
                if self._is_qualification_ratio_suspicious(qual, ratio, level):
                    imbalances.append({
                        'level': level,
                        'qualification': qual,
                        'ratio': ratio,
                        'count': count
                    })
                    
        return imbalances
        
    def _find_isolated_groups(self, structure: NetworkStructure) -> List[Dict]:
        """Поиск изолированных групп партнеров"""
        isolated_groups = []
        visited = set()
        
        def dfs(partner_id, group):
            visited.add(partner_id)
            group.append(partner_id)
            partner = structure.partners[partner_id]
            
            for downline_id in partner.downline_ids:
                if downline_id not in visited:
                    dfs(downline_id, group)
                    
        # Ищем изолированные группы
        for partner_id in structure.partners:
            if partner_id not in visited:
                group = []
                dfs(partner_id, group)
                
                if len(group) >= 3:  # Минимальный размер группы
                    group_volume = sum(
                        structure.partners[pid].pv
                        for pid in group
                    )
                    
                    # Проверяем изолированность
                    if self._is_group_isolated(structure, group):
                        isolated_groups.append({
                            'partners': group,
                            'volume': group_volume,
                            'size': len(group)
                        })
                        
        return isolated_groups
        
    def _get_qualification_chain(self, structure: NetworkStructure, partner_id: int) -> List[str]:
        """Получение цепочки квалификаций от партнера до корня"""
        chain = []
        current_id = partner_id
        
        while current_id is not None:
            partner = structure.partners[current_id]
            chain.append(partner.qualification)
            current_id = partner.upline_id
            
        return chain
        
    def _check_chain_anomaly(self, chain: List[str]) -> Optional[str]:
        """Проверка аномалий в цепочке квалификаций"""
        if not chain:
            return None
            
        # Проверяем инверсию квалификаций
        qual_ranks = {
            'NONE': 0, 'M1': 1, 'M2': 2, 'M3': 3,
            'B1': 4, 'B2': 5, 'B3': 6,
            'TOP1': 7, 'TOP2': 8, 'TOP3': 9,
            'TOP4': 10, 'TOP5': 11, 'TOP': 12
        }
        
        # Пропускаем неизвестные квалификации
        if chain[0] not in qual_ranks:
            return None
            
        prev_rank = qual_ranks[chain[0]]
        inversions = 0
        
        for qual in chain[1:]:
            if qual not in qual_ranks:
                continue
                
            current_rank = qual_ranks[qual]
            if current_rank > prev_rank + 2:  # Слишком резкий скачок
                return 'sharp_increase'
            elif current_rank < prev_rank - 1:  # Инверсия
                inversions += 1
            prev_rank = current_rank
            
        if inversions > 1:
            return 'multiple_inversions'
            
        return None
        
    def _calculate_level_volumes(self, structure: NetworkStructure) -> Dict[int, float]:
        """Расчет объемов по уровням структуры"""
        level_volumes = {}
        
        for partner_id in structure.partners:
            level = self._get_partner_level(structure, partner_id)
            if level not in level_volumes:
                level_volumes[level] = 0
            level_volumes[level] += structure.partners[partner_id].pv
            
        return level_volumes
        
    def _check_level_anomaly(self, level: int, volume: float, 
                            level_volumes: Dict[int, float]) -> Optional[str]:
        """Проверка аномалий в объемах уровня"""
        if level == 0:  # Корневой уровень
            return None
            
        prev_volume = level_volumes.get(level - 1, 0)
        if prev_volume == 0:
            return None
            
        ratio = volume / prev_volume
        
        if ratio > 3:
            return 'volume_spike'
        elif ratio < 0.2:
            return 'volume_drop'
            
        return None
        
    def _analyze_growth_patterns(self, structure: NetworkStructure) -> Dict:
        """Анализ паттернов роста структуры"""
        issues = []
        suspicious = False
        
        # Анализируем историю изменений для каждого партнера
        for partner in structure.partners.values():
            if partner.volume_history:
                growth_anomaly = self._check_growth_anomaly(partner.volume_history)
                if growth_anomaly:
                    suspicious = True
                    issues.append({
                        'type': 'growth_anomaly',
                        'partner_id': partner.id,
                        'anomaly': growth_anomaly
                    })
                    
        return {
            'suspicious': suspicious,
            'issues': issues
        }
        
    def _check_seasonality(self, structure: NetworkStructure) -> Dict:
        """Проверка сезонности в структуре"""
        issues = []
        suspicious = False
        
        # Группируем объемы по месяцам
        monthly_volumes = self._get_monthly_volumes(structure)
        
        # Проверяем сезонные аномалии
        if anomalies := self._find_seasonal_anomalies(monthly_volumes):
            suspicious = True
            issues.extend(anomalies)
            
        return {
            'suspicious': suspicious,
            'issues': issues
        }
        
    def _get_partner_level(self, structure: NetworkStructure, partner_id: int) -> int:
        """Получение уровня партнера в структуре"""
        level = 0
        current_id = structure.partners[partner_id].upline_id
        
        while current_id is not None:
            level += 1
            current_id = structure.partners[current_id].upline_id
            
        return level
        
    def _is_qualification_ratio_suspicious(self, qual: str, ratio: float, level: int) -> bool:
        """Проверка подозрительности соотношения квалификаций"""
        if level == 0:
            return False
            
        # Определяем ожидаемые соотношения для разных уровней
        expected_ratios = {
            'NONE': {1: 0.4, 2: 0.5, 3: 0.6},
            'M1': {1: 0.3, 2: 0.3, 3: 0.2},
            'M2': {1: 0.2, 2: 0.1, 3: 0.1},
            'M3': {1: 0.1, 2: 0.1, 3: 0.1},
            'B1': {2: 0.2, 3: 0.15},
            'B2': {3: 0.1},
            'B3': {3: 0.05}
        }
        
        if qual in expected_ratios and level in expected_ratios[qual]:
            return ratio > expected_ratios[qual][level] * 1.5
            
        return False
        
    def _is_group_isolated(self, structure: NetworkStructure, group: List[int]) -> bool:
        """Проверка изолированности группы партнеров"""
        total_volume = sum(structure.partners[pid].pv for pid in group)
        
        # Проверяем связи с остальной структурой
        connections = 0
        for pid in group:
            partner = structure.partners[pid]
            
            # Проверяем аплайна
            if partner.upline_id and partner.upline_id not in group:
                connections += 1
                
            # Проверяем даунлайн
            for downline_id in partner.downline_ids:
                if downline_id not in group:
                    connections += 1
                    
        # Группа считается изолированной, если мало связей с остальной структурой
        return connections <= 1 and total_volume >= self.min_partner_pv * len(group)
        
    def _check_growth_anomaly(self, volume_history: List[Tuple[datetime, float]]) -> Optional[str]:
        """Проверка аномалий в росте объемов"""
        if not volume_history or len(volume_history) < 3:
            return None
            
        # Извлекаем объемы, учитывая разные форматы данных
        volumes = []
        for record in volume_history:
            if isinstance(record, tuple) and len(record) == 2:
                _, vol = record
                volumes.append(vol)
            elif isinstance(record, (int, float)):
                volumes.append(record)
                
        if len(volumes) < 3:
            return None
            
        growth_rates = []
        for i in range(len(volumes)-1):
            if volumes[i] > 0:
                growth_rates.append((volumes[i+1] - volumes[i]) / volumes[i])
            else:
                growth_rates.append(0)
        
        # Проверяем различные аномалии
        if any(rate > 5.0 for rate in growth_rates):
            return 'explosive_growth'
        elif all(rate < -0.3 for rate in growth_rates):
            return 'consistent_decline'
        elif any(abs(growth_rates[i] - growth_rates[i-1]) > 2.0 
                for i in range(1, len(growth_rates))):
            return 'erratic_changes'
            
        return None
        
    def _get_monthly_volumes(self, structure: NetworkStructure) -> Dict[str, float]:
        """Получение объемов по месяцам"""
        monthly_volumes = {}
        current_date = datetime.now()
        
        for partner in structure.partners.values():
            if not partner.volume_history:
                continue
                
            for record in partner.volume_history:
                # Обработка разных форматов данных
                if isinstance(record, tuple) and len(record) == 2:
                    date, volume = record
                elif isinstance(record, (int, float)):
                    date = current_date
                    volume = record
                else:
                    continue
                    
                month_key = date.strftime('%Y-%m')
                if month_key not in monthly_volumes:
                    monthly_volumes[month_key] = 0
                monthly_volumes[month_key] += volume
                
        return monthly_volumes
        
    def _find_seasonal_anomalies(self, monthly_volumes: Dict[str, float]) -> List[Dict]:
        """Поиск сезонных аномалий"""
        anomalies = []
        
        if len(monthly_volumes) < 6:  # Нужно минимум полгода данных
            return anomalies
            
        # Рассчитываем среднее и отклонение
        volumes = list(monthly_volumes.values())
        avg_volume = sum(volumes) / len(volumes)
        std_dev = (sum((v - avg_volume) ** 2 for v in volumes) / len(volumes)) ** 0.5
        
        # Ищем аномальные месяцы
        for month, volume in monthly_volumes.items():
            if abs(volume - avg_volume) > 2 * std_dev:
                anomalies.append({
                    'type': 'seasonal_anomaly',
                    'month': month,
                    'volume': volume,
                    'deviation': (volume - avg_volume) / std_dev
                })
                
        return anomalies
        
    def _get_nonstandard_recommendations(self, issues: List[Dict]) -> List[Dict]:
        """Генерация рекомендаций по устранению нестандартных конфигураций"""
        recommendations = set()  # Используем множество для уникальных рекомендаций
        
        # Группируем проблемы по типам
        issue_types = {}
        for issue in issues:
            issue_type = issue['type']
            if issue_type not in issue_types:
                issue_types[issue_type] = []
            issue_types[issue_type].append(issue)
        
        # Генерируем рекомендации для каждого типа проблем
        for issue_type, type_issues in issue_types.items():
            if issue_type == 'empty_branches':
                recommendations.add((
                    2,  # priority
                    'Оптимизировать пустые ветки структуры',
                    'Перераспределить объемы для повышения эффективности',
                    f'Найдено пустых веток: {len(type_issues)}'
                ))
            elif issue_type == 'unbalanced_qualifications':
                recommendations.add((
                    1,  # priority
                    'Сбалансировать распределение квалификаций',
                    'Разработать план развития для выравнивания структуры',
                    f'Обнаружено несбалансированных квалификаций: {len(type_issues)}'
                ))
            elif issue_type == 'isolated_groups':
                recommendations.add((
                    1,  # priority
                    'Интегрировать изолированные группы',
                    'Усилить взаимодействие между группами партнеров',
                    f'Найдено изолированных групп: {len(type_issues)}'
                ))
            elif issue_type == 'qualification_chain_anomaly':
                recommendations.add((
                    2,  # priority
                    'Оптимизировать цепочки квалификаций',
                    'Обеспечить более плавное развитие квалификаций',
                    f'Выявлено аномальных цепочек: {len(type_issues)}'
                ))
            elif issue_type == 'growth_anomaly':
                recommendations.add((
                    1,  # priority
                    'Стабилизировать рост структуры',
                    'Внедрить механизмы контроля темпов роста',
                    f'Обнаружено аномалий роста: {len(type_issues)}'
                ))
        
        # Преобразуем кортежи в словари и сортируем по приоритету
        return [
            {
                'priority': priority,
                'description': description,
                'details': details,
                'summary': summary
            }
            for priority, description, details, summary in sorted(recommendations)
        ]

    def _get_level_metrics(self, structure: NetworkStructure, level: int) -> Dict:
        """Детальный анализ уровня структуры"""
        partners = [p for p in structure.partners.values() 
                   if self._get_partner_level(structure, p.id) == level]
        
        return {
            'total_partners': len(partners),
            'pv_distribution': {
                '70_pv': sum(1 for p in partners if p.pv >= 70),
                '200_pv': sum(1 for p in partners if p.pv >= 200)
            },
            'qualifications': {
                qual: sum(1 for p in partners if p.qualification == qual)
                for qual in QUALIFICATIONS
            },
            'total_pv': sum(p.pv for p in partners),
            'avg_pv': sum(p.pv for p in partners) / len(partners) if partners else 0,
            'total_group_volume': sum(
                structure.calculate_group_volume(p.id) for p in partners
            ),
            'total_payout': sum(
                structure.calculate_income(p.id)['total'] for p in partners
            )
        }

    def analyze_level_progression(self, structure: NetworkStructure) -> Dict:
        """Анализ прогрессии по уровням"""
        max_level = max(
            self._get_partner_level(structure, p_id)
            for p_id in structure.partners
        )
        
        level_analysis = {}
        total_payout_progression = []
        current_payout = 0
        
        for level in range(max_level + 1):
            metrics = self._get_level_metrics(structure, level)
            current_payout += metrics['total_payout']
            total_payout_progression.append(current_payout)
            
            level_analysis[f'level_{level}'] = {
                'metrics': metrics,
                'cumulative_payout': current_payout,
                'payout_increase': current_payout - (total_payout_progression[-2] if level > 0 else 0)
            }
        
        return {
            'level_details': level_analysis,
            'payout_progression': total_payout_progression,
            'total_levels': max_level + 1
        }

    def _build_m3_structure(self, structure: NetworkStructure, upline_id: int):
        """Build minimal M3 structure"""
        # Add 4 active partners with optimal PV distribution
        partner_pvs = [800, 800, 700, 700]  # Total 3000 PV
        
        for pv in partner_pvs:
            structure.add_partner(pv, upline_id)
        
    def _build_b3_structure(self, structure: NetworkStructure, upline_id: int):
        """Build minimal B3 structure"""
        # Add 3 M3 partners and additional partners for side volume
        m3_pvs = [2500, 2500, 2000]  # Main branches
        side_pvs = [1000, 1000]      # Side volume
        
        # Create M3 partners
        for pv in m3_pvs:
            m3_id = structure.add_partner(pv, upline_id)
            # Add subpartners to achieve M3
            self._build_minimal_structure(structure, m3_id, 'M3')
        
        # Add partners for side volume
        for pv in side_pvs:
            structure.add_partner(pv, upline_id)
        
    def _build_minimal_structure(self, structure: NetworkStructure, upline_id: int, target_qual: str):
        """Build minimal structure for given qualification"""
        requirements = QUALIFICATIONS[target_qual]
        remaining_pv = requirements['min_go']
        min_partners = requirements['min_partners']
        
        # Distribute PV among minimum required partners
        pv_per_partner = remaining_pv / min_partners
        for _ in range(min_partners):
            structure.add_partner(pv_per_partner, upline_id)

class ScenarioAnalyzer:
    def __init__(self):
        self.optimal_personal_pv = 200
        
    def generate_scenarios(self, total_pv: float) -> List[Dict]:
        """
        Генерирует различные сценарии распределения PV
        Args:
            total_pv: Общий объем PV для распределения
        Returns:
            List[Dict]: Список сценариев с их метриками
        """
        scenarios = []
        
        # Сценарий 1: Все PV в личных продажах
        structure1 = NetworkStructure(total_pv)
        structure1.partners[structure1.root_id].pv = total_pv
        scenarios.append({
            'name': 'Все PV в личных продажах',
            'structure': structure1,
            'metrics': self.analyze_scenario(structure1)
        })
        
        # Сценарий 2: Равномерное распределение между партнерами
        structure2 = NetworkStructure(total_pv)
        optimal_partners = max(1, int(total_pv / self.optimal_personal_pv))
        pv_per_partner = total_pv / (optimal_partners + 1)  # +1 для учета корневого партнера
        structure2.partners[structure2.root_id].pv = pv_per_partner
        for _ in range(optimal_partners):
            structure2.add_partner(pv_per_partner, structure2.root_id)
        scenarios.append({
            'name': 'Равномерное распределение между партнерами',
            'structure': structure2,
            'metrics': self.analyze_scenario(structure2)
        })
        
        # Сценарий 3: Формирование квалификации M3
        if total_pv >= 3000:  # Минимальный GO для M3
            structure3 = NetworkStructure(total_pv)
            structure3.partners[structure3.root_id].pv = self.optimal_personal_pv
            remaining_pv = total_pv - self.optimal_personal_pv
            self._build_qualification_structure(structure3, structure3.root_id, 'M3', remaining_pv)
            scenarios.append({
                'name': 'Формирование квалификации M3',
                'structure': structure3,
                'metrics': self.analyze_scenario(structure3)
            })
        
        # Сценарий 4: Формирование квалификации B3
        if total_pv >= 10000:  # Минимальный GO для B3
            structure4 = NetworkStructure(total_pv)
            structure4.partners[structure4.root_id].pv = self.optimal_personal_pv
            remaining_pv = total_pv - self.optimal_personal_pv
            self._build_qualification_structure(structure4, structure4.root_id, 'B3', remaining_pv)
            scenarios.append({
                'name': 'Формирование квалификации B3',
                'structure': structure4,
                'metrics': self.analyze_scenario(structure4)
            })
        
        # Сценарий 5: Формирование квалификации TOP
        if total_pv >= 16000:  # Минимальный GO для TOP
            structure5 = NetworkStructure(total_pv)
            structure5.partners[structure5.root_id].pv = self.optimal_personal_pv
            remaining_pv = total_pv - self.optimal_personal_pv
            self._build_qualification_structure(structure5, structure5.root_id, 'TOP', remaining_pv)
            scenarios.append({
                'name': 'Формирование квалификации TOP',
                'structure': structure5,
                'metrics': self.analyze_scenario(structure5)
            })
        
        # Сортируем сценарии по общей эффективности
        for scenario in scenarios:
            metrics = scenario['metrics']
            # Рассчитываем общий скор на основе дохода и рисков
            total_score = (metrics['efficiency'] * 0.7 + (1 - metrics['risk_score']) * 0.3)
            metrics['total_score'] = total_score
            
        scenarios.sort(key=lambda x: x['metrics']['total_score'], reverse=True)
        return scenarios

    def analyze_scenario(self, structure: NetworkStructure) -> Dict:
        """
        Анализирует конкретный сценарий распределения PV
        Args:
            structure: Структура сети для анализа
        Returns:
            Dict: Метрики сценария
        """
        structure.update_qualifications()
        root_partner = structure.partners[structure.root_id]
        
        # Расчет личного бонуса (LO)
        personal_bonus = 0
        if root_partner.pv >= 70:  # Базовый уровень активности
            personal_bonus = root_partner.pv * 0.05  # 5% от личных продаж
        if root_partner.pv >= 200:  # Повышенный коэффициент
            personal_bonus = root_partner.pv * 0.10  # 10% от личных продаж
            
        # Расчет партнерского бонуса (PB)
        partner_bonus = 0
        active_partners = len([p for p in structure.partners.values() 
                             if p.upline_id == structure.root_id and p.pv >= 70])
        
        # Премиальные выплаты за количество активных партнеров
        if active_partners >= 15:
            partner_bonus += 500
        elif active_partners >= 12:
            partner_bonus += 400
        elif active_partners >= 9:
            partner_bonus += 300
        elif active_partners >= 7:
            partner_bonus += 200
        elif active_partners >= 5:
            partner_bonus += 100
            
        # Расчет группового бонуса (GO)
        group_bonus = 0
        group_volume = structure.calculate_group_volume(structure.root_id)
        qualification = root_partner.qualification
        
        # Процент от общего объема структуры в зависимости от квалификации
        go_bonus_rates = {
            'M1': 0.05, 'M2': 0.10, 'M3': 0.15,
            'B1': 0.20, 'B2': 0.25, 'B3': 0.30,
            'TOP': 0.35, 'TOP1': 0.37, 'TOP2': 0.39,
            'TOP3': 0.41, 'TOP4': 0.43, 'TOP5': 0.45,
            'AC1': 0.47, 'AC2': 0.49, 'AC3': 0.51,
            'AC4': 0.53, 'AC5': 0.55, 'AC6': 0.57
        }
        
        if qualification in go_bonus_rates:
            group_bonus = group_volume * go_bonus_rates[qualification]
            
        # Расчет клубных бонусов
        club_bonus = 0
        if qualification in ['M3', 'B1', 'B2', 'B3', 'TOP']:
            if qualification == 'M3':
                club_bonus = group_volume * 0.02  # +2% от GO при M3
            elif qualification in ['B1', 'B2', 'B3']:
                club_bonus = group_volume * 0.04  # +4% от GO при B1 и выше
                if qualification == 'B1':
                    club_bonus += group_volume * 0.01  # +1% Travel Club
            elif qualification == 'B3':
                club_bonus += group_volume * 0.01  # +1% TOP Club
                
        total_income = personal_bonus + partner_bonus + group_bonus + club_bonus
        
        metrics = {
            'total_income': total_income,
            'personal_bonus': personal_bonus,
            'partner_bonus': partner_bonus,
            'group_bonus': group_bonus,
            'club_bonus': club_bonus,
            'qualification': qualification,
            'active_partners': active_partners,
            'group_volume': group_volume,
            'side_volume': structure.calculate_side_volume(structure.root_id),
            'efficiency': total_income / structure.total_pv,
            'risk_score': self._calculate_risk_score(structure)
        }
        
        return metrics
        
    def _calculate_risk_score(self, structure: NetworkStructure) -> float:
        """
        Рассчитывает оценку риска для данной структуры
        Args:
            structure: Структура сети
        Returns:
            float: Оценка риска от 0 до 1
        """
        risks = []
        
        # Риск 1: Слишком много PV в одной ветке
        max_branch_volume = max(
            structure.calculate_group_volume(pid) 
            for pid in structure.partners[structure.root_id].downline_ids
        ) if structure.partners[structure.root_id].downline_ids else 0
        
        total_volume = structure.calculate_group_volume(structure.root_id)
        volume_concentration = max_branch_volume / total_volume if total_volume > 0 else 0
        risks.append(volume_concentration * 0.3)  # Вес риска концентрации объема
        
        # Риск 2: Малое количество активных партнеров
        active_partners = structure.calculate_active_partners(structure.root_id)
        min_recommended = 5  # Минимальное рекомендуемое количество партнеров
        partner_risk = max(0, 1 - active_partners / min_recommended)
        risks.append(partner_risk * 0.2)  # Вес риска малого количества партнеров
        
        # Риск 3: Нестабильность квалификации
        qual = structure.partners[structure.root_id].qualification
        qual_requirements = QUALIFICATIONS.get(qual, {})
        required_go = qual_requirements.get('go', 0)
        current_go = structure.calculate_group_volume(structure.root_id)
        
        qualification_stability = (
            1 - (current_go - required_go) / required_go 
            if required_go > 0 else 0
        )
        risks.append(qualification_stability * 0.5)  # Вес риска нестабильности квалификации
        
        return sum(risks)

    def _build_qualification_structure(self, structure: NetworkStructure, 
                                    upline_id: int, target_qual: str, 
                                    remaining_pv: float) -> None:
        """
        Строит структуру для достижения целевой квалификации
        Args:
            structure: Структура сети
            upline_id: ID вышестоящего партнера
            target_qual: Целевая квалификация
            remaining_pv: Оставшийся объем для распределения
        """
        # Получаем требования для квалификации из reward_plan.md
        if target_qual == 'M3':
            # M3 требует:
            # GO: 3,000 PV
            # Активных партнеров: 4
            required_go = 3000
            required_partners = 4
            pv_per_partner = 750  # Распределяем GO равномерно
            
            for _ in range(required_partners):
                if remaining_pv >= pv_per_partner:
                    structure.add_partner(pv_per_partner, upline_id)
                    remaining_pv -= pv_per_partner
                    
        elif target_qual == 'B3':
            # B3 требует:
            # GO: 10,000 PV
            # Боковой объем: 1,000 PV
            # Активных партнеров: 7
            # M3 в структуре: 3
            required_go = 10000
            required_side_volume = 1000
            required_partners = 7
            required_m3 = 3
            
            # Сначала добавляем партнеров для бокового объема
            side_partners = 2  # Минимум 2 партнера для бокового объема
            side_pv = required_side_volume / side_partners
            for _ in range(side_partners):
                if remaining_pv >= side_pv:
                    structure.add_partner(side_pv, upline_id)
                    remaining_pv -= side_pv
            
            # Затем добавляем M3 партнеров
            m3_pv = (required_go - required_side_volume) / required_m3
            for _ in range(required_m3):
                if remaining_pv >= m3_pv:
                    partner_id = structure.add_partner(self.optimal_personal_pv, upline_id)
                    remaining_pv -= self.optimal_personal_pv
                    # Рекурсивно строим M3 структуру
                    self._build_qualification_structure(structure, partner_id, 'M3', 
                                                     m3_pv - self.optimal_personal_pv)
            
            # Добавляем оставшихся активных партнеров
            remaining_partners = required_partners - side_partners - required_m3
            if remaining_partners > 0:
                pv_per_partner = remaining_pv / remaining_partners
                for _ in range(remaining_partners):
                    if remaining_pv >= pv_per_partner:
                        structure.add_partner(pv_per_partner, upline_id)
                        remaining_pv -= pv_per_partner
                        
        elif target_qual == 'TOP':
            # TOP требует:
            # GO: 16,000 PV
            # Боковой объем: 1,000 PV
            # Активных партнеров: 8
            # M3 в структуре: 5
            required_go = 16000
            required_side_volume = 1000
            required_partners = 8
            required_m3 = 5
            
            # Сначала добавляем партнеров для бокового объема
            side_partners = 2
            side_pv = required_side_volume / side_partners
            for _ in range(side_partners):
                if remaining_pv >= side_pv:
                    structure.add_partner(side_pv, upline_id)
                    remaining_pv -= side_pv
            
            # Затем добавляем M3 партнеров
            m3_pv = (required_go - required_side_volume) / required_m3
            for _ in range(required_m3):
                if remaining_pv >= m3_pv:
                    partner_id = structure.add_partner(self.optimal_personal_pv, upline_id)
                    remaining_pv -= self.optimal_personal_pv
                    # Рекурсивно строим M3 структуру
                    self._build_qualification_structure(structure, partner_id, 'M3', 
                                                     m3_pv - self.optimal_personal_pv)
            
            # Добавляем оставшихся активных партнеров
            remaining_partners = required_partners - side_partners - required_m3
            if remaining_partners > 0:
                pv_per_partner = remaining_pv / remaining_partners
                for _ in range(remaining_partners):
                    if remaining_pv >= pv_per_partner:
                        structure.add_partner(pv_per_partner, upline_id)
                        remaining_pv -= pv_per_partner

    # ... rest of the existing code ... 