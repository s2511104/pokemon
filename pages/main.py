import streamlit as st
import random
import csv
import os
import time

# ==========================================
# 0. 설정 및 유틸리티
# ==========================================

st.set_page_config(layout="wide", page_title="포켓몬 농장 시뮬레이션")

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

# 이미지 경로 찾기 도우미 함수 (대소문자 문제 해결)
def get_image_path(pokemon_name):
    # 1. 원래 이름으로 시도 (Bulbasaur.png)
    path = f"pages/image/{pokemon_name}.png"
    if os.path.exists(path):
        return path
    
    # 2. 소문자로 시도 (bulbasaur.png)
    path_lower = f"pages/image/{pokemon_name.lower()}.png"
    if os.path.exists(path_lower):
        return path_lower
        
    return None

# ==========================================
# 1. 데이터 로드
# ==========================================

def load_pokemon_data(filename="pages/pokemonnnn.csv"):
    pokemon_db = []
    
    # 경로 유연성 확보 (현재 폴더 or pages 폴더)
    if not os.path.exists(filename):
        if os.path.exists("pokemonnnn.csv"):
            filename = "pokemonnnn.csv"
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
        st.error(f"데이터 로드 중 오류 발생: {e}")
        return []
        
    return pokemon_db

POKEMON_DB = load_pokemon_data()

# ==========================================
# 2. 초기화 및 세션 상태 관리
# ==========================================

# 기본 초기화
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.turn = 1
    st.session_state.money = 0
    st.session_state.tech = 0
    st.session_state.pokemon_id_counter = 1
    st.session_state.owned_facilities = ["밭"]
    st.session_state.gacha_cost = 100 # 초기 비용
    
    # 첫 포켓몬 지급
    initial_p = POKEMON_DB[0] if POKEMON_DB else None
    if initial_p:
        st.session_state.owned_pokemon = [{"data": initial_p, "id": 0, "assigned_to": "대기중"}]
    else:
        st.session_state.owned_pokemon = []

# [안전장치] 실행 중 코드가 바뀌어 변수가 없을 경우 대비
if 'gacha_cost' not in st.session_state:
    st.session_state.gacha_cost = 100

# ==========================================
# 3. 로직 함수
# ==========================================

def calculate_efficiency(pokemon_data, facility_name):
    if facility_name == "대기중":
        return 0, ""
    
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
        
    base_stat = pokemon_data[fac_info['stat']]
    production = int(base_stat * multiplier)
    
    return production, status

def process_turn():
    total_money_gain = 0
    total_tech_gain = 0
    
    for p in st.session_state.owned_pokemon:
        fac_name = p['assigned_to']
        if fac_name != "대기중":
            prod, _ = calculate_efficiency(p['data'], fac_name)
            if FACILITIES_INFO[fac_name]['output'] == 'money':
                total_money_gain += prod
            else:
                total_tech_gain += prod

    st.session_state.money += total_money_gain
    st.session_state.tech += total_tech_gain
    st.session_state.turn += 1
    
    return total_money_gain, total_tech_gain

def gacha_pokemon(preferred_type):
    if not POKEMON_DB:
        return None, "DB Empty"

    cost = st.session_state.gacha_cost
    if st.session_state.money < cost:
        return None, "No Money"

    # 비용 지불 및 인상
    st.session_state.money -= cost
    st.session_state.gacha_cost += 100

    # 미보유 포켓몬 필터링
    current_names = [p['data']['name'] for p in st.session_state.owned_pokemon]
    available_all = [p for p in POKEMON_DB if p['name'] not in current_names]
    
    if not available_all:
        return None, "All Collected"

    # 확률 로직: 선호 타입 30% / 나머지 70%
    target_group = [p for p in available_all if p['type'] == preferred_type]
    other_group = [p for p in available_all if p['type'] != preferred_type]

    selected_data = None
    if target_group and other_group:
        if random.random() < 0.3:
            selected_data = random.choice(target_group)
        else:
            selected_data = random.choice(other_group)
    elif target_group:
        selected_data = random.choice(target_group)
    else:
        selected_data = random.choice(other_group)

    new_p = {
        "data": selected_data,
        "id": st.session_state.pokemon_id_counter,
        "assigned_to": "대기중"
    }
    st.session_state.owned_pokemon.append(new_p)
    st.session_state.pokemon_id_counter += 1
    
    return selected_data, "Success"

# ==========================================
# 4. UI 구성
# ==========================================

if not POKEMON_DB:
    st.stop()

# --- 상단 상태바 ---
st.title("🚜 포켓몬 농장 관리 시뮬레이션")

col_stat1, col_stat2, col_stat3 = st.columns(3)
col_stat1.metric("📅 DAY (Turn)", st.session_state.turn)
col_stat2.metric("💰 보유 자금", f"{st.session_state.money}원")
col_stat3.metric("💡 기술 점수", f"{st.session_state.tech}점")

st.divider()

# --- 턴 종료 및 애니메이션 ---
anim_placeholder = st.empty()

