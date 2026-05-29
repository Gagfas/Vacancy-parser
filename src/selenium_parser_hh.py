import os
import random
import re
import sys
import time
from typing import List, Optional

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import WebDriverWait

from .vacancy import Vacancy

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import Config

driver_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'webdriver')
driver_path = os.path.join(driver_dir, 'msedgedriver.exe')


class HHSeleniumParser:
    def __init__(self):
        self.driver = None
        self._init_driver()
    
    def _init_driver(self):
        options = webdriver.EdgeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-features=msSmartScreenProtection')
        options.add_experimental_option('prefs', {
            'safebrowsing.enabled': False,
        })

        user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
        ]

        options.add_argument(f'--user-agent={random.choice(user_agents)}')

        service = Service(executable_path=driver_path)
        self.driver = webdriver.Edge(service=service, options = options)

        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        self.wait = WebDriverWait(self.driver, 15)

    def _random_delay(self, min_sec: float = 0.5, max_sec: float = 2.0):
        time.sleep(random.uniform(min_sec, max_sec))

    def _human_scroll(self):
        """Прокрутка до самого низа с ожиданием подгрузки"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
    
        while True:
            # Скроллим вниз
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self._random_delay(2, 3)  # Ждём подгрузку
        
            # Проверяем новую высоту
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break  # Достигли конца
            last_height = new_height

    def search(self, query: str, max_pages: Optional[int] = None) -> List[Vacancy]:
        if max_pages is None:
            max_pages = Config().max_pages
        if max_pages == 0:
            max_pages = 20
            print(f' Режим: без ограничений (макс. {max_pages} страниц)')
    
        vacancies = []
        print(f' HH Selenium: поиск "{query}"')

        for page in range(max_pages):
            try:
                if page == 0:
                    url = (
                        f'https://hh.ru/search/vacancy'
                        f'?search_field=name'
                        f'&search_field=company_name'
                        f'&search_field=description'
                        f'&text={query}'
                        f'&enable_snippets=false'
                        f'&items_on_page=100'
                        f'&page=0'
                        f'&order_by=relevance'
                        )
                    print(f' Страница {page + 1}...')
                    self.driver.delete_all_cookies()
                    self.driver.get('https://hh.ru')
                    self._random_delay(1, 2)
                    self.driver.get(url)
                else:
                    print(f' Страница {page + 1}...')
                    try:
                        next_btn = self.driver.find_element(By.CSS_SELECTOR, '[data-qa="pager-next"]')
                         # Скроллим к кнопке
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
                        self._random_delay(0.5, 1)
                        # Кликаем через JavaScript (надёжнее)
                        self.driver.execute_script("arguments[0].click();", next_btn)
                        self._random_delay(3, 5)  # Ждём загрузку
                    except Exception:
                        print(' Кнопка "далее" не найдена — конец')
                        break

        
                self._random_delay(3, 5)
                self._human_scroll()
                self._random_delay(1, 2)
        
                cards = self.driver.find_elements(By.CSS_SELECTOR, '[data-qa="vacancy-serp__vacancy"]')
                print(f' Найдено карточек: {len(cards)}')
        
                for card in cards:
                    try:
                        vacancy = self._parse_card(card)
                        if vacancy:
                            vacancies.append(vacancy)
                    except Exception:
                        continue

                if page < max_pages - 1:
                    try:
                        next_btn = self.driver.find_element(By.CSS_SELECTOR, '[data-qa="pager-next"]')
                        if not next_btn.is_enabled():
                            print(' Достигнут конец результатов')
                            break
                    except Exception:
                        print(' Пагинация не найдена — конец')
                        break

        
                self._random_delay(3, 6)
        
            except Exception as e:
                print(f' Ошибка на странице {page + 1}: {str(e)[:200]}')
                break
        
        return vacancies
    
    def _parse_card(self, card) -> Vacancy:
        """Парсинг одной карточки вакансии"""
    
        try:
            #Название и ссылка
            title_el = card.find_element(By.CSS_SELECTOR, 'a[data-qa*="title"]')
            title = title_el.text.strip()
            link = title_el.get_attribute('href')

            if not title or not link:
                return None
            #Зарплата
            salary_from = salary_to = 0
            currency = 'RUR'
            try:
                salary_el = card.find_element(By.CSS_SELECTOR, '[data-qa*="compensation"]')
                salary_text = salary_el.text.strip()
                if salary_text:
                    salary_from, salary_to, currency = self._parse_salary(salary_text)
            except NoSuchElementException:
                pass

            #Опыт
            experience = ''
            try:
                exp_el = card.find_element(By.CSS_SELECTOR, '[data-qa*="experience"]')
                experience = exp_el.text.strip()
            except NoSuchElementException:
                pass
            
            #Описание
            description = ''
            try:
                desc_el = card.find_element(By.CSS_SELECTOR, '[data-qa*="snippet"]')
                description = desc_el.text.strip()
            except NoSuchElementException:
                pass

            return Vacancy(
                title=title,
                link=link,
                salary_from=salary_from,
                salary_to=salary_to,
                currency=currency,
                description=description,
                platform='hh',
                experience=experience
            )
        except Exception as e:
            print(f' Ошибка в _parse_card: {str(e)[:100]}')
            return None
    
    def _parse_salary(self, text: str) -> tuple:
        """
        Парсинг зарплаты из текста
        Примеры:
        "от 100 000 до 200 000 руб." -> (100000, 200000, 'RUR')
        "до 150 000 руб." -> (0, 150000, 'RUR')
        "от 80 000 руб." -> (80000, 0, 'RUR')
        """
        if not text:
            return 0, 0, 'RUR'
        
        currency = 'RUR'
        if 'USD' in text or '$' in text:
            currency = 'USD'
        elif 'EUR' in text or '€' in text:
            currency = 'EUR'
        elif 'KZT' in text or '₸' in text:
            currency = 'KZT'
        
        numbers = re.findall(r'\d+[\s\d]*', text)
        numbers = [int(re.sub(r'\s', '', n)) for n in numbers if n.strip()]

        if not numbers:
            return 0, 0, currency
        
        if 'до' in text and 'от' not in text:
            return 0, numbers[0], currency
        
        elif 'от' in text and 'до' in text and len(numbers) >= 2:
            return numbers[0], numbers[1], currency
        elif len(numbers) == 2:
            return numbers[0], numbers[1], currency
        elif len(numbers) == 1:
            return numbers[0], numbers[0], currency
        else:
            return 0, 0, currency

    def close(self):
        """Закрытие драйвера"""              
        if self.driver:
            try:
                self.driver.quit()
                print(' Драйвер закрыт')
            except Exception:
                pass

    def __del__(self):
        self.close()