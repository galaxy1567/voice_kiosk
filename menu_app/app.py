import os
import json
from flask import (
    Flask, render_template, redirect,
    url_for, request, flash
)
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'      # 운영 시 반드시 안전한 값으로 교체

# -------------------------------------------------
# 설정
# -------------------------------------------------
ADMIN_FILE      = 'admin.json'          # 관리자 비밀번호 저장 파일
UPLOAD_FOLDER   = 'static/images'       # 이미지 업로드 폴더
ALLOWED_EXT     = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# -------------------------------------------------
# 기본 메뉴 (14개)
# -------------------------------------------------
DEFAULT_MENU = [
    { 'id': 1,  'name': '불고기 비빔밥', 'price': 9000,  'description': '신선한 야채와 불고기가 어우러진 비빔밥',   'allergies': ['유제품 알러지','콩 알러지'],                     'image_url': '/static/images/bibimbap.jpg'       },
    { 'id': 2,  'name': '해물파전',     'price': 12000, 'description': '각종 해산물이 들어간 바삭한 파전',          'allergies': ['해산물 알러지','밀 알러지','난류 알러지'],     'image_url': '/static/images/pajeon.jpg'          },
    { 'id': 3,  'name': '김치찌개',     'price': 8000,  'description': '매콤한 김치와 돼지고기가 들어간 찌개',      'allergies': ['해산물 알러지'],                               'image_url': '/static/images/kimchi_jjigae.jpg'   },
    { 'id': 4,  'name': '잡채',         'price': 15000, 'description': '당면과 각종 채소, 고기가 어우러진 잡채',    'allergies': ['밀 알러지','콩 알러지'],                     'image_url': '/static/images/japchae.jpg'         },
    { 'id': 5,  'name': '메밀 국수',    'price': 8500,  'description': '시원한 육수의 메밀 국수',                 'allergies': ['메밀 알러지','난류 알러지'],                  'image_url': '/static/images/memil_guksu.jpg'     },
    { 'id': 6,  'name': '견과류 샐러드','price': 7000,  'description': '신선한 채소와 견과류가 들어간 샐러드',      'allergies': ['견과류 알러지'],                              'image_url': '/static/images/salad.jpg'           },
    { 'id': 7,  'name': '두부조림',     'price': 7000,  'description': '부드러운 두부와 매콤한 양념의 조화',      'allergies': ['콩 알러지'],                                  'image_url': '/static/images/dubu_jorim.jpg'      },
    { 'id': 8,  'name': '갈비탕',       'price': 11000, 'description': '진하게 우려낸 소갈비 육수',                'allergies': ['유제품 알러지'],                              'image_url': '/static/images/galbitang.jpg'       },
    { 'id': 9,  'name': '계란말이',     'price': 6000,  'description': '부드럽고 촉촉한 계란말이',                'allergies': ['난류 알러지'],                                'image_url': '/static/images/gyeran_mari.jpg'     },
    { 'id': 10, 'name': '오징어볶음',   'price': 9500,  'description': '매콤하게 볶은 오징어와 채소',              'allergies': ['해산물 알러지'],                              'image_url': '/static/images/ojingeo_bokkeum.jpg' },
    { 'id': 11, 'name': '된장찌개',     'price': 8500,  'description': '구수한 된장과 야채가 어우러진 찌개',       'allergies': ['콩 알러지'],                                  'image_url': '/static/images/doenjang_jjigae.jpg' },
    { 'id': 12, 'name': '치즈돈까스',   'price': 10000, 'description': '치즈가 듬뿍 들어간 바삭한 돈까스',        'allergies': ['유제품 알러지','밀 알러지','난류 알러지'], 'image_url': '/static/images/cheese_donkatsu.jpg'  },
    { 'id': 13, 'name': '쌀국수',       'price': 9000,  'description': '진한 육수와 쌀국수의 조화',              'allergies': [],                                          'image_url': '/static/images/pho.jpg'             },
    { 'id': 14, 'name': '카레라이스',   'price': 8000,  'description': '한국식 매콤한 카레와 밥',                'allergies': ['밀 알러지'],                                  'image_url': '/static/images/curry_rice.jpg'      }
]

