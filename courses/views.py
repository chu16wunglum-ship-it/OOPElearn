import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.decorators import student_required, teacher_required
from accounts.models import User
from exams.models import Attempt
from oopelearn.ai import ask_ai

from .forms import CourseForm, LessonForm
from .models import Course, Enrollment, Lesson, Message, VideoProgress


@login_required
def dashboard(request):
    if request.user.is_teacher:
        return redirect('courses:teacher_dashboard')
    return redirect('courses:student_dashboard')


@teacher_required
def teacher_dashboard(request):
    courses = Course.objects.filter(teacher=request.user)
    return render(request, 'courses/teacher_dashboard.html', {'courses': courses})


@student_required
def student_dashboard(request):
    enrollments = Enrollment.objects.filter(student=request.user).select_related('course')
    return render(request, 'courses/student_dashboard.html', {'enrollments': enrollments})


@teacher_required
def course_create(request):
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.teacher = request.user
            course.save()
            messages.success(request, f'สร้างรายวิชา "{course.title}" เรียบร้อยแล้ว')
            return redirect('courses:course_detail', pk=course.pk)
    else:
        form = CourseForm()
    return render(request, 'courses/course_form.html', {'form': form, 'is_new': True})


def _get_owned_course(request, pk):
    return get_object_or_404(Course, pk=pk, teacher=request.user)


@teacher_required
def course_detail(request, pk):
    course = _get_owned_course(request, pk)
    lessons = course.lessons.all()
    return render(request, 'courses/course_detail.html', {
        'course': course, 'lessons': lessons,
    })


@teacher_required
def course_edit(request, pk):
    course = _get_owned_course(request, pk)
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'บันทึกข้อมูลรายวิชาแล้ว')
            return redirect('courses:course_detail', pk=course.pk)
    else:
        form = CourseForm(instance=course)
    return render(request, 'courses/course_form.html', {'form': form, 'course': course, 'is_new': False})


@teacher_required
def course_delete(request, pk):
    course = _get_owned_course(request, pk)
    if request.method == 'POST':
        title = course.title
        course.delete()
        messages.success(request, f'ลบรายวิชา "{title}" แล้ว')
        return redirect('courses:teacher_dashboard')
    return render(request, 'courses/course_confirm_delete.html', {'course': course})


@teacher_required
def course_roster(request, pk):
    course = _get_owned_course(request, pk)
    enrolled_ids = set(course.enrollments.values_list('student_id', flat=True))
    all_students = User.objects.filter(created_by=request.user).order_by('first_name', 'last_name')
    if request.method == 'POST':
        selected_ids = set(int(i) for i in request.POST.getlist('student_ids'))
        for student in all_students:
            is_selected = student.id in selected_ids
            is_enrolled = student.id in enrolled_ids
            if is_selected and not is_enrolled:
                Enrollment.objects.create(student=student, course=course)
            elif not is_selected and is_enrolled:
                Enrollment.objects.filter(student=student, course=course).delete()
        messages.success(request, 'อัปเดตรายชื่อนักเรียนในวิชานี้แล้ว')
        return redirect('courses:course_roster', pk=course.pk)
    return render(request, 'courses/course_roster.html', {
        'course': course, 'all_students': all_students, 'enrolled_ids': enrolled_ids,
    })


def _lesson_result_for_student(lesson, student):
    quizzes = {q.kind: q for q in lesson.quizzes.all()}
    result = {'lesson': lesson, 'pretest': None, 'posttest': None, 'invideo': None, 'video': None}

    progress = VideoProgress.objects.filter(student=student, lesson=lesson).first()
    result['video'] = progress

    pretest = quizzes.get('pretest')
    if pretest:
        result['pretest'] = Attempt.objects.filter(student=student, quiz=pretest).first()

    posttest = quizzes.get('posttest')
    if posttest:
        result['posttest'] = Attempt.objects.filter(student=student, quiz=posttest).first()

    invideo = quizzes.get('invideo')
    if invideo:
        attempt = Attempt.objects.filter(student=student, quiz=invideo).first()
        result['invideo'] = {
            'attempt': attempt,
            'total': invideo.question_count,
            'correct': attempt.correct_count if attempt else 0,
        }
    return result


