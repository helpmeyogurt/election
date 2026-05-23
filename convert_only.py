import json
import os

# 가공하고자 하는 선거 종류 코드 (3: 시도지사, 4: 시군구청장)
ELEC_CODE = "3"

# 전국 17개 시도 매핑 가이드
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

# 자바스크립트 partyColorLocal의 value 규칙과 완벽 일치화 (최상위 식별용)
PARTY_MAP_INDEX = {
    "더불어민주당": 1, "더불어민주연합": 1, "더불어시민당": 1,
    "국민의힘": 2, "국민의미래": 2, "미래통합당": 2,
    "정의당": 3, "녹색정의당": 3,
    "조국혁신당": 4,
    "진보당": 5,
    "개혁신당": 6,
    "새로운미래": 9,
    "무소속": 9
}

def uncomma(value_str):
    if not value_str: return 0
    try: return int(str(value_str).replace(",", ""))
    except ValueError: return 0

def comma(value_int):
    return f"{value_int:,}"

def find_raw_items(data):
    if isinstance(data, list): return data
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

def add_sgg_data_processor(raw_json, city_code, city_name):
    refined_list = []
    raw_items = find_raw_items(raw_json)
    
    if not raw_items:
        return None

    for item in raw_items:
        sunsu_val = uncomma(item.get("SUNSU", "0"))
        tusu_val = uncomma(item.get("TUSU", "0"))
        tuyul_val = f"{(tusu_val / sunsu_val * 100):.1f}" if sunsu_val > 0 else "0.0"
        
        sggdata = {
            "SDID": int(item.get("SDID", city_code)),
            "SDNAME": item.get("SDNAME", city_name),
            "WIWID": int(item.get("WIWID", 0)),
            "WIWNAME": item.get("WIWNAME", "합계"),
            "SUNSU": item.get("SUNSU", "0"),
            "TUSU": item.get("TUSU", "0"),
            "TOTAL": item.get("TOTAL", "0"),
            "MUTUSU": item.get("MUTUSU", "0"),
            "GIGWON": item.get("GIGWON", "0"),
            "HUBOSU": item.get("HUBOSU", "0"),
            "TUYUL": tuyul_val,
            "name": int(item.get("WIWID", 0)), 
            "nametxt": item.get("WIWNAME", "합계"),
            "data": []
        }

        win_num, win_dugsu, win_dugyul, win_hubo, win_jd = 0, 0, 0.0, "", ""
        sec_num, sec_dugsu, sec_dugyul, sec_hubo, sec_jd = 0, 0, 0.0, "", ""

        for k in range(1, 20):
            suffix = f"{k:02d}"
            hubo_name = item.get(f"HUBO{suffix}")
            party_name = item.get(f"JD{suffix}")
            dugsu_str = item.get(f"DUGSU{suffix}")
            dugyul_str = item.get(f"DUGYUL{suffix}")

            if not hubo_name: break

            current_dugsu = uncomma(dugsu_str)
            current_dugyul = float(dugyul_str) if ... else 0.0

            if k == 1:
                win_num, win_dugsu, win_dugyul, win_hubo, win_jd = k, current_dugsu, current_dugyul, hubo_name, party_name
                sec_dugsu = 0
            elif current_dugsu > win_dugsu:
                sec_num, sec_dugsu, sec_dugyul, sec_hubo, sec_jd = win_num, win_dugsu, win_dugyul, win_hubo, win_jd
                win_num, win_dugsu, win_dugyul, win_hubo, win_jd = k, current_dugsu, current_dugyul, hubo_name, party_name
            elif current_dugsu > sec_dugsu:
                sec_num, sec_dugsu, sec_dugyul, sec_hubo, sec_jd = k, current_dugsu, current_dugyul, hubo_name, party_name

            # 정당 사전에서 육안으로 색상 코드 추출
            party_color = PARTY_MAP_INDEX.get(party_name, 9) # 기본 인덱스 보증안
            # 실제 정당 컬러 매핑 딕셔너리 연동 (예: 민주당=#152484 등)
            # 기존 코드 상단에 정의된 PARTY_COLORS 딕셔너리를 직접 읽어옵니다.
            actual_color = PARTY_COLORS.get(party_name, "#8b8b8b")

            # 🚨 [심각한 문제 해결 구간]
            # 1. 'value' 위치에 백분율(득표율 숫자형)을 대입합니다.
            # 2. 기존의 수치(표)는 'pyo'라는 키로 변경하여 저장합니다.
            # 3. 요구사항에 따라 'percentage' 항목은 제거했습니다.
            sggdata["data"].append({
                "value": current_dugyul,
                "name": hubo_name,
                "party": party_name,
                "pyo": current_dugsu,
                "itemStyle": {"color": actual_color}
            })

        sggdata["WINNUM"] = win_num
        sggdata["WINDUGSU"] = comma(win_dugsu)
        sggdata["WINDUGYUL"] = f"{win_dugyul:.2f}"
        sggdata["WINHUBO"] = win_hubo
        sggdata["WINJD"] = win_jd

        sggdata["SECNUM"] = sec_num
        sggdata["SECDUGSU"] = comma(sec_dugsu)
        sggdata["SECDUGYUL"] = f"{sec_dugyul:.2f}"
        sggdata["SECHUBO"] = sec_hubo
        sggdata["SECJD"] = sec_jd

        # 💡 참고: 최상위의 sggdata["value"] 값은 지도 조각의 '소속 정당 색상 테두리'를 결정하므로 
        # 이전 자바스크립트 규칙(민주당=1, 국힘=2 등)을 그대로 안정적으로 유지 보전합니다.
        if win_dugsu == sec_dugsu:
            sggdata["value"] = 9  
            sggdata["DUGYULCHA"] = "0.00"
        else:
            sggdata["value"] = PARTY_MAP_INDEX.get(win_jd, 9)
            sggdata["DUGYULCHA"] = f"{(win_dugyul - sec_dugyul):.2f}"

        sggdata["DUGSUCHA"] = comma(win_dugsu - sec_dugsu)

        for m in range(1, 20):
            suf = f"{m:02d}"
            if item.get(f"HUBO{suf}"):
                sggdata[f"HUBO{suf}"] = item.get(f"HUBO{suf}")
                sggdata[f"JD{suf}"] = item.get(f"JD{suf}")
                sggdata[f"DUGSU{suf}"] = item.get(f"DUGSU{suf}")
                sggdata[f"DUGYUL{suf}"] = item.get(f"DUGYUL{suf}")

        refined_list.append(sggdata)

    return {city_name: refined_list}

