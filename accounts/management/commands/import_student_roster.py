from django.core.management.base import BaseCommand, CommandError

from accounts.models import User
from courses.models import Course, Enrollment

# (prefix, first_name, last_name)
STUDENTS = [
    ('นาย', 'กมนทรรศน์', 'พงษ์ประเสริฐ'),
    ('นาย', 'กฤษฎินันท์', 'กริชไพศาลวงศ์'),
    ('นาย', 'กวิน', 'ตะเคียนจันทร์'),
    ('นาย', 'กวิน', 'สินสำอางค์'),
    ('น.ส.', 'กิติญา', 'รักษจิตต์'),
    ('นาย', 'คณิน', 'สินสถิตพงศ์'),
    ('น.ส.', 'จิระพินยา', 'นันทพล'),
    ('น.ส.', 'จิราวดี', 'กิ่งหิรัญ'),
    ('น.ส.', 'ชลิสา', 'สกุลจันทร์ศรี'),
    ('นาย', 'ชิษณุพงศ์', 'จุติศรีสุวรรค์'),
    ('น.ส.', 'ญาณิศา', 'ภูทัดฝน'),
    ('นาย', 'ธนวรรธน์', 'รุ่งเจริญชัยศิลป์'),
    ('นาย', 'ธีรโชติ', 'เรืองกัลป์'),
    ('น.ส.', 'ปาริชาติ', 'ป้องไธสง'),
    ('น.ส.', 'เปมิกา', 'ธรรศกมลวร'),
    ('นาย', 'พงศกร', 'มีมา'),
    ('น.ส.', 'พรพรรณ', 'แสงสว่าง'),
    ('นาย', 'พัฒนศักดิ์', 'วสันต์'),
    ('น.ส.', 'พัสวี', 'นันทบุตร'),
    ('นาย', 'พีรดนย์', 'บัญชากร'),
    ('นาย', 'เมธาพร', 'ใหม่เลี้ยง'),
    ('นาย', 'เมธาสิทธิ์', 'ตั้งตระกูลเดชา'),
    ('น.ส.', 'รัชนีวรรณ', 'สมจิตต์'),
    ('น.ส.', 'ลออรัตน์', 'บุญดี'),
    ('น.ส.', 'วรกาญจน์', 'สราวุธจิรพงศ์'),
    ('น.ส.', 'วราภรณ์', 'รอดดี'),
    ('น.ส.', 'วารุณี', 'ชื่นตา'),
    ('น.ส.', 'วิไลรัตน์', 'โตล่ำ'),
    ('น.ส.', 'ศุภวิชญ์', 'ทองนาค'),
    ('น.ส.', 'สุทธีรา', 'ทองมี'),
    ('น.ส.', 'สุภาวดี', 'รุ่งสว่าง'),
    ('นาย', 'อดิศร', 'อินทรนนท์'),
    ('น.ส.', 'อธิชนันท์', 'หิรัญเจริญสมุทร'),
    ('น.ส.', 'กมลชนก', 'ปรีเปรม'),
    ('นาย', 'กฤษณชัย', 'ฟักบุญเลิศ'),
    ('น.ส.', 'กัญญาณัฐ', 'ทุวิลา'),
    ('นาย', 'จิราวุธ', 'ห้องมณี'),
    ('น.ส.', 'ฉันทิสา', 'ติ่วกระโทก'),
    ('น.ส.', 'ณัฐชาพัชร์', 'บริบูรณ์'),
    ('นาย', 'ทรงพล', 'บ่อทรัพย์'),
]


class Command(BaseCommand):
    help = (
        'Imports a fixed roster of 40 students (username std01..std40, '
        'default password = username) and enrolls them into every course '
        'owned by the given teacher.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--teacher', default='TeacherTest',
            help='Username of the teacher whose courses students will be enrolled into.',
        )
        parser.add_argument(
            '--username-prefix', default='std',
            help='Prefix used to build usernames/student codes (default: std).',
        )

    def handle(self, *args, **options):
        teacher_username = options['teacher']
        prefix = options['username_prefix']

        try:
            teacher = User.objects.get(username=teacher_username, role=User.Role.TEACHER)
        except User.DoesNotExist:
            raise CommandError(f'Teacher "{teacher_username}" not found.')

        courses = list(Course.objects.filter(teacher=teacher))
        if not courses:
            raise CommandError(f'Teacher "{teacher_username}" has no courses to enroll students into.')

        created_count = 0
        enrolled_count = 0

        for idx, (name_prefix, first_name, last_name) in enumerate(STUDENTS, start=1):
            username = f'{prefix}{idx:02d}'
            student_code = f'{idx:02d}'
            full_first_name = f'{name_prefix} {first_name}'

            student, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': full_first_name,
                    'last_name': last_name,
                    'role': User.Role.STUDENT,
                    'student_code': student_code,
                    'created_by': teacher,
                },
            )
            if created:
                student.set_password(username)
                student.save()
                created_count += 1
                self.stdout.write(f'Created {username}: {full_first_name} {last_name}')
            else:
                self.stdout.write(f'{username} already exists, skipping creation.')

            for course in courses:
                _, enrolled_created = Enrollment.objects.get_or_create(student=student, course=course)
                if enrolled_created:
                    enrolled_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done. Created {created_count} new student(s), '
            f'added {enrolled_count} new enrollment(s) across {len(courses)} course(s). '
            f'Default password for each student = their username.'
        ))
