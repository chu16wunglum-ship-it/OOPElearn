from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from courses.models import Course, Lesson


class HomeTests(TestCase):
    def test_empty_database_shows_six_document_previews(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-course-card', count=6)
        self.assertFalse(response.context['has_live_courses'])
        self.assertEqual(Course.objects.count(), 0)

    def test_live_catalog_uses_all_courses_and_orders_units_numerically(self):
        teacher = User.objects.create_user(username='teacher', role=User.Role.TEACHER)
        for number in (10, 2, 1):
            course = Course.objects.create(teacher=teacher, title=f'หน่วยที่ {number}', description=f'เนื้อหา {number}')
            Lesson.objects.create(course=course, title=f'บทเรียน {number}', content_notes='PRIVATE_AI_REFERENCE')
        with self.assertNumQueries(2):
            response = self.client.get(reverse('home'))
        self.assertEqual([course['number'] for course in response.context['catalog']], [1, 2, 10])
        self.assertContains(response, 'data-course-card', count=3)
        self.assertContains(response, 'บทเรียน 10')
        self.assertNotContains(response, 'PRIVATE_AI_REFERENCE')
        self.assertTrue(response.context['has_live_courses'])

    def test_course_content_is_escaped(self):
        teacher = User.objects.create_user(username='teacher', role=User.Role.TEACHER)
        Course.objects.create(teacher=teacher, title='<script>alert(1)</script>')
        response = self.client.get(reverse('home'))
        self.assertContains(response, '&lt;script&gt;alert(1)&lt;/script&gt;')
        self.assertNotContains(response, '<script>alert(1)</script>')

    def test_authenticated_users_keep_their_dashboard_redirect(self):
        student = User.objects.create_user(username='student', role=User.Role.STUDENT)
        self.client.force_login(student)
        self.assertRedirects(self.client.get(reverse('home')), reverse('dashboard'), fetch_redirect_response=False)


class WorkspaceUITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from courses.models import Enrollment, VideoProgress
        from exams.models import Quiz, Question, Choice
        cls.teacher = User.objects.create_user(username='ui-teacher', role=User.Role.TEACHER)
        cls.student = User.objects.create_user(username='ui-student', role=User.Role.STUDENT, created_by=cls.teacher)
        cls.course = Course.objects.create(teacher=cls.teacher, title='หน่วยที่ 1 พื้นฐาน OOP')
        cls.lesson = Lesson.objects.create(course=cls.course, title='Class และ Object')
        Enrollment.objects.create(student=cls.student, course=cls.course)
        VideoProgress.objects.create(student=cls.student, lesson=cls.lesson, completed=True, duration_seconds=100, watched_seconds=100)
        cls.quiz = Quiz.objects.create(lesson=cls.lesson, kind='pretest')
        cls.question = Question.objects.create(quiz=cls.quiz, text='Class คืออะไร?')
        cls.choice = Choice.objects.create(question=cls.question, text='ต้นแบบของ Object', is_correct=True)

    def assert_workspace_routes(self, routes):
        for name, kwargs in routes:
            with self.subTest(route=name):
                response = self.client.get(reverse(name, kwargs=kwargs))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'css/workspace.')
                self.assertContains(response, 'id="page-content"')

    def test_teacher_pages_share_the_new_workspace(self):
        self.client.force_login(self.teacher)
        course = {'pk': self.course.pk}
        student = {'pk': self.student.pk}
        lesson = {'pk': self.lesson.pk}
        quiz = {'lesson_id': self.lesson.pk, 'kind': 'pretest'}
        self.assert_workspace_routes([
            ('courses:teacher_dashboard', {}), ('courses:course_create', {}),
            ('courses:course_detail', course), ('courses:course_edit', course),
            ('courses:course_delete', course), ('courses:course_roster', course),
            ('courses:course_report', course), ('courses:assessment_scores', {}),
            ('courses:student_report', {'course_pk': self.course.pk, 'student_id': self.student.pk}),
            ('courses:lesson_create', {'course_pk': self.course.pk}),
            ('courses:lesson_detail', lesson), ('courses:lesson_edit', lesson), ('courses:lesson_delete', lesson),
            ('accounts:student_list', {}), ('accounts:student_add', {}),
            ('accounts:student_bulk_add', {}), ('accounts:student_edit', student),
            ('accounts:student_delete', student), ('accounts:student_reset_password', student),
            ('exams:pretest_import', {}), ('exams:quiz_manage', quiz), ('exams:question_add', quiz),
            ('exams:question_edit', {'pk': self.question.pk}), ('exams:question_delete', {'pk': self.question.pk}),
        ])

    def test_student_learning_and_quiz_submission(self):
        from exams.models import Attempt
        self.client.force_login(self.student)
        self.assert_workspace_routes([
            ('courses:student_dashboard', {}), ('courses:lesson_detail', {'pk': self.lesson.pk}),
            ('exams:quiz_take', {'lesson_id': self.lesson.pk, 'kind': 'pretest'}),
            ('exams:boss_battle_hub', {}), ('exams:boss_battle_play', {'lesson_id': self.lesson.pk}),
        ])
        response = self.client.post(reverse('exams:quiz_take', kwargs={'lesson_id': self.lesson.pk, 'kind': 'pretest'}), {f'question_{self.question.pk}': self.choice.pk})
        attempt = Attempt.objects.get(student=self.student, quiz=self.quiz)
        self.assertEqual(attempt.score, 100)
        self.assertRedirects(response, reverse('exams:attempt_result', kwargs={'pk': attempt.pk}))
        self.assert_workspace_routes([('exams:attempt_result', {'pk': attempt.pk})])

    def test_auth_pages_share_3d_design_and_login_still_works(self):
        self.assert_workspace_routes([('accounts:login', {}), ('accounts:register_teacher', {})])
        self.teacher.set_password('Testing-local-478!')
        self.teacher.save()
        response = self.client.post(reverse('accounts:login'), {'username': self.teacher.username, 'password': 'Testing-local-478!'})
        self.assertRedirects(response, reverse('dashboard'), fetch_redirect_response=False)
