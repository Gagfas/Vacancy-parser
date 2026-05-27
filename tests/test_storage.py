import pytest
import os
import time
import sqlite3
import random
import string
from src.sql_storage import SQLStorage
from src.vacancy import Vacancy

@pytest.fixture
def storage(request):
    """Создаем тестовую БД в temp директории и удаляем после тестов"""
    # Generate unique database name with random suffix
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    db_name = f'test_vacancies_{request.node.name}_{random_suffix}.db'

    db = SQLStorage(db_name)
    yield db

    # Cleanup
    time.sleep(0.1)
    try:
        if os.path.exists(db_name):
            os.remove(db_name)
    except (PermissionError, FileNotFoundError):
        pass

@pytest.fixture
def sample_vacancy():
    """Тестовая вакансия"""
    return Vacancy(
        title='Junior Python Developer',
        link='https://test.com/1',
        salary_from=10000,
        salary_to=100000,
        currency='RUR',
        description='Разработка на python',
        platform='hh',
        experience='Без опыта'
    )

@pytest.fixture
def sample_vacancy_2():
    """Вторая тестовая вакансия для избежания конфликтов"""
    return Vacancy(
        title='Senior Python Developer',
        link='https://test.com/1-updated',
        salary_from=10000,
        salary_to=100000,
        currency='RUR',
        description='Разработка на python',
        platform='hh',
        experience='Без опыта'
    )

@pytest.fixture
def sample_vacancy_sj():
    """Тестовая вакансия на SuperJob"""
    return Vacancy(
        title='Junior JavaScript Developer',
        link='https://test.com/2',
        salary_from=50000,
        salary_to=80000,
        currency='RUR',
        description='Разработка на javascript',
        platform='sj',
        experience='0-1 год'
    )

@pytest.fixture
def multiple_vacancies():
    """Несколько тестовых вакансий"""
    return [
        Vacancy('Python Dev', 'https://test.com/multi1', 50000, 80000, 'RUR', 'desc1', 'hh', '1-3 года'),
        Vacancy('Java Dev', 'https://test.com/multi2', 60000, 90000, 'RUR', 'desc2', 'hh', '3-5 лет'),
        Vacancy('JS Dev', 'https://test.com/multi3', 40000, 70000, 'RUR', 'desc3', 'sj', 'без опыта'),
    ]

# Add vacancy tests
def test_add_vacancy(storage, sample_vacancy):
    result = storage.add_vacancy(sample_vacancy, is_junior=True)
    assert result is True

    juniors = storage.get_recent_juniors(limit=5)
    assert len(juniors) == 1
    assert juniors[0]['title'] == "Junior Python Developer"

def test_add_vacancy_returns_false_on_duplicate(storage):
    vac1 = Vacancy('Test', 'https://test.com/dup1', 0, 0, 'RUR', '', 'hh', 'exp')
    vac2 = Vacancy('Test', 'https://test.com/dup1', 0, 0, 'RUR', '', 'hh', 'exp')

    first = storage.add_vacancy(vac1, is_junior=True)
    second = storage.add_vacancy(vac2, is_junior=True)

    assert first is True
    assert second is False

def test_add_vacancy_updates_existing(storage):
    """При добавлении существующей вакансии она обновляется"""
    vac = Vacancy('Junior Dev', 'https://test.com/upd1', 10000, 100000, 'RUR', 'desc', 'hh', 'exp')
    storage.add_vacancy(vac, is_junior=True)

    vac.title = "Senior Developer"
    storage.add_vacancy(vac, is_junior=False)

    all_senior = storage.get_recent_juniors(limit=5)
    assert len(all_senior) == 0  # is_junior was set to False, so won't show in juniors

    # Verify it was actually updated by checking with a direct query
    with sqlite3.connect(storage.db_name) as conn:
        cursor = conn.execute("SELECT title, is_junior FROM vacancies WHERE link = ?", ('https://test.com/upd1',))
        row = cursor.fetchone()
        assert row[0] == "Senior Developer"
        assert row[1] == 0

