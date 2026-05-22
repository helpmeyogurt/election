import json
import os

# 시도 정보 테이블
CITIES = [
    {"CODE": 1100, "NAME": "서울특별시"},
    {"CODE": 2600, "NAME": "부산광역시"},
    {"CODE": 2700, "NAME": "대구광역시"},
    {"CODE": 2800, "NAME": "인천광역시"},
    {"CODE": 2900, "NAME": "광주광역시"},
    {"CODE": 3000, "NAME": "대전광역시"},
    {"CODE": 3100, "NAME": "울산광역시"},
    {"CODE": 5100, "NAME": "세종특별자치시"},
    {"CODE": 4100, "NAME": "경기도"},
    {"CODE": 4200, "NAME": "강원도"},
    {"CODE": 4300, "NAME": "충청북도"},
    {"CODE": 4400, "NAME": "충청남도"},
    {"CODE": 4500, "NAME": "전라북도"},
    {"CODE": 4600, "NAME": "전라남도"},
    {"CODE": 4700, "NAME": "경상북도"},
    {"CODE": 4800, "NAME": "경상남도"},
    {"CODE": 4900, "NAME": "제주특별자치도"},
]

# 정당 색상 사전
PARTY_COLORS = {
    "더불어민주당": "#152484", "국민의힘": "#E61E2B", "더불어민주연합": "#152484", "국민의미래": "#E61E2B",
    "녹색정의당": "#007C36", "새로운미래": "#46bbbd", "개혁신당": "#FF7920", "진보당": "#D6001C",
    "자유통일당": "#E24A49", "조국혁신당": "#004099", "기본소득당": "#00D2C3", "무소속": "#8b8b8b",
    "국민의당": "#EA5504", "미래통합당": "#EF426F", "미래한국당": "#EF426F", "더불어시민당": "#006CB7",
    "정의당": "#ffca05", "열린민주당": "#003E98", "소나무당": "#1A246B", "우리공화당": "#009944",
    "한국국민당": "#013588", "새진보연합": "#00d2c3", "없음": "#8b8b8b"
}

def get_party_color(party_name):
    cleaned_name = party_name.strip() if party_name else ""
    return PARTY_COLORS.get(cleaned_name, "#8b8b8b")

def find_raw_items(data):
    """원본 JSON 데이터에서 실제 선거 결과 리스트가 들어있는 위치를 유연하게 탐색합니다."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ["data", "jsonResult", "result", "list"]:
            if key in data:
                res = find_raw_items(data[key])
                if res: return res
        for key, value in data.items():
            if isinstance(value, list) and len(value) > 0:
                if isinstance(value[0], dict) and any(k in value[0] for k in ["HUBO01", "WIWNAME", "SDNAME"]):
                    return value
            elif isinstance(value, dict):
                res = find_raw_items(value)
                if res: return res
    return []

def parse_raw_data(raw_json, city_code, city_name):
    """로컬 원본 데이터를 정제 포맷으로 가공합니다."""
    refined_list = []
    raw_items = find_raw_items(raw_json)
    
    if not raw_items:
        return None

    for item in raw_items:
        refined_item = {
            "SDID": int(city_code),
            "SDNAME": item.get("SDNAME", city_name),
            "WIWID": int(item.get("WIWID", 0)),
            "WIWNAME": item.get("WIWNAME", "합계"),
            "SUNSU": item.get("SUNSU", "0"),
            "TUSU": item.get("TUSU", "0"),
            "TOTAL": item.get("TOTAL", "0"),
            "MUTUSU": item.get("MUTUSU", "0"),
            "GIGWON": item.get("GIGWON", "0"),
            "HUBOSU": item.get("HUBOSU", "0"),
            "data": [],
        }

        hubo_count = 0
        for i in range(1, 16):
            suffix = f"{i:02d}"
            hubo_name = item.get(f"HUBO{suffix}") or item.get(f"hubo{suffix}")
            party_name = item.get(f"JD{suffix}") or item.get(f"jd{suffix}")
            dugsu_str = item.get(f"DUGSU{suffix}") or item.get(f"dugsu{suffix}")
            dugyul = item.get(f"DUGYUL{suffix}") or item.get(f"dugyul{suffix}")

            if not hubo_name:
                break
                
            hubo_count += 1

            try:
                val = int(str(dugsu_str).replace(",", ""))
            except (ValueError, AttributeError):
                val = 0

            refined_item["data"].append({
                "value": val,
                "name": hubo_name,
                "itemStyle": {"color": get_party_color(party_name)},
            })

            refined_item[f"HUBO{suffix}"] = hubo_name
            refined_item[f"JD{suffix}"] = party_name
            refined_item[f"DUGSU{suffix}"] = dugsu_str
            refined_item[f"DUGYUL{suffix}"] = dugyul

        refined_item["HUBOSU"] = str(hubo_count)
        refined_list.append(refined_item)

    return {city_name: refined_list}

def main():
    target_dir = os.path.join("data", "jibang", "8")
    
    if not os.path.exists(target_dir):
        print(f"❌ '{target_dir}' 폴더를 찾을 수 없습니다. 원본 파일이 있는지 확인해 주세요.")
        return

    print("🔄 로컬 저장된 원본 파일을 기반으로 '데이터 변환 작업'만 시작합니다.")

    for city in CITIES:
        code_str = str(city["CODE"])
        name_str = city["NAME"]
        
        ori_file_path = os.path.join(target_dir, f"ori_{code_str}.json")
        refined_file_path = os.path.join(target_dir, f"{code_str}.json")

        # 기존 로컬에 받아둔 원본 파일이 존재하는지 체크
        if os.path.exists(ori_file_path):
            try:
                with open(ori_file_path, "r", encoding="utf-8") as f:
                    raw_json = json.load(f)

                refined_json = parse_raw_data(raw_json, code_str, name_str)
                
                if refined_json is not None:
                    with open(refined_file_path, "w", encoding="utf-8") as f:
                        json.dump(refined_json, f, ensure_ascii=False, indent=4)
                    print(f"🟢 [{name_str}] 변환 성공 -> {code_str}.json 완료")
                else:
                    print(f"⚠️ [{name_str}] 원본 파일 내부에서 선거 데이터 리스트 위치를 찾지 못했습니다.")

            except Exception as e:
                print(f"🔴 [{name_str}] 변환 중 에러 발생: {e}")
        else:
            print(f"⚪ [{name_str}] 원본 파일({f'ori_{code_str}.json'})이 폴더에 없어 패스합니다.")

    print("✨ 모든 파일 변환 프로세스가 끝났습니다.")

if __name__ == "__main__":
    main()
