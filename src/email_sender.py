import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
from datetime import datetime

class EmailSender:
    def __init__(self, smtp_server: str, smtp_port: int, login: str, password: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.login = login
        self.password = password
    
    def _create_html_report(self, vacancies: List[dict], stats: Dict = None) -> str:
        """Создание красивого HTML отчета"""
        html = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ 
                    font-family: 'Segoe UI', Arial, sans-serif; 
                    max-width: 800px; 
                    margin: 0 auto;
                    background-color: #f5f5f5;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px 10px 0 0;
                    text-align: center;
                }}
                .content {{ padding: 20px; background: white; }}
                .stats {{
                    display: flex;
                    justify-content: space-around;
                    margin: 20px 0;
                    padding: 15px;
                    background: #f8f9fa;
                    border-radius: 10px;
                }}
                .stat-item {{
                    text-align: center;
                    padding: 10px;
                }}
                .stat-number {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #667eea;
                }}
                .vacancy {{ 
                    border: 1px solid #e1e4e8;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 15px 0;
                    background: white;
                    transition: transform 0.2s;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .vacancy:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
                }}
                .vacancy-title {{
                    font-size: 18px;
                    font-weight: 600;
                    color: #24292e;
                    margin-bottom: 10px;
                }}
                .platform-badge {{
                    display: inline-block;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: 500;
                    margin-right: 10px;
                }}
                .hh-badge {{ background: #ff6b6b; color: white; }}
                .sj-badge {{ background: #4ecdc4; color: white; }}
                .salary {{
                    font-size: 16px;
                    color: #28a745;
                    font-weight: 600;
                    margin: 10px 0;
                }}
                .experience {{
                    color: #6f42c1;
                    font-size: 14px;
                    margin: 5px 0;
                }}
                .description {{
                    color: #586069;
                    font-size: 14px;
                    margin: 10px 0;
                    line-height: 1.5;
                    max-height: 100px;
                    overflow: hidden;
                }}
                .link-button {{
                    display: inline-block;
                    padding: 8px 16px;
                    background: #0366d6;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                    margin-top: 10px;
                    font-size: 14px;
                }}
                .footer {{
                    text-align: center;
                    padding: 20px;
                    color: #586069;
                    font-size: 12px;
                    border-top: 1px solid #e1e4e8;
                }}
                .no-vacancies {{
                    text-align: center;
                    padding: 40px;
                    color: #586069;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚀 Junior Python Developer</h1>
                <p>Новые вакансии за последние 6 часов</p>
                <p style="font-size: 14px; opacity: 0.9;">
                    {datetime.now().strftime('%d.%m.%Y %H:%M')}
                </p>
            </div>
            
            <div class="content">
        """
        
        # Добавляем статистику если есть
        if stats:
            html += f"""
                <div class="stats">
                    <div class="stat-item">
                        <div class="stat-number">{stats.get('total_new', 0)}</div>
                        <div>Новых вакансий</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">{stats.get('hh_juniors', 0)}</div>
                        <div>HH Junior</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">{stats.get('sj_juniors', 0)}</div>
                        <div>SJ Junior</div>
                    </div>
                </div>
            """
        
        if not vacancies:
            html += """
                <div class="no-vacancies">
                    <h2>📭 Новых вакансий не найдено</h2>
                    <p>Проверьте позже или измените критерии поиска</p>
                </div>
            """
        else:
            # Сортируем по зарплате
            vacancies_sorted = sorted(
                vacancies, 
                key=lambda x: (x.get('salary_from', 0) or 0), 
                reverse=True
            )
            
            for i, vac in enumerate(vacancies_sorted, 1):
                platform_class = 'hh-badge' if vac.get('platform') == 'hh' else 'sj-badge'
                platform_name = 'HeadHunter' if vac.get('platform') == 'hh' else 'SuperJob'
                
                salary = self._format_salary(
                    vac.get('salary_from'), 
                    vac.get('salary_to'), 
                    vac.get('currency', 'RUR')
                )
                
                experience = vac.get('experience', '')
                if not experience:
                    experience = 'Не требуется'
                
                description = vac.get('description', '')[:200]
                if len(vac.get('description', '')) > 200:
                    description += '...'
                
                html += f"""
                <div class="vacancy">
                    <div class="vacancy-title">
                        {i}. {vac.get('title', 'Python Developer')}
                    </div>
                    <span class="platform-badge {platform_class}">{platform_name}</span>
                    <div class="salary">💰 {salary}</div>
                    <div class="experience">📚 Опыт: {experience}</div>
                    <div class="description">📝 {description if description else 'Описание отсутствует'}</div>
                    <a href="{vac.get('link', '#')}" class="link-button" target="_blank">
                        🔗 Открыть вакансию
                    </a>
                </div>
                """
        
        html += f"""
            </div>
            <div class="footer">
                <p>🤖 Автоматический парсер вакансий</p>
                <p>Следующая проверка через 6 часов</p>
                <p>{datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            </div>
        </body>
        </html>
        """
        return html
    
    def _format_salary(self, salary_from, salary_to, currency) -> str:
        """Красивое форматирование зарплаты"""
        if not salary_from and not salary_to:
            return "Не указана"
        
        parts = []
        if salary_from and salary_from > 0:
            parts.append(f"от {int(salary_from):,}".replace(',', ' '))
        if salary_to and salary_to > 0:
            parts.append(f"до {int(salary_to):,}".replace(',', ' '))
        
        salary_str = " — ".join(parts)
        currency_map = {
            'RUR': '₽',
            'USD': '$',
            'EUR': '€',
            'KZT': '₸'
        }
        currency_symbol = currency_map.get(currency, currency)
        
        return f"{salary_str} {currency_symbol}"
    
    def send_report(self, to_email: str, vacancies: List[dict], stats: Dict = None):
        """Отправка отчета на email"""
        if not vacancies:
            subject = '📭 Junior Python Developer - новых вакансий нет'
        else:
            subject = f'🔥 Junior Python Developer - {len(vacancies)} новых вакансий!'
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.login
        msg['To'] = to_email
        
        html_content = self._create_html_report(vacancies, stats)
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        
        try:
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.login, self.password)
                server.send_message(msg)
            print(f"✅ Отчет успешно отправлен на {to_email}")
            return True
        except Exception as e:
            print(f"❌ Ошибка отправки email: {str(e)}")
            return False