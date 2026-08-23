from django.conf import settings
from django.db import models


class Quiz(models.Model):
    class Kind(models.TextChoices):
        PRETEST = 'pretest', 'แบบทดสอบก่อนเรียน'
        POSTTEST = 'posttest', 'แบบทดสอบหลังเรียน'
        INVIDEO = 'invideo', 'คำถามระหว่างวิดีโอ'

    lesson = models.ForeignKey('courses.Lesson', on_delete=models.CASCADE, related_name='quizzes')
    kind = models.CharField(max_length=10, choices=Kind.choices)
    title = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('lesson', 'kind')
        ordering = ['kind']

    def __str__(self):
        return f'{self.lesson.title} - {self.get_kind_display()}'

    @property
    def question_count(self):
        return self.questions.count()


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField('คำถาม')
    order = models.PositiveIntegerField(default=0)
    is_true_false = models.BooleanField('แบบถูก/ผิด', default=False)
    trigger_time = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='วินาทีในวิดีโอที่จะแสดงคำถามนี้ (ใช้เฉพาะคำถามระหว่างวิดีโอ)',
    )

    class Meta:
        ordering = ['trigger_time', 'order']

    def __str__(self):
        return self.text[:60]


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField('ตัวเลือก', max_length=500)
    is_correct = models.BooleanField('คำตอบที่ถูกต้อง', default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.text


class Attempt(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    score = models.FloatField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'quiz')

    def __str__(self):
        return f'{self.student} - {self.quiz} ({self.score}%)'

    @property
    def correct_count(self):
        return self.answers.filter(is_correct=True).count()

    @property
    def answered_count(self):
        return self.answers.count()

    def recompute_score(self):
        total = self.quiz.question_count
        if total == 0:
            self.score = 0
        else:
            self.score = round(self.correct_count / total * 100, 1)
        self.save(update_fields=['score'])


class AnswerRecord(models.Model):
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answer_records')
    choice = models.ForeignKey(Choice, on_delete=models.SET_NULL, null=True, related_name='answer_records')
    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('attempt', 'question')

    def __str__(self):
        return f'{self.attempt} - {self.question}'
