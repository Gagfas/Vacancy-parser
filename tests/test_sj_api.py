from unittest.mock import Mock, patch

import pytest

from ..src.api import SuperJobAPI


@pytest.fixture
def sj_api():
    return SuperJobAPI(api_key='test_key')


@patch('requests.get')
def test_get_vacancies(mock_get, sj_api):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'object':[]}
    mock_get.return_value = mock_response
    result = sj_api.get_vacancies('Python', page=0)
    assert len(result) == 1

@patch('requests.get')
def test_get_vacancies_bad_code(mock_get, sj_api):
    mock_response = Mock()
    mock_response.status_code = 401
    mock_get.return_value = mock_response
    result = sj_api.get_vacancies('Python', page=0)
    assert len(result) == 0

