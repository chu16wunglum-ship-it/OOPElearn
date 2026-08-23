import json
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.decorators import student_required, teacher_required
from courses.models import Course, Enrollment, Lesson
from oopelearn.ai import ask_ai

from .docx_import import parse_pretest_bank
from .forms import QuestionForm
from .models import Attempt, Choice, Question, Quiz

PRETEST_DOCX_RELPATH = 'pretest/pretest.docx'

KIND_LABELS = dict(Quiz.Kind.choices)
WIZARD_ORDER = [Quiz.Kind.PRETEST, Quiz.Kind.INVIDEO, Quiz.Kind.POSTTEST]


def _get_owned_lesson(request, lesson_id):
    return get_object_or_404(Lesson, pk=lesson_id, course__teacher=request.user)


def _valid_kind(kind):
    if kind not in Quiz.Kind.values:
        raise PermissionDenied('ประเภทแบบทดสอบไม่ถูกต้อง')
    return kind


@teacher_required
def pretest_import(request):
    docx_path = Path(settings.MEDIA_ROOT) / PRETEST_DOCX_RELPATH
    docx_exists = docx_path.exists()
    bank = {}
    parse_error = None
    if docx_exists:
        try:
            bank = parse_pretest_bank(docx_path)
        except Exception:
            parse_error = 'ไม่สามารถอ่านไฟล์ pretest.docx ได้ กรุณาตรวจสอบรูปแบบไฟล์'

    TITLES = {
        'pretest': 'แบบทดสอบก่อนเรียน',
        'retest': 'แบบทดสอบหลังเรียน',
    }

    if request.method == 'POST':
        if not docx_exists or parse_error:
            messages.error(request, parse_error or 'ไม่พบไฟล์ pretest.docx')
            return redirect('exams:pretest_import')

        target_kind = request.POST.get('target_kind', 'pretest')
        if target_kind not in TITLES:
            raise PermissionDenied('ประเภทแบบทดสอบไม่ถูกต้อง')

        unit_number = request.POST.get('unit_number')
        course = get_object_or_404(Course, pk=request.POST.get('course_id'), teacher=request.user)
        lesson = course.lessons.order_by('order').first()
        questions = bank.get(int(unit_number), [])

        if not lesson:
            messages.error(request, f'{course.title} ยังไม่มีบทเรียน กรุณาสร้างบทเรียนก่อน')
        elif not questions:
            messages.error(request, f'ไม่พบคำถามสำหรับหน่วยที่ {unit_number} ในไฟล์ pretest.docx')
        elif any(q['answer_index'] is None or len(q['choices']) != 4 for q in questions):
            messages.error(request, f'ข้อมูลคำถามหน่วยที่ {unit_number} ในไฟล์ไม่ครบถ้วน กรุณาตรวจสอบไฟล์ต้นฉบับ')
        else:
            quiz, _ = Quiz.objects.get_or_create(lesson=lesson, kind=target_kind)
            quiz.title = f'{TITLES[target_kind]} {course.title}'
            quiz.source_file = PRETEST_DOCX_RELPATH
            quiz.save()
            quiz.questions.all().delete()
            for q in questions:
                question = Question.objects.create(quiz=quiz, text=q['text'], order=q['num'])
                for idx, ctext in enumerate(q['choices']):
                    Choice.objects.create(
                        question=question, text=ctext, order=idx,
                        is_correct=(idx == q['answer_index']),
                    )
            messages.success(request, f'นำเข้า{TITLES[target_kind]} {len(questions)} ข้อ สำหรับ{course.title} แล้ว')
        return redirect('exams:pretest_import')

    rows = []
    courses = sorted(
        Course.objects.filter(teacher=request.user),
        key=lambda c: (c.unit_number is None, c.unit_number or 0, c.created_at),
    )
    for course in courses:
        lesson = course.lessons.order_by('order').first()
        pretest_quiz = lesson.quizzes.filter(kind='pretest').first() if lesson else None
        retest_quiz = lesson.quizzes.filter(kind='retest').first() if lesson else None
        unit_number = course.unit_number
        rows.append({
            'course': course,
            'lesson': lesson,
            'pretest_quiz': pretest_quiz,
            'retest_quiz': retest_quiz,
            'available_count': len(bank.get(unit_number, [])) if unit_number else 0,
        })

    return render(request, 'exams/pretest_import.html', {
        'rows': rows, 'docx_exists': docx_exists, 'parse_error': parse_error,
    })


