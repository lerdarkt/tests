import pytest
from django.urls import reverse
from rest_framework import status
from model_bakery import baker
from students.models import Course, Student
from django.test import override_settings


@pytest.mark.django_db
class TestCourseStudentLimits:
    """Тесты для ограничения количества студентов на курсе"""

    def test_add_student_to_course_within_limit(self, api_client, course_factory, student_factory):
        """Тест добавления студента на курс при соблюдении лимита"""
        # Создаем курс
        course = course_factory()
        
        # Создаем студента
        student = student_factory()
        
        # Добавляем студента на курс
        url = reverse('courses-add-student', args=[course.id])
        response = api_client.post(url, {'student_id': student.id}, format='json')
        
        # Проверяем успешное добавление
        assert response.status_code == status.HTTP_200_OK
        assert student in course.students.all()

    @pytest.mark.parametrize('max_students', [1, 5, 10, 20])
    def test_add_student_to_course_limit_enforced(self, api_client, course_factory, 
                                                   student_factory, settings, max_students):
        """Параметризованный тест проверки ограничения лимита"""
        # Устанавливаем лимит через настройки
        settings.MAX_STUDENTS_PER_COURSE = max_students
        
        # Создаем курс
        course = course_factory()
        
        # Создаем студентов в количестве, превышающем лимит на 1
        students = student_factory(_quantity=max_students + 1)
        
        # Добавляем студентов до предела
        for student in students[:max_students]:
            url = reverse('courses-add-student', args=[course.id])
            response = api_client.post(url, {'student_id': student.id}, format='json')
            assert response.status_code == status.HTTP_200_OK
        
        # Проверяем, что на курсе сейчас max_students студентов
        assert course.students.count() == max_students
        
        # Пытаемся добавить еще одного студента
        extra_student = students[max_students]
        url = reverse('courses-add-student', args=[course.id])
        response = api_client.post(url, {'student_id': extra_student.id}, format='json')
        
        # Проверяем, что добавление не удалось
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'maximum' in response.data['error'].lower() or 'limit' in response.data['error'].lower()
        assert extra_student not in course.students.all()

    @pytest.mark.parametrize('limit, num_students, should_succeed', [
        (20, 15, True),   # 15 < 20 - успех
        (20, 20, True),   # 20 == 20 - успех (на границе)
        (20, 21, False),  # 21 > 20 - ошибка
        (10, 5, True),    # 5 < 10 - успех
        (10, 10, True),   # 10 == 10 - успех
        (10, 11, False),  # 11 > 10 - ошибка
    ])
    def test_course_student_limit_boundaries(self, api_client, course_factory, 
                                              student_factory, settings, 
                                              limit, num_students, should_succeed):
        """Параметризованный тест граничных значений лимита"""
        # Устанавливаем лимит
        settings.MAX_STUDENTS_PER_COURSE = limit
        
        # Создаем курс
        course = course_factory()
        
        # Создаем студентов
        students = student_factory(_quantity=num_students)
        
        # Пытаемся добавить всех студентов
        success_count = 0
        for student in students:
            url = reverse('courses-add-student', args=[course.id])
            response = api_client.post(url, {'student_id': student.id}, format='json')
            if response.status_code == status.HTTP_200_OK:
                success_count += 1
        
        # Проверяем результат
        if should_succeed:
            assert success_count == num_students
            assert course.students.count() == num_students
        else:
            assert success_count == limit
            assert course.students.count() == limit
            # Проверяем, что последние студенты не были добавлены
            for student in students[limit:]:
                assert student not in course.students.all()

    def test_add_same_student_multiple_times(self, api_client, course_factory, student_factory, settings):
        """Тест добавления одного и того же студента несколько раз"""
        # Устанавливаем большой лимит
        settings.MAX_STUDENTS_PER_COURSE = 20
        
        # Создаем курс и студента
        course = course_factory()
        student = student_factory()
        
        # Добавляем студента первый раз
        url = reverse('courses-add-student', args=[course.id])
        response = api_client.post(url, {'student_id': student.id}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert student in course.students.all()
        
        # Пытаемся добавить того же студента второй раз
        response = api_client.post(url, {'student_id': student.id}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'already' in response.data['error'].lower() or 'exists' in response.data['error'].lower()
        
        # Проверяем, что студент все еще один в списке
        assert course.students.count() == 1

    def test_remove_student_from_course(self, api_client, course_factory, student_factory, settings):
        """Тест удаления студента с курса"""
        # Устанавливаем лимит
        settings.MAX_STUDENTS_PER_COURSE = 20
        
        # Создаем курс и студентов
        course = course_factory()
        students = student_factory(_quantity=3)
        
        # Добавляем студентов
        for student in students:
            url = reverse('courses-add-student', args=[course.id])
            response = api_client.post(url, {'student_id': student.id}, format='json')
            assert response.status_code == status.HTTP_200_OK
        
        # Проверяем, что все три студента на курсе
        assert course.students.count() == 3
        
        # Удаляем одного студента
        url = reverse('courses-remove-student', args=[course.id])
        response = api_client.delete(url, {'student_id': students[0].id}, format='json')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Проверяем, что студент удален
        assert course.students.count() == 2
        assert students[0] not in course.students.all()
        assert students[1] in course.students.all()
        assert students[2] in course.students.all()
        
        # Теперь можем добавить нового студента
        new_student = student_factory()
        url = reverse('courses-add-student', args=[course.id])
        response = api_client.post(url, {'student_id': new_student.id}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert new_student in course.students.all()
        assert course.students.count() == 3
