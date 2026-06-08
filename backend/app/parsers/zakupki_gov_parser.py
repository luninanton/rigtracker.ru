import httpx
import logging
import re
import xml.etree.ElementTree as ET
import urllib.parse
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from backend.app.parsers.base import BaseParser
from config import settings

logger = logging.getLogger(__name__)

class ZakupkiGovParser(BaseParser):
    def __init__(self):
        super().__init__(
            source_name="ЕИС Закупки",
            base_url="https://zakupki.gov.ru"
        )
        self.keywords = None

    async def parse(self) -> List[Dict[str, Any]]:
        api_url = f"{self.base_url}/epz/order/extendedsearch/rss.html"
        kw_list = self.keywords if self.keywords is not None else settings.KEYWORDS
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/xml, text/xml, */*"
        }

        parsed_tenders = []
        seen_urls = set()

        try:
            async with httpx.AsyncClient() as client:
                for kw in kw_list:
                    # Construct search params
                    params = {
                        "searchString": kw,
                        "morphology": "on",
                        "fz44": "on",
                        "fz223": "on",
                        "orderStages": "AF",  # Active stages (collecting bids)
                        "sortDirection": "false",  # Newest first
                        "recordsPerPage": "_20"   # Fetch last 20 for this keyword
                    }
                    
                    try:
                        response = await client.get(api_url, params=params, headers=headers, timeout=12.0)
                        if response.status_code != 200:
                            logger.error(f"ZakupkiGov API returned status code {response.status_code} for keyword {kw}")
                            continue
                        
                        root = ET.fromstring(response.content)
                        items = root.findall(".//item")
                        
                        for item in items:
                            link_elem = item.find("link")
                            if link_elem is None or not link_elem.text:
                                continue
                            
                            url = link_elem.text.strip()
                            if url in seen_urls:
                                continue
                            seen_urls.add(url)

                            desc_elem = item.find("description")
                            html_desc = desc_elem.text if desc_elem is not None else ""
                            
                            title, price, customer, law, ikz = self._parse_description(html_desc)
                            
                            pub_date_elem = item.find("pubDate")
                            date_end = None
                            if pub_date_elem is not None and pub_date_elem.text:
                                try:
                                    date_end = datetime.strptime(pub_date_elem.text.strip(), "%a, %d %b %Y %H:%M:%S %Z")
                                except Exception:
                                    pass
                            
                            platform_name = f"{self.source_name} ({law})"
                            full_description = f"Заказчик: {customer}\nЗакон: {law}"
                            
                            parsed_tenders.append({
                                "title": title,
                                "description": full_description,
                                "price_start": price,
                                "price_current": price,
                                "source_platform": platform_name,
                                "url": url,
                                "region": customer,
                                "date_end": date_end,
                                "ikz": ikz
                            })
                            
                    except Exception as kw_err:
                        logger.error(f"Error parsing ZakupkiGov RSS for keyword {kw}: {kw_err}")
                
                return parsed_tenders
                
        except Exception as e:
            logger.error(f"Error querying ZakupkiGov RSS: {e}")
            return []

    def _parse_description(self, html: str) -> Tuple[str, float, str, str, Optional[str]]:
        title_match = re.search(r'Наименование объекта закупки:\s*</strong\s*>\s*(.*?)(?:<br/>|<br>)', html, re.IGNORECASE)
        price_match = re.search(r'Начальная цена контракта:\s*</strong\s*>\s*([\d\.]+)', html, re.IGNORECASE)
        customer_match = re.search(r'Наименование Заказчика:\s*</strong\s*>\s*(.*?)(?:<br/>|<br>)', html, re.IGNORECASE)
        law_match = re.search(r'Размещение выполняется по:\s*</strong\s*>\s*(.*?)(?:<br/>|<br>)', html, re.IGNORECASE)
        ikz_match = re.search(r'Идентификационный код закупки\s*\(ИКЗ\):\s*</strong\s*>\s*(\d+)', html, re.IGNORECASE)
        
        title = title_match.group(1).strip() if title_match else "Без названия"
        # Strip XML/HTML tags if present inside title (like <span class='highlightColor'>)
        title = re.sub(r'<span[^>]*>|</span>', '', title)
        
        price = float(price_match.group(1).strip()) if price_match else 0.0
        customer = customer_match.group(1).strip() if customer_match else "Не указан"
        law = law_match.group(1).strip() if law_match else "44-ФЗ"
        ikz = ikz_match.group(1).strip() if ikz_match else None
        
        return title, price, customer, law, ikz
