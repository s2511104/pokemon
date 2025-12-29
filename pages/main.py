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
    /* 밤/낮 애니메이션용 스타일 */
    .overlay-text {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        color: white;
        font-size: 3em;
        text-align: center;
        font-weight: bold;
        text-shadow: 2px 2px 4px #000000;
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

# --- 밸런스 설정 ---
# output 키는 이제 참고용이며, 실제 로직은 calculate_efficiency에서 처리함
FACILITIES_INFO = {
    "밭": {"cost": 0, "banned": "독", "boost": "물", "stat": "hp"},
    "과수원": {"cost": 100, "banned": "불꽃", "boost": "풀", "stat": "hp"},
    "닭장": {"cost": 300, "banned": "벌레", "boost": "비행", "stat": "hp"},
    "채석장": {"cost": 500, "banned": "물", "boost": "바위", "stat": "attack"},
    "도서관": {"cost": 800, "banned": "격투", "boost": "에스퍼", "stat": "sp_atk"}, 
    "광산": {"cost": 1200, "banned": "드래곤", "boost": "땅", "stat": "attack"},
    "풍차": {"cost": 1500, "banned": "전기", "boost": "격투", "stat": "defense"},
    "용광로": {"cost": 2000, "banned": "강철", "boost": "불꽃", "stat": "sp_def"},
    "대장간": {"cost": 2500, "banned": "고스트", "boost": "강철", "stat": "attack"},
    "발전소": {"cost": 3000, "banned": "땅", "boost": "전기", "stat": "sp_atk"},
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
    """밤 -> 새벽 -> 아침으로 이어지는 애니메이션"""
    placeholder = st.empty()
    
    # 1. 밤 (Black Background)
    placeholder.markdown("""
        <div style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; 
        background-color: black; z-index: 999999; display: flex; align-items: center; justify-content: center;">
            <div class="overlay-text">
                🌙<br>밤이 깊었습니다...
            </div>
        </div>
    """, unsafe_allow_html=True)
    time.sleep(1.5)
    
    # 2. 새벽 (Dark Grey Background)
    placeholder.markdown("""
        <div style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; 
        background-color: #2c3e50; z-index: 999999; display: flex; align-items: center; justify-content: center;">
            <div class="overlay-text" style="color: #f1c40f;">
                🐔<br>꼬끼오!!<br><span style="font-size:0.5em">아침이 밝아옵니다.</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    time.sleep(1.5)
    
    # 3. 아침 (Clear)
    placeholder.empty()
    st.toast("☀️ 상쾌한 아침입니다! 자원 생산이 완료되었습니다.")

# ==========================================
# 1. 데이터 로드 및 로직
# ==========================================

def load_pokemon_data(filename="pages/pokemonnnn.csv"):
    pokemon_db = []
    # 파일 경로 체크
    target_file = filename
    if not os.path.exists(target_file):
        if os.path.exists("pokemonnnn.csv"): target_file = "pokemonnnn.csv"
        else: return []
        
    try:
        with open(target_file, newline='', encoding='utf-8') as csvfile:
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
    """
    수정된 생산 로직:
    1. 모든 시설: 기본적으로 Tech 점수 = Special Attack 만큼 생산
    2. 도서관: Money = 0, Tech = Special Attack * 2 (에스퍼는 5배)
    3. 일반 시설: Money = Stat * 2 * 상성배수
    """
    if facility_name == "대기중": return 0, 0, ""
    
    fac_info = FACILITIES_INFO[facility_name]
    p_type = pokemon_data['type']
    sp_atk = pokemon_data['sp_atk']
    
    # --- 1. 상성(Type Match) 체크 (돈 생산에 영향) ---
    multiplier = 1.0
    status = "정상"
    if p_type == fac_info['banned']:
        multiplier = 0.0
        status = "불가(타입)"
    elif p_type == fac_info['boost']:
        multiplier = 2.0
        status = "최적(2배)"
        
    money_prod = 0
    tech_prod = 0
    
    # --- 2. 시설별 로직 적용 ---
    if facility_name == "도서관":
        # 도서관 특수 규칙: 돈 0, 기술점수 증폭
        money_prod = 0
        if p_type == "에스퍼":
            tech_prod = int(sp_atk * 5)
            status = "초능력(5배)"
        else:
            tech_prod = int(sp_atk * 2)
            if status == "정상": status = "학구열(2배)"
    else:
        # 일반 시설 규칙
        # 돈: 해당 스탯 * 상성 * 2
        base_stat_val = pokemon_data[fac_info['stat']]
        money_prod = int(base_stat_val * multiplier * 2.0)
        
        # 기술: 특수공격력만큼 (상성 무관, 단순 지능 수치 반영)
        tech_prod = sp_atk

    return money_prod, tech_prod, status

def process_turn():
    m_gain_total, t_gain_total = 0, 0
    
    for p in st.session_state.owned_pokemon:
        fac = p['assigned_to']
        if fac != "대기중":
            m_prod, t_prod, _ = calculate_efficiency(p['data'], fac)
            m_gain_total += m_prod
            t_gain_total += t_prod
            
    st.session_state.money += m_gain_total
    st.session_state.tech += t_gain_total
    st.session_state.turn += 1
    return m_gain_total, t_gain_total

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

# [애니메이션 적용] 턴 종료 버튼
if st.button("🌙 턴 종료 (하루 마감)", type="primary", use_container_width=True):
    run_night_animation() 
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
                # 도서관은 설명 별도 처리
                if fac == "도서관":
                    st.caption(f"특수: 돈생산X, 기술점수 대폭 상승 (에스퍼 유리)")
                else:
                    st.caption(f"조건: {info['boost']}↑ {info['banned']}X")
                
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
        
        # 합계 계산
        total_m = 0
        total_t = 0
        for w in workers:
            m, t, _ = calculate_efficiency(w['data'], fac)
            total_m += m
            total_t += t
            
        with st.expander(f"{fac} (일꾼 {len(workers)}명) ➡ 💰+{total_m} / 💡+{total_t}", expanded=True):
            if not workers: st.caption("일꾼이 없습니다.")
            for w in workers:
                c_img, c_info, c_act = st.columns([1, 2, 1.5])
                with c_img:
                    img_path = get_image_path(w['data']['name'])
                    if img_path: st.markdown(img_to_html(img_path, w['data'], width=50), unsafe_allow_html=True)
                with c_info:
                    m_prod, t_prod, status = calculate_efficiency(w['data'], fac)
                    color = "green" if "최적" in status or "5배" in status else "red" if "불가" in status else "blue"
                    st.markdown(f"**{w['data']['name']}**")
                    # 돈과 기술점수 생산량 병기
                    st.markdown(f":{color}[{status} (💰{m_prod}, 💡{t_prod})]")
                with c_act:
                    if st.button("휴식", key=f"rest_{w['id']}"):
                        w['assigned_to'] = "대기중"
                        st.rerun()
