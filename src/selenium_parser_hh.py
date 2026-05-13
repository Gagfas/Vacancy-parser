import os
import time
import random
import re
from typing import List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .vacancy import Vacancy

driver_path = "C:\\Users\\Evgeny\\Documents\\python\\vacancy_parser\\webdriver\\msedgedriver.exe"


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
        total_height = self.driver.execute_script('return document.body.scrollHeight')
        current = 0
        while current < total_height:
            scroll_by = random.randint(100,300)
            current += scroll_by
            self.driver.execute_script(f'window.scrollTo(0,{current});')
            self._random_delay(0.1, 0.3)
        
        if random.random() > 0.5:
            self.driver.execute_script('window.scrollTo(0, 0);')
            self._random_delay(0.5, 1.0)

    def search(self, query: str, max_pages: int = 3) -> List[Vacancy]:
        vacancies = []
        print(f' HH Selenium: поиск "{query}"')

        for page in range(max_pages):
            try:
                url = f'https://hh.ru/search/vacancy?search_field=name&text={query}&page={page}&area=113'
                print(f' Страница {page + 1}...')
                self.driver.delete_all_cookies()
                self.driver.get(url)
                self._random_delay(2, 4)
                self._human_scroll()
                self._random_delay(1, 2)
                try:
                    cards = self.wait.until(
                        EC.presence_of_all_elements_located(
                            (By.CSS_SELECTOR, '[data-qa="vacancy-serp__vacancy"]')
                        )
                    )
                except TimeoutException:
                    print(f' Вакансии не найдены на странице {page + 1}')
                    break
                print(f' Найдено карточек: {len(cards)}')

                for card in cards:
                    try:
                        vacancy = self._parse_card(card)
                        if vacancy:
                            vacancies.append(vacancy)
                    except Exception as e:
                        print(f' Ошибка парсинга карточки {e}')
                        continue
                
                if len(cards) < 20:
                    print(f' Достигнут конец результатов')
                    break

                if page < max_pages -1:
                    self._random_delay(3, 6)
            except Exception as e:
                print(f' Ошибка на странице {page + 1}: {str(e)[:200]}')
                break
        print(f' Всего собрано: {len(vacancies)} вакансий')
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

            #Компания
            company = ''
            try:
                company_el = card.find_element(By.CSS_SELECTOR, '[data-qa*="company"]')
                company = company_el.text.strip()
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
            except:
                pass

    def __del__(self):
        self.close()
