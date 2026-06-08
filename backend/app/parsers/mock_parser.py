import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from backend.app.parsers.base import BaseParser

class MockMachineryParser(BaseParser):
    def __init__(self):
        super().__init__(source_name="Федресурс (Мок)", base_url="https://fedresurs.ru")

    async def parse(self) -> List[Dict[str, Any]]:
        # Simulate network latency
        await asyncio.sleep(0.5)
        
        return [
            {
                "title": "Продажа б/у Самосвала КАМАЗ 65115",
                "description": "Самосвал в хорошем состоянии, 2017 года выпуска. Использовался на строительных объектах.",
                "price_start": 3000000.0,
                "price_current": 2700000.0,
                "source_platform": self.source_name,
                "url": "https://fedresurs.ru/lot/kamaz-65115-123",
                "region": "Московская обл.",
                "date_end": datetime.utcnow() + timedelta(days=10)
            },
            {
                "title": "Аренда Гусеничного Экскаватора JCB 220",
                "description": "Сдаем в аренду экскаватор с машинистом и топливом.",
                "price_start": 2000.0,
                "price_current": 2000.0,
                "source_platform": self.source_name,
                "url": "https://fedresurs.ru/lot/jcb-220-rent",
                "region": "Санкт-Петербург",
                "date_end": datetime.utcnow() + timedelta(days=5)
            },
            {
                "title": "Бульдозер гусеничный CAT D6R",
                "description": "Реализация имущества банкротов. Торги на понижение. Исправный бульдозер Caterpillar.",
                "price_start": 9000000.0,
                "price_current": 6300000.0,
                "source_platform": self.source_name,
                "url": "https://fedresurs.ru/lot/cat-d6r-bankruptcy",
                "region": "Татарстан",
                "date_end": datetime.utcnow() + timedelta(days=15)
            },
            {
                "title": "Запчасти и шины для погрузчика Komatsu",
                "description": "Комплект шин и дисков для вилочного погрузчика Komatsu.",
                "price_start": 70000.0,
                "price_current": 70000.0,
                "source_platform": self.source_name,
                "url": "https://fedresurs.ru/lot/komatsu-parts-456",
                "region": "Краснодарский край",
                "date_end": datetime.utcnow() + timedelta(days=2)
            }
        ]
