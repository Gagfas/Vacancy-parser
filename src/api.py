import re
import time

import requests

from .vacancy import Vacancy


class SuperJobAPI:
    def __init__(self, api_key: str):
        self.base_url = 'https://api.superjob.ru/2.0/vacancies/'
        self.headers = {
            'X-Api-App-Id': api_key,
            'User-Agent': 'VacancyParser/1.0'
        }

    def get_vacancies(self, search_query: str, page: int = 0) -> list:
        params = {
            'keyword': search_query,
            'page': page,
            'count': 20,
            'no_agreement': 0,
        }
        try:
            response = requests.get(
                self.base_url, params=params, headers=self.headers, timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('objects', [])
            else:
                print(f"   SJ API Error: {response.status_code}")
                return []
        except Exception as e:
            print(f'   SJ API Exception: {e}')
            return []

    def get_vacancies_all_pages(self, search_query: str, max_pages: int = 20) -> list:
        vacancies = []
        for page in range(max_pages):
            data = self.get_vacancies(search_query, page)
            if not data:
                break
            for item in data:
                vacancy = self._parse_vacancy(item)
                vacancies.append(vacancy)
            time.sleep(1)
        return vacancies

    def _parse_vacancy(self, raw_data: dict) -> Vacancy:
        title = raw_data.get('profession', 'Без названия')
        link = raw_data.get('link', '')
        payment_from = raw_data.get('payment_from', 0) or 0
        payment_to = raw_data.get('payment_to', 0) or 0
        currency = raw_data.get('currency', 'rub')
        experience_data = raw_data.get('experience', {})
        experience = experience_data.get('title', '') if isinstance(experience_data, dict) else ''
        
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
        
        return Vacancy(
            title=title, link=link,
            salary_from=payment_from, salary_to=payment_to, currency=currency,
            description=description, platform='sj', experience=experience
        )