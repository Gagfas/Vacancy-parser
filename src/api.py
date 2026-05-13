import re
from abc import ABC
from .vacancy import Vacancy
import requests
import os
import time

class BaseApi(ABC):
    @classmethod
    def get_vacancies(self, search_query: str, page: int=0) -> list:
        pass

    @classmethod
    def _parse_vacancy(self, raw_data: dict) -> Vacancy:
        pass

    def get_vacancies_all_pages(self, search_query: str, max_pages: int=20) -> list:
        vacancies = []
        for page in range(max_pages):
            data = self.get_vacancies(search_query, page)
            if not data:
                break
            for item in data:
                vacancy = self._parse_vacancy(item)
                vacancies.append(vacancy)
            if data:
                time.sleep(1)
        return vacancies
    
class HHAPI(BaseApi):
    def __init__(self, email=None):
        self.base_url = "https://api.hh.ru/vacancies"
        # Используем ваш email из .env для User-Agent
        contact_email = os.getenv('EMAIL_LOGIN', 'user@example.com') # Берём из .env или ставим заглушку
        self.headers = {
            'User-Agent': f'VacancyParser/1.0 ({contact_email})',
            'Accept': 'application/json'
        }

    

    def get_vacancies(self, search_query: str, page: int = 0) -> list:
        params = {
            'text' : search_query,
            'per_page':20,
            'page': page,
            'search_field': ['name'],
        }

        print(f"🔍 HH API запрос: {search_query}, страница {page}")

        try:
            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=15
            )
            
            print(f"   Статус: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                total = data.get('found', 0)
                print(f'  Найдено всего: {total}, на странице: {len(items)}')
                
                for item in items[:3]:
                    print(f'   -{item.get('name')}')
                return items
            elif response.status_code == 403:
                print(f' Доступ запрещен. Проверьте User-Agent')
                return []
            else:
                print(f'   Ошибка: {response.text[:200]}')
                return []
        except requests.exceptions.RequestException as e:
            print(f'Ошибка запроса: {e}')
            return []

    def _parse_vacancy(self, raw_data: dict) -> Vacancy:

        title = raw_data.get('name')
        link = raw_data.get('alternate_url')
        salary_info = raw_data.get('salary')
        experience = raw_data.get('experience', {}).get('name')
        if salary_info:
            salary_from = salary_info.get('from')
            salary_to = salary_info.get('to')
            currency = salary_info.get('currency')
        else:
            salary_from = None
            salary_to = None
            currency = None

        snippet = raw_data.get('snippet', {})
        description = snippet.get('requirement', '') or snippet.get('responsibility', '')

        return Vacancy(
            title=title,
            link=link,
            salary_from=salary_from,
            salary_to=salary_to,
            currency=currency,
            description = description if description else "",
            platform="hh",
            experience=experience
        )
    
class SuperJobAPI(BaseApi):
    def __init__(self, api_key: str):
        self.base_url = 'https://api.superjob.ru/2.0/vacancies/'
        self.headers = {
            'X-Api-App-Id': api_key,
            'User-Agent': 'VacancyParser/1.0'
        }
        pass

    def get_vacancies(self, search_query: str, page: int = 0) -> list:

        params = {
            'keyword': search_query,
            'page': page,
            'count': 20,
            'no_agreement': 0,
        }

        try:
            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                objects = data.get('objects', [])
                print(f"   SJ API: найдено {len(objects)}, на странице: {len(objects)}")
                return objects
            else:
                print(f"   Ошибка: {response.text[:200]}")
                return []
                
        except Exception as e:
            print(f'   SJ API Exeption: {e}')
            return [] 
    
    def _parse_vacancy(self, raw_data: dict) -> Vacancy:
        title = raw_data.get('profession', 'Без названия')
        link = raw_data.get('link', '')
        payment_from = raw_data.get('payment_from', 0) or 0
        payment_to = raw_data.get('payment_to', 0) or 0
        currency = raw_data.get('currency', 'rub')
        experience_data = raw_data.get('experience', {})
        if isinstance(experience_data, dict):
            experience = experience_data.get('title', '')
        else:
            experience = str(experience_data) if experience_data else ''
        
        description = ''
        candidat = raw_data.get('candidat', '')
        
        if candidat:
            description = re.sub(r'<[^>]+>', ' ', candidat)
            description = re.sub(r'\s+', ' ', description).strip()
        if not description:
            vacancy_rich = raw_data.get('vacancyRichText', '')
            if vacancy_rich:
                description = re.sub(r'<[^>]+>', ' ', vacancy_rich)
                description = re.sub(r'\s+', ' ', description).strip()
        town_data = raw_data.get('town', {})
        if isinstance(town_data, dict):
            city = town_data.get('title', '')
        else:
            city = ''
        
        firm_name = raw_data.get('firm_name', '') or raw_data.get('client', {}).get('title', '')
        work_type = raw_data.get('type_of_work', {})
        if isinstance(work_type, dict):
            work_type = work_type.get('title', '')

            
        return Vacancy(
            title=title,
            link=link,
            salary_from=payment_from,
            salary_to=payment_to,
            currency=currency,
            description=description,
            platform='sj',
            experience=experience
        )

    