import streamlit as st
import random
import csv
import os
import time

# ==========================================
# 0. 설정 및 유틸리티
# ==========================================

st.set_page_config(layout="wide", page_title="포켓몬 농장 시뮬레이션")

# --- CSS 스타일링 (공원 느낌 내기) ---
st.markdown("""
<style>
    /* 공원 구역 스타일 */
    .park-container {
        background-color: #e8f5e9;
        border: 2px dashed #4caf50;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .park-title {
        color: #2e7d32;
        font-weight: bold;
        text-align: center;
        margin-bottom: 10px;
    }
    /* 시설 구역 스타일 */
    .facility-container {
        background-color: #fff3e0;
        border: 2px solid #ff9800;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# 영어 타입을 한글로 변환
TYPE_TRANSLATION = {
    "grass": "풀", "poison": "독", "fire": "불꽃", "flying": "비행",
    "water": "물", "bug": "벌레", "normal": "노말", "electric": "전기",
    "ground": "땅", "fairy": "페어리", "fighting": "격투", "psychic": "에스퍼",
    "rock": "바위", "steel": "강철", "ice": "얼음", "ghost": "고스트",
    "dragon": "드래곤", "dark": "악"
}

# 시설 정보 정의
FACILITIES_INFO = {
    "밭": {"cost": 0, "tech_req": 0, "banned": "독", "boost": "물", "stat": "hp", "output": "money"},
    "과수원": {"cost": 100, "tech_req": 10, "banned": "불꽃", "boost": "풀", "stat": "hp", "output": "money"},
    "닭장": {"cost": 300, "tech_req": 30, "banned": "벌레", "boost": "비행", "stat": "hp", "output": "money"},
    "채석장": {"cost": 500, "tech_req": 50, "banned": "물", "boost": "바위", "stat": "attack", "output": "money"},
    "도서관": {"cost": 800, "tech_req": 80, "banned": "격투", "boost": "에스퍼", "stat": "sp_atk", "output": "tech"},
    "광산": {"cost": 1200, "tech_req": 120, "banned": "드래곤", "boost": "땅", "stat": "attack", "output": "money"},
    "풍차": {"cost": 1500, "tech_req": 150, "banned": "전기", "boost": "격투", "stat": "defense", "output": "money"},
    "용광로": {"cost": 2000, "tech_req": 200, "banned": "강철", "boost": "불꽃", "stat": "sp_def", "output": "money"},
    "대장간": {"cost": 2500, "tech_req": 250, "banned": "고스트", "boost": "강철", "stat": "attack", "output": "money"},
    "발전소": {"cost": 3000, "tech_req": 300, "banned": "땅", "boost": "전기", "stat": "sp_atk", "output": "money"},
}

def get_image_path(pokemon_name):
    path = f"pages/image/{pokemon_name}.png"
    if os.path.exists(path): return path
    path_lower = f"pages/image/{pokemon_name.lower()}.png"
    if os.path.exists(path_lower): return path_lower
    return None

def get_stats_tooltip(data):
    """마우스 오버 시 보여줄 스탯 정보 문자열 생성"""
    return f"""
    [상세 정보]
    ❤ HP: {data['hp']}
    ⚔ 공격: {data['attack']} | 🛡 방어: {data['defense']}
    🔮 특공: {data['sp_atk']} | 🛡 특방: {data['sp_def']}
    ⚡ 스피드: {data['speed']}
    """

# ==========================================
# 1. 데이터 로드 및 로직
# ==========================================

def load_pokemon_data(filename="pages/pokemonnnn.csv"):
    pokemon_db = []
    if not os.path.exists(filename):
        if os.path.exists("pokemonnnn.csv"): filename = "pokemonnnn.csv"
        else:
            st.error(f"❌ '{filename}' 파일을 찾을 수 없습니다.")
            return []
    try:
        with open(filename, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                p_type_eng = row['type_1'].lower()
                p_type_kor = TYPE_TRANSLATION.get(p_type_eng, "노말")
                pokemon_db.append({
                    "name": row['name'],
                    "type": p_type_kor,
                    "hp": int(row['hp']),
                    "attack": int(row['attack']),
                    "defense": int(row['defense']),
                    "sp_atk": int(row['special_attack']),
                    "sp_def": int(row['special_defense']),
                    "speed": int(row['speed'])
                })
    except Exception as e:
        st.error(f"오류: {e}")
        return []
    return pokemon_db

POKEMON_DB = load_pokemon_data()

# 초기화
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.turn = 1
    st.session_state.money = 0
    st.session_state.tech = 0
    st.session_state.pokemon_id_counter = 1
    st.session_state.owned_facilities = ["밭"]
    st.session_state.gacha_cost = 100
    if POKEMON_DB:
        st.session_state.owned_pokemon = [{"data": POKEMON_DB[0], "id": 0, "assigned_to": "대기중"}]
    else:
        st.session_state.owned_pokemon = []

if 'gacha_cost' not in st.session_state: st.session_state.gacha_cost = 100

def calculate_efficiency(pokemon_data, facility_name):
    if facility_name == "대기중": return 0, ""
    fac_info = FACILITIES_INFO[facility_name]
    p_type = pokemon_data['type']
    multiplier = 1.0
    status = "정상"
    if p_type == fac_info['banned']:
        multiplier = 0.0
        status = "불가(타입)"
    elif p_type == fac_info['boost']:
        multiplier = 2.0
        status = "최적(2배)"
    production = int(pokemon_data[fac_info['stat']] * multiplier)
    return production, status

def process_turn():
    m_gain, t_gain = 0, 0
    for p in st.session_state.owned_pokemon:
        fac = p['assigned_to']
        if fac != "대기중":
            prod, _ = calculate_efficiency(p['data'], fac)
            if FACILITIES_INFO[fac]['output'] == 'money': m_gain += prod
            else: t_gain += prod
    st.session_state.money += m_gain
    st.session_state.tech += t_gain
    st.session_state.turn += 1
    return m_gain, t_gain

def gacha_pokemon(preferred_type):
    if not POKEMON_DB: return None, "DB Empty"
    cost = st.session_state.gacha_cost
    if st.session_state.money < cost: return None, "No Money"
    
    st.session_state.money -= cost
    st.session_state.gacha_cost += 100
    
    current_names = [p['data']['name'] for p in st.session_state.owned_pokemon]
    available = [p for p in POKEMON_DB if p['name'] not in current_names]
    if not available: return None, "All Collected"
    
    target = [p for p in available if p['type'] == preferred_type]
    other = [p for p in available if p['type'] != preferred_type]
    
    if target and other: selected = random.choice(target) if random.random() < 0.3 else random.choice(other)
    elif target: selected = random.choice(target)
    else: selected = random.choice(other)
    
    st.session_state.owned_pokemon.append({"data": selected, "id": st.session_state.pokemon_id_counter, "assigned_to": "대기중"})
    st.session_state.pokemon_id_counter += 1
    return selected, "Success"

# ==========================================
# 2. UI 구성
# ==========================================

st.title("🚜 포켓몬 농장 관리 시뮬레이션")
c1, c2, c3 = st.columns(3)
c1.metric("📅 DAY", st.session_state.turn)
c2.metric("💰 자금", f"{st.session_state.money}원")
c3.metric("💡 기술", f"{st.session_state.tech}점")

if st.button("🌙 턴 종료 (하루 마감)", type="primary", use_container_width=True):
    with st.spinner("🌙 밤이 지나는 중..."):
        time.sleep(1.2)
    m, t = process_turn()
    st.toast(f"수익 발생! 💰+{m}, 💡+{t}")
    st.rerun()

st.divider()

# 레이아웃: 왼쪽(가챠/건설) vs 오른쪽(공원 및 배치)
col_left, col_right = st.columns([1, 1.5])

with col_left:
    st.subheader("🌳 생명의 나무")
    with st.container(border=True):
        st.write(f"소환 비용: **{st.session_state.gacha_cost}원**")
        t_type = st.selectbox("기원 타입", list(TYPE_TRANSLATION.values()))
        if st.button("🔮 소환하기", use_container_width=True):
            res, msg = gacha_pokemon(t_type)
            if msg == "Success":
                st.balloons()
                img = get_image_path(res['name'])
                if img: st.image(img, width=150)
                st.success(f"{res['name']} 획득!")
                st.rerun()
            elif msg == "No Money": st.error("돈 부족!")
            elif msg == "All Collected": st.warning("도감 완성!")

    st.subheader("🏗️ 시설 건설")
    for fac, info in FACILITIES_INFO.items():
        if fac not in st.session_state.owned_facilities:
            can_build = st.session_state.money >= info['cost'] and st.session_state.tech >= info['tech_req']
            with st.expander(f"{fac} ({info['cost']}원)"):
                st.caption(f"생산: {info['output']} | 조건: {info['boost']}↑ {info['banned']}X")
                if can_build:
                    if st.button("건설", key=f"b_{fac}"):
                        st.session_state.money -= info['cost']
                        st.session_state.owned_facilities.append(fac)
                        st.rerun()
                else:
                    st.caption("🔒 자원 부족")

with col_right:
    # === 1. 평화의 공원 (대기 중인 포켓몬) ===
    st.markdown('<div class="park-container"><div class="park-title">🌿 평화의 공원 (대기중)</div>', unsafe_allow_html=True)
    
    idle_pokemons = [p for p in st.session_state.owned_pokemon if p['assigned_to'] == "대기중"]
    
    if not idle_pokemons:
        st.caption("공원이 비어있습니다. 모두 일하는 중!")
    else:
        # 그리드 형태로 배치 (한 줄에 3마리씩)
        cols = st.columns(3)
        for idx, p in enumerate(idle_pokemons):
            with cols[idx % 3]:
                with st.container(border=True):
                    # 이미지 표시
                    img_path = get_image_path(p['data']['name'])
                    if img_path:
                        st.image(img_path, use_container_width=True)
                    
                    st.markdown(f"**{p['data']['name']}**")
                    st.caption(f"타입: {p['data']['type']}")
                    
                    # 툴팁이 적용된 배치 변경 위젯
                    available_facilities = ["대기중"] + st.session_state.owned_facilities
                    
                    # help 파라미터에 스탯 정보 넣기 (마우스 오버 시 보임)
                    new_loc = st.selectbox(
                        "배치", 
                        available_facilities, 
                        key=f"sel_{p['id']}", 
                        index=0,
                        label_visibility="collapsed",
                        help=get_stats_tooltip(p['data'])  # ✨ 여기가 핵심! 마우스 올리면 스탯 뜸
                    )
                    
                    if new_loc != "대기중":
                        p['assigned_to'] = new_loc
                        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # === 2. 작업장 현황 ===
    st.subheader("🏭 작업 현황")
    
    active_facilities = st.session_state.owned_facilities
    if "대기중" in active_facilities: active_facilities.remove("대기중")

    for fac in active_facilities:
        workers = [p for p in st.session_state.owned_pokemon if p['assigned_to'] == fac]
        fac_info = FACILITIES_INFO[fac]
        
        # 시설 총 생산량 계산
        total_prod = sum([calculate_efficiency(w['data'], fac)[0] for w in workers])
        
        with st.expander(f"{fac} (일꾼 {len(workers)}명) ➡ +{total_prod} {fac_info['output']}", expanded=True):
            if not workers:
                st.caption("일꾼이 없습니다.")
            
            for w in workers:
                c_img, c_info, c_act = st.columns([1, 2, 1.5])
                with c_img:
                    img = get_image_path(w['data']['name'])
                    if img: st.image(img, width=50)
                
                with c_info:
                    prod, status = calculate_efficiency(w['data'], fac)
                    color = "green" if "최적" in status else "red" if "불가" in status else "blue"
                    st.markdown(f"**{w['data']['name']}**")
                    st.markdown(f":{color}[{status} (+{prod})]")

                with c_act:
                    if st.button("휴식", key=f"rest_{w['id']}", help=get_stats_tooltip(w['data'])):
                        w['assigned_to'] = "대기중"
                        st.rerun()
