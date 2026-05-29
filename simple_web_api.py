import sqlite3
from parser import VacancyParser
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from config import Config

app = FastAPI(title='Парсер вакансий Python', version='2.0')

parser = None

def get_parser():
    global parser
    if parser is None:
        parser = VacancyParser()
    return parser

def get_db():
    conn = sqlite3.connect('vacancies.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/", response_class=HTMLResponse)
async def index():
    config = Config()
    search_query = config.search_query
    return generate_main_page(search_query)

@app.get('/api/vacancies')
async def get_vacancies(
    search: str = Query(default=''),
    platform: str = Query(default=''),
    is_junior: Optional[bool] = Query(default=None),
    min_salary: Optional[int] = Query(default=None),
    limit: int = Query(default=100),
    offset: int = Query(default=0)
):
    conn = get_db()
    cursor = conn.cursor()
    query = 'SELECT * FROM vacancies WHERE 1=1'
    params = []

    if is_junior is not None:
        query += ' AND is_junior = ?'
        params.append(is_junior)

    if platform:
        query += ' AND platform = ?'
        params.append(platform)
    
    if min_salary:
        query += ' AND (salary_from >= ? OR salary_to >= ?)'
        params.extend([min_salary, min_salary])

    if search:
        query += ' AND (title LIKE ? OR description LIKE ?)'
        params.extend([f'%{search}', f'%{search}'])

    count_query = query.replace('SELECT *', 'SELECT COUNT(*) as total')
    cursor.execute(count_query, params)
    total = cursor.fetchone()['total']
    query += ' ORDER BY first_seen_at DESC LIMIT ? OFFSET ?'
    params.extend([limit, offset])
    cursor.execute(query, params)
    vacancies = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {'total': total, 'vacancies':vacancies, 'limit':limit, 'offset':offset}

@app.get("/api/stats")
async def get_stats():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN is_junior = 1 THEN 1 ELSE 0 END) as junior_count,
            SUM(CASE WHEN platform = 'hh' THEN 1 ELSE 0 END) as hh_count,
            SUM(CASE WHEN platform = 'sj' THEN 1 ELSE 0 END) as sj_count,
            AVG(
                CASE 
                    WHEN salary_from > 0 AND salary_to > 0 THEN (salary_from + salary_to) / 2.0
                    WHEN salary_from > 0 THEN salary_from
                    WHEN salary_to > 0 THEN salary_to
                    ELSE NULL
                END
            ) as avg_salary
        FROM vacancies
    """)
    
    stats = dict(cursor.fetchone())
    
    # Получаем время последнего парсинга
    cursor.execute("SELECT MAX(parse_time) as last_parse FROM parse_log")
    last_parse = cursor.fetchone()['last_parse']
    
    stats['last_update'] = last_parse
    stats['avg_salary'] = int(stats['avg_salary']) if stats['avg_salary'] else 0
    
    conn.close()
    return stats

@app.post('/api/parse')
async def trigger_parse():
    #Start parser
    try:
        p = get_parser()
        stats = p.parse_vacancies()
        return {'status':'success', 'stats':stats}
    except Exception as e:
        return {'status':'error', 'message': str(e)}
    
@app.get('/api/parse/status')
async def parse_status():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT MAX(first_seen_at) as last_parse FROM vacancies')
    result = cursor.fetchone()
    conn.close()

    return {
        'last_parse': result['last_parse'] if result else None,
        'parser_ready': parser is not None
    }

def generate_main_page(search_query: str):
    """Генерация HTML главной страницы"""
    html_content = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🐍 Парсер вакансий SEARCH_QUERY_PLACEHOLDER</title>
    """
    
    
    html_content += """
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #ffffff 0%, #4d006e 100%);
                min-height: 100vh;
                color: #eee;
            }
            
            .container {
                max-width: 1400px;
                margin: 0 auto;
                padding: 20px;
            }
            
            .header {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 30px;
                margin-bottom: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                text-align: center;
            }
            
            .header h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
                background: linear-gradient(135deg, #667eea, #764ba2);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            
            .header p {
                color: #666;
                font-size: 1.1em;
            }
            
            .controls {
                display: flex;
                gap: 15px;
                justify-content: center;
                margin-top: 20px;
                flex-wrap: wrap;
            }
            
            .btn {
                padding: 12px 30px;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                cursor: pointer;
                transition: all 0.3s;
                font-weight: 500;
                text-decoration: none;
                display: inline-flex;
                align-items: center;
                gap: 8px;
            }
            
            .btn-primary {
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
            }
            
            .btn-primary:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            }
            
            .btn-success {
                background: #28a745;
                color: white;
            }
            
            .btn-success:hover {
                background: #218838;
                transform: translateY(-2px);
            }
            
            .btn:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            
            .stat-card {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                padding: 25px;
                text-align: center;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                transition: transform 0.3s;
            }
            
            .stat-card:hover {
                transform: translateY(-5px);
            }
            
            .stat-value {
                font-size: 2.5em;
                font-weight: bold;
                background: linear-gradient(135deg, #667eea, #764ba2);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            
            .stat-label {
                color: #666;
                margin-top: 10px;
                font-size: 0.9em;
            }
            
            .filters-bar {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }
            
            .filter-group {
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
                align-items: center;
            }
            
            .filter-group input,
            .filter-group select {
                padding: 10px 15px;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                font-size: 14px;
                outline: none;
                transition: border-color 0.3s;
            }
            
            .filter-group input:focus,
            .filter-group select:focus {
                border-color: #667eea;
            }
            
            .vacancies-container {
                display: grid;
                gap: 20px;
            }
            
            .vacancy-card {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                padding: 25px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                transition: all 0.3s;
                border-left: 4px solid #667eea;
            }
            
            .vacancy-card:hover {
                transform: translateX(5px);
                box-shadow: 0 8px 25px rgba(0,0,0,0.15);
            }
            
            .vacancy-card.junior {
                border-left-color: #ffd700;
            }
            
            .vacancy-header {
                display: flex;
                justify-content: space-between;
                align-items: start;
                margin-bottom: 15px;
                flex-wrap: wrap;
                gap: 10px;
            }
            
            .vacancy-title {
                font-size: 1.2em;
                font-weight: 600;
                color: #333;
                flex: 1;
            }
            
            .badge {
                padding: 5px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 500;
                white-space: nowrap;
            }
            
            .badge-hh {
                background: #ff6b6b;
                color: white;
            }
            
            .badge-sj {
                background: #4ecdc4;
                color: white;
            }
                        
            .badge-zp {
                background: #f39c12; 
                color: white; 
            }
                        
            .badge-junior {
                background: #ffd700;
                color: #333;
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.7; }
            }
            
            .salary {
                font-size: 1.1em;
                color: #28a745;
                font-weight: 600;
                margin: 10px 0;
            }
            
            .description {
                color: #666;
                line-height: 1.6;
                margin: 10px 0;
                max-height: 100px;
                overflow-y: auto;
            }
            
            .meta {
                display: flex;
                gap: 20px;
                color: #999;
                font-size: 0.85em;
                margin-top: 15px;
                flex-wrap: wrap;
            }
            
            .loading {
                text-align: center;
                padding: 40px;
                color: white;
                font-size: 1.2em;
            }
            
            .spinner {
                border: 4px solid rgba(255,255,255,0.3);
                border-top: 4px solid white;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 20px;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .empty-state {
                text-align: center;
                padding: 60px;
                color: white;
            }
            
            .empty-state h2 {
                font-size: 2em;
                margin-bottom: 20px;
            }
            
            .toast {
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 15px 25px;
                border-radius: 10px;
                color: white;
                font-weight: 500;
                z-index: 1000;
                animation: slideIn 0.3s ease-out;
            }
            
            @keyframes slideIn {
                from { transform: translateX(100px); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔍 Вакансии: SEARCH_QUERY_PLACEHOLDER</h1>
                <p>Актуальные вакансии для начинающих разработчиков</p>
                <div class="controls">
                    <button class="btn btn-primary" onclick="fetchStats()">
                        📊 Обновить статистику
                    </button>
                    <button class="btn btn-success" onclick="triggerParse()" id="parseBtn">
                        🔄 Запустить парсинг
                    </button>
                    <a href="/docs" class="btn" style="background: #6c757d; color: white;">
                        📚 API Docs
                    </a>
                </div>
            </div>
            
            <div class="stats-grid" id="statsGrid">
                <div class="stat-card">
                    <div class="stat-value" id="totalVacancies">-</div>
                    <div class="stat-label">Всего вакансий</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="juniorCount">-</div>
                    <div class="stat-label">Junior вакансий</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="avgSalary">-</div>
                    <div class="stat-label">Средняя зарплата</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="lastUpdate">-</div>
                    <div class="stat-label">Последнее обновление</div>
                </div>
            </div>
            
            <div class="filters-bar">
                <div class="filter-group">
                    <input type="text" id="searchInput" placeholder="🔍 Поиск по названию..." onkeyup="filterVacancies()">
                    <select id="platformFilter" onchange="filterVacancies()">
                        <option value="">Все платформы</option>
                        <option value="hh">HeadHunter</option>
                        <option value="sj">SuperJob</option>
                        <option value="zp">Zarplata</option>
                    </select>
                    <select id="juniorFilter" onchange="filterVacancies()">
                        <option value="">Все уровни</option>
                        <option value="true">Только Junior</option>
                    </select>
                    <button class="btn btn-primary" onclick="filterVacancies()">🔍 Применить</button>
                </div>
            </div>
            
            <div id="vacanciesContainer" class="vacancies-container">
                <div class="loading">
                    <div class="spinner"></div>
                    Загрузка вакансий...
                </div>
            </div>
        </div>
        
        <script>
            let allVacancies = [];
            
            document.addEventListener('DOMContentLoaded', function() {
                fetchStats();
                fetchVacancies();
            });
            
            function fetchStats() {
                fetch('/api/stats')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('totalVacancies').textContent = data.total || 0;
                        document.getElementById('juniorCount').textContent = data.junior_count || 0;
                        document.getElementById('avgSalary').textContent = (data.avg_salary || 0) + ' ₽';
                        
                        if (data.last_update) {
                            const date = new Date(data.last_update);
                            document.getElementById('lastUpdate').textContent = 
                                date.toLocaleString('ru-RU');
                        } else {
                            document.getElementById('lastUpdate').textContent = 'Никогда';
                        }
                    })
                    .catch(error => console.error('Error fetching stats:', error));
            }
            
            function fetchVacancies() {
                const search = document.getElementById('searchInput').value;
                const platform = document.getElementById('platformFilter').value;
                const isJunior = document.getElementById('juniorFilter').value;
                
                let url = '/api/vacancies?limit=100';
                if (search) url += '&search=' + encodeURIComponent(search);
                if (platform) url += '&platform=' + platform;
                if (isJunior) url += '&is_junior=' + isJunior;
                
                fetch(url)
                    .then(response => response.json())
                    .then(data => {
                        allVacancies = data.vacancies || [];
                        renderVacancies(allVacancies);
                    })
                    .catch(error => {
                        console.error('Error fetching vacancies:', error);
                        document.getElementById('vacanciesContainer').innerHTML = 
                            '<div class="loading">❌ Ошибка загрузки</div>';
                    });
            }
            
            function renderVacancies(vacancies) {
                const container = document.getElementById('vacanciesContainer');
                
                if (!vacancies || vacancies.length === 0) {
                    container.innerHTML = '<div class="empty-state"><h2>📭 Вакансии не найдены</h2><p>Запустите парсинг или измените фильтры</p></div>';
                    return;
                }
                
                let html = '';
                vacancies.forEach(vac => {
                    const platformBadge = vac.platform === 'hh' ? 'badge-hh' : 
                                          vac.platform === 'sj' ? 'badge-sj' : 'badge-zp';
                    const platformName = vac.platform === 'hh' ? 'HH' : 
                                         vac.platform === 'sj' ? 'SJ' : 'ZP';
                    const juniorClass = vac.is_junior ? 'junior' : '';
                    const juniorBadge = vac.is_junior ? '<span class="badge badge-junior">Junior</span>' : '';
                    
                    let salaryText = '💰 Зарплата не указана';
                    if (vac.salary_from || vac.salary_to) {
                        let parts = [];
                        if (vac.salary_from > 0) parts.push('от ' + formatNumber(vac.salary_from));
                        if (vac.salary_to > 0) parts.push('до ' + formatNumber(vac.salary_to));
                        if (parts.length > 0) {
                            salaryText = '💰 ' + parts.join(' - ') + ' ' + (vac.currency || 'rub');
                        }
                    }
                    
                    let desc = vac.description || '';
                    if (desc.length > 300) desc = desc.substring(0, 300) + '...';
                    
                    const date = vac.first_seen_at ? new Date(vac.first_seen_at).toLocaleString('ru-RU') : '';
                    
                    html += '<div class="vacancy-card ' + juniorClass + '">' +
                        '<div class="vacancy-header">' +
                            '<div class="vacancy-title">' + (vac.title || 'Без названия') + '</div>' +
                            '<div>' +
                                '<span class="badge ' + platformBadge + '">' + platformName + '</span>' +
                                juniorBadge +
                            '</div>' +
                        '</div>' +
                        '<div class="salary">' + salaryText + '</div>' +
                        '<div class="description">' + desc + '</div>' +
                        '<div class="meta">' +
                            '<span>📅 ' + date + '</span>' +
                            '<span>📚 ' + (vac.experience || 'Не указан') + '</span>' +
                            '<span>🔗 <a href="' + vac.link + '" target="_blank" style="color: #667eea;">Открыть вакансию</a></span>' +
                        '</div>' +
                    '</div>';
                });
                
                container.innerHTML = html;
            }
            
            function filterVacancies() {
                fetchVacancies();
            }
            
            function triggerParse() {
                const btn = document.getElementById('parseBtn');
                btn.disabled = true;
                btn.textContent = '⏳ Парсинг...';
                
                fetch('/api/parse', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            showToast('✅ Парсинг завершен!', 'success');
                            fetchStats();
                            fetchVacancies();
                        } else {
                            showToast('❌ Ошибка: ' + data.message, 'error');
                        }
                        btn.disabled = false;
                        btn.textContent = '🔄 Запустить парсинг';
                    })
                    .catch(error => {
                        showToast('❌ Ошибка соединения', 'error');
                        btn.disabled = false;
                        btn.textContent = '🔄 Запустить парсинг';
                    });
            }
            
            function showToast(message, type) {
                const toast = document.createElement('div');
                toast.className = 'toast';
                toast.style.background = type === 'success' ? '#28a745' : '#dc3545';
                toast.textContent = message;
                document.body.appendChild(toast);
                
                setTimeout(() => { toast.remove(); }, 3000);
            }
            
            function formatNumber(num) {
                return num.toString().replace(/\\B(?=(\\d{3})+(?!\\d))/g, ' ');
            }
        </script>
    </body>
    </html>
    """
    
    html_content = html_content.replace("SEARCH_QUERY_PLACEHOLDER", search_query)
    
    return HTMLResponse(content=html_content)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