def main():
    target_dir = os.path.join("data", "jibang", "8")
    if not os.path.exists(target_dir): return

    print(f"🔄 선거코드 [{ELEC_CODE}] 기준 새 스펙 데이터 가공을 시작합니다.")

    for city in CITIES:
        code_str = str(city["CODE"])
        name_str = city["NAME"]
        
        ori_file_path = os.path.join(target_dir, f"ori_{ELEC_CODE}_{code_str}.json")
        refined_file_path = os.path.join(target_dir, f"{ELEC_CODE}_{code_str}.json")

        if os.path.exists(ori_file_path):
            try:
                with open(ori_file_path, "r", encoding="utf-8") as f:
                    raw_json = json.load(f)

                refined_json = add_sgg_data_processor(raw_json, code_str, name_str)
                if refined_json is not None:
                    with open(refined_file_path, "w", encoding="utf-8") as f:
                        json.dump(refined_json, f, ensure_ascii=False, indent=4)
                    print(f"🟢 [{name_str}] 새 규격 변환 성공 -> {ELEC_CODE}_{code_str}.json")
            except Exception as e:
                print(f"🔴 [{name_str}] 가공 오류: {e}")

    print("✨ 데이터 세부 스펙 변경 가공 작업이 성공적으로 끝났습니다.")

if __name__ == "__main__":
    main()
