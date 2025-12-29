import streamlit as st
import random
import csv
import os
import time
import base64

# ==========================================
# 0. 설정 및 유틸리티
# ==========================================

st.set_page_config(layout="wide", page_title="포켓몬 농장 시뮬레이션")

# --- CSS 스타일링 & 애니메이션 ---
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
    /* 툴팁 이미지 스타일 */
    .poke-img:hover {
        transform: scale(1.15);
        transition: transform 0.2s;
        cursor: help;
    }
    /* 밤/낮 애니메이션 오버레이 */
    .night-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background-color: black;
        z-index: 999999;
        pointer-events: none;
        opacity: 0;
        transition: opacity 1.5s ease-in-out;
    }
</style>
""", unsafe_allow_html=True)

TYPE_TRANSLATION = {
    "grass": "풀", "poison": "독", "fire": "불꽃", "flying": "비행",
    "water": "물", "bug": "벌레", "normal": "노말", "electric": "전기",
    "ground": "땅", "fairy": "페어리", "fighting": "격투", "psychic": "에스퍼",
    "rock": "바위", "steel": "강철", "ice": "얼음", "ghost": "고스트",
    "dragon": "드래곤", "dark": "악"
}

# --- 밸런스 설정 (요청사항 반영) ---
# 자금 생산량 2배 적용 예정 (로직에서 처리)
# 기술 요구량은 비용의 0.75배로 자동 계산 (로직에서 처리)
FACILITIES_INFO = {
    "밭": {"cost": 0, "banned": "독", "boost": "물", "stat": "hp", "output": "money"},
    "과수원": {"cost": 100, "banned": "불꽃", "boost": "풀", "stat": "hp", "output": "money"},
    "닭장": {"cost": 300, "banned": "벌레", "boost": "비행", "stat": "hp", "output": "money"},
    "채석장": {"cost": 500, "banned": "물", "boost": "바위", "stat": "attack", "output": "money"},
    "도서관": {"cost": 800, "banned": "격투", "boost": "에스퍼", "stat": "sp_atk", "output": "tech"},
    "광산": {"cost": 1200, "banned": "드래곤", "boost": "땅", "stat": "attack", "output": "money"},
    "풍차": {"cost": 1500, "banned": "전기", "boost": "격투", "stat": "defense", "output": "money"},
    "용광로": {"cost": 2000, "banned": "강철", "boost": "불꽃", "stat": "sp_def", "output": "money"},
    "대장간": {"cost": 2500, "banned": "고스트", "boost": "강철", "stat": "attack", "output": "money"},
    "발전소": {"cost": 3000, "banned": "땅", "boost": "전기", "stat": "sp_atk", "output": "money"},
}

# [밸런스 패치] 기술 요구량 자동 계산 (자금의 0.75배)
for f_name, f_data in FACILITIES_INFO.items():
    f_data['tech_req'] = int(f_data['cost'] * 0.75)

def get_image_path(pokemon_name):
    path = f"pages/image/{pokemon_name}.png"
    if os.path.exists(path): return path
    path_lower = f"pages/image/{pokemon_name.lower()}.png"
    if os.path.exists(path_lower): return path_lower
    return None

def img_to_html(img_path, pokemon_data, width=100):
    if not img_path or not os.path.exists(img_path): return ""
    with open(img_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    tooltip_text = (f"[{pokemon_data['name']}]\n타입: {pokemon_data['type']}\n"
                    f"❤ HP: {pokemon_data['hp']}\n⚔ 공격: {pokemon_data['attack']} / 🛡 방어: {pokemon_data['defense']}\n"
                    f"🔮 특공: {pokemon_data['sp_atk']} / 🛡 특방: {pokemon_data['sp_def']}\n⚡ 스피드: {pokemon_data['speed']}")
    return f"""<img src="data:image/png;base64,{encoded}" class="poke-img" title="{tooltip_text}" style="width:{width}px; border-radius:10px; display:block; margin:auto;">"""

def run_night_animation():
    """화면 전체가 어두워졌다가 밝아지는 연출"""
    placeholder = st.empty()
    
    # 1. 밤이 됨 (검은 화면 페이드 인)
    placeholder.markdown("""
        <div style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; 
        background-color: black; z-index: 999999; opacity: 1; transition: opacity 1s;">
            <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: white; font-size: 2em;">
                🌙 밤이 깊었습니다...
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    time.sleep(2.0) # 밤 지속 시간
    
    # 2. 아침이 됨 (오버레이 제거 - 페이드 아웃 효과는 없지만 깜빡임으로 아침 표현)
    placeholder.empty()
    st.toast("☀️ 꼬끼오~ 아침이 밝았습니다!")

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
                    "hp": int(row['hp']), "attack": int(row['attack']), "defense": int(row['defense']),
                    "sp_atk": int(row['special_attack']), "sp_def": int(row['special_defense']), "speed": int(row['speed'])
                })
    except Exception as e:
        st.error(f"오류: {e}")
        return []
    return pokemon_db

POKEMON_DB = load_pokemon_data()

