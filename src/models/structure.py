import networkx as nx
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from utils.constants import (
    QUALIFICATIONS, BONUS_RATES, COMPRESSION_THRESHOLD,
    DYNAMIC_GO_BONUS_RATES, MENTORSHIP_BONUSES,
    DYNAMICS_CALCULATION_PERIODS, QUALIFICATION_MAINTENANCE_PERIODS,
    STARTER_KITS, STARTER_KIT_PRIVILEGES, QUICK_START_BONUSES,
    CLUB_LEVELS, CLUB_BENEFITS, CLUB_EVENTS,
    REGIONS, COMPRESSION_RULES, COMPRESSION_WARNINGS, RECOVERY_CONDITIONS,
    CURRENCY_RATES
)

class Partner:
    def __init__(self, id: int, pv: float = 0, region: str = 'RU'):
        self.id = id
        self.pv = pv
        self.qualification = 'NONE'
        self.active = True
        self.upline_id = None
        self.downline_ids = []
        
        # Региональные настройки
        self.region = region
        self.region_settings = REGIONS[region]
        self.currency = self.region_settings['currency']
        
        # История объемов и квалификаций
        self.volume_history = []  # [(datetime, pv, go), ...]
        self.qualification_history = []  # [(datetime, qualification), ...]
        self.mentorship_bonuses_received = set()  # Квалификации, за которые получен бонус
        
        # Стартовый набор и привилегии
        self.starter_kit = None
        self.privileges = set()
        self.privilege_expiry = {}  # Сроки действия привилегий
        self.quick_start_bonuses = {}  # Полученные быстрые бонусы
        
        # Клубная система
        self.club_memberships = set()  # Активные клубные членства
        self.club_history = []  # [(datetime, club_level), ...]
        self.attended_events = []  # [(datetime, event_name), ...]
        self.leadership_mentees = set()  # ID партнеров в программе лидерства
        
        # Компрессия
        self.compression_warnings = []
        self.compression_history = []
        self.recovery_status = None
        self.recovery_bonus_expiry = None
        self.last_compression_date = None
        self.warning_notifications = set()
        
    def add_volume_record(self, date: datetime, pv: float, go: float):
        """Добавить запись об объемах"""
        self.volume_history.append((date, pv, go))
        # Оставляем только последние 12 месяцев
        if len(self.volume_history) > 12:
            self.volume_history.pop(0)
            
    def add_qualification_record(self, date: datetime, qualification: str):
        """Добавить запись о квалификации"""
        self.qualification_history.append((date, qualification))
        # Оставляем только последние 12 месяцев
        if len(self.qualification_history) > 12:
            self.qualification_history.pop(0)
            
    def calculate_go_growth(self, months: int = 3) -> float:
        """Рассчитать рост GO за указанный период"""
        if len(self.volume_history) < months + 1:
            return 0.0
            
        current_go = self.volume_history[-1][2]  # Последний GO
        past_go = self.volume_history[-months-1][2]  # GO в начале периода
        
        if past_go == 0:
            return 0.0
            
        return (current_go - past_go) / past_go
        
    def get_dynamic_bonus_rate(self) -> float:
        """Получить ставку динамического бонуса"""
        growth = self.calculate_go_growth()
        bonus_rate = 0.0
        
        for threshold, rate in sorted(DYNAMIC_GO_BONUS_RATES.items()):
            if growth >= threshold:
                bonus_rate = rate
                
        return bonus_rate
        
    def calculate_mentorship_bonus(self, new_qualification: str) -> float:
        """Рассчитать бонус наставничества"""
        if (new_qualification in MENTORSHIP_BONUSES and 
            new_qualification not in self.mentorship_bonuses_received):
            self.mentorship_bonuses_received.add(new_qualification)
            return MENTORSHIP_BONUSES[new_qualification]
        return 0.0
        
    def get_qualification_maintenance_period(self, qualification: str) -> int:
        """Получить период поддержания квалификации в месяцах"""
        current_date = datetime.now()
        maintenance_period = 0
        
        for date, qual in reversed(self.qualification_history):
            if qual == qualification:
                maintenance_period += 1
            else:
                break
                
        return maintenance_period
        
    def get_compression_rule(self) -> dict:
        """Получить правила компрессии для региона"""
        if self.region in ['UZ', 'KG']:
            return COMPRESSION_RULES['SOFT']
        elif self.region in ['RU', 'KZ']:
            return COMPRESSION_RULES['STRICT']
        return COMPRESSION_RULES['STANDARD']
        
    def check_compression_status(self) -> tuple:
        """Проверить статус компрессии и вернуть (is_compressed, warning_level)"""
        current_date = datetime.now()
        rule = self.get_compression_rule()
        
        # Проверка периода восстановления
        if self.recovery_status:
            recovery_end = self.last_compression_date + timedelta(days=30*rule['recovery_period'])
            if current_date <= recovery_end:
                if self.pv >= rule['min_recovery_pv']:
                    self.recovery_status = None
                    return False, None
                    
        # Проверка порога компрессии
        if self.pv < self.region_settings['compression_threshold']:
            # Проверка льготного периода
            if self.last_compression_date:
                grace_end = self.last_compression_date + timedelta(days=30*self.region_settings['grace_period'])
                if current_date <= grace_end:
                    return False, 'NOTICE'
                    
            # Определение уровня предупреждения
            for level, warning in COMPRESSION_WARNINGS.items():
                if self.pv <= warning['threshold']:
                    if warning['notification_type'] not in self.warning_notifications:
                        self.warning_notifications.add(warning['notification_type'])
                        self.compression_warnings.append((current_date, level, warning['message']))
                    return True, level
                    
        self.warning_notifications.clear()
        return False, None
        
    def apply_compression(self) -> bool:
        """Применить компрессию к партнеру"""
        current_date = datetime.now()
        is_compressed, warning_level = self.check_compression_status()
        
        if is_compressed:
            self.last_compression_date = current_date
            self.compression_history.append((current_date, self.pv))
            self.recovery_status = 'GRADUAL'  # Начинаем с постепенного восстановления
            
            # Очистка старой истории
            year_ago = current_date - timedelta(days=365)
            self.compression_history = [(date, pv) for date, pv in self.compression_history 
                                     if date > year_ago]
            return True
            
        return False
        
    def try_recovery(self) -> bool:
        """Попытка восстановления после компрессии"""
        if not self.recovery_status:
            return False
            
        current_date = datetime.now()
        recovery_condition = RECOVERY_CONDITIONS[self.recovery_status]
        
        if self.pv >= recovery_condition['required_pv']:
            # Успешное восстановление
            self.recovery_bonus_expiry = current_date + timedelta(days=30*recovery_condition['period'])
            self.recovery_status = None
            return True
            
        return False
        
    def get_recovery_bonus_rate(self) -> float:
        """Получить бонусную ставку восстановления"""
        if not self.recovery_bonus_expiry:
            return 0.0
            
        current_date = datetime.now()
        if current_date <= self.recovery_bonus_expiry:
            recovery_type = self.recovery_status or 'GRADUAL'
            return RECOVERY_CONDITIONS[recovery_type]['bonus_rate']
            
        return 0.0
        
    def update_qualification(self, go: float, active_partners: int, side_volume: float = 0):
        """Обновить квалификацию партнера с учетом региональных особенностей"""
        current_date = datetime.now()
        old_qualification = self.qualification
        
        for qual, requirements in QUALIFICATIONS.items():
            # Применяем региональные корректировки
            adjusted_requirements = requirements.copy()
            if qual in self.region_settings.get('qualification_adjustments', {}):
                adjusted_requirements.update(
                    self.region_settings['qualification_adjustments'][qual]
                )
                
            if (go >= adjusted_requirements['min_go'] and
                active_partners >= adjusted_requirements['min_partners'] and
                side_volume >= adjusted_requirements['side_volume']):
                self.qualification = qual
                
        # Если квалификация изменилась, добавляем запись в историю
        if old_qualification != self.qualification:
            self.add_qualification_record(current_date, self.qualification)
            
    def is_compressed(self) -> bool:
        """Проверить, подлежит ли партнер компрессии"""
        return self.pv < COMPRESSION_THRESHOLD
        
    def purchase_starter_kit(self, kit_type: str) -> bool:
        """Покупка стартового набора"""
        if kit_type not in STARTER_KITS or self.starter_kit is not None:
            return False
            
        kit = STARTER_KITS[kit_type]
        self.starter_kit = kit_type
        self.pv += kit['pv']
        
        # Активация привилегий
        current_date = datetime.now()
        for privilege in kit['privileges']:
            self.privileges.add(privilege)
            if privilege in STARTER_KIT_PRIVILEGES:
                priv_info = STARTER_KIT_PRIVILEGES[privilege]
                if 'duration' in priv_info:
                    expiry = current_date + timedelta(days=priv_info['duration'])
                    self.privilege_expiry[privilege] = expiry
                    
        return True
        
    def has_privilege(self, privilege: str) -> bool:
        """Проверка наличия и актуальности привилегии"""
        if privilege not in self.privileges:
            return False
            
        if privilege in self.privilege_expiry:
            current_date = datetime.now()
            if current_date > self.privilege_expiry[privilege]:
                self.privileges.remove(privilege)
                del self.privilege_expiry[privilege]
                return False
                
        return True
        
    def get_discount(self) -> float:
        """Получить текущую скидку партнера"""
        if self.has_privilege('personal_discount'):
            return STARTER_KIT_PRIVILEGES['personal_discount']['value']
        return 0.0
        
    def get_quick_start_bonus(self) -> float:
        """Расчет бонуса быстрого старта"""
        current_date = datetime.now()
        registration_date = self.qualification_history[0][0] if self.qualification_history else current_date
        months_active = (current_date - registration_date).days // 30
        
        total_bonus = 0
        for qual, bonus_info in QUICK_START_BONUSES.items():
            if (qual not in self.quick_start_bonuses and 
                months_active <= bonus_info['period'] and 
                self.qualification >= qual):
                total_bonus += bonus_info['bonus']
                self.quick_start_bonuses[qual] = current_date
                
        return total_bonus
        
    def get_club_level(self) -> str:
        """Получить текущий клубный уровень"""
        for level, requirements in CLUB_LEVELS.items():
            if (self.qualification >= requirements['qualification'] and
                self.get_qualification_maintenance_period(requirements['qualification']) >= 
                requirements['maintenance_period']):
                return level
        return None
        
    def update_club_membership(self):
        """Обновить клубное членство"""
        current_date = datetime.now()
        new_level = self.get_club_level()
        
        if new_level and new_level not in self.club_memberships:
            self.club_memberships.add(new_level)
            self.club_history.append((current_date, new_level))
            
            # Очистка истории старше года
            year_ago = current_date - timedelta(days=365)
            self.club_history = [(date, level) for date, level in self.club_history 
                               if date > year_ago]
                               
    def get_club_benefits(self) -> list:
        """Получить список активных клубных привилегий"""
        benefits = []
        for club in self.club_memberships:
            benefits.extend(CLUB_LEVELS[club]['benefits'])
        return list(set(benefits))  # Убираем дубликаты
        
    def get_event_discount(self, event_level: str) -> float:
        """Получить скидку на мероприятие определенного уровня"""
        if event_level in self.club_memberships:
            benefit_key = f"{event_level.lower()}_events"
            if benefit_key in CLUB_BENEFITS:
                return CLUB_BENEFITS[benefit_key]['discount']
        return 0.0
        
    def can_attend_event(self, event_level: str) -> bool:
        """Проверить возможность посещения мероприятия"""
        return event_level in self.club_memberships
        
    def attend_event(self, event_name: str, date: datetime):
        """Зарегистрировать посещение мероприятия"""
        self.attended_events.append((date, event_name))
        
        # Очистка истории старше года
        year_ago = date - timedelta(days=365)
        self.attended_events = [(d, e) for d, e in self.attended_events 
                              if d > year_ago]
                              
    def get_club_bonus_rate(self) -> float:
        """Рассчитать дополнительную ставку клубного бонуса"""
        total_rate = 0.0
        benefits = self.get_club_benefits()
        
        for benefit in benefits:
            if benefit in CLUB_BENEFITS and 'rate' in CLUB_BENEFITS[benefit]:
                # Проверяем дополнительные условия для бонуса
                if benefit == 'travel_bonus':
                    if self.calculate_group_volume() >= CLUB_BENEFITS[benefit]['min_go']:
                        total_rate += CLUB_BENEFITS[benefit]['rate']
                else:
                    total_rate += CLUB_BENEFITS[benefit]['rate']
                    
        return total_rate
        
    def get_leadership_bonus(self) -> float:
        """Рассчитать бонус программы лидерства"""
        if 'leadership_program' not in self.get_club_benefits():
            return 0.0
            
        return len(self.leadership_mentees) * CLUB_BENEFITS['leadership_program']['mentoring_bonus']
        
    def add_leadership_mentee(self, mentee_id: int):
        """Добавить партнера в программу лидерства"""
        if 'leadership_program' in self.get_club_benefits():
            self.leadership_mentees.add(mentee_id)
            
    def remove_leadership_mentee(self, mentee_id: int):
        """Удалить партнера из программы лидерства"""
        self.leadership_mentees.discard(mentee_id)

    def calculate_income(self) -> Dict[str, float]:
        """Рассчитать доход с учетом региональных особенностей и бонусов восстановления"""
        income = super().calculate_income()
        
        # Применяем бонус восстановления
        recovery_bonus_rate = self.get_recovery_bonus_rate()
        if recovery_bonus_rate > 0:
            recovery_bonus = income['total'] * recovery_bonus_rate
            income['recovery_bonus'] = recovery_bonus
            income['total'] += recovery_bonus
            
        # Конвертируем в местную валюту
        currency_rate = CURRENCY_RATES[self.currency]
        for key in income:
            income[key] *= currency_rate
            
        return income

