from django import forms

from oopelearn.formutils import BootstrapFormMixin

TRUE_LABEL = 'ถูก'
FALSE_LABEL = 'ผิด'


class QuestionForm(BootstrapFormMixin, forms.Form):
    QUESTION_TYPE_CHOICES = [('mc', 'แบบเลือกตอบ'), ('tf', 'แบบถูก/ผิด')]

    question_type = forms.ChoiceField(
        label='ประเภทคำถาม', choices=QUESTION_TYPE_CHOICES,
        widget=forms.RadioSelect, initial='mc',
    )
    text = forms.CharField(label='คำถาม', widget=forms.Textarea(attrs={'rows': 2}))
    trigger_time = forms.IntegerField(
        label='แสดงคำถามที่วินาทีที่ (ของวิดีโอ)', required=False, min_value=0,
        widget=forms.NumberInput(attrs={'placeholder': 'เช่น 90'}),
    )
    choice_1 = forms.CharField(label='ตัวเลือกที่ 1', max_length=500, required=False)
    choice_2 = forms.CharField(label='ตัวเลือกที่ 2', max_length=500, required=False)
    choice_3 = forms.CharField(label='ตัวเลือกที่ 3', max_length=500, required=False)
    choice_4 = forms.CharField(label='ตัวเลือกที่ 4', max_length=500, required=False)
    correct_choice = forms.ChoiceField(
        label='ตัวเลือกที่ถูกต้อง',
        choices=[('1', 'ตัวเลือกที่ 1'), ('2', 'ตัวเลือกที่ 2'), ('3', 'ตัวเลือกที่ 3'), ('4', 'ตัวเลือกที่ 4')],
        widget=forms.RadioSelect,
    )

    def __init__(self, *args, requires_trigger_time=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.requires_trigger_time = requires_trigger_time
        if requires_trigger_time:
            self.fields['trigger_time'].required = True

    def clean(self):
        cleaned = super().clean()
        correct = cleaned.get('correct_choice')

        if cleaned.get('question_type') == 'tf':
            cleaned['choice_1'] = TRUE_LABEL
            cleaned['choice_2'] = FALSE_LABEL
            cleaned['choice_3'] = ''
            cleaned['choice_4'] = ''
            if correct not in ('1', '2'):
                self.add_error('correct_choice', 'กรุณาเลือกว่าคำตอบที่ถูกต้องคือ ถูก หรือ ผิด')
        else:
            if not cleaned.get('choice_1'):
                self.add_error('choice_1', 'กรุณากรอกตัวเลือกที่ 1')
            if not cleaned.get('choice_2'):
                self.add_error('choice_2', 'กรุณากรอกตัวเลือกที่ 2')
            if correct and not cleaned.get(f'choice_{correct}'):
                self.add_error('correct_choice', 'ตัวเลือกที่เลือกว่าถูกต้องต้องมีข้อความ')
        return cleaned
