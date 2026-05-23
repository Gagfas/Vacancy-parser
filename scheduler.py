import time
from datetime import datetime
from parser import VacancyParser


class ParserScheduler:
    def __init__(self):
        self.parser = VacancyParser()
        self.run_count = 0
    
    def job(self):
        """Задача для выполнения по расписанию"""
        self.run_count += 1
        print(f'\n{"="*60}')
        print(f'Запуск #{self.run_count}: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        print(f'{"="*60}')
        
        try:
            # Парсим вакансии
            self.parser.parse_vacancies()
            
            # Отправляем если есть новые
            self.parser.send_report_if_needed()
            
        except Exception as e:
            print(f'❌ Ошибка при выполнении: {str(e)}')
            import traceback
            traceback.print_exc()
        
        next_run = datetime.now().replace(hour=(datetime.now().hour + 6) % 24)
        print(f'\n⏰ Следующий запуск примерно в {next_run.strftime("%H:%M")}')
        print(f'{"="*60}\n')
    
    def start(self):
        """Запуск планировщика"""
        print('🤖 Парсер вакансий запущен')
        print('📅 Интервал: каждые 6 часов')
        print('🚀 Первый запуск: сейчас\n')
        
        try:
            while True:
                self.job()
                # Ждем 6 часов
                time.sleep(6 * 3600)
                
        except KeyboardInterrupt:
            print(f'\n\n👋 Парсер остановлен. Выполнено запусков: {self.run_count}')

if __name__ == '__main__':
    scheduler = ParserScheduler()
    scheduler.start()