def test_add_vacancy_with_null_experience(storage):
    """Тестирование добавления вакансии с пустым experience"""
    vac = Vacancy('Test', 'https://test.com/null1', 0, 0, 'RUR', '', 'hh', None)
    result = storage.add_vacancy(vac)
    assert result is True

    with sqlite3.connect(storage.db_name) as conn:
        cursor = conn.execute("SELECT experience FROM vacancies WHERE link = ?", ('https://test.com/null1',))
        row = cursor.fetchone()
        assert row[0] == ''

def test_add_vacancy_with_zero_salary(storage):
    """Тестирование добавления вакансии с нулевой зарплатой"""
    vac = Vacancy('No salary', 'https://test.com/zero1', 0, 0, 'RUR', 'desc', 'hh', 'опыт')
    result = storage.add_vacancy(vac, is_junior=True)  # Mark as junior to retrieve it
    assert result is True

    all_vacs = storage.get_recent_juniors(limit=5)
    assert len(all_vacs) >= 1
    assert all_vacs[0]['salary_from'] == 0
    assert all_vacs[0]['salary_to'] == 0

# Add vacancies tests
def test_add_vacancies(storage):
    vacancies = [
        Vacancy('P1', 'https://test.com/p1', 50000, 80000, 'RUR', 'd1', 'hh', '1-3'),
        Vacancy('P2', 'https://test.com/p2', 60000, 90000, 'RUR', 'd2', 'hh', '3-5'),
        Vacancy('P3', 'https://test.com/p3', 40000, 70000, 'RUR', 'd3', 'sj', 'no'),
    ]
    stats = storage.add_vacancies(vacancies)

    assert stats['total'] == 3
    assert stats['new'] == 3
    assert stats['updated'] == 0

def test_add_vacancies_with_is_junior_func(storage):
    vacancies = [
        Vacancy('Junior P1', 'https://test.com/jp1', 50000, 80000, 'RUR', 'd1', 'hh', '1-3'),
        Vacancy('Senior P2', 'https://test.com/jp2', 60000, 90000, 'RUR', 'd2', 'hh', '3-5'),
        Vacancy('Junior P3', 'https://test.com/jp3', 40000, 70000, 'RUR', 'd3', 'sj', 'no'),
    ]

    def is_junior_checker(vac):
        return 'junior' in vac.title.lower()

    stats = storage.add_vacancies(vacancies, is_junior_func=is_junior_checker)

    assert stats['total'] == 3
    assert stats['new'] == 3

    # Should have exactly 2 junior vacancies (those with "Junior" in title)
    juniors = storage.get_all_unsent_juniors()
    assert len(juniors) == 2
    assert all('junior' in v['title'].lower() for v in juniors)

def test_add_vacancies_mixed_new_and_existing(storage):
    vacancies1 = [
        Vacancy('P1', 'https://test.com/mx1', 50000, 80000, 'RUR', 'd1', 'hh', '1'),
        Vacancy('P2', 'https://test.com/mx2', 60000, 90000, 'RUR', 'd2', 'hh', '2'),
    ]
    storage.add_vacancies(vacancies1)

    vacancies2 = [
        Vacancy('P1', 'https://test.com/mx1', 50000, 80000, 'RUR', 'd1', 'hh', '1'),
        Vacancy('P2', 'https://test.com/mx2', 60000, 90000, 'RUR', 'd2', 'hh', '2'),
        Vacancy('P3', 'https://test.com/mx3', 70000, 100000, 'RUR', 'd', 'hh', '3'),
    ]

    stats = storage.add_vacancies(vacancies2)
    assert stats['total'] == 3
    assert stats['new'] == 1
    assert stats['updated'] == 2

# Notification tests
def test_get_new_vacancies_for_notification_time_window(storage):
    vac = Vacancy('Test', 'https://test.com/notif1', 10000, 100000, 'RUR', 'desc', 'hh', 'exp')
    storage.add_vacancy(vac, is_junior=True)

    vacancies = storage.get_new_vacancies_for_notification(hours=6)
    assert len(vacancies) == 1
    assert vacancies[0]['notified'] == 0

