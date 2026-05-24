import os

from dotenv import load_dotenv


class Config:
    def __init__(self, env_file='.env'):
        """Загружает конфигурацию из .env файла"""
        # Загружаем .env из той же папки, где config.py
        env_path = os.path.join(os.path.dirname(__file__), env_file)
        load_dotenv(env_path)
        
    @property
    def sj_api_key(self) -> str:
        return os.getenv('SJ_KEY')
    
    @property
    def search_query(self) -> str:
        return os.getenv('SEARCH_QUERY', 'Python разработчик')
    
    @property
    def max_pages(self) -> int:
        return int(os.getenv('MAX_PAGES', '3'))
    
    @property
    def check_hours(self) -> int:
        return int(os.getenv('CHECK_HOURS', '6'))
    
    @property
    def raw_mode(self) -> bool:
        return os.getenv('RAW_MODE', 'FALSE')
    
    def print_config(self):
        """Выводит текущую конфигурацию"""
        print("\n📋 Конфигурация:")
        print(f"   Поиск: '{self.search_query}'")
        print(f"   Страниц: {self.max_pages}")
        print(f"   Интервал: {self.check_hours} ч.")
        print(f"   SJ API: {'✓' if self.sj_api_key else '❌ НЕ УКАЗАН'}")
        print()