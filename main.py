import streamlit as st
import random
from streamlit_sortables import sort_items

# ==========================================
# 1. 데이터 및 설정 (상수 정의)
# ==========================================

# 포켓몬 데이터베이스 (예시 데이터)
POKEMON_DB = [
    {"name": "이상해씨", "type": "풀", "hp": 45, "attack": 49, "defense": 49, "sp_atk": 65, "sp_def": 65, "speed": 45},
    {"name": "파이리", "type": "불꽃", "hp": 39, "attack": 52, "defense": 43, "sp_atk": 60, "sp_def": 50, "speed": 65},
    {"name": "꼬부기", "type": "물", "hp": 44, "attack": 48, "defense": 65, "sp_atk": 50, "sp_def": 64, "speed": 43},
    {"name": "캐터피", "type": "벌레", "hp": 45, "attack": 30, "defense": 35, "sp_atk": 20, "sp_def": 20, "speed": 45},
    {"name": "구구", "type": "비행", "hp": 40, "attack": 45, "defense": 40, "sp_atk": 35, "sp_def": 35, "speed": 56},
    {"name": "꼬마돌", "type": "바위", "hp": 40, "attack": 80, "defense": 100, "sp_atk": 30, "sp_def": 30, "speed": 20},
    {"name": "알통몬", "type": "격투", "hp": 70, "attack": 80, "defense": 50, "sp_atk": 35, "sp_def": 35, "speed": 35},
    {"name": "케이시", "type": "에스퍼", "hp": 25, "attack": 20, "defense": 15, "sp_atk": 105, "sp_def": 55, "speed": 90},
    {"name": "피카츄", "type": "전기", "hp": 35, "attack": 55, "defense": 40, "sp_atk": 50, "sp_def": 50, "speed": 90},
    {"name": "코일", "type": "강철", "hp": 25, "attack": 35, "defense": 70, "sp_atk": 95, "sp_def": 55, "speed": 45},
    {"name": "미뇽", "type": "드래곤", "hp": 41, "attack": 64, "defense": 45, "sp_atk": 50, "sp_def": 50, "speed": 50},
    {"name": "고오스", "type": "고스트", "hp": 30, "attack": 35, "defense": 30, "sp_atk": 100, "sp_def": 35, "speed": 80},
    {"name": "디그다", "type": "땅", "hp": 10, "attack": 55, "defense": 25, "sp_atk": 35, "sp_def": 45, "speed": 95},
]

