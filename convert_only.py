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

    win_party_counter = {}
    
    total_sunsu_sum = 0
    total_tusu_sum = 0

    for item in raw_items:
        wiw_id_raw = item.get("WIWID", "0")
        wiw_name_raw = item.get("WIWNAME", "").strip()
        sgg_name_raw = item.get("SGGNAME", "").strip()
        sgg_id_raw = item.get("SGGID", "0")

        # 🚨 [규칙 1]: 경기도 전체 데이터 파일 맨 위에 가끔 들어있는 '도 전체 합계'는
        # SGGNAME이 '선거구합계'이거나 빈값으로 옵니다. 이건 무조건 스킵합니다.
        if sgg_name_raw == "선거구합계" or not sgg_name_raw:
            continue

        # 🚨 [규칙 2 - 핵심 필터]: 
        # 군포시의 '군포시' 자식 행 스킵! 수원의 '장안구', '권선구', '팔달구', '영통구' 자식 행 전면 스킵!
        # 오직 완벽한 총합 데이터가 계산되어 있는 "WIWNAME == 합계" 행만 정밀 저격해서 통과시킵니다.
        if wiw_name_raw != "합계":
            continue

        # 🟢 필터를 통과한 행은 군포시 전체 합계 행 1개, 수원시 전체 합계 행 1개식으로 딱 정리됩니다.
        display_name = sgg_name_raw # "군포시", "수원시"가 정갈하게 담깁니다.

        sunsu_val = uncomma(item.get("SUNSU", "0"))
        tusu_val = uncomma(item.get("TUSU", "0"))
        
        # 중복이 싹 걷어진 알짜배기 시군구 총합 데이터만 도합산 저금통에 누적! (투표율 뻥튀기 200% 차단)
        total_sunsu_sum += sunsu_val
        total_tusu_sum += tusu_val

        tuyul_val = f"{(tusu_val / sunsu_val * 100):.1f}" if sunsu_val > 0 else "0.0"
        
        # 🚨 [프론트엔드 연동 가공]: 합계 행은 WIWID가 0으로 오기 때문에, 
        # 지도 엔진(ECharts)이 인식할 수 있도록 고유 번호인 SGGID(예: 4410300)를 가공해서 꽂아줍니다.
        final_wiw_id = int(sgg_id_raw) if str(sgg_id_raw).isdigit() else 0

        sggdata = {
            "SDID": int(item.get("SDID", city_code)),
            "SDNAME": item.get("SDNAME", city_name),
            "SGGID": str(sgg_id_raw),
            "SGGNAME": display_name,             # 🟢 "합계" 대신 "수원시", "군포시"
            "WIWID": final_wiw_id,                # 🟢 0 대신 진짜 지도 연동 코드 주입
            "WIWNAME": display_name,
            "SUNSU": comma(sunsu_val),
            "TUSU": comma(tusu_val),
            "TOTAL": item.get("TOTAL", "0"),
            "MUTUSU": item.get("MUTUSU", "0"),
            "GIGWON": item.get("GIGWON", "0"),
            "HUBOSU": item.get("HUBOSU", "0"),
            "TUYUL": tuyul_val,
            "name": final_wiw_id, 
            "nametxt": display_name,
            "data": []
        }

        # --- 후보자 데이터 파싱 구역 (사장님 오리지널 엔진 100% 동일 유지) ---
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

        if win_jd and win_dugsu > sec_dugsu:
            cleaned_win_jd = win_jd.strip()
            win_party_counter[cleaned_win_jd] = win_party_counter.get(cleaned_win_jd, 0) + 1

        refined_list.append(sggdata)

    # 3. 최상단 '시도 합산 요약 노드' 생성 구역
    if ELEC_CODE == "4":
        summary_pie_data = []
        for party, count in win_party_counter.items():
            summary_pie_data.append({
                "name": party,
                "value": count,
                "itemStyle": {"color": PARTY_COLORS.get(party, "#8b8b8b")}
            })
            
        custom_order = ["더불어민주당", "국민의힘", "정의당", "진보당", "무소속"]
        summary_pie_data.sort(key=lambda x: custom_order.index(x["name"]) if x["name"] in custom_order else 999)

        total_tuyul_calc = f"{(total_tusu_sum / total_sunsu_sum * 100):.1f}" if total_sunsu_sum > 0 else "0.0"

        summary_node = {
            "SDID": int(city_code),
            "SDNAME": city_name,
            "SGGID": "0",
            "SGGNAME": "합계",
            "WIWID": 0,
            "WIWNAME": "합계",
            "SUNSU": comma(total_sunsu_sum),     
            "TUSU": comma(total_tusu_sum),       
            "TUYUL": total_tuyul_calc,           
            "data": summary_pie_data
        }

        refined_list.insert(0, summary_node)

    return {city_name: refined_list}

def main():
    target_dir = os.path.join("data", "jibang", "8")
    if not os.path.exists(target_dir): return

    print(f"🔄 선거코드 [{ELEC_CODE}] 기준 고정 정당 순서 가공을 시작합니다.")

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
                    print(f"🟢 [{name_str}] 고정 정당 정렬 변환 완료 -> {ELEC_CODE}_{code_str}.json")
            except Exception as e:
                print(f"🔴 [{name_str}] 가공 오류: {e}")

    print("✨ 지정한 정당 순서 명세가 파일 구조에 완벽하게 빌드되었습니다.")

if __name__ == "__main__":
    main()