@teacher_required
def course_report(request, pk):
    course = _get_owned_course(request, pk)
    lessons = list(course.lessons.all())
    students = User.objects.filter(enrollments__course=course).order_by('first_name', 'last_name')

    rows = []
    for student in students:
        lesson_data = [_lesson_result_for_student(lesson, student) for lesson in lessons]
        rows.append({'student': student, 'lessons': lesson_data})

    return render(request, 'courses/course_report.html', {
        'course': course, 'lessons': lessons, 'rows': rows,
    })


@teacher_required
def student_report(request, course_pk, student_id):
    course = _get_owned_course(request, course_pk)
    student = get_object_or_404(User, pk=student_id, role=User.Role.STUDENT)
    if not Enrollment.objects.filter(course=course, student=student).exists():
        raise PermissionDenied('นักเรียนคนนี้ไม่ได้ลงทะเบียนในวิชานี้')
    lessons = course.lessons.all()
    results = [_lesson_result_for_student(lesson, student) for lesson in lessons]

    chart_data = {
        'labels': [entry['lesson'].title for entry in results],
        'pretest': [entry['pretest'].score if entry['pretest'] else None for entry in results],
        'video': [entry['video'].percent_watched if entry['video'] else 0 for entry in results],
        'invideo': [
            round(entry['invideo']['correct'] / entry['invideo']['total'] * 100, 1)
            if entry['invideo'] and entry['invideo']['total'] else None
            for entry in results
        ],
        'posttest': [entry['posttest'].score if entry['posttest'] else None for entry in results],
    }

    return render(request, 'courses/student_report.html', {
        'course': course, 'student': student, 'results': results, 'chart_data': chart_data,
    })


@teacher_required
@require_POST
def student_ai_summary(request, course_pk, student_id):
    course = _get_owned_course(request, course_pk)
    student = get_object_or_404(User, pk=student_id, role=User.Role.STUDENT)
    if not Enrollment.objects.filter(course=course, student=student).exists():
        raise PermissionDenied('นักเรียนคนนี้ไม่ได้ลงทะเบียนในวิชานี้')

    lessons = course.lessons.all()
    lines = []
    for lesson in lessons:
        entry = _lesson_result_for_student(lesson, student)
        pretest = f'{entry["pretest"].score}%' if entry['pretest'] else '-'
        posttest = f'{entry["posttest"].score}%' if entry['posttest'] else '-'
        video = f'{entry["video"].percent_watched}%' if entry['video'] else '0%'
        invideo = '-'
        if entry['invideo'] and entry['invideo']['total']:
            invideo = f'{entry["invideo"]["correct"]}/{entry["invideo"]["total"]}'
        lines.append(
            f'- บทเรียน "{lesson.title}": ก่อนเรียน {pretest}, '
            f'ดูวิดีโอ {video}, คำถามระหว่างวิดีโอ {invideo}, หลังเรียน {posttest}'
        )
    report_text = '\n'.join(lines) if lines else 'ยังไม่มีข้อมูลการเรียนในวิชานี้'

    system_prompt = (
        'คุณเป็นผู้ช่วยครูที่วิเคราะห์ผลการเรียนของนักเรียนตลอดทั้งรายวิชา '
        'สรุปภาพรวมความก้าวหน้า จุดแข็ง จุดที่ควรพัฒนา และคำแนะนำสำหรับครูในการช่วยเหลือนักเรียนคนนี้ '
        'เป็นภาษาไทย กระชับ ตรงประเด็น ความยาวไม่เกิน 250 คำ'
    )
    user_message = (
        f'นักเรียน: {student.first_name} {student.last_name}\n'
        f'รายวิชา: {course.title}\n\n'
        f'ผลการเรียนรายบทเรียน:\n{report_text}'
    )
    ok, text = ask_ai(system_prompt, user_message, max_tokens=1024)
    if not ok:
        return JsonResponse({'error': text}, status=502)
    return JsonResponse({'summary': text})


@teacher_required
def lesson_create(request, course_pk):
    course = _get_owned_course(request, course_pk)
    if request.method == 'POST':
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            lesson.save()
            messages.success(request, f'เพิ่มบทเรียน "{lesson.title}" แล้ว ตอนนี้มาสร้างแบบทดสอบก่อนเรียนกันเลย')
            return redirect('exams:quiz_manage', lesson_id=lesson.id, kind='pretest')
    else:
        form = LessonForm(initial={'order': course.lessons.count() + 1})
    return render(request, 'courses/lesson_form.html', {'form': form, 'course': course, 'is_new': True})


