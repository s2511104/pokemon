import streamlit as st
import random
import csv
import os

# ==========================================
# 1. 데이터 로드 및 변환 함수
# ==========================================

# 영어 타입을 한글로 변환하기 위한 사전
TYPE_TRANSLATION = {
    "grass": "풀", "poison": "독", "fire": "불꽃", "flying": "비행",
    "water": "물", "bug": "벌레", "normal": "노말", "electric": "전기",
    "ground": "땅", "fairy": "페어리", "fighting": "격투", "psychic": "에스퍼",
    "rock": "바위", "steel": "강철", "ice": "얼음", "ghost": "고스트",
    "dragon": "드래곤", "dark": "악"
}

def load_pokemon_data(filename="pokemon/pages/pokemonnnn.csv"):
    pokemon_db = []
    
    if not os.path.exists(filename):
        st.error(f"'{filename}' 파일을 찾을 수 없습니다! 같은 폴더에 파일을 만들어주세요.")
        return []

    with open(filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # CSV 데이터를 게임 데이터 형식으로 변환
            p_type_eng = row['type_1'].lower()
            p_type_kor = TYPE_TRANSLATION.get(p_type_eng, "노말") # 없으면 노말
            
            pokemon_db.append({
                "name": row['name'],          # 이름은 영어 그대로 사용 (Bulbasaur 등)
                "type": p_type_kor,           # 타입은 한글로 변환
                "hp": int(row['hp']),
                "attack": int(row['attack']),
                "defense": int(row['defense']),
                "sp_atk": int(row['special_attack']),  # 컬럼명 매핑
                "sp_def": int(row['special_defense']),
                "speed": int(row['speed'])
            })
    return pokemon_db

# 데이터 로드
POKEMON_DB = load_pokemon_data()

# 시설 정보 (기존 유지)
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
    
    # DB가 비어있지 않다면 첫 번째 포켓몬 지급
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

def gacha_pokemon():
    if not POKEMON_DB:
        return None
        
    # 현재 없는 포켓몬 중 랜덤 뽑기 (이름 기준 중복 체크)
    current_names = [p['data']['name'] for p in st.session_state.owned_pokemon]
    available = [p for p in POKEMON_DB if p['name'] not in current_names]
    
    if available:
        new_data = random.choice(available)
        new_p = {
            "data": new_data,
            "id": st.session_state.pokemon_id_counter,
            "assigned_to": "대기중"
        }
        st.session_state.owned_pokemon.append(new_p)
        st.session_state.pokemon_id_counter += 1
        return new_data
    return None

# ==========================================
# 4. UI 구성
# ==========================================

st.set_page_config(layout="wide", page_title="CSV 포켓몬 농장")

if not POKEMON_DB:
    st.warning("⚠️ 'pokemon.csv' 파일이 없습니다. 코드가 있는 폴더에 파일을 만들어주세요.")
    st.stop()

# --- 사이드바 ---
with st.sidebar:
    st.title(f"Turn {st.session_state.turn}")
    st.metric("💰 자금", st.session_state.money)
    st.metric("💡 기술", st.session_state.tech)
    
    st.divider()
    st.subheader("🌳 생명의 나무")
    
    if st.button("🍲 요리하기 (일꾼 소환)", use_container_width=True):
        new_mon = gacha_pokemon()
        if new_mon:
            st.success(f"{new_mon['name']}({new_mon['type']}) 획득!")
        else:
            st.warning("데이터베이스의 모든 포켓몬을 모았습니다!")

    st.divider()
    st.subheader("🏗️ 시설 건설")
    
    for fac_name, info in FACILITIES_INFO.items():
        if fac_name in st.session_state.owned_facilities:
            continue
            
        if st.session_state.money >= info['cost'] and st.session_state.tech >= info['tech_req']:
            if st.button(f"{fac_name} 건설 ({info['cost']}원)", use_container_width=True):
                st.session_state.money -= info['cost']
                st.session_state.owned_facilities.append(fac_name)
                st.rerun()
        else:
            status = []
            if st.session_state.money < info['cost']: status.append("돈 부족")
            if st.session_state.tech < info['tech_req']: status.append("기술 부족")
            st.text(f"🔒 {fac_name}: {', '.join(status)}")

# --- 메인 화면 ---

st.title("📊 CSV 기반 포켓몬 농장")
st.caption(f"총 {len(POKEMON_DB)}마리의 포켓몬 데이터가 로드되었습니다.")

if st.button("🌙 턴 종료 (작업 시작)", type="primary", use_container_width=True):
    m_gain, t_gain = process_turn()
    st.toast(f"수익 발생! 💰+{m_gain}, 💡+{t_gain}")
    st.rerun()

st.divider()

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📋 일꾼 배치 관리")
    
    location_options = ["대기중"] + st.session_state.owned_facilities
    
    for p in st.session_state.owned_pokemon:
        with st.container(border=True):
            c1, c2 = st.columns([2, 3])
            with c1:
                st.markdown(f"**{p['data']['name']}**")
                # 타입에 색상 적용 (시각적 효과)
                st.caption(f"타입: {p['data']['type']}")
            with c2:
                try:
                    current_idx = location_options.index(p['assigned_to'])
                except ValueError:
                    current_idx = 0
                
                new_loc = st.selectbox(
                    "작업장 선택",
                    location_options,
                    index=current_idx,
                    key=f"sel_{p['id']}",
                    label_visibility="collapsed"
                )
                
                if new_loc != p['assigned_to']:
                    p['assigned_to'] = new_loc
                    st.rerun()
            
            if p['assigned_to'] != "대기중":
                prod, status = calculate_efficiency(p['data'], p['assigned_to'])
                out_type = FACILITIES_INFO[p['assigned_to']]['output']
                color = "green" if status == "최적(2배)" else "red" if status == "불가(타입)" else "blue"
                st.markdown(f":{color}[효율: {status} (+{prod} {out_type})]")

with col2:
    st.subheader("🏭 시설 현황")
    
    total_prod_money = 0
    total_prod_tech = 0
    
    for fac in st.session_state.owned_facilities:
        fac_info = FACILITIES_INFO[fac]
        workers = [p for p in st.session_state.owned_pokemon if p['assigned_to'] == fac]
        
        fac_prod = 0
        worker_names = []
        
        for w in workers:
            prod, _ = calculate_efficiency(w['data'], fac)
            fac_prod += prod
            worker_names.append(w['data']['name'])
        
        if fac_info['output'] == 'money':
            total_prod_money += fac_prod
        else:
            total_prod_tech += fac_prod
            
        with st.expander(f"{fac} (현재 일꾼: {len(workers)}명)", expanded=True):
            st.write(f"**생산량:** +{fac_prod} {fac_info['output']}")
            st.caption(f"조건: {fac_info['boost']} 2배 / {fac_info['banned']} 금지")
            if worker_names:
                st.text(f"배치됨: {', '.join(worker_names)}")
            else:
                st.text("일꾼 없음")

    st.success(f"예상 턴 수익: 💰 +{total_prod_money} / 💡 +{total_prod_tech}")
