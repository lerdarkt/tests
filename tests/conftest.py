import pytest
from rest_framework.test import APIClient
from model_bakery import baker
from students.models import Course, Student


@pytest.fixture
def api_client():
    """Фикстура для API-клиента"""
    return APIClient()


@pytest.fixture
def course_factory():
    """Фикстура-фабрика для создания курсов"""
    def make_course(**kwargs):
        return baker.make(Course, **kwargs)
    return make_course


@pytest.fixture
def student_factory():
    """Фикстура-фабрика для создания студентов"""
    def make_student(**kwargs):
        return baker.make(Student, **kwargs)
    return make_student