def _get_owned_lesson(request, pk):
    return get_object_or_404(Lesson, pk=pk, course__teacher=request.user)


@teacher_required
def lesson_edit(request, pk):
    lesson = _get_owned_lesson(request, pk)
    if request.method == 'POST':
        form = LessonForm(request.POST, instance=lesson)
        if form.is_valid():
            form.save()
            messages.success(request, 'บันทึกบทเรียนแล้ว')
            return redirect('courses:course_detail', pk=lesson.course.pk)
    else:
        form = LessonForm(instance=lesson)
    return render(request, 'courses/lesson_form.html', {
        'form': form, 'course': lesson.course, 'is_new': False, 'lesson': lesson,
    })


@teacher_required
def lesson_delete(request, pk):
    lesson = _get_owned_lesson(request, pk)
    if request.method == 'POST':
        course_pk = lesson.course.pk
        title = lesson.title
        lesson.delete()
        messages.success(request, f'ลบบทเรียน "{title}" แล้ว')
        return redirect('courses:course_detail', pk=course_pk)
    return render(request, 'courses/lesson_confirm_delete.html', {'lesson': lesson})


def _lesson_access(request, lesson):
    course = lesson.course
    is_teacher_owner = request.user.is_teacher and course.teacher_id == request.user.id
    is_enrolled_student = request.user.is_student and Enrollment.objects.filter(
        student=request.user, course=course
    ).exists()
    if not (is_teacher_owner or is_enrolled_student):
        raise PermissionDenied('คุณไม่มีสิทธิ์เข้าถึงบทเรียนนี้')
    return is_teacher_owner, is_enrolled_student