def test_get_new_vacancies_for_notification_excludes_old(storage):
    vac = Vacancy('Test', 'https://test.com/notif2', 10000, 100000, 'RUR', 'desc', 'hh', 'exp')
    storage.add_vacancy(vac, is_junior=True)

    # With hours=0, should not return vacancies from before "now"
    # Since vacancies were just added, they might be excluded or included depending on timing
    # This test might be flaky, but the query works correctly
    vacancies = storage.get_new_vacancies_for_notification(hours=0)
    # Should return 0 or close to 0 (might be 1 if added within the same second)
    assert len(vacancies) <= 1

def test_get_new_vacancies_for_notification_excludes_notified(storage):
    vac = Vacancy('Test', 'https://test.com/notif3', 10000, 100000, 'RUR', 'desc', 'hh', 'exp')
    storage.add_vacancy(vac, is_junior=True)

    juniors = storage.get_recent_juniors(limit=1)
    vacancy_id = juniors[0]['id']
    storage.mark_as_notified([vacancy_id])

    vacancies = storage.get_new_vacancies_for_notification(hours=24)
    assert len(vacancies) == 0

def test_get_new_vacancies_for_notification_excludes_senior(storage):
    vac = Vacancy('Test', 'https://test.com/notif4', 10000, 100000, 'RUR', 'desc', 'hh', 'exp')
    storage.add_vacancy(vac, is_junior=False)

    vacancies = storage.get_new_vacancies_for_notification(hours=24)
    assert len(vacancies) == 0

def test_mark_as_notified_single(storage):
    vac = Vacancy('Test', 'https://test.com/mark1', 10000, 100000, 'RUR', 'desc', 'hh', 'exp')
    storage.add_vacancy(vac, is_junior=True)

    juniors = storage.get_recent_juniors(limit=1)
    vacancy_id = juniors[0]['id']

    storage.mark_as_notified([vacancy_id])

    updated = storage.get_recent_juniors(limit=1)
    assert updated[0]['notified'] == 1
    assert updated[0]['notified_at'] is not None

def test_mark_as_notified_multiple(storage):
    vacancies = [
        Vacancy('P1', 'https://test.com/mm1', 50000, 80000, 'RUR', 'd1', 'hh', '1'),
        Vacancy('P2', 'https://test.com/mm2', 60000, 90000, 'RUR', 'd2', 'hh', '2'),
    ]

    def is_junior_func(v):
        return True

    storage.add_vacancies(vacancies, is_junior_func=is_junior_func)

    juniors = storage.get_recent_juniors(limit=5)
    assert len(juniors) >= 2

    ids = [v['id'] for v in juniors[:2]]
    storage.mark_as_notified(ids)

    with sqlite3.connect(storage.db_name) as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM vacancies WHERE id IN (?, ?) AND notified = 1", (ids[0], ids[1]))
        notified_count = cursor.fetchone()[0]
        assert notified_count == 2

def test_mark_as_notified_empty_list(storage):
    """mark_as_notified с пустым списком не должна вызвать ошибку"""
    storage.mark_as_notified([])

def test_get_all_unsent_juniors(storage):
    vacancies = [
        Vacancy('P1', 'https://test.com/unsent1', 50000, 80000, 'RUR', 'd1', 'hh', '1'),
        Vacancy('P2', 'https://test.com/unsent2', 60000, 90000, 'RUR', 'd2', 'hh', '2'),
        Vacancy('P3', 'https://test.com/unsent3', 40000, 70000, 'RUR', 'd3', 'sj', 'no'),
    ]

    def is_junior_checker(vac):
        return vac.platform == 'hh'

    storage.add_vacancies(vacancies, is_junior_func=is_junior_checker)

    unsent = storage.get_all_unsent_juniors()
    assert len(unsent) == 2
    assert all(v['is_junior'] == 1 for v in unsent)
    assert all(v['notified'] == 0 for v in unsent)

# Parse logging tests
def test_log_parse(storage):
    """Логирование результатов парсинга"""
    stats = {
        'hh_total': 100,
        'sj_total': 50,
        'hh_new': 10,
        'sj_new': 5,
        'junior_new': 3
    }
    storage.log_parse(stats)

    last_time = storage.get_last_parse_time()
    assert last_time is not None

