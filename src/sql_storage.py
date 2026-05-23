import sqlite3
from datetime import datetime
from typing import List

from .vacancy import Vacancy


class SQLStorage:
    def __init__(self, db_name: str = 'vacancies.db'):
        self.db_name = db_name
        self._create_tables()
    
    def _create_tables(self):
        """Создание таблиц если их нет"""
        with sqlite3.connect(self.db_name) as conn:
            # Таблица вакансий
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vacancies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    link TEXT UNIQUE NOT NULL,
                    salary_from REAL DEFAULT 0,
                    salary_to REAL DEFAULT 0,
                    currency TEXT DEFAULT 'RUR',
                    description TEXT DEFAULT '',
                    platform TEXT NOT NULL,
                    experience TEXT DEFAULT '',
                    is_junior BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notified BOOLEAN DEFAULT 0,
                    notified_at TIMESTAMP
                )
            """)
            
            # Таблица логов парсинга
            conn.execute("""
                CREATE TABLE IF NOT EXISTS parse_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    parse_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    hh_total INTEGER DEFAULT 0,
                    sj_total INTEGER DEFAULT 0,
                    new_vacancies INTEGER DEFAULT 0,
                    new_juniors INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'success'
                )
            """)
            
            # Индексы
            conn.execute("CREATE INDEX IF NOT EXISTS idx_platform ON vacancies(platform)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_is_junior ON vacancies(is_junior)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_notified ON vacancies(notified)")
            
            conn.commit()
    
    def log_parse(self, stats: dict, status: str = 'success'):
        """Логирование результатов парсинга"""
        with sqlite3.connect(self.db_name) as conn:
            conn.execute("""
                INSERT INTO parse_log (hh_total, sj_total, new_vacancies, new_juniors, status)
                VALUES (?, ?, ?, ?, ?)
            """, (
                stats.get('hh_total', 0),
                stats.get('sj_total', 0),
                stats.get('hh_new', 0) + stats.get('sj_new', 0),
                stats.get('junior_new', 0),
                status
            ))
            conn.commit()
    
    def get_last_parse_time(self):
        """Получить время последнего парсинга"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.execute(
                "SELECT MAX(parse_time) as last_parse FROM parse_log"
            )
            result = cursor.fetchone()
            return result[0] if result else None
    
    def add_vacancy(self, vacancy: Vacancy, is_junior: bool = False) -> bool:
        """Добавление одной вакансии"""
        with sqlite3.connect(self.db_name) as conn:
            try:
                existing = conn.execute(
                    "SELECT id, notified FROM vacancies WHERE link = ?", 
                    (vacancy.link,)
                ).fetchone()
                
                if existing:
                    conn.execute("""
                        UPDATE vacancies 
                        SET title = ?, salary_from = ?, salary_to = ?, 
                            currency = ?, description = ?, experience = ?,
                            is_junior = ?
                        WHERE link = ?
                    """, (
                        vacancy.title,
                        vacancy.salary_from,
                        vacancy.salary_to,
                        vacancy.currency,
                        vacancy.description,
                        vacancy.experience or '',
                        is_junior or existing[1],
                        vacancy.link
                    ))
                    conn.commit()
                    return False
                else:
                    conn.execute("""
                        INSERT INTO vacancies 
                        (title, link, salary_from, salary_to, currency, description, 
                         platform, experience, is_junior, first_seen_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        vacancy.title,
                        vacancy.link,
                        vacancy.salary_from,
                        vacancy.salary_to,
                        vacancy.currency,
                        vacancy.description,
                        vacancy.platform,
                        vacancy.experience or '',
                        is_junior,
                        datetime.now()
                    ))
                    conn.commit()
                    return True
                    
            except sqlite3.IntegrityError as e:
                print(f"Ошибка при добавлении вакансии: {e}")
                return False
    
    def add_vacancies(self, vacancies: List[Vacancy], is_junior_func=None) -> dict:
        """Добавление списка вакансий, возвращает статистику"""
        stats = {'new': 0, 'updated': 0, 'total': len(vacancies)}
        
        for vac in vacancies:
            is_junior = is_junior_func(vac) if is_junior_func else False
            if self.add_vacancy(vac, is_junior):
                stats['new'] += 1
            else:
                stats['updated'] += 1
        
        print(f'📊 Обработано: {stats["total"]}, новых: {stats["new"]}, обновлено: {stats["updated"]}')
        return stats
    
    def get_new_vacancies_for_notification(self, hours: int = 6) -> list:
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM vacancies 
                WHERE is_junior = 1 
                  AND notified = 0
                  AND first_seen_at >= datetime('now', '-' || ? || ' hours')
                ORDER BY first_seen_at DESC, platform, salary_from DESC
            """, (hours,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_unsent_juniors(self) -> list:
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM vacancies 
                WHERE is_junior = 1 AND notified = 0
                ORDER BY first_seen_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def mark_as_notified(self, vacancy_ids: list):
        if not vacancy_ids:
            return
        
        with sqlite3.connect(self.db_name) as conn:
            conn.executemany("""
                UPDATE vacancies 
                SET notified = 1, notified_at = ? 
                WHERE id = ?
            """, [(datetime.now(), id) for id in vacancy_ids])
            conn.commit()
    
    def get_stats(self) -> dict:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.execute("""
                SELECT 
                    platform,
                    COUNT(*) as total,
                    SUM(CASE WHEN is_junior = 1 THEN 1 ELSE 0 END) as junior_count,
                    SUM(CASE WHEN notified = 1 THEN 1 ELSE 0 END) as notified_count,
                    SUM(CASE WHEN is_junior = 1 AND notified = 0 THEN 1 ELSE 0 END) as new_juniors,
                    MIN(first_seen_at) as first_vacancy,
                    MAX(first_seen_at) as last_vacancy
                FROM vacancies 
                GROUP BY platform
            """)
            
            stats = {}
            for row in cursor.fetchall():
                stats[row[0]] = {
                    'total': row[1],
                    'junior': row[2],
                    'notified': row[3],
                    'new_juniors': row[4],
                    'first_vacancy': row[5],
                    'last_vacancy': row[6]
                }
            return stats
    
    def get_recent_juniors(self, limit: int = 5) -> list:
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM vacancies 
                WHERE is_junior = 1
                ORDER BY first_seen_at DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
        
    def remove_stale_vacancies(self, current_links: list):
        """
        Удаляет вакансии, которых больше нет на сайте
        current_links - список актуальных ссылок, полученных при парсинге"""
        if not current_links:
            print('Нет ссылок для проверки, удаление пропущено')
            return 0
        with sqlite3.connect(self.db_name) as conn:
            #Удаляем все не из списка актуальных
            placeholders = ','.join('?' * len(current_links))
            cursor = conn.execute(f"""
                DELETE FROM vacancies
                WHERE link NOT IN ({placeholders})
            """, current_links)
            deleted = cursor.rowcount
            conn.commit()

            if deleted > 0:
                print(f' Удалено устаревших вакансий: {deleted}')
            else:
                print(' Все вакансии актуальны')
            return deleted
        
        