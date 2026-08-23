from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        TEACHER = 'teacher', 'ครู'
        STUDENT = 'student', 'นักเรียน'

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    student_code = models.CharField(max_length=20, blank=True, help_text='รหัสนักเรียน')
    created_by = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='created_students', limit_choices_to={'role': Role.TEACHER},
    )

    @property
    def is_teacher(self):
        return self.role == self.Role.TEACHER

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT
