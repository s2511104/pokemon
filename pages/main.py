# [1] 포켓몬 배치 (체크박스/라디오 스타일) - 이미지 추가 버전
    st.subheader("📋 일꾼 작업 지시")
    st.info("각 포켓몬 카드의 옵션을 선택(체크)하여 배치하세요.")
    
    available_locations = ["대기중"] + st.session_state.owned_facilities
    
    for p in st.session_state.owned_pokemon:
        with st.container(border=True):
            # 컬럼 비율 조정 (이미지 공간 확보를 위해 c1을 조금 더 넓힘)
            c1, c2 = st.columns([1.5, 2.5]) 
            
            with c1:
                # 🖼️ [이미지 추가 로직]
                # 파일 경로: pages/image/이름.png
                img_path = f"pages/image/{p['data']['name']}.png"
                
                # 파일이 실제로 있는지 확인 후 출력 (에러 방지)
                if os.path.exists(img_path):
                    st.image(img_path, width=100) # 너비 100px로 조절
                else:
                    # 이미지가 없으면 텍스트로 대체하거나 비워둠
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
                new_loc = st.radio(
                    f"{p['data']['name']}의 작업장:",
                    available_locations,
                    key=f"radio_{p['id']}",
                    index=available_locations.index(p['assigned_to']),
                    horizontal=True
                )
                
                if new_loc != p['assigned_to']:
                    p['assigned_to'] = new_loc
                    st.rerun()
