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
    
    # 2. 아침이 됨 (오
