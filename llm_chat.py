import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model = os.getenv("OPENAI_MODEL", "gpt-4o")

def extract_command(user_input):
    system_prompt = """
    너는 음식 키오스크의 AI야.
    사용자의 요청을 다음 JSON 중 하나의 형태로 변환해줘:

    - 알러지가 없는 메뉴: { "action": "filter", "target": "allergy", "value": "eggs" }
    - 알러지가 들어간 메뉴만: { "action": "only", "target": "allergy", "value": "eggs" }
    - 비건 단계 필터링: { "action": "filter", "target": "vegan_level", "value": "비건" }
    - 초기화: { "action": "reset" }

    JSON 외에는 아무것도 출력하지 마.
    """

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        temperature=0
    )

    content = response.choices[0].message.content.strip()
    return eval(content)
