import random
import string

import openpyxl
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from courses.models import Course, Enrollment

from .decorators import teacher_required
from .forms import StudentBulkCreateForm, StudentCreateForm, TeacherRegisterForm
from .models import User


def register_teacher(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = TeacherRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'ยินดีต้อนรับอาจารย์ {user.first_name} สมัครสมาชิกสำเร็จ')
            return redirect('dashboard')
    else:
        form = TeacherRegisterForm()
    return render(request, 'accounts/register_teacher.html', {'form': form})


@teacher_required
def student_list(request):
    students = User.objects.filter(created_by=request.user).order_by('first_name', 'last_name')
    courses = Course.objects.filter(teacher=request.user)
    return render(request, 'accounts/student_list.html', {'students': students, 'courses': courses})


@teacher_required
def student_add(request):
    courses = Course.objects.filter(teacher=request.user)
    if request.method == 'POST':
        form = StudentCreateForm(request.POST)
        if form.is_valid():
            student = form.save(teacher=request.user)
            course_id = request.POST.get('course')
            if course_id:
                course = get_object_or_404(Course, pk=course_id, teacher=request.user)
                Enrollment.objects.get_or_create(student=student, course=course)
            messages.success(request, f'เพิ่มนักเรียน {student.first_name} {student.last_name} เรียบร้อยแล้ว')
            return redirect('accounts:student_list')
    else:
        form = StudentCreateForm()
    return render(request, 'accounts/student_add.html', {'form': form, 'courses': courses})


def _rows_from_excel(excel_file):
    """Read an uploaded .xlsx file into rows of stripped-string cells, skipping the header row."""
    rows = []
    workbook = openpyxl.load_workbook(excel_file, read_only=True, data_only=True)
    try:
        sheet = workbook.active
        for i, row in enumerate(sheet.iter_rows(values_only=True)):
            if i == 0:
                continue
            parts = [str(cell).strip() if cell is not None else '' for cell in row]
            if any(parts):
                rows.append(parts)
    finally:
        workbook.close()
    return rows


@teacher_required
def student_bulk_add(request):
    courses = Course.objects.filter(teacher=request.user)
    created = []
    errors = []
    if request.method == 'POST':
        form = StudentBulkCreateForm(request.POST, request.FILES)
        course_id = request.POST.get('course')
        if form.is_valid():
            course = None
            if course_id:
                course = get_object_or_404(Course, pk=course_id, teacher=request.user)
            excel_file = form.cleaned_data.get('excel_file')
            if excel_file:
                try:
                    rows = _rows_from_excel(excel_file)
                except Exception:
                    rows = []
                    messages.error(request, 'ไม่สามารถอ่านไฟล์ Excel ได้ กรุณาตรวจสอบว่าเป็นไฟล์ .xlsx ที่ถูกต้อง')
            else:
                lines = [l.strip() for l in form.cleaned_data['raw_list'].splitlines() if l.strip()]
                rows = [[p.strip() for p in line.split(',')] for line in lines]
            for parts in rows:
                username = parts[0] if len(parts) > 0 else ''
                first_name = parts[1] if len(parts) > 1 else ''
                last_name = parts[2] if len(parts) > 2 else ''
                student_code = parts[3] if len(parts) > 3 else ''
                if not username:
                    continue
                if User.objects.filter(username=username).exists():
                    errors.append(f'{username}: มีชื่อผู้ใช้นี้อยู่แล้ว ข้าม')
                    continue
                student = User(
                    username=username, first_name=first_name, last_name=last_name,
                    student_code=student_code, role=User.Role.STUDENT, created_by=request.user,
                )
                student.set_password(username)
                student.save()
                if course:
                    Enrollment.objects.get_or_create(student=student, course=course)
                created.append(student)
            if created:
                messages.success(request, f'เพิ่มนักเรียนสำเร็จ {len(created)} คน (รหัสผ่านเริ่มต้น = ชื่อผู้ใช้)')
            if errors:
                for e in errors:
                    messages.warning(request, e)
            if created and not errors:
                return redirect('accounts:student_list')
    else:
        form = StudentBulkCreateForm()
    return render(request, 'accounts/student_bulk_add.html', {'form': form, 'courses': courses})


@teacher_required
def student_edit(request, pk):
    student = get_object_or_404(User, pk=pk, created_by=request.user, role=User.Role.STUDENT)
    if request.method == 'POST':
        student.first_name = request.POST.get('first_name', student.first_name)
        student.last_name = request.POST.get('last_name', student.last_name)
        student.student_code = request.POST.get('student_code', student.student_code)
        student.save()
        messages.success(request, 'บันทึกข้อมูลนักเรียนแล้ว')
        return redirect('accounts:student_list')
    return render(request, 'accounts/student_edit.html', {'student': student})


@teacher_required
def student_delete(request, pk):
    student = get_object_or_404(User, pk=pk, created_by=request.user, role=User.Role.STUDENT)
    if request.method == 'POST':
        name = f'{student.first_name} {student.last_name}'
        student.delete()
        messages.success(request, f'ลบนักเรียน {name} แล้ว')
        return redirect('accounts:student_list')
    return render(request, 'accounts/student_confirm_delete.html', {'student': student})


@teacher_required
def student_reset_password(request, pk):
    student = get_object_or_404(User, pk=pk, created_by=request.user, role=User.Role.STUDENT)
    if request.method == 'POST':
        new_password = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        student.set_password(new_password)
        student.save()
        messages.success(request, f'ตั้งรหัสผ่านใหม่ของ {student.first_name} เป็น: {new_password}')
        return redirect('accounts:student_list')
    return render(request, 'accounts/student_reset_password.html', {'student': student})