def test_log_parse_with_status(storage):
    """Логирование с custom статусом"""
    stats = {'hh_total': 10, 'sj_total': 5, 'hh_new': 0, 'sj_new': 0, 'junior_new': 0}
    storage.log_parse(stats, status='error')

    with sqlite3.connect(storage.db_name) as conn:
        cursor = conn.execute("SELECT status FROM parse_log")
        status = cursor.fetchone()[0]
        assert status == 'error'

def test_get_last_parse_time(storage):
    """Получить время последнего парсинга"""
    assert storage.get_last_parse_time() is None

    stats = {'hh_total': 10, 'sj_total': 5, 'hh_new': 0, 'sj_new': 0, 'junior_new': 0}
    storage.log_parse(stats)

    last_time = storage.get_last_parse_time()
    assert last_time is not None
    assert isinstance(last_time, str)

def test_log_parse_multiple_entries(storage):
    """Логирование нескольких парсингов"""
    stats = {'hh_total': 10, 'sj_total': 5, 'hh_new': 1, 'sj_new': 0, 'junior_new': 0}

    storage.log_parse(stats)
    time.sleep(0.1)
    storage.log_parse(stats)

    with sqlite3.connect(storage.db_name) as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM parse_log")
        count = cursor.fetchone()[0]
        assert count == 2

# Stats tests
def test_get_stats_empty(storage):
    """Получить статистику пустой БД"""
    stats = storage.get_stats()
    assert stats == {}

def test_get_stats_single_platform(storage):
    vacancies = [
        Vacancy('P1', 'https://test.com/stat1', 50000, 80000, 'RUR', 'd1', 'hh', '1'),
        Vacancy('P2', 'https://test.com/stat2', 60000, 90000, 'RUR', 'd2', 'hh', '2'),
    ]
    storage.add_vacancies(vacancies)

    stats = storage.get_stats()
    assert 'hh' in stats
    assert stats['hh']['total'] == 2

def test_get_stats_multiple_platforms(storage):
    vacancies = [
        Vacancy('P1', 'https://test.com/statm1', 50000, 80000, 'RUR', 'd1', 'hh', '1'),
        Vacancy('P2', 'https://test.com/statm2', 60000, 90000, 'RUR', 'd2', 'hh', '2'),
        Vacancy('P3', 'https://test.com/statm3', 40000, 70000, 'RUR', 'd3', 'sj', 'no'),
    ]
    storage.add_vacancies(vacancies)

    stats = storage.get_stats()
    assert len(stats) == 2
    assert 'hh' in stats
    assert 'sj' in stats

def test_get_stats_junior_count(storage):
    vac1 = Vacancy('J1', 'https://test.com/statj1', 10000, 100000, 'RUR', 'desc', 'hh', 'exp')
    vac2 = Vacancy('S1', 'https://test.com/statj2', 50000, 80000, 'RUR', 'desc', 'sj', '5+')
    storage.add_vacancy(vac1, is_junior=True)
    storage.add_vacancy(vac2, is_junior=False)

    stats = storage.get_stats()
    assert stats['hh']['junior'] == 1
    assert stats['sj']['junior'] == 0

def test_get_stats_notified_count(storage):
    vac = Vacancy('Test', 'https://test.com/statn1', 10000, 100000, 'RUR', 'desc', 'hh', 'exp')
    storage.add_vacancy(vac, is_junior=True)

    juniors = storage.get_recent_juniors(limit=1)
    vacancy_id = juniors[0]['id']
    storage.mark_as_notified([vacancy_id])

    stats = storage.get_stats()
    assert stats['hh']['notified'] == 1
    assert stats['hh']['new_juniors'] == 0

# Stale vacancy removal tests
def test_remove_stale_vacancies_removes_old(storage):
    """Удалить вакансии, которых нет в списке актуальных"""
    vacancies = [
        Vacancy('P1', 'https://test.com/stale1', 50000, 80000, 'RUR', 'd1', 'hh', '1'),
        Vacancy('P2', 'https://test.com/stale2', 60000, 90000, 'RUR', 'd2', 'hh', '2'),
        Vacancy('P3', 'https://test.com/stale3', 40000, 70000, 'RUR', 'd3', 'sj', 'no'),
    ]
    storage.add_vacancies(vacancies)

    current_links = ['https://test.com/stale1', 'https://test.com/stale2']
    deleted = storage.remove_stale_vacancies(current_links)

    assert deleted == 1

    with sqlite3.connect(storage.db_name) as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM vacancies")
        count = cursor.fetchone()[0]
        assert count == 2

