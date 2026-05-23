from typing import List, Optional

from selenium.webdriver.common.by import By

from .selenium_parser_hh import HHSeleniumParser
from .vacancy import Vacancy


class ZarplataSeleniumParser(HHSeleniumParser):
    def search(self, query: str, max_pages: Optional[int] = None) -> List[Vacancy]:
        vacancies = []
        for page in range(max_pages):
            url = f'https://zarplata.ru/search/vacancy?text={query}&page={page}'
            self.driver.get(url)
            self._random_delay(3,5)
            self._human_scroll()
            
            cards = self.driver.find_elements(
                By.CSS_SELECTOR, '[data-qa="vacancy-serp__vacancy"]'
            )
            print(f' Найдено карточек: {len(cards)}')

            for card in cards:
                vacancy = self._parse_card(card)
                if vacancy:
                    vacancies.append(vacancy)

            try:
                next_btn = self.driver.find_element(By.CSS_SELECTOR, '[data-qa="pager-next"]')
                if not next_btn.is_enabled():
                    break
            except Exception:
                break

        return vacancies
    
    def _parse_card(self, card) -> Vacancy:
        try:
            title_el = card.find_element(By.CSS_SELECTOR, 'a[data-qa*="title"]')
            title = title_el.text.strip()
            link = title_el.get_attribute('href')
            salary_from = salary_to = 0
            currency = 'RUR'
            try:
                salary_el = card.find_element(By.CSS_SELECTOR, '[data-qa*="compensation"]')
                salary_text = salary_el.text.strip()
                if salary_text:
                    salary_from, salary_to, currency = self._parse_salary(salary_text)
            except Exception:
                pass

            experience = ''
            try:
                exp_el = card.find_element(By.CSS_SELECTOR, '[data-qa*="experience"]')
                experience = exp_el.text.strip()
            except Exception:
                pass

            description = ''
            try:
                desc_el = card.find_element(By.CSS_SELECTOR, '[data-qa*="snippet"]')
                description = desc_el.text.strip()
            except Exception:
                pass
            
            return Vacancy(
                title = title, link = link,
                salary_from = salary_from, salary_to=salary_to, currency=currency,
                description=description, platform='zp', experience=experience
            )
        except Exception:
            return None
        
        
