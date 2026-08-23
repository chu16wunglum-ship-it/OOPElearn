from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from courses.models import Course, Lesson

COVER_EXTS = {'.jpg', '.jpeg', '.png', '.webp'}
VIDEO_EXTS = {'.mp4', '.webm', '.mov', '.mkv'}
SLIDE_EXTS = {'.pdf', '.ppt', '.pptx'}


class Command(BaseCommand):
    help = (
        'Scans course_content/unit_<N>/ folders and syncs any cover image, '
        'video, and slide file found into the course titled "หน่วยที่ <N> ...". '
        'Re-run after adding or replacing files in a unit folder.'
    )

    def handle(self, *args, **options):
        root = Path(settings.BASE_DIR) / 'course_content'
        if not root.exists():
            self.stdout.write(self.style.WARNING(f'ไม่พบโฟลเดอร์ {root}'))
            return

        for unit_dir in sorted(root.glob('unit_*')):
            if not unit_dir.is_dir():
                continue
            try:
                number = int(unit_dir.name.split('_', 1)[1])
            except (IndexError, ValueError):
                self.stdout.write(self.style.WARNING(f'ข้าม {unit_dir.name}: ชื่อโฟลเดอร์ไม่ถูกต้อง'))
                continue

            course = Course.objects.filter(title__startswith=f'หน่วยที่ {number}').first()
            if not course:
                self.stdout.write(self.style.WARNING(f'ไม่พบวิชาที่ตรงกับ "หน่วยที่ {number}" ({unit_dir.name})'))
                continue

            files = [f for f in unit_dir.iterdir() if f.is_file() and f.name != 'README.txt']
            cover = next((f for f in files if f.suffix.lower() in COVER_EXTS), None)
            video = next((f for f in files if f.suffix.lower() in VIDEO_EXTS), None)
            slide = next((f for f in files if f.suffix.lower() in SLIDE_EXTS), None)

            if not (cover or video or slide):
                self.stdout.write(f'{unit_dir.name}: ยังไม่มีไฟล์ ข้าม')
                continue

            if cover:
                with cover.open('rb') as fh:
                    course.cover_image.save(cover.name, File(fh), save=False)
                course.save()
                self.stdout.write(self.style.SUCCESS(f'{course.title}: ตั้งรูปปก "{cover.name}"'))

            if video or slide:
                lesson, _ = Lesson.objects.get_or_create(
                    course=course, order=1,
                    defaults={'title': course.title},
                )
                if video:
                    with video.open('rb') as fh:
                        lesson.video_file.save(video.name, File(fh), save=False)
                    self.stdout.write(self.style.SUCCESS(f'{course.title}: ตั้งวิดีโอ "{video.name}"'))
                if slide:
                    with slide.open('rb') as fh:
                        lesson.slide_file.save(slide.name, File(fh), save=False)
                    self.stdout.write(self.style.SUCCESS(f'{course.title}: ตั้งเอกสาร "{slide.name}"'))
                lesson.save()
