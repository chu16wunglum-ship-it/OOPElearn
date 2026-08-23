import re

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse


YOUTUBE_ID_RE = re.compile(
    r'(?:youtube(?:-nocookie)?\.com/(?:watch\?v=|embed/|shorts/)|youtu\.be/)([A-Za-z0-9_-]{11})'
)

UNIT_NUMBER_RE = re.compile(r'หน่วยที่\s*(\d+)')


def extract_youtube_id(url):
    if not url:
        return ''
    match = YOUTUBE_ID_RE.search(url)
    if match:
        return match.group(1)
    if re.fullmatch(r'[A-Za-z0-9_-]{11}', url.strip()):
        return url.strip()
    return ''


class Course(models.Model):
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='courses', limit_choices_to={'role': 'teacher'},
    )
    title = models.CharField(max_length=200, default='การเขียนโปรแกรมเชิงวัตถุเบื้องต้น')
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='course_covers/', blank=True, null=True, help_text='อัปโหลดรูปปกจากเครื่อง (ไม่บังคับ)')
    cover_url = models.URLField(blank=True, help_text='หรือใส่ลิงก์รูปปกจากอินเทอร์เน็ต (ไม่บังคับ)')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('courses:course_detail', args=[self.pk])

    @property
    def cover_image_url(self):
        if self.cover_image:
            return self.cover_image.url
        return self.cover_url

    @property
    def unit_number(self):
        match = UNIT_NUMBER_RE.search(self.title)
        return int(match.group(1)) if match else None

    @property
    def lesson_count(self):
        return self.lessons.count()

    @property
    def student_count(self):
        return self.enrollments.count()


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    youtube_url = models.URLField(blank=True, help_text='ลิงก์วิดีโอ YouTube ของบทเรียนนี้')
    video_file = models.FileField(
        upload_to='lesson_videos/', blank=True, null=True,
        help_text='หรืออัปโหลดไฟล์วิดีโอโดยตรงจากเครื่อง (MP4 แนะนำ)',
    )
    slide_file = models.FileField(
        upload_to='lesson_slides/', blank=True, null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'ppt', 'pptx'])],
        help_text='ไฟล์เอกสารประกอบการเรียน (PDF หรือ PowerPoint)',
    )
    extra_file = models.FileField(
        upload_to='lesson_extras/', blank=True, null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'ppt', 'pptx'])],
        help_text='เอกสารเสริมเพิ่มเติม (ถ้ามี)',
    )
    order = models.PositiveIntegerField(default=0)
    content_notes = models.TextField(
        blank=True,
        help_text='เนื้อหา/สรุปบทเรียนแบบละเอียด ใช้เป็นข้อมูลอ้างอิงให้ AI ผู้ช่วยตอบคำถามนักเรียนเฉพาะเรื่องนี้เท่านั้น',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f'{self.course.title} - {self.title}'

    def get_absolute_url(self):
        return reverse('courses:lesson_detail', args=[self.pk])

    @property
    def youtube_id(self):
        return extract_youtube_id(self.youtube_url)

    @property
    def video_kind(self):
        if self.video_file:
            return 'file'
        if self.youtube_id:
            return 'youtube'
        return ''

    @property
    def slide_extension(self):
        if not self.slide_file:
            return ''
        return self.slide_file.name.rsplit('.', 1)[-1].lower()

    @property
    def extra_extension(self):
        if not self.extra_file:
            return ''
        return self.extra_file.name.rsplit('.', 1)[-1].lower()


class Enrollment(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='enrollments', limit_choices_to={'role': 'student'},
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f'{self.student} -> {self.course}'


class VideoProgress(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='video_progresses',
    )
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progresses')
    watched_seconds = models.FloatField(default=0)
    duration_seconds = models.FloatField(default=0)
    completed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'lesson')

    def __str__(self):
        return f'{self.student} - {self.lesson} ({self.percent_watched}%)'

    @property
    def percent_watched(self):
        if not self.duration_seconds:
            return 0
        return min(100, round(self.watched_seconds / self.duration_seconds * 100))


class Message(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='messages')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lesson_messages')
    text = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.author} @ {self.lesson}: {self.text[:40]}'
