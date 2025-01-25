from typing import Dict, List, Optional
from datetime import datetime, timedelta
from utils.constants import QUALIFICATIONS, BONUS_RATES, CLUB_LEVELS, CLUB_BENEFITS

class Partner:
    def __init__(self, id: int, pv: float = 0, upline_id: Optional[int] = None):
        self.id = id
        self.pv = pv
        self.upline_id = upline_id
        self.downline_ids = []
        self.qualification = 'NONE'
        self.region = None
        self.starter_kit = None
        self.privileges = set()
        self.club_memberships = set()
        
        # История изменений
        self.volume_history = []  # List[Tuple[datetime, float]]
        self.qualification_history = []  # List[Tuple[datetime, str]]
        self.compression_history = []  # List[Tuple[datetime, float]]
        
        # Статусы и периоды
        self.recovery_status = None
        self.grace_period_end = None
        self.last_compression_date = None
        
    def add_downline(self, partner_id: int):
        """Добавить партнера в даунлайн"""
        if partner_id not in self.downline_ids:
            self.downline_ids.append(partner_id)
            
    def remove_downline(self, partner_id: int):
        """Удалить партнера из даунлайна"""
        if partner_id in self.downline_ids:
            self.downline_ids.remove(partner_id)
            
    def update_qualification(self, new_qualification: str):
        """Обновить квалификацию и записать в историю"""
        if new_qualification != self.qualification:
            self.qualification = new_qualification
            self.qualification_history.append((datetime.now(), new_qualification))
            
    def add_volume_record(self, pv: float):
        """Добавить запись об изменении объема"""
        self.pv = pv
        self.volume_history.append((datetime.now(), pv))
        # Сохраняем только последние 12 месяцев
        cutoff_date = datetime.now() - timedelta(days=365)
        self.volume_history = [
            (date, vol) for date, vol in self.volume_history
            if date > cutoff_date
        ]
        
    def is_compressed(self) -> bool:
        """Проверить, находится ли партнер в компрессии"""
        return self.last_compression_date is not None and \
               (self.recovery_status is None or \
                datetime.now() <= self.grace_period_end)
                
    def compress(self):
        """Применить компрессию к партнеру"""
        self.last_compression_date = datetime.now()
        self.compression_history.append((datetime.now(), self.pv))
        self.grace_period_end = datetime.now() + timedelta(days=90)  # 3 месяца
        
    def recover(self, recovery_type: str):
        """Восстановить партнера после компрессии"""
        self.recovery_status = recovery_type
        self.last_compression_date = None
        self.grace_period_end = None
        
    def check_compression_status(self) -> tuple[bool, str]:
        """Проверить статус компрессии и уровень предупреждения"""
        if not self.is_compressed():
            return False, 'none'
            
        days_compressed = (datetime.now() - self.last_compression_date).days
        if days_compressed > 60:
            return True, 'critical'
        elif days_compressed > 30:
            return True, 'warning'
        return True, 'notice'
        
    def get_compression_rule(self) -> Dict:
        """Получить правило компрессии для текущей квалификации"""
        qualification_rules = {
            'NONE': {'threshold': 50, 'grace_period': 1},
            'M1': {'threshold': 100, 'grace_period': 2},
            'M2': {'threshold': 200, 'grace_period': 2},
            'M3': {'threshold': 300, 'grace_period': 3},
            'B1': {'threshold': 400, 'grace_period': 3},
            'B2': {'threshold': 500, 'grace_period': 3},
            'B3': {'threshold': 600, 'grace_period': 3}
        }
        return qualification_rules.get(self.qualification, {'threshold': 50, 'grace_period': 1})
        
    def purchase_starter_kit(self, kit_type: str):
        """Приобрести стартовый набор"""
        self.starter_kit = kit_type
        # Добавить привилегии в зависимости от типа набора
        kit_privileges = {
            'START': ['quick_start', 'basic_training'],
            'START_PLUS': ['quick_start', 'basic_training', 'business_tools'],
            'BUSINESS': ['quick_start', 'basic_training', 'business_tools', 'mentorship'],
            'VIP': ['quick_start', 'basic_training', 'business_tools', 'mentorship', 'vip_support']
        }
        self.privileges.update(kit_privileges.get(kit_type, []))
        
    def has_privilege(self, privilege: str) -> bool:
        """Проверить наличие привилегии"""
        if privilege not in self.privileges:
            return False
            
        # Проверяем срок действия привилегии
        privilege_durations = {
            'quick_start': 30,
            'basic_training': 90,
            'business_tools': 180,
            'mentorship': 365,
            'vip_support': 365
        }
        
        if self.starter_kit:
            kit_purchase_date = next(
                (date for date, _ in self.volume_history),
                datetime.now()
            )
            days_since_purchase = (datetime.now() - kit_purchase_date).days
            return days_since_purchase <= privilege_durations.get(privilege, 0)
            
        return False
        
    def update_club_membership(self):
        """Обновить членство в клубе"""
        for level, requirements in CLUB_LEVELS.items():
            if self.qualification == requirements['qualification'] and \
               self._check_qualification_maintenance(requirements['maintenance_period']):
                self.club_memberships.add(level)
                
    def get_club_level(self) -> Optional[str]:
        """Получить текущий уровень клуба"""
        if not self.club_memberships:
            return None
        # Возвращаем высший уровень клуба
        club_ranks = {'AC1': 1, 'AC2': 2, 'AC3': 3, 'AC4': 4, 'AC5': 5, 'AC6': 6}
        return max(self.club_memberships, key=lambda x: club_ranks.get(x, 0))
        
    def get_club_benefits(self) -> List[str]:
        """Получить список активных клубных привилегий"""
        benefits = set()
        for club in self.club_memberships:
            if club in CLUB_BENEFITS:
                benefits.update(CLUB_BENEFITS[club])
        return list(benefits)
        
    def get_event_discount(self, club_level: str) -> float:
        """Получить скидку на мероприятия для уровня клуба"""
        discount_rates = {
            'AC1': 0.1,
            'AC2': 0.15,
            'AC3': 0.2,
            'AC4': 0.25,
            'AC5': 0.3,
            'AC6': 0.35
        }
        return discount_rates.get(club_level, 0.0)
        
    def get_club_bonus_rate(self) -> float:
        """Получить ставку клубного бонуса"""
        bonus_rates = {
            'AC1': 0.01,
            'AC2': 0.02,
            'AC3': 0.03,
            'AC4': 0.04,
            'AC5': 0.05,
            'AC6': 0.06
        }
        club_level = self.get_club_level()
        return bonus_rates.get(club_level, 0.0)
        
    def get_quick_start_bonus(self) -> float:
        """Рассчитать бонус быстрого старта"""
        if 'quick_start' not in self.privileges:
            return 0.0
            
        # Базовая ставка бонуса
        base_rate = 0.05
        
        # Повышенная ставка для определенных наборов
        kit_bonuses = {
            'START_PLUS': 0.07,
            'BUSINESS': 0.1,
            'VIP': 0.15
        }
        
        bonus_rate = kit_bonuses.get(self.starter_kit, base_rate)
        return self.pv * bonus_rate
        
    def get_leadership_bonus(self) -> float:
        """Рассчитать бонус лидерства"""
        if self.qualification not in ['B1', 'B2', 'B3', 'TOP']:
            return 0.0
            
        leadership_rates = {
            'B1': 0.01,
            'B2': 0.02,
            'B3': 0.03,
            'TOP': 0.05
        }
        
        return self.pv * leadership_rates[self.qualification]
        
    def _check_qualification_maintenance(self, months: int) -> bool:
        """Проверить поддержание квалификации за период"""
        if not self.qualification_history:
            return False
            
        cutoff_date = datetime.now() - timedelta(days=months * 30)
        recent_history = [
            (date, qual) for date, qual in self.qualification_history
            if date > cutoff_date
        ]
        
        if not recent_history:
            return False
            
        # Проверяем, что квалификация не опускалась ниже текущей
        current_qual = self.qualification
        for _, qual in recent_history:
            if qual != current_qual:
                return False
                
        return True 