# 시설 정보 정의
FACILITIES_INFO = {
    "밭": {"cost": 0, "tech_req": 0, "banned": "독", "boost": "물", "stat": "hp", "output": "money"},
    "과수원": {"cost": 100, "tech_req": 10, "banned": "불꽃", "boost": "풀", "stat": "hp", "output": "money"},
    "닭장": {"cost": 300, "tech_req": 30, "banned": "벌레", "boost": "비행", "stat": "hp", "output": "money"},
    "채석장": {"cost": 500, "tech_req": 50, "banned": "물", "boost": "바위", "stat": "attack", "output": "money"},
    "도서관": {"cost": 800, "tech_req": 80, "banned": "격투", "boost": "에스퍼", "stat": "sp_atk", "output": "tech"}, # 기술 생산
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
    st.session_state.owned_pokemon = [POKEMON_DB[0]] # 초기: 이상해씨
    st.session_state.owned_facilities = ["밭"] # 초기: 밭
    # 배치 상태 저장 (Facility Name -> List of Pokemon Names)
    st.session_state.assignments = {"대기중": ["이상해씨"], "밭": []}
    
    # 드래그 앤 드롭 위젯 상태 유지를 위한 키
    st.session_state.sortable_key = 0 

# ==========================================
# 3. 로직 함수
# ==========================================

def get_pokemon_by_name(name):
    for p in st.session_state.owned_pokemon:
        if p['name'] == name:
            return p
    return None

def calculate_efficiency(pokemon, facility_name):
    if facility_name == "대기중":
        return 0, ""
    
    fac_info = FACILITIES_INFO[facility_name]
    p_type = pokemon['type']
    
    multiplier = 1.0
    status = "정상"
    
    if p_type == fac_info['banned']:
        multiplier = 0.0
        status = "불가(타입)"
    elif p_type == fac_info['boost']:
        multiplier = 2.0
        status = "최적(2배)"
        
    base_stat = pokemon[fac_info['stat']]
    production = int(base_stat * multiplier)
    
    return production, status

def process_turn():
    total_money_gain = 0
    total_tech_gain = 0
    
    # 현재 배치 상태(assignments)를 순회하며 생산량 계산
    # assignments는 드래그 앤 드롭 결과로 업데이트됨
    for fac_name, assigned_list in st.session_state.assignments.items():
        if fac_name == "대기중":
            continue
            
        fac_info = FACILITIES_INFO.get(fac_name)
        if not fac_info: continue
        
        for p_name in assigned_list:
            pokemon = get_pokemon_by_name(p_name)
            if pokemon:
                prod, _ = calculate_efficiency(pokemon, fac_name)
                if fac_info['output'] == 'money':
                    total_money_gain += prod
                else:
                    total_tech_gain += prod

    st.session_state.money += total_money_gain
    st.session_state.tech += total_tech_gain
    st.session_state.turn += 1
    
    return total_money_gain, total_tech_gain

def gacha_pokemon():
    # 현재 없는 포켓몬 중 랜덤 하나 뽑기
    owned_names = [p['name'] for p in st.session_state.owned_pokemon]
    available = [p for p in POKEMON_DB if p['name'] not in owned_names]
    
    if available:
        new_p = random.choice(available)
        st.session_state.owned_pokemon.append(new_p)
        # 새로 얻은 포켓몬은 '대기중' 리스트에 추가
        st.session_state.assignments["대기중"].append(new_p['name'])
        st.session_state.sortable_key += 1 # 위젯 갱신 트리거
        return new_p
    return None

# ==========================================
# 4. UI 구성
# ==========================================

st.set_page_config(layout="wide", page_title="포켓몬 농장 타이쿤")

# --- 사이드바 (정보 및 가챠) ---
with st.sidebar:
    st.title(f"Turn {st.session_state.turn}")
    st.metric("💰 자금", st.session_state.money)
    st.metric("💡 기술", st.session_state.tech)
    
    st.divider()
    st.subheader("🌳 생명의 나무")
    st.caption("나무 앞 냄비에 음식을 끓이면 포켓몬이 몰려듭니다.")
    
    if st.button("🍲 요리하기 (일꾼 뽑기)"):
        new_mon = gacha_pokemon()
        if new_mon:
            st.success(f"야생의 {new_mon['name']}({new_mon['type']})가 나타났다!")
        else:
            st.warning("이 세계의 모든 포켓몬을 모았습니다!")

    st.divider()
    st.subheader("🏗️ 시설 건설")
    
    # 건설 가능한 시설 목록 표시
    for fac_name, info in FACILITIES_INFO.items():
        if fac_name in st.session_state.owned_facilities:
            continue
            
        if st.session_state.money >= info['cost'] and st.session_state.tech >= info['tech_req']:
            if st.button(f"{fac_name} 건설 ({info['cost']}원)"):
                st.session_state.money -= info['cost']
                st.session_state.owned_facilities.append(fac_name)
                # 새 시설을 배치 목록에 추가
                st.session_state.assignments[fac_name] = []
                st.session_state.sortable_key += 1
                st.rerun()
        else:
            # 조건 불만족 시 비활성화된 텍스트만 표시
            status_text = []
            if st.session_state.money < info['cost']: status_text.append(f"돈 부족({info['cost']})")
            if st.session_state.tech < info['tech_req']: status_text.append(f"기술 부족({info['tech_req']})")
            st.text(f"🔒 {fac_name}: {', '.join(status_text)}")

# --- 메인 화면 ---

st.title("포켓몬 생산 시설 관리")
st.info("포켓몬을 드래그하여 시설에 배치하세요. 배치가 끝나면 사이드바에서 턴을 넘기세요.")

# 턴 넘기기 버튼을 상단에 배치
if st.button("🌙 턴 종료 (생산 시작)", type="primary"):
    m_gain, t_gain = process_turn()
    st.toast(f"이번 턴 수익: 💰+{m_gain}, 💡+{t_gain}")
    st.rerun()

st.divider()

# --- 드래그 앤 드롭 시스템 (핵심 구현) ---

# 1. sort_items를 위한 데이터 구조 생성
# list_of_items = [ {"header": "대기중", "items": [...]}, {"header": "밭", "items": [...]}, ... ]
original_items = []

# 대기중 리스트 먼저 추가
original_items.append({
    "header": "대기중",
    "items": st.session_state.assignments.get("대기중", [])
})

# 보유한 시설 리스트 추가
for fac in st.session_state.owned_facilities:
    original_items.append({
        "header": fac,
        "items": st.session_state.assignments.get(fac, [])
    })

# 2. sort_items 위젯 렌더링
# key를 변경하면 강제로 위젯을 새로고침할 수 있음 (시설 추가/포켓몬 획득 시)
sorted_items = sort_items(original_items, multi_containers=True, key=f"sortable_{st.session_state.sortable_key}")

# 3. 드래그 앤 드롭 결과 동기화
# 사용자가 드래그를 하면 sorted_items의 구조가 바뀜 -> 이를 session_state에 반영
new_assignments = {}
for container in sorted_items:
    header = container['header']
    items = container['items']
    new_assignments[header] = items

# 상태 업데이트
st.session_state.assignments = new_assignments

# --- 배치 결과 미리보기 (효율 표시) ---
st.divider()
st.subheader("📊 현재 배치 효율 현황")

cols = st.columns(len(st.session_state.owned_facilities) + 1)

# 대기중인 포켓몬 표시
with cols[0]:
    st.markdown("**💤 대기중**")
    for p_name in st.session_state.assignments.get("대기중", []):
        p = get_pokemon_by_name(p_name)
        st.text(f"- {p_name}({p['type']})")

# 각 시설별 효율 표시
for idx, fac in enumerate(st.session_state.owned_facilities):
    with cols[idx+1]:
        info = FACILITIES_INFO[fac]
        st.markdown(f"**🏭 {fac}**")
        st.caption(f"금지:{info['banned']} / 2배:{info['boost']}")
        st.caption(f"기반능력:{info['stat']}")
        
        current_workers = st.session_state.assignments.get(fac, [])
        total_prod = 0
        
        for p_name in current_workers:
            p = get_pokemon_by_name(p_name)
            prod, status = calculate_efficiency(p, fac)
            total_prod += prod
            
            # 텍스트 색상 및 포맷팅
            if status == "불가(타입)":
                st.markdown(f":red[- {p_name}: 0 ({status})]")
            elif status == "최적(2배)":
                st.markdown(f":green[- {p_name}: {prod} ({status})]")
            else:
                st.markdown(f"- {p_name}: {prod}")
        
        st.markdown(f"**합계: +{total_prod} {info['output']}**")