if st.button("🌙 턴 종료 (하루 마감)", type="primary", use_container_width=True):
    with anim_placeholder.container():
        st.info("☀️ 해가 저물고 있습니다...")
        time.sleep(0.7)
        st.warning("🌙 밤이 되었습니다. 포켓몬들이 정산을 시작합니다...")
        time.sleep(0.7)
        st.success("☀️ 꼬끼오~ 아침이 밝았습니다!")
        time.sleep(0.5)
    
    m_gain, t_gain = process_turn()
    st.toast(f"지난 밤 수익: 💰+{m_gain}, 💡+{t_gain}")
    st.rerun()

st.divider()

# --- 메인 레이아웃 ---
col_left, col_right = st.columns([1, 1.2])

# === 왼쪽: 생명의 나무 & 시설 건설 ===
with col_left:
    # 1. 생명의 나무 (가챠)
    st.subheader("🌳 생명의 나무 (소환)")
    with st.container(border=True):
        st.write(f"현재 소환 비용: **{st.session_state.gacha_cost}원**")
        st.caption("비용은 매번 100원씩 증가합니다.")
        
        type_options = list(TYPE_TRANSLATION.values())
        target_type = st.selectbox("기원할 타입 (확률 30% UP)", type_options)
        
        if st.button("🔮 영혼의 부름 (소환)", use_container_width=True):
            result_data, msg = gacha_pokemon(target_type)
            if msg == "Success":
                st.balloons()
                
                # 가챠 이미지 표시
                img_path = get_image_path(result_data['name'])
                if img_path:
                    st.image(img_path, width=200)
                    
                st.success(f"야생의 **{result_data['name']}**({result_data['type']}) 등장!")
                time.sleep(1.5)
                st.rerun()
            elif msg == "No Money":
                st.error("돈이 부족합니다!")
            elif msg == "All Collected":
                st.warning("이 지역의 모든 포켓몬을 잡았습니다!")

    st.divider()

    # 2. 시설 건설
    st.subheader("🏗️ 시설 건설")
    for fac_name, info in FACILITIES_INFO.items():
        if fac_name in st.session_state.owned_facilities:
            continue
            
        can_build = (st.session_state.money >= info['cost']) and (st.session_state.tech >= info['tech_req'])
        
        with st.expander(f"{fac_name} (비용: {info['cost']} / 기술: {info['tech_req']})"):
            st.write(f"효과: {info['output']} 생산")
            st.caption(f"👍 {info['boost']} 2배 / 👎 {info['banned']} 금지")
            
            if can_build:
                if st.button(f"🔨 {fac_name} 건설하기", key=f"build_{fac_name}"):
                    st.session_state.money -= info['cost']
                    st.session_state.owned_facilities.append(fac_name)
                    st.rerun()
            else:
                if st.session_state.money < info['cost']: st.caption("❌ 자금 부족")
                if st.session_state.tech < info['tech_req']: st.caption("❌ 기술 부족")

# === 오른쪽: 현황 & 배치 ===
with col_right:
    # 3. 시설 현황
    st.subheader("🏭 시설 현황")
    for fac in st.session_state.owned_facilities:
        workers = [p for p in st.session_state.owned_pokemon if p['assigned_to'] == fac]
        fac_prod = 0
        for w in workers:
            prod, _ = calculate_efficiency(w['data'], fac)
            fac_prod += prod
            
        output_type = FACILITIES_INFO[fac]['output']
        with st.expander(f"{fac} (일꾼 {len(workers)}명) ➡ +{fac_prod} {output_type}", expanded=False):
            for w in workers:
                st.text(f"- {w['data']['name']}")

    st.divider()

    # 4. 일꾼 배치 (이미지 포함)
    st.subheader("📋 일꾼 작업 지시")
    st.info("각 포켓몬의 업무를 배정하세요.")
    
    available_locations = ["대기중"] + st.session_state.owned_facilities
    
    for p in st.session_state.owned_pokemon:
        with st.container(border=True):
            # 레이아웃: 이미지(작게) + 텍스트(중간) + 선택버튼(크게)
            c1, c2 = st.columns([1.5, 2.5])
            
            with c1:
                # 포켓몬 이미지 표시
                img_path = get_image_path(p['data']['name'])
                if img_path:
                    st.image(img_path, width=100)
                else:
                    st.caption("No Image")

                st.markdown(f"#### {p['data']['name']}")
                st.caption(f"타입: **{p['data']['type']}**")
                
                # 효율 표시
                curr_loc = p['assigned_to']
                if curr_loc != "대기중":
                    prod, status = calculate_efficiency(p['data'], curr_loc)
                    color = "green" if "최적" in status else "red" if "불가" in status else "blue"
                    st.markdown(f":{color}[{status} (+{prod})]")
                else:
                    st.markdown(":grey[휴식 중]")

            with c2:
                # 라디오 버튼으로 시설 선택
                new_loc = st.radio(
                    f"{p['data']['name']} 작업장:",
                    available_locations,
                    key=f"radio_{p['id']}",
                    index=available_locations.index(p['assigned_to']),
                    horizontal=True,
                    label_visibility="collapsed"
                )
                
                if new_loc != p['assigned_to']:
                    p['assigned_to'] = new_loc
                    st.rerun()