@teacher_required
def quiz_manage(request, lesson_id, kind):
    lesson = _get_owned_lesson(request, lesson_id)
    kind = _valid_kind(kind)
    quiz, _ = Quiz.objects.get_or_create(lesson=lesson, kind=kind)
    questions = quiz.questions.prefetch_related('choices')

    step_index = WIZARD_ORDER.index(kind) if kind in WIZARD_ORDER else None
    next_kind = (
        WIZARD_ORDER[step_index + 1] if step_index is not None and step_index + 1 < len(WIZARD_ORDER) else None
    )

    return render(request, 'exams/quiz_manage.html', {
        'lesson': lesson, 'quiz': quiz, 'questions': questions,
        'kind': kind, 'kind_label': KIND_LABELS[kind],
        'next_kind': next_kind, 'next_kind_label': KIND_LABELS.get(next_kind),
        'wizard_step': (step_index + 1) if step_index is not None else None, 'wizard_total': len(WIZARD_ORDER),
    })


@teacher_required
def question_add(request, lesson_id, kind):
    lesson = _get_owned_lesson(request, lesson_id)
    kind = _valid_kind(kind)
    quiz, _ = Quiz.objects.get_or_create(lesson=lesson, kind=kind)
    requires_trigger = kind == Quiz.Kind.INVIDEO
    if request.method == 'POST':
        form = QuestionForm(request.POST, requires_trigger_time=requires_trigger)
        if form.is_valid():
            _save_question(quiz, form, order=quiz.question_count + 1)
            messages.success(request, 'เพิ่มคำถามแล้ว')
            return redirect('exams:quiz_manage', lesson_id=lesson.id, kind=kind)
    else:
        form = QuestionForm(requires_trigger_time=requires_trigger)
    return render(request, 'exams/question_form.html', {
        'form': form, 'lesson': lesson, 'kind': kind, 'kind_label': KIND_LABELS[kind], 'is_new': True,
    })


def _save_question(quiz, form, order):
    question = Question.objects.create(
        quiz=quiz,
        text=form.cleaned_data['text'],
        trigger_time=form.cleaned_data.get('trigger_time'),
        order=order,
        is_true_false=(form.cleaned_data['question_type'] == 'tf'),
    )
    correct = form.cleaned_data['correct_choice']
    for i in range(1, 5):
        text = form.cleaned_data.get(f'choice_{i}')
        if text:
            Choice.objects.create(question=question, text=text, is_correct=(str(i) == correct), order=i)
    return question


@teacher_required
def question_edit(request, pk):
    question = get_object_or_404(Question, pk=pk, quiz__lesson__course__teacher=request.user)
    kind = question.quiz.kind
    requires_trigger = kind == Quiz.Kind.INVIDEO
    choices = list(question.choices.all())
    if request.method == 'POST':
        form = QuestionForm(request.POST, requires_trigger_time=requires_trigger)
        if form.is_valid():
            question.text = form.cleaned_data['text']
            question.trigger_time = form.cleaned_data.get('trigger_time')
            question.is_true_false = form.cleaned_data['question_type'] == 'tf'
            question.save()
            question.choices.all().delete()
            correct = form.cleaned_data['correct_choice']
            for i in range(1, 5):
                text = form.cleaned_data.get(f'choice_{i}')
                if text:
                    Choice.objects.create(question=question, text=text, is_correct=(str(i) == correct), order=i)
            messages.success(request, 'บันทึกคำถามแล้ว')
            return redirect('exams:quiz_manage', lesson_id=question.quiz.lesson_id, kind=kind)
    else:
        initial = {
            'text': question.text, 'trigger_time': question.trigger_time,
            'question_type': 'tf' if question.is_true_false else 'mc',
        }
        correct_choice = '1'
        for i, choice in enumerate(choices[:4], start=1):
            initial[f'choice_{i}'] = choice.text
            if choice.is_correct:
                correct_choice = str(i)
        initial['correct_choice'] = correct_choice
        form = QuestionForm(initial=initial, requires_trigger_time=requires_trigger)
    return render(request, 'exams/question_form.html', {
        'form': form, 'lesson': question.quiz.lesson, 'kind': kind, 'kind_label': KIND_LABELS[kind],
        'is_new': False, 'question': question,
    })


@teacher_required
def question_delete(request, pk):
    question = get_object_or_404(Question, pk=pk, quiz__lesson__course__teacher=request.user)
    lesson_id = question.quiz.lesson_id
    kind = question.quiz.kind
    if request.method == 'POST':
        question.delete()
        messages.success(request, 'ลบคำถามแล้ว')
        return redirect('exams:quiz_manage', lesson_id=lesson_id, kind=kind)
    return render(request, 'exams/question_confirm_delete.html', {'question': question})


def _get_enrolled_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, pk=lesson_id)
    if not Enrollment.objects.filter(student=request.user, course=lesson.course).exists():
        raise PermissionDenied('คุณไม่ได้ลงทะเบียนในวิชานี้')
    return lesson


