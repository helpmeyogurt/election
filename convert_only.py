import json
import os

# 가공하고자 하는 선거 종류 코드 (3: 시도지사, 4: 시군구청장)
ELEC_CODE = "4"

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

    # 정당별 당선자 카운터
    win_party_counter = {}

    for item in raw_items:
        sunsu_val = uncomma(item.get("SUNSU", "0"))
        tusu_val = uncomma(item.get("TUSU", "0"))
        tuyul_val = f"{(tusu_val / sunsu_val * 100):.1f}" if sunsu_val > 0 else "0.0"
        
        wiw_id_raw = item.get("WIWID", "0")
        wiw_name_raw = item.get("WIWNAME", "합계")

        # 🚨 [수정 반영] 유형 4의 원본 값을 신뢰하여 변조 없이 그대로 추출
        sgg_id_val = str(item.get("SGGID", wiw_id_raw))
        sgg_name_val = item.get("SGGNAME", wiw_name_raw)

        sggdata = {
            "SDID": int(item.get("SDID", city_code)),
            "SDNAME": item.get("SDNAME", city_name),
            "SGGID": sgg_id_val,          # 원본 SGGID 그대로 바인딩
            "SGGNAME": sgg_name_val,      # 원본 SGGNAME 그대로 바인딩
            "WIWID": int(wiw_id_raw),
            "WIWNAME": wiw_name_raw,
            "SUNSU": item.get("SUNSU", "0"),
            "TUSU": item.get("TUSU", "0"),
            "TOTAL": item.get("TOTAL", "0"),
            "MUTUSU": item.get("MUTUSU", "0"),
            "GIGWON": item.get("GIGWON", "0"),
            "HUBOSU": item.get("HUBOSU", "0"),
            "TUYUL": tuyul_val,
            "name": int(wiw_id_raw), 
            "nametxt": wiw_name_raw,
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
            current_dugyul = float(dugyul_str) if dugyul_str else 0.0

            if k == 1:
                win_num, win_dugsu, win_dugyul, win_hubo, win_jd = k, current_dugsu, current_dugyul, hubo_name, party_name
                sec_dugsu = 0
            elif current_dugsu > win_dugsu:
                sec_num, sec_dugsu, sec_dugyul, sec_hubo, sec_jd = win_num, win_dugsu, win_dugyul, win_hubo, win_jd
                win_num, win_dugsu, win_dugyul, win_hubo, win_jd = k, current_dugsu, current_dugyul, hubo_name, party_name
            elif current_dugsu > sec_dugsu:
                sec_num, sec_dugsu, sec_dugyul, sec_hubo, sec_jd = k, current_dugsu, current_dugyul, hubo_name, party_name

            cleaned_party = party_name.strip() if party_name else "없음"
            actual_color = PARTY_COLORS.get(cleaned_party, "#8b8b8b")

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

        # WIWNAME이 "합계"이고 실제 지역구(WIWID != 0)인 당선 정당 집계
        if ELEC_CODE == "4" and wiw_name_raw == "합계" and int(wiw_id_raw) != 0:
            if win_jd and win_dugsu > sec_dugsu:
                win_party_counter[win_jd] = win_party_counter.get(win_jd, 0) + 1

        refined_list.append(sggdata)

    # 🚨 [수정 반영] 기존 시군구 항목을 건드리지 않고, 맨 앞에 독립적인 빈 배열/오브젝트를 생성하여 삽입
    if ELEC_CODE == "4":
        summary_pie_data = []
        for party, count in win_party_counter.items():
            summary_pie_data.append({
                "name": party,
                "value": count,
                "itemStyle": {"color": PARTY_COLORS.get(party, "#8b8b8b")}
            })
        summary_pie_data.sort(key=lambda x: x["value"], reverse=True)

        # 0번 인덱스 전용 빈 요약 껍데기 오브젝트 생성
        summary_node = {
            "SDID": int(city_code),
            "SDNAME": city_name,
            "SGGID": "0",
            "SGGNAME": "합계",
            "WIWID": 0,
            "WIWNAME": "합계",
            "data": summary_pie_data  # 👈 하위 data 항목에 순수하게 정당 당선자 수만 정리
        }

        # refined_list의 가장 맨 앞([0])에 새롭게 만든 요약 노드를 인서트합니다.
        refined_list.insert(0, summary_node)

    return {city_name: refined_list}

def main():
    target_dir = os.path.join("data", "jibang", "8")
    if not os.path.exists(target_dir): return

    print(f"🔄 선거코드 [{ELEC_CODE}] 기준 새 스펙 전체 변환을 시작합니다.")

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
                    print(f"🟢 [{name_str}] 맨 앞 독립 요약 노드 인서트 및 순수 추출 변환 성공")
            except Exception as e:
                print(f"🔴 [{name_str}] 가공 오류: {e}")

    print("✨ 요약 통계 분리 가공 작업이 완벽하게 완료되었습니다.")

if __name__ == "__main__":
    main()
