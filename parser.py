import os
import sys
from datetime import datetime
from typing import Dict
from config import Config
from src.api import SuperJobAPI
from src.sql_storage import SQLStorage
from src.vacancy import Vacancy
from src.selenium_parser_hh import HHSeleniumParser
from src.selenium_parser_zarplata import ZarplataSeleniumParser

class VacancyParser:
    def __init__(self):
        # Загружаем конфигурацию
        self.config = Config()
        
        # Инициализация API используя Config
        self.hh_parser = None
        self.zarplata_parser = None
        self.sj_api = SuperJobAPI(api_key=self.config.sj_api_key)
        
        # Инициализация хранилища (база в корне проекта)
        db_path = os.path.join(os.path.dirname(__file__), 'vacancies.db')
        self.storage = SQLStorage(db_path)
        
        # Показываем конфигурацию при запуске
        self.config.print_config()
    
    def is_junior_vacancy(self, vacancy: Vacancy) -> bool:
        """Определяет, является ли вакансия junior"""
        # Проверяем название
        title_lower = vacancy.title.lower()
        desc_lower = vacancy.description.lower() if vacancy.description else ''


        blacklist = [
    'военный', 'военная', 'военное', 'полиция', 'полицейский',
    'мвд', 'фсб', 'минобороны', 'вооруженные силы', 'армия',
    'вмп', 'днр', 'лнр', 'спецопераци', 'мобилизац',
    'солдат', 'сержант', 'офицер', 'контрактник',
    'повестка', 'военкомат', 'призыв', 'воинск',
    'рота', 'роте', 'полиции', 'батальон', 'полк', 'дивизия'
        ]

        for word in blacklist:
            if word in title_lower or word in desc_lower:
                print(f'   🗑️ Отсеяно по слову "{word}": {vacancy.title[:60]}')
                return False
            
        tech_keywords = [
        'python', 'питон', 'разработчик', 'программист', 'developer',
        'программирование', 'software', 'backend', 'frontend',
        'web', 'аналитик', 'тестировщик', 'qa', 'devops',
        'data scientist', 'machine learning', 'искуственный интеллект',
        'инженер', 'engineer', 'it', 'ии', 'айти'
        ]
        is_tech = any(keyword in title_lower for keyword in tech_keywords)

        if not is_tech and vacancy.description:
            is_tech = any(keyword in desc_lower for keyword in tech_keywords)

        
        if not is_tech:
            return False
        
        junior_keywords = [
        'junior', 'джуниор', 'начинающий', 'стажер', 'стажёр',
        'trainee', 'младший', 'intern', 'internship',
        'стажировка', 'начальный уровень', 'entry level',
        'помощник', 'ученик'
        ]
        
        has_junior_keywords = any(keyword in title_lower for keyword in junior_keywords)
        
        if not has_junior_keywords and vacancy.description:
            has_junior_keywords = any(keyword in desc_lower for keyword in junior_keywords)


        no_experience_phrases = [
        "нет опыта", "без опыта", "для начинающих",
        "студентов", "выпускников", "entry level",
        "не требуется", "до 1 года",
        "опыт не обязателен", "можно без опыта",
        "без опыта работы", "от 0 лет"
        ]

        has_no_exp = False

        if vacancy.experience:
            exp_lower = vacancy.experience.lower()
            has_no_exp = any(phrase in exp_lower for phrase in no_experience_phrases)
        
        # Проверяем описание
        if not has_no_exp and vacancy.description:
            has_no_exp = any(phrase in desc_lower for phrase in no_experience_phrases)

        return has_junior_keywords or has_no_exp
    
    def parse_vacancies(self, search_query: str = None, max_pages: int = None) -> Dict:
        """Парсинг вакансий и сохранение в БД"""
        if search_query is None:
            search_query = self.config.search_query
        if max_pages is None:
            max_pages = self.config.max_pages
        if max_pages == 0:
            max_pages = 20
            print(f' Режим: без ограничений (макс. {max_pages} страниц)')
            
        print(f'\n{"="*60}')
        print(f'🔄 Запуск парсера: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        print(f'\n{"="*60}')
        stats = {'hh_total': 0, 'sj_total': 0, 'zp_total': 0, 'hh_new': 0, 'sj_new': 0, 'zp_new': 0}
        
        all_current_links = []

        # Парсим HH
        print('\n📥 Парсинг HeadHunter через Selenium...')
        try:
            self.hh_parser = HHSeleniumParser()
            hh_vacancies = self.hh_parser.search(search_query, max_pages)
            self.hh_parser.close()

            stats['hh_total'] = len(hh_vacancies)

            if hh_vacancies:
                result = self.storage.add_vacancies(hh_vacancies, self.is_junior_vacancy)
                stats['hh_new'] = result['new']
                print(f' Всего: {stats["hh_total"]}, новых junior: {stats["hh_new"]}')
        
        except Exception as e:
            print(f' Ошибка HH: {e}')
        finally:
            if self.hh_parser:
                self.hh_parser.close()
        
        if hh_vacancies:
            all_current_links.extend([v.link for v in hh_vacancies])

        #Парсим ZarplataRU
        print('Парсим Zarplata.ru с помощью Selenium...')
        try:
            self.zarplata_parser = ZarplataSeleniumParser()
            zp_vacancies = self.zarplata_parser.search(search_query, max_pages)
            self.zarplata_parser.close()
            stats['zp_total'] = len(zp_vacancies)

            if zp_vacancies:
                result = self.storage.add_vacancies(zp_vacancies, self.is_junior_vacancy)
                stats['zp_new'] = result['new']
                print(f'Всего: {stats["zp_total"]}, новых junior: {stats["zp_new"]}')
        
        except Exception as e:
            print(f'Ошибка: {e}')
        finally:
            if self.zarplata_parser:
                self.zarplata_parser.close()
        if zp_vacancies:
            all_current_links.extend([v.link for v in zp_vacancies])

                
        # Парсим SuperJob
        print('\n📥 Парсинг SuperJob...')
        search_variants = [
        search_query,
        'Python разработчик',
        'Python стажер',
        'Python junior',
        'программист Python',
        ]
        all_vacancies = []
        seen_links = set()

        for variant in search_variants[:3]:
            try:
                vacancies = self.sj_api.get_vacancies_all_pages(variant, max_pages)
                print(f'   По запросу "{variant}": {len(vacancies)} вакансий')
                for vac in vacancies:
                    if vac.link not in seen_links:
                        seen_links.add(vac.link)
                        all_vacancies.append(vac)
            except Exception as e:
                print(f'   ⚠️ Ошибка для "{variant}": {e}')
        print(f'   Всего уникальных: {len(all_vacancies)}')

        it_keywords = ['python', 'питон', 'разработчик', 'программист', 'developer',
                   'software', 'web', 'backend', 'frontend', 'аналитик', 
                   'тестировщик', 'qa', 'devops', 'data', 'machine learning']
        
        blacklist = ['военный', 'полиция', 'вмп', 'днр', 'роте', 'рота', 'солдат', 'офицер']

        filtered = []
        filtered_out = []

        for vac in all_vacancies:
            title_lower = vac.title.lower()
            desc_lower = vac.description.lower() if vac.description else ''
            
            if any(word in title_lower or word in desc_lower for word in blacklist):
                print(f'Отфильтровано: {vac.title[:60]}')
                continue
            
            is_it = any(keyword in title_lower for keyword in it_keywords) or \
                any(keyword in desc_lower for keyword in it_keywords)
            if is_it:
                filtered.append(vac)
            else:
                filtered_out.append(vac)
        if filtered_out:
            print(f'   🗑️ Отфильтровано не IT: {len(filtered_out)}')
            for vac in filtered_out[:3]:  # Показываем первые 3
                print(f'      - {vac.title[:70]}')
        stats['sj_total'] = len(filtered)
        print(f" После фильтрации IT: {stats['sj_total']}")
        if filtered:
            result = self.storage.add_vacancies(filtered, self.is_junior_vacancy)
            stats['sj_new'] = result['new']
            print(f'Сохранено новых junior: {stats["sj_new"]}')
            if stats['sj_new'] > 0:
                print('\n Примеры новых junior вакансий:')
                juniors = self.storage.get_recent_juniors(5)
                for i, vac in enumerate(juniors, 1):
                    salary = f"{vac.get('salary_from', 0)}-{vac.get('salary_to', 0)} {vac.get('currency', '')}"
                    if vac.get('salary_from') == 0 and vac.get('salary_to') == 0:
                        salary = 'з/п не указана'
                        print(f"  {i}. {vac['title'][:50]}")
                        print(f"   {salary} | {vac.get('experience', 'опыт не указан')}")
        
        if filtered:
            all_current_links.extend([v.link for v in filtered])
        
        if all_current_links:
            print('\n Проверка актуальности вакансий...')
            self.storage.remove_stale_vacancies(all_current_links)
        #Логируем результаты
        self.storage.log_parse(stats)
        return stats
    
    
    def print_stats(self):
        """Вывод статистики"""
        stats = self.storage.get_stats()
        print('\n📊 Общая статистика:')
        print('-' * 50)
        
        if not stats:
            print('   Статистика пока недоступна')
            return
            
        for platform, data in stats.items():
            platform_name = 'HeadHunter' if platform == 'hh' else 'SuperJob' if platform == 'sj' else 'Zarplata'
            print(f'\n{platform_name}:')
            print(f'   Всего в базе: {data["total"]}')
            print(f'   Junior вакансий: {data["junior"]}')
            print(f'   Отправлено уведомлений: {data["notified"]}')
            print(f'   Новых junior: {data["new_juniors"]}')
    
    def show_recent_juniors(self, limit: int = 5):
        """Показать последние junior вакансии"""
        recent = self.storage.get_recent_juniors(limit)
        print(f'\n🔥 Последние {len(recent)} junior вакансий:')
        print('-' * 60)
        
        for i, vac in enumerate(recent, 1):
            salary = f"{vac.get('salary_from', 0)} - {vac.get('salary_to', 0)} {vac.get('currency', '')}"
            notified = '✅' if vac['notified'] else '🆕'
            print(f"{notified} {i}. {vac['title'][:60]}")
            print(f"   💰 {salary} | 📚 {vac.get('experience', 'Не указан')} | {vac['platform']}")
            print()


def main():
    try:
        print('🚀 Запуск парсера вакансий...')
        
        # Аргументы командной строки
        pages = None
        query = None
        if len(sys.argv) > 1:
            try:
                pages = int(sys.argv[1])
            except ValueError:
                pass
        if len(sys.argv) > 2:
            query = sys.argv[2]
        
        parser = VacancyParser()
        parser.parse_vacancies(search_query=query, max_pages=pages)
        parser.send_report_if_needed()
        parser.show_recent_juniors(5)
        
        print('\n✅ Работа парсера успешно завершена')
    except KeyboardInterrupt:
        print('\n⚠️  Работа прервана пользователем')
    except Exception as e:
        print(f'\n❌ Критическая ошибка: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()