# 가변 전역 리스트
menu_items = DEFAULT_MENU.copy()

# -------------------------------------------------
# 보조 함수
# -------------------------------------------------
def ensure_menu_items():
    """menu_items 가 비어 있으면 DEFAULT_MENU 로 복구"""
    if not menu_items:
        menu_items.extend(DEFAULT_MENU.copy())

def get_allergies():
    """전체 알러지 목록 추출"""
    return sorted({a for item in menu_items for a in item['allergies']})

def allowed_file(filename: str) -> bool:
    """허용된 이미지 확장자 확인"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

def load_password() -> str:
    """관리자 비밀번호 읽기, 없으면 생성"""
    if not os.path.exists(ADMIN_FILE):
        save_password('12345')
    with open(ADMIN_FILE, 'r', encoding='utf-8') as f:
        return json.load(f).get('password', '12345')

def save_password(new_pw: str) -> None:
    """관리자 비밀번호 저장"""
    with open(ADMIN_FILE, 'w', encoding='utf-8') as f:
        json.dump({'password': new_pw}, f, ensure_ascii=False)

# -------------------------------------------------
# 라우트
# -------------------------------------------------
@app.route('/')
def index():
    ensure_menu_items()
    selected   = request.args.get('allergy')
    allergies  = get_allergies()
    menu       = [m for m in menu_items if selected in m['allergies']] if selected else menu_items
    return render_template('index.html',
                           menu_items=menu,
                           allergies=allergies,
                           selected_allergy=selected)

@app.route('/menu/<int:menu_id>')
def menu_detail(menu_id):
    ensure_menu_items()
    item = next((m for m in menu_items if m['id'] == menu_id), None)
    return render_template('detail.html', menu_item=item) \
        if item else redirect(url_for('index'))

@app.route('/add', methods=['GET', 'POST'])
def add_food():
    ensure_menu_items()
    if request.method == 'POST':
        if request.form.get('admin_password') != load_password():
            flash('관리자 비밀번호가 틀렸습니다.', 'danger')
            return redirect(url_for('add_food'))

        name        = request.form.get('name')
        price       = int(request.form.get('price', 0))
        description = request.form.get('description')
        allergies   = request.form.getlist('allergies')

        img_file = request.files.get('image')
        if img_file and allowed_file(img_file.filename):
            filename  = secure_filename(img_file.filename)
            img_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_url = f'/static/images/{filename}'
        else:
            image_url = '/static/images/default.jpg'

        new_id = max((m['id'] for m in menu_items), default=0) + 1
        menu_items.append({
            'id': new_id,
            'name': name,
            'price': price,
            'description': description,
            'allergies': allergies,
            'image_url': image_url
        })

        flash('음식이 추가되었습니다!', 'success')
        return redirect(url_for('index'))

    return render_template('add_food.html', allergies=get_allergies())

@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST':
        current_pw = request.form.get('current_password')
        new_pw     = request.form.get('new_password')
        confirm_pw = request.form.get('confirm_password')

        if current_pw != load_password():
            flash('현재 비밀번호가 틀렸습니다.', 'danger')
        elif new_pw != confirm_pw:
            flash('새 비밀번호가 일치하지 않습니다.', 'danger')
        else:
            save_password(new_pw)
            flash('비밀번호가 변경되었습니다!', 'success')
            return redirect(url_for('index'))

    return render_template('change_password.html')

# -------------------------------------------------
# 애플리케이션 실행
# -------------------------------------------------
if __name__ == '__main__':
    ensure_menu_items()
    if not os.path.exists(ADMIN_FILE):
        save_password('12345')
    app.run(debug=True)
