import os
import json

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

def uncomma(value_str):
    if not value_str: return 0
    try: return int(str(value_str).replace(",", ""))
    except ValueError: return 0

def comma(value_int):
    return f"{value_int:,}"

def generate_national_summary(input_dir, output_filepath):
    # 1100(서울)부터 5300(제주)까지의 시도 코드 매핑 정보 (예시 포맷 기준 데이터 보완용)
    city_meta = {
        1100: {"nametxt": "서울", "center": [126.735, 37.9802], "radius": 38},
        2600: {"nametxt": "부산", "center": [128.9251, 35.139], "radius": 12},
        # ... 필요에 따라 나머지 시도 메타데이터 추가 가능
    }
    national_list = []
    
    # 전체 합산을 위한 변수
    total_sunsu_sum = 0
    total_tusu_sum = 0
    national_win_party_counter = {}

    # 정제된 파일 목록 순회 (3_1100.json ~ 3_5300.json)
    city_codes = [1100, 2600, 2700, 2800, 2900, 3000, 3100, 5100, 4100, 5200, 4300, 4400, 5300, 4700, 4800, 4900]
    
    for code in city_codes:
        filename = f"3_{code}.json"
        filepath = os.path.join(input_dir, filename)
        
        if not os.path.exists(filepath):
            continue
            
        with open(filepath, "r", encoding="utf-8") as f:
            city_data = json.load(f)
            
        # 각 파일은 { "서울특별시": [ ... ] } 형태로 저장되어 있으므로 첫 번째 값을 가져옴
        city_name = list(city_data.keys())[0]
        nodes = city_data[city_name]
        
        if not nodes:
            continue
            
        # 🟢 규칙: 정제된 파일의 맨 위(0번 인덱스)는 항상 해당 시도의 '합계' 노드임
        summary_node = nodes[0]
        
        # 전국 단위 합산을 위해 콤마 제거 후 누적
        sunsu_val = uncomma(summary_node.get("SUNSU", "0"))
        tusu_val = uncomma(summary_node.get("TUSU", "0"))
        total_sunsu_sum += sunsu_val
        total_tusu_sum += tusu_val
        
        # 당선 정당 집계 (WINJD 기준)
        win_party = summary_node.get("WINJD")
        if win_party:
            national_win_party_counter[win_party] = national_win_party_counter.get(win_party, 0) + 1
            
        # 형식 요구사항에 맞게 노드 데이터 정제/변형
        meta = city_meta.get(code, {})
        
        refined_node = {
            "name": int(str(code)[:2]),  # '1100' -> 11
            "WIWNAME": int(str(code)[:2]),  # '1100' -> 11
            "WIWID": int(str(code)[:2]),  # '1100' -> 11
            "value": summary_node.get("value", 0),
            "nametxt": meta.get("nametxt", city_name[:2]), # '서울특별시' -> '서울'
            "SUNSU": summary_node.get("SUNSU", "0"),
            "TUSU": summary_node.get("TUSU", "0"),
            "TOTAL": summary_node.get("TOTAL", summary_node.get("TUSU", "0")), 
            "MUTUSU": summary_node.get("MUTUSU", "0"),
            "GIGWON": summary_node.get("GIGWON", "0"),
            "HUBOSU": str(len(summary_node.get("data", []))),
            "TUYUL": summary_node.get("TUYUL", "0.0"),
            "SDNAME": city_name,
            "WINHUBO": summary_node.get("WINHUBO", ""),
            "DUGYULCHA": summary_node.get("DUGYULCHA", "0.00"),
            "center": meta.get("center", [127.0, 37.0]),
            "radius": meta.get("radius", 20),
            "data": summary_node.get("data", [])
        }
        
        for key, val in summary_node.items():
            if key not in refined_node and key != "data":
                refined_node[key] = val
                
        national_list.append(refined_node)

    # 🟢 0번 인덱스에 들어갈 "전국 합계" 노드 생성
    national_pie_data = []
    for party, count in national_win_party_counter.items():
        national_pie_data.append({
            "name": party,
            "value": count,
            "itemStyle": {"color": PARTY_COLORS.get(party, "#8b8b8b")}
        })
    
    custom_order = ["더불어민주당", "국민의힘", "정의당", "진보당", "무소속"]
    national_pie_data.sort(key=lambda x: custom_order.index(x["name"]) if x["name"] in custom_order else 999)

    national_tuyul = f"{(total_tusu_sum / total_sunsu_sum * 100):.1f}" if total_sunsu_sum > 0 else "0.0"

    total_summary_node = {
        "name": 0,
        "nametxt": "전국 합계",
        "SUNSU": comma(total_sunsu_sum),
        "TUSU": comma(total_tusu_sum),
        "TUYUL": national_tuyul,
        "data": national_pie_data
    }
    
    national_list.insert(0, total_summary_node)
    
    final_output = {
        "전국": national_list
    }
    
    with open(output_filepath, "w", encoding="utf-8") as f:
        json.dump(final_output, f, ensure_ascii=False, indent=4)
        
    print(f"✅ 전국 요약 파일 생성 완료: {output_filepath}")


# 🚨 여기에 넣으시면 됩니다! (파일의 가장 최하단)
if __name__ == "__main__":
    # 데이터가 저장되어 있는 실제 target 디렉토리
    target_dir = "data/jibang/9"
    
    # 저장할 결과 파일 전체 경로 (3_0000.json)
    output_file_path = os.path.join(target_dir, "3_0000.json")
    
    # 전국 요약 함수 호출
    generate_national_summary(target_dir, output_file_path)
