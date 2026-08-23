import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.models import User


class Command(BaseCommand):
    help = (
        'Creates a teacher and/or student user from env vars '
        '(DJANGO_TEACHER_USERNAME/EMAIL/PASSWORD, '
        'DJANGO_STUDENT_USERNAME/EMAIL/PASSWORD) if they don\'t already '
        'exist. Safe to run on every deploy.'
    )

    def handle(self, *args, **options):
        self._ensure_user('TEACHER', User.Role.TEACHER)
        self._ensure_user('STUDENT', User.Role.STUDENT)

    def _ensure_user(self, prefix, role):
        username = os.environ.get(f'DJANGO_{prefix}_USERNAME')
        email = os.environ.get(f'DJANGO_{prefix}_EMAIL', '')
        password = os.environ.get(f'DJANGO_{prefix}_PASSWORD')

        if not username or not password:
            self.stdout.write(f'DJANGO_{prefix}_USERNAME/PASSWORD not set, skipping.')
            return

        UserModel = get_user_model()
        if UserModel.objects.filter(username=username).exists():
            self.stdout.write(f'User "{username}" already exists, skipping.')
            return

        UserModel.objects.create_user(
            username=username, email=email, password=password, role=role,
        )
        self.stdout.write(self.style.SUCCESS(f'Created {role} user "{username}".'))
