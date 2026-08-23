from django import forms

from oopelearn.formutils import BootstrapFormMixin

from .models import Course, Lesson


class CourseForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'cover_image', 'cover_url']
        labels = {
            'title': 'ชื่อวิชา',
            'description': 'คำอธิบายรายวิชา',
            'cover_image': 'อัปโหลดรูปปกจากเครื่อง',
            'cover_url': 'หรือใส่ลิงก์รูปปกจากอินเทอร์เน็ต',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class LessonForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'description', 'youtube_url', 'video_file', 'slide_file', 'extra_file', 'order', 'content_notes']
        labels = {
            'title': 'ชื่อบทเรียน',
            'description': 'คำอธิบายบทเรียน',
            'youtube_url': 'ลิงก์วิดีโอ YouTube',
            'video_file': 'อัปโหลดไฟล์วิดีโอ',
            'slide_file': 'เอกสารประกอบ (PDF/PowerPoint)',
            'extra_file': 'เอกสารเสริม (ถ้ามี)',
            'order': 'ลำดับ',
            'content_notes': 'เนื้อหาบทเรียนแบบละเอียด (สำหรับ AI ผู้ช่วย)',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'content_notes': forms.Textarea(attrs={'rows': 8}),
        }
