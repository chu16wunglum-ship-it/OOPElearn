import requests
from django.conf import settings

MODEL = 'gemini-2.5-flash'
GEMINI_URL = f'https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent'


def ask_ai(system_prompt, user_message, max_tokens=1024, history=None):
    """Send a request to Gemini, optionally continuing a prior conversation. Returns (ok, text)."""
    if not settings.GEMINI_API_KEY:
        return False, 'ยังไม่ได้ตั้งค่า GEMINI_API_KEY บนเซิร์ฟเวอร์'

    contents = []
    for turn in (history or []):
        role = 'model' if turn.get('role') == 'assistant' else 'user'
        contents.append({'role': role, 'parts': [{'text': turn.get('content', '')}]})
    contents.append({'role': 'user', 'parts': [{'text': user_message}]})

    payload = {
        'system_instruction': {'parts': [{'text': system_prompt}]},
        'contents': contents,
        'generationConfig': {'maxOutputTokens': max_tokens},
    }
    try:
        response = requests.post(
            GEMINI_URL, params={'key': settings.GEMINI_API_KEY}, json=payload, timeout=30,
        )
    except requests.RequestException:
        return False, 'ไม่สามารถติดต่อ AI ได้ในขณะนี้ กรุณาลองใหม่อีกครั้ง'

    if response.status_code != 200:
        return False, 'ไม่สามารถติดต่อ AI ได้ในขณะนี้ กรุณาลองใหม่อีกครั้ง'

    candidates = response.json().get('candidates') or []
    if not candidates:
        return False, 'AI ไม่สามารถตอบคำถามนี้ได้'

    parts = candidates[0].get('content', {}).get('parts', [])
    text = ''.join(p.get('text', '') for p in parts if 'text' in p)
    if not text:
        return False, 'AI ไม่สามารถตอบคำถามนี้ได้'
    return True, text
