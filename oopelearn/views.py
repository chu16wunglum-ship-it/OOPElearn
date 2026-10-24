from django.shortcuts import redirect, render
from django.db.models import Prefetch

from courses.models import Course, Lesson


# Public previews summarize the six units shipped with the repository.
CURRICULUM = [
    {'title': 'ความรู้พื้นฐานเกี่ยวกับโปรแกรมเชิงวัตถุ', 'description': 'เริ่มมองโลกในแบบ Object เข้าใจคลาส คุณลักษณะ และพฤติกรรม ก่อนก้าวสู่การเขียนโปรแกรม', 'topics': ['แนวคิด Object-Oriented Programming', 'Class, Object, Attribute และ Method', 'หลักการสำคัญของ OOP'], 'tag': 'OOP FUNDAMENTALS', 'symbol': '{ }'},
    {'title': 'ภาษาในการเขียนโปรแกรมเชิงวัตถุเบื้องต้น', 'description': 'ทำความรู้จักภาษา C# และ .NET เตรียมเครื่องมือ พร้อมสร้างคลาสและวัตถุแรกของคุณ', 'topics': ['ภาษา C# และแพลตฟอร์ม .NET', 'ชนิดข้อมูลและตัวแปร', 'การสร้างคลาสและเรียกใช้เมธอด'], 'tag': 'C# & .NET', 'symbol': 'C#'},
    {'title': 'หลักการเขียนโปรแกรมเชิงวัตถุเบื้องต้น', 'description': 'วางรากฐานการคิดอย่างเป็นขั้นตอน ฝึกเขียนโปรแกรมแบบลำดับและทำงานกับข้อมูล', 'topics': ['ลำดับการทำงานของโปรแกรม', 'ตัวแปรและตัวดำเนินการ', 'การรับข้อมูลและแสดงผล'], 'tag': 'PROGRAMMING LOGIC', 'symbol': '</>'},
    {'title': 'คำสั่งการตรวจสอบและควบคุม', 'description': 'ให้โปรแกรมตัดสินใจและทำงานซ้ำด้วยเงื่อนไข ลูป และอาร์เรย์ เพื่อแก้โจทย์ที่ซับซ้อนขึ้น', 'topics': ['if–else และ switch–case', 'Loop และ Array', 'ตัวดำเนินการเชิงตรรกะ'], 'tag': 'CONTROL FLOW', 'symbol': '↻'},
    {'title': 'การสร้าง Windows Forms Application', 'description': 'เปลี่ยนโค้ดให้เป็นแอปที่โต้ตอบได้ ออกแบบหน้าต่าง วางคอนโทรล และเขียนคำสั่งจัดการเหตุการณ์', 'topics': ['ออกแบบหน้าต่างด้วย Visual Studio', 'Label, TextBox และ Button', 'Properties และ Event Handling'], 'tag': 'BUILD AN APPLICATION', 'symbol': '▤'},
    {'title': 'ออกแบบโปรแกรมเชิงวัตถุเพื่องานธุรกิจ', 'description': 'เชื่อมทุกสิ่งที่เรียนสู่โจทย์ธุรกิจ ฝึกวิเคราะห์งาน ออกแบบคลาส และประยุกต์แนวคิดเชิงวัตถุ', 'topics': ['วิเคราะห์ปัญหาและความต้องการ', 'ออกแบบคลาสและความสัมพันธ์', 'ประยุกต์ OOP ในงานธุรกิจ'], 'tag': 'REAL-WORLD PROJECT', 'symbol': '◇'},
]


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    courses = sorted(
        Course.objects.prefetch_related(Prefetch('lessons', queryset=Lesson.objects.only('id', 'course_id', 'title', 'order', 'created_at'))),
        key=lambda course: (course.unit_number is None, course.unit_number or 0, course.created_at),
    )
    catalog = []
    for index, course in enumerate(courses):
        style = CURRICULUM[index % len(CURRICULUM)]
        catalog.append({
            'title': course.title, 'description': course.description,
            'topics': [lesson.title for lesson in course.lessons.all()],
            'tag': style['tag'], 'symbol': style['symbol'],
            'number': course.unit_number or index + 1, 'is_live': True,
        })
    if not catalog:
        catalog = [dict(unit, number=index + 1, is_live=False) for index, unit in enumerate(CURRICULUM)]
    return render(request, 'home.html', {'catalog': catalog, 'has_live_courses': bool(courses)})