class NetworkSnapshot:
    """Снимок состояния сети на определенном этапе"""
    def __init__(self, stage_name: str, metrics: Dict, partners_state: Dict):
        self.stage_name = str(stage_name)  # Убеждаемся, что имя этапа - строка
        self.metrics = metrics
        self.partners_state = partners_state
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict:
        return {
            'stage_name': str(self.stage_name),  # Убеждаемся, что возвращаем строку
            'metrics': self.metrics,
            'partners_state': self.partners_state,
            'timestamp': self.timestamp.isoformat()
        }

class NetworkStructure:
    def __init__(self, total_pv: float):
        self.total_pv = total_pv
        self.partners: Dict[int, Partner] = {}
        self.network = nx.DiGraph()
        self.next_id = 0
        self.current_date = datetime.now()
        self.history: List[NetworkSnapshot] = []  # История изменений сети
        
        # Initialize root partner
        self.root_id = self.add_partner(200)  # Optimal personal PV
        
    def add_partner(self, pv: float, upline_id: Optional[int] = None) -> int:
        partner = Partner(self.next_id, pv)
        self.partners[self.next_id] = partner
        self.network.add_node(self.next_id, pv=pv)
        
        if upline_id is not None:
            self.partners[upline_id].downline_ids.append(self.next_id)
            partner.upline_id = upline_id
            self.network.add_edge(upline_id, self.next_id)
            
        self.next_id += 1
        return partner.id
        
    def calculate_group_volume(self, partner_id: int) -> float:
        partner = self.partners[partner_id]
        total_volume = partner.pv
        
        for downline_id in partner.downline_ids:
            if not self.partners[downline_id].is_compressed():
                total_volume += self.calculate_group_volume(downline_id)
                
        return total_volume
        
    def calculate_side_volume(self, partner_id: int) -> float:
        partner = self.partners[partner_id]
        volumes = []
        
        for downline_id in partner.downline_ids:
            volumes.append(self.calculate_group_volume(downline_id))
            
        if not volumes:
            return 0
            
        return sum(volumes) - max(volumes)  # Total volume minus largest branch
        
    def calculate_active_partners(self, partner_id: int) -> int:
        partner = self.partners[partner_id]
        count = 1 if partner.active else 0
        
        for downline_id in partner.downline_ids:
            if not self.partners[downline_id].is_compressed():
                count += self.calculate_active_partners(downline_id)
                
        return count
        
    def update_qualifications(self):
        """Update qualifications for all partners based on current structure"""
        for partner_id in self.partners:
            partner = self.partners[partner_id]
            go = self.calculate_group_volume(partner_id)
            active_partners = self.calculate_active_partners(partner_id)
            side_volume = self.calculate_side_volume(partner_id)
            
            # Добавляем запись об объемах
            partner.add_volume_record(self.current_date, partner.pv, go)
            
            # Обновляем квалификацию
            partner.update_qualification(go, active_partners, side_volume)
            
    def calculate_income(self, partner_id: int) -> Dict[str, float]:
        """Calculate total income for a partner including all bonus types"""
        partner = self.partners[partner_id]
        go = self.calculate_group_volume(partner_id)
        
        # Personal bonus
        if partner.pv >= 200:
            personal_bonus = partner.pv * BONUS_RATES['PERSONAL'][200]
        elif partner.pv >= 70:
            personal_bonus = partner.pv * BONUS_RATES['PERSONAL'][70]
        else:
            personal_bonus = 0
            
        # Group bonus with dynamic rate
        base_group_rate = BONUS_RATES['GROUP'].get(partner.qualification, 0)
        dynamic_rate = partner.get_dynamic_bonus_rate()
        total_group_rate = base_group_rate + dynamic_rate
        group_bonus = go * total_group_rate
        
        # Club bonuses
        club_bonus = 0
        if partner.qualification in ['M3', 'B1', 'B2', 'B3']:
            maintenance_period = partner.get_qualification_maintenance_period(partner.qualification)
            
            if partner.qualification == 'M3' and maintenance_period >= QUALIFICATION_MAINTENANCE_PERIODS['M3']:
                club_bonus += go * BONUS_RATES['CLUB']['MIDDLE']
                
            if partner.qualification in ['B1', 'B2', 'B3'] and maintenance_period >= QUALIFICATION_MAINTENANCE_PERIODS['B1']:
                club_bonus += go * (BONUS_RATES['CLUB']['BUSINESS'] + 
                                  BONUS_RATES['CLUB']['TRAVEL'])
                
            if partner.qualification == 'B3' and maintenance_period >= QUALIFICATION_MAINTENANCE_PERIODS['B3']:
                club_bonus += go * BONUS_RATES['CLUB']['TOP']
                
        # Mentorship bonus (if qualification changed)
        mentorship_bonus = partner.calculate_mentorship_bonus(partner.qualification)
        
        # Инициализируем recovery_bonus
        recovery_bonus = 0.0
                
        # Применяем бонус восстановления
        recovery_bonus_rate = partner.get_recovery_bonus_rate()
        if recovery_bonus_rate > 0:
            recovery_bonus = (personal_bonus + group_bonus + club_bonus + mentorship_bonus) * recovery_bonus_rate
            personal_bonus += recovery_bonus
            group_bonus += recovery_bonus
            club_bonus += recovery_bonus
            mentorship_bonus += recovery_bonus
            
        # Конвертируем в местную валюту
        currency_rate = CURRENCY_RATES[partner.currency]
        personal_bonus *= currency_rate
        group_bonus *= currency_rate
        club_bonus *= currency_rate
        mentorship_bonus *= currency_rate
        recovery_bonus *= currency_rate
        dynamic_bonus = go * dynamic_rate * currency_rate
        
        return {
            'personal_bonus': personal_bonus,
            'group_bonus': group_bonus,
            'club_bonus': club_bonus,
            'mentorship_bonus': mentorship_bonus,
            'dynamic_bonus': dynamic_bonus,
            'recovery_bonus': recovery_bonus,
            'total': personal_bonus + group_bonus + club_bonus + mentorship_bonus + dynamic_bonus + recovery_bonus
        }
        
    def get_metrics(self) -> Dict:
        """Get network metrics for analysis"""
        total_partners = len(self.partners)
        active_partners = sum(1 for p in self.partners.values() if p.active)
        total_pv = sum(p.pv for p in self.partners.values())
        qualification_counts = {}
        
        for p in self.partners.values():
            qualification_counts[p.qualification] = qualification_counts.get(p.qualification, 0) + 1
            
        root_income = self.calculate_income(self.root_id)
        
        # Добавляем динамику роста
        root_partner = self.partners[self.root_id]
        growth_metrics = {
            'monthly_growth': root_partner.calculate_go_growth(1),
            'quarterly_growth': root_partner.calculate_go_growth(3),
            'yearly_growth': root_partner.calculate_go_growth(12)
        }
        
        return {
            'total_partners': total_partners,
            'active_partners': active_partners,
            'total_pv': total_pv,
            'qualification_counts': qualification_counts,
            'expected_income': root_income['total'],
            'income_breakdown': root_income,
            'growth_metrics': growth_metrics
        }
        
    def to_dict(self) -> Dict:
        """Convert structure to dictionary for serialization"""
        return {
            'total_pv': self.total_pv,
            'partners': {
                pid: {
                    'pv': p.pv,
                    'qualification': p.qualification,
                    'active': p.active,
                    'upline_id': p.upline_id,
                    'downline_ids': p.downline_ids,
                    'volume_history': p.volume_history,
                    'qualification_history': p.qualification_history
                }
                for pid, p in self.partners.items()
            }
        }

    def create_snapshot(self, snapshot_data: Dict) -> None:
        """Создать снимок текущего состояния сети"""
        stage_name = str(snapshot_data['name'])  # Убеждаемся, что имя этапа - строка
        
        # Получаем базовые метрики
        base_metrics = self.get_metrics()
        
        # Объединяем с переданными метриками
        metrics = base_metrics.copy()
        if 'metrics' in snapshot_data:
            metrics.update(snapshot_data['metrics'])
        
        # Добавляем дополнительные метрики, если их нет
        if 'total_partners' not in metrics:
            metrics['total_partners'] = len(self.partners)
        if 'active_partners' not in metrics:
            metrics['active_partners'] = sum(1 for p in self.partners.values() if p.active)
        if 'total_pv' not in metrics:
            metrics['total_pv'] = sum(p.pv for p in self.partners.values())
        if 'qualification_counts' not in metrics:
            qualification_counts = {}
            for p in self.partners.values():
                qualification_counts[p.qualification] = qualification_counts.get(p.qualification, 0) + 1
            metrics['qualification_counts'] = qualification_counts
        
        partners_state = {
            pid: {
                'pv': p.pv,
                'qualification': p.qualification,
                'active': p.active,
                'upline_id': p.upline_id,
                'downline_ids': p.downline_ids.copy(),
                'volume_history': p.volume_history.copy()
            }
            for pid, p in self.partners.items()
        }
        
        snapshot = NetworkSnapshot(stage_name, metrics, partners_state)
        self.history.append(snapshot)

    def get_history(self) -> List[Dict]:
        """Получить историю изменений сети"""
        return [snapshot.to_dict() for snapshot in self.history]

    def get_qualification_changes(self) -> List[Dict]:
        """Получение изменений квалификаций в сети"""
        changes = []
        
        for partner in self.partners.values():
            if len(partner.qualification_history) >= 2:
                # Берем последние два изменения квалификации
                prev_qual = partner.qualification_history[-2][1] if len(partner.qualification_history) > 1 else 'NONE'
                current_qual = partner.qualification
                
                if prev_qual != current_qual:
                    changes.append({
                        'partner_id': partner.id,
                        'from_qualification': prev_qual,
                        'to_qualification': current_qual,
                        'group_volume': self.calculate_group_volume(partner.id)
                    })
        
        return changes 