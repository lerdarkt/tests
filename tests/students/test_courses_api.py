import pytest
from django.urls import reverse
from rest_framework import status
from model_bakery import baker
from students.models import Course


@pytest.mark.django_db
class TestCoursesAPI:
    """Тесты для API курсов"""

    def test_retrieve_course(self, api_client, course_factory):
        """Тест получения конкретного курса (retrieve-логика)"""
        # Создаем курс через фабрику
        course = course_factory(name="Test Course", description="Test Description")
        
        # Строим URL и делаем запрос
        url = reverse('courses-detail', args=[course.id])
        response = api_client.get(url)
        
        # Проверяем, что вернулся именно тот курс
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == course.id
        assert response.data['name'] == course.name
        assert response.data['description'] == course.description

    def test_list_courses(self, api_client, course_factory):
        """Тест получения списка курсов (list-логика)"""
        # Создаем несколько курсов через фабрику
        courses = course_factory(_quantity=3)
        
        # Делаем запрос на список
        url = reverse('courses-list')
        response = api_client.get(url)
        
        # Проверяем результат
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3
        
        # Проверяем, что все созданные курсы есть в ответе
        response_ids = [course['id'] for course in response.data]
        for course in courses:
            assert course.id in response_ids

    def test_filter_courses_by_id(self, api_client, course_factory):
        """Тест фильтрации списка курсов по id"""
        # Создаем курсы
        target_course = course_factory(name="Target Course")
        other_courses = course_factory(_quantity=3)
        
        # Фильтруем по id
        url = reverse('courses-list')
        response = api_client.get(url, {'id': target_course.id})
        
        # Проверяем, что вернулся только нужный курс
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['id'] == target_course.id
        assert response.data[0]['name'] == target_course.name

    def test_filter_courses_by_name(self, api_client, course_factory):
        """Тест фильтрации списка курсов по name"""
        # Создаем курсы с разными именами
        target_course = course_factory(name="Python Programming")
        course_factory(name="Java Programming")
        course_factory(name="Django Course")
        
        # Фильтруем по имени
        url = reverse('courses-list')
        response = api_client.get(url, {'name': "Python Programming"})
        
        # Проверяем, что вернулся только нужный курс
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['name'] == "Python Programming"
        assert response.data[0]['id'] == target_course.id

    def test_create_course_success(self, api_client):
        """Тест успешного создания курса"""
        # Подготавливаем JSON-данные
        course_data = {
            'name': 'New Course',
            'description': 'This is a new course'
        }
        
        # Отправляем POST-запрос
        url = reverse('courses-list')
        response = api_client.post(url, course_data, format='json')
        
        # Проверяем результат
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == course_data['name']
        assert response.data['description'] == course_data['description']
        
        # Проверяем, что курс действительно создался в базе
        assert Course.objects.count() == 1
        course = Course.objects.first()
        assert course.name == course_data['name']
        assert course.description == course_data['description']

    def test_update_course_success(self, api_client, course_factory):
        """Тест успешного обновления курса"""
        # Создаем курс через фабрику
        course = course_factory(name="Old Name", description="Old Description")
        
        # Подготавливаем данные для обновления
        updated_data = {
            'name': 'Updated Name',
            'description': 'Updated Description'
        }
        
        # Отправляем PATCH-запрос
        url = reverse('courses-detail', args=[course.id])
        response = api_client.patch(url, updated_data, format='json')
        
        # Проверяем результат
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == updated_data['name']
        assert response.data['description'] == updated_data['description']
        
        # Проверяем, что данные обновились в базе
        course.refresh_from_db()
        assert course.name == updated_data['name']
        assert course.description == updated_data['description']

    def test_delete_course_success(self, api_client, course_factory):
        """Тест успешного удаления курса"""
        # Создаем курс через фабрику
        course = course_factory(name="To Be Deleted")
        
        # Убеждаемся, что курс создался
        assert Course.objects.count() == 1
        
        # Отправляем DELETE-запрос
        url = reverse('courses-detail', args=[course.id])
        response = api_client.delete(url)
        
        # Проверяем результат
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Проверяем, что курс удален из базы
        assert Course.objects.count() == 0
