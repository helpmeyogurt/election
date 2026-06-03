import os
import json

# 1. 정당 컬러 및 인덱스 매핑
PARTY_COLORS = {
    "더불어민주당": "#152484", "국민의힘": "#E61E2B", "더불어민주연합": "#152484", "국민의미래": "#E61E2B",
    "녹색정의당": "#007C36", "새로운미래": "#46bbbd", "개혁신당": "#FF7920", "진보당": "#D6001C",
    "자유통일당": "#E24A49", "조국혁신당": "#004099", "기본소득당": "#00D2C3", "무소속": "#8b8b8b",
    "국민의당": "#EA5504", "미래통합당": "#EF426F", "미래한국당": "#EF426F", "더불어시민당": "#006CB7",
    "정의당": "#ffca05", "열린민주당": "#003E98", "소나무당": "#1A246B", "우리공화당": "#009944",
    "한국국민당": "#013588", "새진보연합": "#00d2c3", "없음": "#8b8b8b"
}

PARTY_MAP_INDEX = {
    "더불어민주당": 1, "더불어민주연합": 1, "더불어시민당": 1,
    "국민의힘": 2, "국민의미래": 2, "미래통합당": 2,
    "정의당": 3, "녹색정의당": 3, "조국혁신당": 4, "진보당": 5, "개혁신당": 6,
    "새로운미래": 9, "무소속": 9
}

# 2. 지정된 경로 및 파일 코드 설정
BASE_DIR = "data/jibang/9"
sido_codes = [1100, 2600, 2700, 2800, 2900, 3000, 3100, 4100, 5200, 4300, 4400, 5300, 4600, 4700, 4800]

OUTPUT_FILE = os.path.join(BASE_DIR, "4_0000.json")

# 전국 통계 집계용 변수
total_sunsu = 0
total_tusu = 0
national_party_wins = {}

# 최종 시군구 결과 리스트
result_list = []

# 3. 지정된 sido_codes 리스트 순회하며 파일 읽기
for code in sido_codes:
    file_name = f"4_{code}.json"
    file_path = os.path.join(BASE_DIR, file_name)
    
    if not os.path.exists(file_path):
        print(f"경고: 파일을 찾을 수 없습니다. 건너뜁니다 -> {file_path}")
        continue
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        # 최상위 지역명 키(예: "서울특별시") 내부의 리스트 가져오기
        if not raw_data:
            continue
        items = list(raw_data.values())[0]
        
        for sgg_data in items:
            # '합계' 데이터는 개별 구 데이터가 아니므로 스킵 (전국 통계 오염 방지)
            if sgg_data.get('SGGNAME') == '합계' or sgg_data.get('WIWNAME') == '합계':
                continue
                
            sgg_code = int(sgg_data.get('name') or sgg_data.get('WIWID') or sgg_data.get('SGG_CODE', 0))
            sgg_name = sgg_data.get('nametxt') or sgg_data.get('WIWNAME') or sgg_data.get('SGG_NAME', '')
            sd_name = sgg_data.get('SDNAME') or sgg_data.get('SD_NAME', '')
            
            # 선거인수, 투표수 정수 변환 (콤마 제거)
            sunsu = int(str(sgg_data.get('SUNSU', '0')).replace(',', ''))
            tusu = int(str(sgg_data.get('TUSU', '0')).replace(',', ''))
            total_sunsu += sunsu
            total_tusu += tusu
            
            # 데이터 구조 내 제공된 당선 정당(WINJD) 우선 사용, 없으면 직접 계산
            winner_party = sgg_data.get('WINJD')
            
            if not winner_party:
                winner_party = "무소속"
                max_pyo = -1
                party_data_list = sgg_data.get('data', [])
                if isinstance(party_data_list, list):
                    for p in party_data_list:
                        vote_count = p.get('pyo', 0) # 득표수(pyo) 기준으로 변경
                        if isinstance(vote_count, str):
                            vote_count = int(vote_count.replace(',', ''))
                        if vote_count > max_pyo:
                            max_pyo = vote_count
                            winner_party = p.get('party') or p.get('name', '무소속')
            
            # 정당 인덱스 가져오기 (매핑에 없으면 9번 무소속)
            party_value = PARTY_MAP_INDEX.get(winner_party, 9)
            
            # 전국 통계용 승리 횟수 카운팅
            national_party_wins[winner_party] = national_party_wins.get(winner_party, 0) + 1
            
            # 데이터 구조화
            result_list.append({
                "name": sgg_code,
                "value": party_value,
                "nametxt": sgg_name,
                "SDNAME": sd_name
            })
            
    except Exception as e:
        print(f"{file_name} 처리 중 에러 발생: {e}")

# 4. 전국 합계 데이터 오브젝트 생성
national_data = []
for party_name, color in PARTY_COLORS.items():
    win_count = national_party_wins.get(party_name, 0)
    # 단 한 번이라도 이긴 정당만 통계 리스트에 추가하고 싶다면 아래 주석을 해제하세요.
    # if win_count == 0: continue 
    national_data.append({
        "name": party_name,
        "value": win_count,
        "itemStyle": {
            "color": color
        }
    })

tuyul = round((total_tusu / total_sunsu) * 100, 1) if total_sunsu > 0 else 0.0

national_summary = {
    "name": 0,
    "nametxt": "전국 합계",
    "SUNSU": f"{total_sunsu:,}",
    "TUSU": f"{total_tusu:,}",
    "TUYUL": str(tuyul),
    "data": national_data
}

# 5. 최종 딕셔너리 구조 결합
final_result = {
    "전국": [national_summary] + result_list
}

# 6. 지정된 경로에 4_0000.json으로 저장
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(final_result, f, ensure_ascii=False, indent=4)

print(f"🎯 병합 완료! 결과 파일이 다음 경로에 저장되었습니다: {OUTPUT_FILE}")
