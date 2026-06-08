import httpx
import logging
from datetime import datetime
from typing import List, Dict, Any
from config import settings
from backend.app.parsers.base import BaseParser

logger = logging.getLogger(__name__)

class TorgiGovParser(BaseParser):
    def __init__(self):
        super().__init__(
            source_name="Torgi.gov.ru",
            base_url="https://torgi.gov.ru"
        )

    async def parse(self) -> List[Dict[str, Any]]:
        # Torgi.gov.ru Public API search endpoint
        api_url = f"{self.base_url}/new/api/public/lotcards/search"
        
        # We query the configured categories:
        categories = settings.TORGI_GOV_CATEGORIES
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*"
        }

        parsed_tenders = []
        seen_urls = set()

        try:
            async with httpx.AsyncClient() as client:
                for cat in categories:
                    # Query parameters for each category
                    params = {
                        "catCode": cat,
                        "lotStatus": "PUBLISHED",
                        "size": 15,
                        "sort": "publishDate,desc"
                    }
                    try:
                        response = await client.get(api_url, params=params, headers=headers, timeout=10.0)
                        if response.status_code != 200:
                            logger.error(f"TorgiGov API returned status code {response.status_code} for category {cat}")
                            continue
                        
                        data = response.json()
                        lots = data.get("content", [])
                        
                        for lot in lots:
                            lot_id = lot.get("id")
                            if not lot_id:
                                continue
                            
                            # Construct direct lot link
                            url = f"{self.base_url}/new/public/lots/lot/{lot_id}"
                            if url in seen_urls:
                                continue
                            seen_urls.add(url)

                            title = lot.get("lotName") or "Без названия"
                            description = lot.get("lotDescription") or ""
                            
                            # Prices
                            price_start = lot.get("priceMin") or lot.get("priceStart") or 0.0
                            price_current = lot.get("priceMin") or lot.get("priceStart") or 0.0
                            
                            # Location / Region
                            region = lot.get("okatoName") or lot.get("kladrName") or "Не указан"
                            
                            # Dates
                            date_end_str = lot.get("endDateReceiptApp")
                            date_end = None
                            if date_end_str:
                                try:
                                    # Parse ISO timestamp (e.g. 2026-06-15T18:00:00.000+0300)
                                    # Truncate timezone offset for simplicity
                                    date_end = datetime.fromisoformat(date_end_str.split(".")[0].split("+")[0])
                                except Exception:
                                    pass
                            
                            parsed_tenders.append({
                                "title": title,
                                "description": description,
                                "price_start": float(price_start),
                                "price_current": float(price_current),
                                "source_platform": self.source_name,
                                "url": url,
                                "region": region,
                                "date_end": date_end
                            })
                    except Exception as cat_err:
                        logger.error(f"Error while querying TorgiGov API for category {cat}: {cat_err}")
                
                return parsed_tenders
                
        except Exception as e:
            logger.error(f"Error while querying TorgiGov API: {e}")
            return []

