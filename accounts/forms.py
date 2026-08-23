from django import forms
from django.contrib.auth.forms import UserCreationForm

from oopelearn.formutils import BootstrapFormMixin

from .models import User


class TeacherRegisterForm(BootstrapFormMixin, UserCreationForm):
    first_name = forms.CharField(label='ชื่อ', max_length=150)
    last_name = forms.CharField(label='นามสกุล', max_length=150)
    email = forms.EmailField(label='อีเมล', required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.TEACHER
        if commit:
            user.save()
        return user


class StudentCreateForm(BootstrapFormMixin, forms.ModelForm):
    password = forms.CharField(
        label='รหัสผ่าน', widget=forms.PasswordInput,
        help_text='อย่างน้อย 6 ตัวอักษร ระบุให้นักเรียนใช้เข้าสู่ระบบ',
        min_length=6,
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'student_code']
        labels = {
            'username': 'ชื่อผู้ใช้',
            'first_name': 'ชื่อ',
            'last_name': 'นามสกุล',
            'student_code': 'รหัสนักเรียน',
        }

    def save(self, commit=True, teacher=None):
        user = super().save(commit=False)
        user.role = User.Role.STUDENT
        user.created_by = teacher
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class StudentBulkCreateForm(BootstrapFormMixin, forms.Form):
    raw_list = forms.CharField(
        label='รายชื่อนักเรียน',
        required=False,
        widget=forms.Textarea(attrs={'rows': 8, 'placeholder': 'username, ชื่อ, นามสกุล, รหัสนักเรียน\nต่อบรรทัดละ 1 คน เช่น\nstd001, สมชาย, ใจดี, 12345'}),
        help_text='หนึ่งบรรทัดต่อนักเรียนหนึ่งคน คั่นด้วยจุลภาค (,) รูปแบบ: username, ชื่อ, นามสกุล, รหัสนักเรียน(ไม่บังคับ) — รหัสผ่านเริ่มต้นจะถูกสร้างให้อัตโนมัติเป็นรหัสเดียวกับ username',
    )
    excel_file = forms.FileField(
        label='อัปโหลดไฟล์ Excel (.xlsx)',
        required=False,
        widget=forms.FileInput(attrs={'accept': '.xlsx'}),
        help_text='คอลัมน์เรียงตามลำดับ username, ชื่อ, นามสกุล, รหัสนักเรียน(ไม่บังคับ) แถวแรกให้เป็นหัวตาราง (จะถูกข้าม)',
    )

    def clean_excel_file(self):
        excel_file = self.cleaned_data.get('excel_file')
        if excel_file and not excel_file.name.lower().endswith('.xlsx'):
            raise forms.ValidationError('รองรับเฉพาะไฟล์นามสกุล .xlsx เท่านั้น')
        return excel_file

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('raw_list') and not cleaned.get('excel_file'):
            raise forms.ValidationError('กรุณากรอกรายชื่อนักเรียน หรืออัปโหลดไฟล์ Excel อย่างใดอย่างหนึ่ง')
        return cleaned
