import pytest
import os
import time
from src.sql_storage import SQLStorage
from src.vacancy import Vacancy

@pytest.fixture
def storage():
    """Создаем тестовую БД и удаляем после тестов"""
    db = SQLStorage('test_vacancies.db')
    yield db
    time.sleep(0.1)
    try:
        if os.path.exists('test_vacancies.db'):
            os.remove('test_vacancies.db')
    except PermissionError:
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

def test_add_vacancy(storage, sample_vacancy):
    storage.add_vacancy(sample_vacancy, is_junior=True)
    
    juniors = storage.get_recent_juniors(limit=5)
    
    assert len(juniors) == 1
    assert juniors[0]['title'] == "Junior Python Developer"

def test_no_duplicate(storage, sample_vacancy):
    first = storage.add_vacancy(sample_vacancy, is_junior = True)
    second = storage.add_vacancy(sample_vacancy, is_junior = True)
    all_vacs = storage.get_recent_juniors(limit=5)
    assert len(all_vacs) == 1

def test_remove_old_vacancies(storage, sample_vacancy):
    storage.add_vacancy(sample_vacancy)
    storage.remove_stale_vacancies([])
    all_vacs = storage.get_all_unsent_juniors()
    assert len(all_vacs) == 0

def test_get_recent_juniors(storage, sample_vacancy):
    """Получение последних junior вакансий"""
    storage.add_vacancy(sample_vacancy, is_junior=True)
    juniors = storage.get_recent_juniors(limit=5)
    assert len(juniors) == 1
    assert juniors[0]['title'] == 'Junior Python Developer'