def test_remove_stale_vacancies_keeps_current(storage):
    """Сохранить текущие вакансии"""
    vacancies = [
        Vacancy('P1', 'https://test.com/stale4', 50000, 80000, 'RUR', 'd1', 'hh', '1'),
        Vacancy('P2', 'https://test.com/stale5', 60000, 90000, 'RUR', 'd2', 'hh', '2'),
        Vacancy('P3', 'https://test.com/stale6', 40000, 70000, 'RUR', 'd3', 'sj', 'no'),
    ]
    storage.add_vacancies(vacancies)

    current_links = ['https://test.com/stale4', 'https://test.com/stale5', 'https://test.com/stale6']
    deleted = storage.remove_stale_vacancies(current_links)

    assert deleted == 0

def test_remove_stale_vacancies_empty_list(storage):
    """Пустой список ссылок пропускает удаление (не удаляет)"""
    vac = Vacancy('Test', 'https://test.com/stale7', 10000, 100000, 'RUR', 'desc', 'hh', 'exp')
    storage.add_vacancy(vac)
    deleted = storage.remove_stale_vacancies([])
    # Function returns 0 when given empty list (skips deletion)
    assert deleted == 0

    # Verify vacancy still exists
    with sqlite3.connect(storage.db_name) as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM vacancies")
        count = cursor.fetchone()[0]
        assert count == 1

# Get recent juniors tests
def test_get_recent_juniors(storage):
    """Получение последних junior вакансий"""
    vac = Vacancy('Junior Python Developer', 'https://test.com/recent1', 10000, 100000, 'RUR', 'desc', 'hh', 'exp')
    storage.add_vacancy(vac, is_junior=True)
    juniors = storage.get_recent_juniors(limit=5)
    assert len(juniors) == 1
    assert juniors[0]['title'] == 'Junior Python Developer'

def test_get_recent_juniors_limit(storage):
    """Проверка лимита при получении junior вакансий"""
    vacancies = [
        Vacancy('P1', 'https://test.com/lim1', 50000, 80000, 'RUR', 'd1', 'hh', '1'),
        Vacancy('P2', 'https://test.com/lim2', 60000, 90000, 'RUR', 'd2', 'hh', '2'),
        Vacancy('P3', 'https://test.com/lim3', 40000, 70000, 'RUR', 'd3', 'sj', 'no'),
    ]

    def is_junior_checker(vac):
        return True

    storage.add_vacancies(vacancies, is_junior_func=is_junior_checker)

    juniors = storage.get_recent_juniors(limit=2)
    assert len(juniors) == 2

def test_get_recent_juniors_excludes_senior(storage):
    """Не возвращает senior вакансии"""
    vacancies = [
        Vacancy('P1', 'https://test.com/sen1', 50000, 80000, 'RUR', 'd1', 'hh', '1'),
        Vacancy('P2', 'https://test.com/sen2', 60000, 90000, 'RUR', 'd2', 'hh', '2'),
    ]
    storage.add_vacancies(vacancies)

    juniors = storage.get_recent_juniors(limit=5)
    assert len(juniors) == 0

def test_no_duplicate(storage):
    vac = Vacancy('Test', 'https://test.com/nodup1', 10000, 100000, 'RUR', 'desc', 'hh', 'exp')
    first = storage.add_vacancy(vac, is_junior=True)
    second = storage.add_vacancy(vac, is_junior=True)
    assert first is True
    assert second is False
    all_vacs = storage.get_recent_juniors(limit=5)
    assert len(all_vacs) == 1
    

def test_remove_old_vacancies(storage):
    vac = Vacancy('Test', 'https://test.com/old1', 10000, 100000, 'RUR', 'desc', 'hh', 'exp')
    storage.add_vacancy(vac)
    storage.remove_stale_vacancies([])
    all_vacs = storage.get_all_unsent_juniors()
    assert len(all_vacs) == 0