@login_required
def lesson_detail(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    course = lesson.course
    is_teacher_owner, is_enrolled_student = _lesson_access(request, lesson)

    quizzes = {q.kind: q for q in lesson.quizzes.all()}
    pretest_quiz = quizzes.get('pretest')
    posttest_quiz = quizzes.get('posttest')
    invideo_quiz = quizzes.get('invideo')

    pretest_attempt = None
    posttest_attempt = None
    progress = None
    invideo_questions = []
    video_locked = False
    posttest_locked = False

    if is_enrolled_student:
        student = request.user
        progress, _ = VideoProgress.objects.get_or_create(student=student, lesson=lesson)
        if pretest_quiz:
            pretest_attempt = Attempt.objects.filter(student=student, quiz=pretest_quiz).first()
        if posttest_quiz:
            posttest_attempt = Attempt.objects.filter(student=student, quiz=posttest_quiz).first()
        video_locked = bool(pretest_quiz and not pretest_attempt)
        posttest_locked = bool(posttest_quiz and not progress.completed)

        if invideo_quiz:
            answered_qids = set()
            invideo_attempt = Attempt.objects.filter(student=student, quiz=invideo_quiz).first()
            if invideo_attempt:
                answered_qids = set(invideo_attempt.answers.values_list('question_id', flat=True))
            for q in invideo_quiz.questions.all():
                invideo_questions.append({
                    'id': q.id,
                    'text': q.text,
                    'trigger_time': q.trigger_time or 0,
                    'answered': q.id in answered_qids,
                    'choices': [{'id': c.id, 'text': c.text} for c in q.choices.all()],
                })
    else:
        # Teacher preview: show everything unlocked, no progress tracking saved.
        progress = VideoProgress(watched_seconds=0, duration_seconds=0)
        if invideo_quiz:
            for q in invideo_quiz.questions.all():
                invideo_questions.append({
                    'id': q.id, 'text': q.text, 'trigger_time': q.trigger_time or 0,
                    'answered': False,
                    'choices': [{'id': c.id, 'text': c.text} for c in q.choices.all()],
                })

    board_messages = lesson.messages.select_related('author')

    return render(request, 'courses/lesson_detail.html', {
        'lesson': lesson, 'course': course,
        'is_teacher_owner': is_teacher_owner, 'is_enrolled_student': is_enrolled_student,
        'pretest_quiz': pretest_quiz, 'posttest_quiz': posttest_quiz, 'invideo_quiz': invideo_quiz,
        'pretest_attempt': pretest_attempt, 'posttest_attempt': posttest_attempt,
        'progress': progress, 'video_locked': video_locked, 'posttest_locked': posttest_locked,
        'invideo_questions': invideo_questions, 'board_messages': board_messages,
    })


def _serialize_message(message):
    return {
        'id': message.id,
        'author_name': f'{message.author.first_name} {message.author.last_name}'.strip() or message.author.username,
        'is_teacher': message.author.is_teacher,
        'text': message.text,
        'created_at': timezone.localtime(message.created_at).strftime('%d/%m/%Y %H:%M'),
    }


@login_required
def lesson_board(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    _lesson_access(request, lesson)

    if request.method == 'POST':
        try:
            payload = json.loads(request.body)
            text = payload.get('text', '').strip()
        except (ValueError, json.JSONDecodeError):
            return JsonResponse({'error': 'invalid payload'}, status=400)
        if not text:
            return JsonResponse({'error': 'ข้อความว่างเปล่า'}, status=400)
        message = Message.objects.create(lesson=lesson, author=request.user, text=text[:2000])
        return JsonResponse({'message': _serialize_message(message)})

    after_id = request.GET.get('after_id')
    qs = lesson.messages.select_related('author')
    if after_id:
        qs = qs.filter(id__gt=after_id)
    return JsonResponse({'messages': [_serialize_message(m) for m in qs]})


@student_required
@require_POST
def update_video_progress(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    if not Enrollment.objects.filter(student=request.user, course=lesson.course).exists():
        return JsonResponse({'error': 'not enrolled'}, status=403)
    try:
        payload = json.loads(request.body)
        position = float(payload.get('position', 0))
        duration = float(payload.get('duration', 0))
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({'error': 'invalid payload'}, status=400)

    progress, _ = VideoProgress.objects.get_or_create(student=request.user, lesson=lesson)
    progress.watched_seconds = max(progress.watched_seconds, position)
    if duration:
        progress.duration_seconds = duration
    if progress.duration_seconds and progress.watched_seconds / progress.duration_seconds >= 0.9:
        progress.completed = True
    progress.save()
    return JsonResponse({
        'percent_watched': progress.percent_watched,
        'completed': progress.completed,
    })


@login_required
@require_POST
def lesson_ai_ask(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    _lesson_access(request, lesson)

    try:
        payload = json.loads(request.body)
        question = payload.get('question', '').strip()
    except (ValueError, json.JSONDecodeError):
        return JsonResponse({'error': 'invalid payload'}, status=400)
    if not question:
        return JsonResponse({'error': 'กรุณาพิมพ์คำถาม'}, status=400)

    reference_text = lesson.content_notes.strip() or '(ครูยังไม่ได้เพิ่มเนื้อหาละเอียดสำหรับบทเรียนนี้)'
    system_prompt = (
        'คุณเป็นผู้ช่วยสอนประจำบทเรียน "{lesson}" ในวิชา "{course}" เท่านั้น\n'
        'กฎการตอบ:\n'
        '1. ตอบโดยอ้างอิงจาก "เนื้อหาอ้างอิงบทเรียน" ที่ให้มาเป็นหลัก และความรู้ทั่วไปด้านการเขียนโปรแกรมเชิงวัตถุ '
        'ที่เกี่ยวข้องกับหัวข้อของบทเรียนนี้เท่านั้น\n'
        '2. หากคำถามไม่เกี่ยวกับเนื้อหาบทเรียนนี้หรือไม่เกี่ยวกับการเขียนโปรแกรมเชิงวัตถุ '
        'ให้ปฏิเสธอย่างสุภาพและแนะนำให้ไปถามครูผู้สอนแทน อย่าตอบคำถามนอกเรื่อง\n'
        '3. ตอบเป็นภาษาไทย กระชับ เข้าใจง่าย ยกตัวอย่างประกอบเมื่อเหมาะสม ความยาวไม่เกิน 200 คำ'
    ).format(course=lesson.course.title, lesson=lesson.title)
    user_message = (
        f'คำอธิบายรายวิชา: {lesson.course.description}\n\n'
        f'คำอธิบายบทเรียนโดยย่อ: {lesson.description}\n\n'
        f'เนื้อหาอ้างอิงบทเรียน:\n{reference_text}\n\n'
        f'คำถามของนักเรียน: {question}'
    )

    ok, text = ask_ai(system_prompt, user_message, max_tokens=700)
    if not ok:
        return JsonResponse({'error': text}, status=502)
    return JsonResponse({'answer': text})
