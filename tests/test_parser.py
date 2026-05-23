from parser import VacancyParser

from src.vacancy import Vacancy

parser = VacancyParser()

def test_junior_python_developer():
    vacancy = Vacancy(
        title='Junior Python разработчик',
        description='Разработчик',
        experience='None',
        link='www.balbes.com',
        salary_from='250',
        salary_to='500',
        currency='RUR',
        platform='hh'
    )
    result = parser.is_junior_vacancy(vacancy)
    assert result, f'Ожидалось True, получено {result}'


def test_vacancy_from_blacklist():
    vacancy = Vacancy(
        title='Junior военный истрибитель',
        description='военный',
        experience='None',
        link='www.balbes.com',
        salary_from='250',
        salary_to='500',
        currency='RUR',
        platform='hh'
    )
    result = parser.is_junior_vacancy(vacancy)
    assert not result, f'Ожидалось False, получено {result}'


def test_senior_with_exp():
    vacancy = Vacancy(
        title='Senior Python Developer',
        description='Разработчик ПО',
        experience='5',
        link='www.balbes.com',
        salary_from='250',
        salary_to='500',
        currency='RUR',
        platform='hh'
    )
    result = parser.is_junior_vacancy(vacancy)
    assert not result, f'Должно быть false, получили {result}'

def test_junior_low_lvl():
    vacancy = Vacancy(
        title='Стажер без опыта',
        description='Разработчик python без опыта',
        experience='None',
        link='www.balbes.com',
        salary_from='250',
        salary_to='500',
        currency='RUR',
        platform='hh'
    )
    result = parser.is_junior_vacancy(vacancy)
    assert result, f'Должно быть True, получили {result}'

def test_seller_not_developer():
    vacancy = Vacancy(
        title='Продавец консультант',
        description='Продавать носки',
        experience='None',
        link='www.balbes.com',
        salary_from='250',
        salary_to='500',
        currency='RUR',
        platform='hh'
    )
    result = parser.is_junior_vacancy(vacancy)
    assert not result, f'Должно быть False, получили {result}'


if __name__ == '__main__':
    test_junior_python_developer()
    test_vacancy_from_blacklist()
    test_senior_with_exp()
    print("Все тесты пройдены")



