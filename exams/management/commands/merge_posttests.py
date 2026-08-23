from django.core.management.base import BaseCommand
from django.db import transaction

from courses.models import Lesson
from exams.models import Quiz


class Command(BaseCommand):
    help = (
        'Merges every lesson-level posttest quiz into a single final posttest '
        'hosted on the last lesson (highest course unit number). Safe to run '
        'more than once: subsequent runs find nothing left to merge.'
    )

    @transaction.atomic
    def handle(self, *args, **options):
        posttest_quizzes = list(
            Quiz.objects.filter(kind=Quiz.Kind.POSTTEST).select_related('lesson__course')
        )
        if not posttest_quizzes:
            self.stdout.write('No posttest quizzes found.')
            return

        host_quiz = max(
            posttest_quizzes,
            key=lambda q: (q.lesson.course.unit_number or 0, q.lesson.order),
        )
        host_lesson = host_quiz.lesson
        self.stdout.write(f'Host lesson: {host_lesson} (quiz {host_quiz.id})')

        other_quizzes = [q for q in posttest_quizzes if q.id != host_quiz.id]
        if not other_quizzes:
            self.stdout.write('Already merged, nothing to do.')
            return

        other_quizzes.sort(key=lambda q: (q.lesson.course.unit_number or 0, q.lesson.order))

        order_counter = host_quiz.questions.count()
        moved = 0
        for quiz in other_quizzes:
            questions = list(quiz.questions.order_by('order'))
            for question in questions:
                question.quiz = host_quiz
                question.order = order_counter
                question.save(update_fields=['quiz', 'order'])
                order_counter += 1
                moved += 1
            quiz.delete()
            self.stdout.write(f'  merged {len(questions)} questions from {quiz.lesson} and removed its quiz')

        self.stdout.write(self.style.SUCCESS(
            f'Moved {moved} questions into host quiz {host_quiz.id}. '
            f'Host now has {host_quiz.question_count} questions total.'
        ))
