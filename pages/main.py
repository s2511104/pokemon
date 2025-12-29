def calculate_production(facility_type, char_type, special_attack):
    """
    생산 시설과 캐릭터 타입에 따른 자원 생산량을 계산하는 함수
    
    Args:
        facility_type (str): 시설 종류 (예: "Library", "Factory")
        char_type (str): 캐릭터/유닛 타입 (예: "Esper", "Human")
        special_attack (int): 캐릭터의 특수 공격력 (special_attack)
        
    Returns:
        dict: 생산된 자원 {'money': int, 'tech_points': int}
    """
    
    # 기본 생산량 초기화
    production = {
        'money': 0,        # 돈
        'tech_points': 0   # 기술점수
    }

    # 1. 도서관(Library)인 경우의 로직
    if facility_type == "Library":
        production['money'] = 0  # 도서관은 돈을 생산하지 않음
        
        # 에스퍼(Esper) 타입 확인
        if char_type == "Esper":
            # 에스퍼 타입은 특수공격력의 5배
            production['tech_points'] = special_attack * 5
        else:
            # 그 외 타입은 특수공격력의 2배
            production['tech_points'] = special_attack * 2

    # 2. 그 외 모든 일반 생산 시설
    else:
        # 일반 시설의 기술점수는 특수공격력과 동일 (1배)
        production['tech_points'] = special_attack
        
        # (참고) 일반 시설의 돈 생산 로직은 기존 규칙을 따름
        # production['money'] = calculate_normal_money(...) 

    return production