if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.turn = 1
    st.session_state.money = 0
    st.session_state.tech = 0
    st.session_state.pokemon_id_counter = 1
    st.session_state.owned_facilities = ["밭"]
    st.session_state.gacha_cost = 100
    st.session_state.owned_pokemon = [{"data": POKEMON_DB[0], "id": 0, "assigned_to": "대기중"}] if POKEMON_DB else []

if 'gacha_cost' not in st.session_state: st.session_state.gacha_cost = 100

def calculate_efficiency(pokemon_data, facility_name):
    if facility_name == "대기중": return 0, ""
    fac_info = FACILITIES_INFO[facility_name]
    p_type = pokemon_data['type']
    
    # 1. 타입 보너스/페널티 확인
    multiplier = 1.0
    status = "정상"
    if p_type == fac_info['banned']:
        multiplier = 0.0
        status = "불가(타입)"
    elif p_type == fac_info['boost']:
        multiplier = 2.0
        status = "최적(2배)"
    
    # 2. 생산량 계산 (밸런스 패치 적용)
    base_stat_val = pokemon_data[fac_info['stat']]
    
    if fac_info['output'] == 'money':
        # [변경] 자금 생산은 기본 2배
        production = int(base_stat_val * multiplier * 2.0)
    else:
        # [변경] 기술(Tech) 생산: 도서관 등
        if facility_name == "도서관":
            # 도서관은 sp_atk의 1.5배
            production = int(pokemon_data['sp_atk'] * multiplier * 1.5)
        else:
            # 기타 기술 시설은 sp_atk의 0.5배 (기본 규칙)
            production = int(pokemon_data['sp_atk'] * multiplier * 0.5)
            
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

# [애니메이션] 턴 종료 버튼 로직 변경
if st.button("🌙 턴 종료 (하루 마감)", type="primary", use_container_width=True):
    run_night_animation() # 화면 전체가 어두워지는 함수 호출
    m, t = process_turn()
    st.rerun()

st.divider()

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
                time.sleep(1)
                st.rerun()
            elif msg == "No Money": st.error("돈 부족!")
            elif msg == "All Collected": st.warning("도감 완성!")

    st.subheader("🏗️ 시설 건설")
    for fac, info in FACILITIES_INFO.items():
        if fac not in st.session_state.owned_facilities:
            can_build = st.session_state.money >= info['cost'] and st.session_state.tech >= info['tech_req']
            with st.expander(f"{fac} (💰{info['cost']} / 💡{info['tech_req']})"):
                st.caption(f"생산: {info['output']} | 조건: {info['boost']}↑ {info['banned']}X")
                if can_build:
                    if st.button("건설", key=f"b_{fac}"):
                        st.session_state.money -= info['cost']
                        st.session_state.owned_facilities.append(fac)
                        st.rerun()
                else:
                    if st.session_state.money < info['cost']: st.caption("❌ 자금 부족")
                    if st.session_state.tech < info['tech_req']: st.caption("❌ 기술 부족")

with col_right:
    # === 1. 평화의 공원 ===
    st.markdown('<div class="park-container"><div class="park-title">🌿 평화의 공원 (대기중)</div>', unsafe_allow_html=True)
    idle_pokemons = [p for p in st.session_state.owned_pokemon if p['assigned_to'] == "대기중"]
    if not idle_pokemons: st.caption("공원이 비어있습니다.")
    else:
        cols = st.columns(3)
        for idx, p in enumerate(idle_pokemons):
            with cols[idx % 3]:
                with st.container(border=True):
                    img_path = get_image_path(p['data']['name'])
                    if img_path:
                        st.markdown(img_to_html(img_path, p['data'], width=100), unsafe_allow_html=True)
                    else: st.caption(p['data']['name'])
                    st.markdown(f"**{p['data']['name']}**")
                    new_loc = st.selectbox("배치", ["대기중"] + st.session_state.owned_facilities, key=f"sel_{p['id']}", label_visibility="collapsed")
                    if new_loc != "대기중":
                        p['assigned_to'] = new_loc
                        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # === 2. 작업장 ===
    st.subheader("🏭 작업 현황")
    active_facilities = [f for f in st.session_state.owned_facilities if f != "대기중"]
    
    for fac in active_facilities:
        workers = [p for p in st.session_state.owned_pokemon if p['assigned_to'] == fac]
        fac_info = FACILITIES_INFO[fac]
        total_prod = sum([calculate_efficiency(w['data'], fac)[0] for w in workers])
        
        with st.expander(f"{fac} (일꾼 {len(workers)}명) ➡ +{total_prod} {fac_info['output']}", expanded=True):
            if not workers: st.caption("일꾼이 없습니다.")
            for w in workers:
                c_img, c_info, c_act = st.columns([1, 2, 1.5])
                with c_img:
                    img_path = get_image_path(w['data']['name'])
                    if img_path: st.markdown(img_to_html(img_path, w['data'], width=50), unsafe_allow_html=True)
                with c_info:
                    prod, status = calculate_efficiency(w['data'], fac)
                    color = "green" if "최적" in status else "red" if "불가" in status else "blue"
                    st.markdown(f"**{w['data']['name']}**")
                    st.markdown(f":{color}[{status} (+{prod})]")
                with c_act:
                    if st.button("휴식", key=f"rest_{w['id']}"):
                        w['assigned_to'] = "대기중"
                        st.rerun()
