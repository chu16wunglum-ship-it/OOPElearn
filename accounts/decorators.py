from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied


def _is_teacher(user):
    if not user.is_authenticated or not user.is_teacher:
        raise PermissionDenied('เฉพาะครูผู้สอนเท่านั้นที่เข้าถึงหน้านี้ได้')
    return True


def _is_student(user):
    if not user.is_authenticated or not user.is_student:
        raise PermissionDenied('เฉพาะนักเรียนเท่านั้นที่เข้าถึงหน้านี้ได้')
    return True


def teacher_required(view_func):
    return login_required(user_passes_test(_is_teacher)(view_func))


def student_required(view_func):
    return login_required(user_passes_test(_is_student)(view_func))