@student_required
def quiz_take(request, lesson_id, kind):
    lesson = _get_enrolled_lesson(request, lesson_id)
    kind = _valid_kind(kind)
    quiz = get_object_or_404(Quiz, lesson=lesson, kind=kind)
    questions = list(quiz.questions.prefetch_related('choices'))

    if request.method == 'POST':
        attempt, _ = Attempt.objects.get_or_create(student=request.user, quiz=quiz)
        attempt.answers.all().delete()
        for question in questions:
            choice_id = request.POST.get(f'question_{question.id}')
            if not choice_id:
                continue
            choice = question.choices.filter(pk=choice_id).first()
            if choice:
                attempt.answers.create(question=question, choice=choice, is_correct=choice.is_correct)
        attempt.submitted_at = timezone.now()
        attempt.save(update_fields=['submitted_at'])
        attempt.recompute_score()
        messages.success(request, f'ส่งคำตอบแล้ว คะแนน {attempt.score}%')
        return redirect('exams:attempt_result', pk=attempt.pk)

    return render(request, 'exams/quiz_take.html', {
        'lesson': lesson, 'quiz': quiz, 'questions': questions, 'kind_label': KIND_LABELS[kind],
    })


@student_required
def attempt_result(request, pk):
    attempt = get_object_or_404(Attempt, pk=pk, student=request.user)
    quiz = attempt.quiz
    questions = quiz.questions.prefetch_related('choices')
    answers_by_question = {a.question_id: a for a in attempt.answers.select_related('choice')}

    review = []
    for question in questions:
        answer = answers_by_question.get(question.id)
        correct_choice = next((c for c in question.choices.all() if c.is_correct), None)
        review.append({
            'question': question,
            'chosen_choice': answer.choice if answer else None,
            'correct_choice': correct_choice,
            'is_correct': answer.is_correct if answer else False,
        })

    return render(request, 'exams/attempt_result.html', {
        'attempt': attempt, 'quiz': quiz, 'lesson': quiz.lesson,
        'kind_label': KIND_LABELS[quiz.kind], 'review': review,
    })


@student_required
@require_POST
def attempt_ai_summary(request, pk):
    attempt = get_object_or_404(Attempt, pk=pk, student=request.user)
    quiz = attempt.quiz

    lines = []
    for answer in attempt.answers.select_related('question', 'choice'):
        correct_choice = answer.question.choices.filter(is_correct=True).first()
        lines.append(
            f'- คำถาม: {answer.question.text}\n'
            f'  คำตอบที่เลือก: {answer.choice.text if answer.choice else "(ไม่ได้ตอบ)"} '
            f'({"ถูก" if answer.is_correct else "ผิด"})\n'
            f'  คำตอบที่ถูกต้อง: {correct_choice.text if correct_choice else "-"}'
        )
    qa_text = '\n'.join(lines) if lines else 'นักเรียนยังไม่ได้ตอบคำถามใด ๆ'

    system_prompt = (
        'คุณเป็นผู้ช่วยสอนที่วิเคราะห์ผลการทำแบบทดสอบของนักเรียน '
        'สรุปจุดแข็งและจุดที่ควรปรับปรุงจากคำตอบที่ให้มา เป็นภาษาไทย '
        'กระชับ ให้กำลังใจ และให้คำแนะนำที่นำไปปฏิบัติได้จริง ความยาวไม่เกิน 200 คำ'
    )
    user_message = (
        f'บทเรียน: {quiz.lesson.title}\n'
        f'ประเภทแบบทดสอบ: {KIND_LABELS[quiz.kind]}\n'
        f'คะแนนรวม: {attempt.score}%\n\n'
        f'รายละเอียดคำตอบ:\n{qa_text}'
    )
    ok, text = ask_ai(system_prompt, user_message, max_tokens=1024)
    if not ok:
        return JsonResponse({'error': text}, status=502)
    return JsonResponse({'summary': text})


@student_required
@require_POST
def invideo_answer(request, lesson_id):
    lesson = _get_enrolled_lesson(request, lesson_id)
    quiz = get_object_or_404(Quiz, lesson=lesson, kind=Quiz.Kind.INVIDEO)
    try:
        payload = json.loads(request.body)
        question_id = int(payload.get('question_id'))
        choice_id = int(payload.get('choice_id'))
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({'error': 'invalid payload'}, status=400)

    question = get_object_or_404(Question, pk=question_id, quiz=quiz)
    choice = get_object_or_404(Choice, pk=choice_id, question=question)

    attempt, _ = Attempt.objects.get_or_create(student=request.user, quiz=quiz)
    answer, created = attempt.answers.get_or_create(
        question=question, defaults={'choice': choice, 'is_correct': choice.is_correct},
    )
    if created:
        attempt.recompute_score()

    correct_choice = question.choices.filter(is_correct=True).first()
    return JsonResponse({
        'is_correct': answer.is_correct,
        'correct_choice_id': correct_choice.id if correct_choice else None,
        'correct_choice_text': correct_choice.text if correct_choice else '',
    })
