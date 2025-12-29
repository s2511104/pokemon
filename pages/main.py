import streamlit as st
import random
import csv
import os
import time  # 애니메이션용

# ==========================================
# 1. 데이터 로드 및 변환 함수
# ==========================================

TYPE_TRANSLATION = {
    "grass": "풀", "poison": "독", "fire": "불꽃", "flying": "비행",
    "water": "물", "bug": "벌레", "normal": "노말", "electric": "전기",
    "ground": "땅", "fairy": "페어리", "fighting": "격투", "psychic": "에스퍼",
    "rock": "바위", "steel": "강철", "ice": "얼음", "ghost": "고스트",
    "dragon": "드래곤", "dark": "악"
}

def load_pokemon_data(filename="pages/pokemonnnn.csv"): # 경로 주의
    pokemon_db = []
    
    # 파일 경로 체크 (경로가 다르면 여기서 수정 필요)
    if not os.path.exists(filename):
        # 혹시 현재 폴더에 있을 수도 있으니 체크
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

# ==========================================
# 2. 초기화 및 세션 상태 관리
# ==========================================

if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.turn = 1
    st.session_state.money = 0
    st.session_state.tech = 0
    st.session_state.gacha_cost = 100  # 초기 뽑기 비용
    
    initial_p = POKEMON_DB[0] if POKEMON_DB else None
    if initial_p:
        st.session_state.owned_pokemon = [{"data": initial_p, "id": 0, "assigned_to": "대기중"}]
    else:
        st.session_state.owned_pokemon = []
        
    st.session_state.pokemon_id_counter = 1
    st.session_state.owned_facilities = ["밭"]

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

    # 돈 확인
    cost = st.session_state.gacha_cost
    if st.session_state.money < cost:
        return None, "No Money"

    # 돈 차감 및 가격 인상
    st.session_state.money -= cost
    st.session_state.gacha_cost += 100

    # 보유하지 않은 포켓몬 리스트
    current_names = [p['data']['name'] for p in st.session_state.owned_pokemon]
    available_all = [p for p in POKEMON_DB if p['name'] not in current_names]
    
    if not available_all:
        return None, "All Collected"

    # 확률 로직 적용
    # 1. 선호 타입 그룹과 나머지 그룹 분리
    target_group = [p for p in available_all if p['type'] == preferred_type]
    other_group = [p for p in available_all if p['type'] != preferred_type]

    selected_data = None

    # 둘 다 있으면 확률 적용 (30% vs 70%)
    if target_group and other_group:
        if random.random() < 0.3: # 30% 확률로 선호 타입
            selected_data = random.choice(target_group)
        else: # 70% 확률로 나머지
            selected_data = random.choice(other_group)
    elif target_group: # 선호 타입만 남았으면 100%
        selected_data = random.choice(target_group)
    else: # 선호 타입이 없으면 나머지에서 100%
        selected_data = random.choice(other_group)

    # 등록
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

st.set_page_config(layout="wide", page_title="CSV 포켓몬 농장")

if not POKEMON_DB:
    st.stop()

# --- [2] 상단 상태바 (돈, 턴, 기술) ---
# 기존 사이드바 대신 메인 상단에 배치
st.title("🚜 포켓몬 농장 관리 시뮬레이션")

# 상단 지표 표시
col_stat1, col_stat2, col_stat3 = st.columns(3)
col_stat1.metric("📅 DAY (Turn)", st.session_state.turn)
col_stat2.metric("💰 보유 자금", f"{st.session_state.money}원")
col_stat3.metric("💡 기술 점수", f"{st.session_state.tech}점")

st.divider()

# --- [4] 턴 종료 버튼 및 애니메이션 ---
# 애니메이션을 위한 공간 확보
anim_placeholder = st.empty()

if st.button("🌙 턴 종료 (하루 마감)", type="primary", use_container_width=True):
    # 애니메이션 효과 (단순 딜레이와 텍스트 변화로 구현)
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

# --- 메인 레이아웃 (사이드바 대신 탭이나 컬럼 활용) ---
col_left, col_right = st.columns([1, 1.2])

# === 왼쪽: 생명의 나무 & 시설 건설 ===
with col_left:
    # [3] 생명의 나무 (가챠)
    st.subheader("🌳 생명의 나무 (소환)")
    with st.container(border=True):
        st.write(f"현재 소환 비용: **{st.session_state.gacha_cost}원**")
        st.caption("비용은 매번 100원씩 증가합니다.")
        
        # 타입 선택
        type_options = list(TYPE_TRANSLATION.values())
        target_type = st.selectbox("기원할 타입 (확률 30% UP)", type_options)
        
        if st.button("🔮 영혼의 부름 (소환)", use_container_width=True):
            result_data, msg = gacha_pokemon(target_type)
            if msg == "Success":
                st.balloons()
                st.success(f"야생의 **{result_data['name']}**({result_data['type']}) 등장!")
                st.rerun()
            elif msg == "No Money":
                st.error("돈이 부족합니다!")
            elif msg == "All Collected":
                st.warning("이 지역의 모든 포켓몬을 잡았습니다!")

    st.divider()

    st.subheader("🏗️ 시설 건설")
    for fac_name, info in FACILITIES_INFO.items():
        if fac_name in st.session_state.owned_facilities:
            continue
            
        # 건설 조건 확인
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

# === 오른쪽: 포켓몬 배치 & 현황 ===
with col_right:
    st.subheader("🏭 시설 현황")
    
    # 시설별 요약 (아코디언)
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

    # [1] 포켓몬 배치 (체크박스/라디오 스타일)
    st.subheader("📋 일꾼 작업 지시")
    st.info("각 포켓몬 카드의 옵션을 선택(체크)하여 배치하세요.")
    
    # 현재 건설된 시설 목록 (대기중 포함)
    available_locations = ["대기중"] + st.session_state.owned_facilities
    
    for p in st.session_state.owned_pokemon:
        with st.container(border=True):
            c1, c2 = st.columns([1, 2])
            with c1:
                st.markdown(f"#### {p['data']['name']}")
                st.caption(f"타입: **{p['data']['type']}**")
                
                # 현재 배치 상태에 따른 효율 표시
                curr_loc = p['assigned_to']
                if curr_loc != "대기중":
                    prod, status = calculate_efficiency(p['data'], curr_loc)
                    color = "green" if "최적" in status else "red" if "불가" in status else "blue"
                    st.markdown(f":{color}[{status} (+{prod})]")
                else:
                    st.markdown(":grey[휴식 중]")

            with c2:
                # [1] 체크박스 대신 Radio 버튼 사용 (하나만 선택해야 하므로)
                # 건설되지 않은 시설은 보이지 않으므로 자동으로 처리됨
                new_loc = st.radio(
                    f"{p['data']['name']}의 작업장:",
                    available_locations,
                    key=f"radio_{p['id']}",
                    index=available_locations.index(p['assigned_to']),
                    horizontal=True # 가로로 배치해서 공간 절약
                )
                
                # 값이 바뀌면 즉시 반영 및 리런
                if new_loc != p['assigned_to']:
                    p['assigned_to'] = new_loc
                    st.rerun()
