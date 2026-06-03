import json
import os
import sys
# 가공하고자 하는 선거 종류 코드 (3: 시도지사, 4: 시군구청장)
ELEC_CODE = "3"

# 인자값 강제 디버깅 및 적용
if len(sys.argv) > 1:
    passed_arg = str(sys.argv[1]).strip()
    print(f"📢 [시스템 통신] GitHub Actions로부터 전달받은 인자값: '{passed_arg}'")
    if passed_arg in ["3", "4"]:
        ELEC_CODE = passed_arg
    else:
        print(f"⚠️ 경고: 인자값 '{passed_arg}'가 유효하지 않아 기본값 '{ELEC_CODE}'으로 진행합니다.")
else:
    print(f"📢 [시스템 통신] 전달된 인자가 없어 기본값 '{ELEC_CODE}'으로 진행합니다.")
    
CITIES = [
    {"CODE": 1100, "NAME": "서울특별시"},
    {"CODE": 2600, "NAME": "부산광역시"},
    {"CODE": 2700, "NAME": "대구광역시"},
    {"CODE": 2800, "NAME": "인천광역시"},
    {"CODE": 2900, "NAME": "광주광역시"},
    {"CODE": 3000, "NAME": "대전광역시"},
    {"CODE": 3100, "NAME": "울산광역시"},
    {"CODE": 4100, "NAME": "경기도"},
    {"CODE": 5200, "NAME": "강원도"},
    {"CODE": 4300, "NAME": "충청북도"},
    {"CODE": 4400, "NAME": "충청남도"},
    {"CODE": 5300, "NAME": "전라북도"},
    {"CODE": 4600, "NAME": "전라남도"},
    {"CODE": 4700, "NAME": "경상북도"},
    {"CODE": 4800, "NAME": "경상남도"}
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
        wiw_name_raw = item.get("WIWNAME", "").strip()
        sgg_name_raw = item.get("SGGNAME", "").strip()
        
        # 선거구합계 노드 제외 및 시군구 필터링
        if sgg_name_raw == "선거구합계" or not sgg_name_raw or wiw_name_raw != "합계":
            continue

        display_name = sgg_name_raw
        sunsu_val = uncomma(item.get("SUNSU", "0"))
        tusu_val = uncomma(item.get("TUSU", "0"))
        
        gaepyo_raw = item.get("GAEPYOYUL", "").strip()
        if not gaepyo_raw or gaepyo_raw == "0":
            gaepyo_raw = "0.00"
            
        gaepyo_val = f"{gaepyo_raw}%"
        
        total_sunsu_sum += sunsu_val
        total_tusu_sum += tusu_val

        sgg_id_str = str(item.get("SGGID", "0"))
        final_wiw_id = int(sgg_id_str[1:5]) if len(sgg_id_str) >= 5 else int(sgg_id_str)

        sggdata = {
            "SDID": int(item.get("SDID", city_code)),
            "SDNAME": item.get("SDNAME", city_name),
            "SGGID": sgg_id_str,
            "SGGNAME": display_name,
            "WIWID": final_wiw_id, 
            "WIWNAME": display_name,
            "SUNSU": comma(sunsu_val),
            "TUSU": comma(tusu_val),
            "TUYUL": f"{(tusu_val / sunsu_val * 100):.1f}" if sunsu_val > 0 else "0.0",
            "GPYUL": gaepyo_val,
            "name": final_wiw_id, 
            "nametxt": display_name,
            "data": []
        }

        candidates = []
        hubo_count_raw = item.get("HUBOSU")
        hubo_count = int(hubo_count_raw) if hubo_count_raw else 0
        
        for k in range(1, hubo_count + 1):
            suffix = f"{k:02d}"
            hubo_name = item.get(f"HUBO{suffix}")
            
            if not hubo_name: 
                continue
            
            party_name = item.get(f"JD{suffix}", "무소속").strip()
            dugsu = uncomma(item.get(f"DUGSU{suffix}", "0"))
            
            try:
                dugyul = float(item.get(f"DUGYUL{suffix}", 0.0))
            except (ValueError, TypeError):
                dugyul = 0.0
            
            candidates.append({
                "num": k, 
                "hubo": hubo_name, 
                "jd": party_name, 
                "dugsu": dugsu, 
                "dugyul": dugyul
            })
            
            sggdata[f"HUBO{suffix}"] = hubo_name
            sggdata[f"JD{suffix}"] = party_name
            sggdata[f"DUGSU{suffix}"] = item.get(f"DUGSU{suffix}", "0")
            sggdata[f"DUGYUL{suffix}"] = item.get(f"DUGYUL{suffix}", "0.00")
            
            sggdata["data"].append({
                "value": dugyul, 
                "name": hubo_name, 
                "party": party_name,
                "pyo": dugsu, 
                "itemStyle": {"color": PARTY_COLORS.get(party_name, "#8b8b8b")}
            })

        is_before_counting = all(c["dugsu"] == 0 for c in candidates)

        if is_before_counting:
            candidates.sort(key=lambda x: x["num"])
        else:
            candidates.sort(key=lambda x: x["dugsu"], reverse=True)
        
        if candidates:
            win = candidates[0]
            sggdata.update({
                "WINNUM": win["num"], 
                "WINDUGSU": comma(win["dugsu"]), 
                "WINDUGYUL": f"{win['dugyul']:.2f}", 
                "WINHUBO": win["hubo"], 
                "WINJD": win["jd"]
            })
            
            win_party_key = win["jd"]
            win_party_counter[win_party_key] = win_party_counter.get(win_party_key, 0) + 1
            
            if len(candidates) >= 2:
                sec = candidates[1]
                dugyul_cha = f"{(win['dugyul'] - sec['dugyul']):.2f}" if not is_before_counting else "0.00"
                dugsu_cha = comma(win["dugsu"] - sec["dugsu"]) if not is_before_counting else "0"

                sggdata.update({
                    "SECNUM": sec["num"], 
                    "SECDUGSU": comma(sec["dugsu"]), 
                    "SECDUGYUL": f"{sec['dugyul']:.2f}", 
                    "SECHUBO": sec["hubo"], 
                    "SECJD": sec["jd"],
                    "DUGYULCHA": dugyul_cha, 
                    "DUGSUCHA": dugsu_cha
                })
            else:
                sggdata.update({
                    "SECNUM": 0, "SECDUGSU": "0", "SECDUGYUL": "0.00", 
                    "SECHUBO": "", "SECJD": "", 
                    "DUGYULCHA": f"{win['dugyul']:.2f}", "DUGSUCHA": comma(win['dugsu'])
                })
            
            sggdata["value"] = PARTY_MAP_INDEX.get(win["jd"], 9)

        refined_list.append(sggdata)

    # 🟢 [수정] 요청사항 반영: ELEC_CODE == "4" 일 때만 최상단 요약 노드를 만들어 리스트 맨 앞에 결합합니다.
    if ELEC_CODE == "4" and refined_list:
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
    target_dir = os.path.join("data", "jibang", "9")
    if not os.path.exists(target_dir):
        print(f"🔴 디렉토리가 존재하지 않습니다: {target_dir}")
        return

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
                else:
                    print(f"🟡 [{name_str}] 파싱할 데이터가 원본 파일에 없습니다.")
            except Exception as e:
                print(f"🔴 [{name_str}] 가공 오류: {e}")
        else:
            print(f"⚪ [{name_str}] 원본 파일이 없습니다: ori_{ELEC_CODE}_{code_str}.json")

    print("✨ 지정한 정당 순서 명세가 파일 구조에 완벽하게 빌드되었습니다.")

if __name__ == "__main__":
    main()
