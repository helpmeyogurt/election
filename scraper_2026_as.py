import json
import os
import time
import requests
import random

URL = "https://info.nec.go.kr/m/electioninfo/electionInfo_report.json"

# ==========================================
# [설정 변수] 원하시는 옵션을 상단에서 편하게 수정하세요.
# ==========================================
MIN_DELAY = 10.0    # 최소 대기 시간
MAX_DELAY = 15.0    # 최대 대기 시간
MAX_RETRIES = 3     # 💡 최대 재시도 횟수 (실패 시 총 3번 더 시도)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://info.nec.go.kr",
    "Referer": "https://info.nec.go.kr/m/main.xhtml",
    "Connection": "keep-alive"
}

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
    
def process_and_transform(raw_json):
    """
    선관위 원본 JSON 데이터를 파싱하여 
    사용자가 요청한 선거구별 Object 중첩 형식으로 변환합니다.
    """
    transformed_result = {}
    
    # 안전하게 body 리스트 가져오기
    body_data = raw_json.get("jsonResult", {}).get("body", [])
    if not body_data:
        return transformed_result

    for item in body_data:
        wiw_name = str(item.get("WIWNAME") or "").strip()
        sgg_name = str(item.get("SGGNAME") or "").strip()
        
        # 🟢 규칙: '소계' 노드나 시군구 합계 데이터만 타겟으로 잡습니다.
        if wiw_name != "소계" and wiw_name != "합계" and sgg_name != wiw_name:
            continue
            
        if not sgg_name:
            continue

        sunsu_val = uncomma(item.get("SUNSU", "0"))
        tusu_val = uncomma(item.get("TUSU") or item.get("TTUHAMSU", "0"))
        mutusu_val = uncomma(item.get("MUTUSU", "0"))
        gigwon_val = uncomma(item.get("GIGWON", "0"))
        
        # 총 유효투표수 계산 (투표수 - 무효투표수)
        total_valid_votes = tusu_val - mutusu_val
        if total_valid_votes < 0: 
            total_valid_votes = uncomma(item.get("TOTALDUGSU", "0"))

        sgg_id_str = str(item.get("SGGID", "0"))
        final_wiw_id = int(sgg_id_str[1:5]) if len(sgg_id_str) >= 5 else int(sgg_id_str)
        
        hubosu_count = int(item.get("HUBOSU", "0"))

        sgg_object = {
            "SDID": int(item.get("SDID", 0)),
            "SDNAME": item.get("SDNAME", ""),
            "SGGID": sgg_id_str,
            "SGGNAME": sgg_name,
            "WIWID": final_wiw_id,
            "WIWNAME": sgg_name,  # 요구 양식에 맞춤
            "SUNSU": comma(sunsu_val),
            "TUSU": comma(tusu_val),
            "TOTAL": comma(total_valid_votes),
            "MUTUSU": comma(mutusu_val),
            "GIGWON": comma(gigwon_val),
            "HUBOSU": str(hubosu_count),
            "TUYUL": f"{(tusu_val / sunsu_val * 100):.1f}" if sunsu_val > 0 else "0.0",
            "name": final_wiw_id,
            "nametxt": sgg_name,
            "data": []
        }

        candidates = []
        for k in range(1, hubosu_count + 1):
            suffix = f"{k:02d}"
            hubo_name = item.get(f"HUBO{suffix}")
            if not hubo_name:
                continue
                
            party_name = str(item.get(f"JD{suffix}") or "무소속").strip()
            dugsu = uncomma(item.get(f"DUGSU{suffix}", "0"))
            
            try:
                dugyul = float(item.get(f"DUGYUL{suffix}", 0.0))
            except (ValueError, TypeError):
                dugyul = 0.0

            candidates.append({
                "num": k,
                "name": hubo_name,
                "party": party_name,
                "pyo": dugsu,
                "value": dugyul,
                "itemStyle": {"color": PARTY_COLORS.get(party_name, "#8b8b8b")}
            })

        # 득표순 정렬 (개표 전이면 기호순)
        is_before_counting = all(c["pyo"] == 0 for c in candidates)
        if is_before_counting:
            candidates.sort(key=lambda x: x["num"])
        else:
            candidates.sort(key=lambda x: x["pyo"], reverse=True)

        # 차트 연동용 data 배열 조립 및 플랫 키 재생성
        for c in candidates:
            sgg_object["data"].append({
                "value": c["value"],
                "name": c["name"],
                "party": c["party"],
                "pyo": c["pyo"],
                "itemStyle": c["itemStyle"]
            })
            
            # 오리지널 포맷 플랫 키 백업 복원
            idx_str = f"{c['num']:02d}"
            sgg_object[f"HUBO{idx_str}"] = c["name"]
            sgg_object[f"JD{idx_str}"] = c["party"]
            sgg_object[f"DUGSU{idx_str}"] = comma(c["pyo"])
            sgg_object[f"DUGYUL{idx_str}"] = f"{c['value']:.2f}"

        # 1위 / 2위 정보 분석 및 격차 기록
        if candidates:
            win = candidates[0]
            sgg_object.update({
                "WINNUM": win["num"],
                "WINDUGSU": comma(win["pyo"]),
                "WINDUGYUL": f"{win['value']:.2f}",
                "WINHUBO": win["name"],
                "WINJD": win["party"],
                "value": PARTY_MAP_INDEX.get(win["party"], 9) # 지도 채색을 위해 승리 정당 인덱스 매핑
            })
            
            if len(candidates) >= 2:
                sec = candidates[1]
                dugyul_cha = f"{(win['value'] - sec['value']):.2f}" if not is_before_counting else "0.00"
                dugsu_cha = comma(win["pyo"] - sec["pyo"]) if not is_before_counting else "0"
                
                sgg_object.update({
                    "SECNUM": sec["num"],
                    "SECDUGSU": comma(sec["pyo"]),
                    "SECDUGYUL": f"{sec['value']:.2f}",
                    "SECHUBO": sec["name"],
                    "SECJD": sec["party"],
                    "DUGYULCHA": dugyul_cha,
                    "DUGSUCHA": dugsu_cha
                })
            else:
                sgg_object.update({
                    "SECNUM": 0, "SECDUGSU": "0", "SECDUGYUL": "0.00",
                    "SECHUBO": "", "SECJD": "",
                    "DUGYULCHA": f"{win['value']:.2f}", "DUGSUCHA": comma(win['pyo'])
                })

        transformed_result[sgg_name] = sgg_object

    return transformed_result

def main():
    output_dir = os.path.join("data")
    os.makedirs(output_dir, exist_ok=True)

    print(f"국회의원 선거 원본 데이터 수집을 시작합니다.", flush=True)
    print(f"설정 옵션 - 대기 범위: {MIN_DELAY}초 ~ {MAX_DELAY}초 | 최대 재시도: {MAX_RETRIES}회", flush=True)

    # 🛠️ 들여쓰기 정상화 완료
    code_str = "0000"
    name_str = "국회의원보궐"

    payload = {
        "electionId": "0020260603",
        "secondMenuId": "VCCP09",
        "electionCode": "2",
        "cityCode": "0",
        "statementId": "VCCP09_#2",
    }

    success = False
        
    # 재시도 루프 구성 (0번째 시도가 최초 시도이며, 이후 MAX_RETRIES까지 회차 증가)
    for attempt in range(MAX_RETRIES + 1):
        if attempt == 0:
            print(f"\n[{name_str}] 데이터 요청 중 (코드: {code_str})...", flush=True)
        else:
            print(f"🔄 [{name_str}] 네트워크 지연/실패로 인해 재시도 중... ({attempt}/{MAX_RETRIES}회차)", flush=True)

        try:
            # 네트워크 일시 먹통 방지 타임아웃 10초 설정
            response = requests.post(URL, headers=HEADERS, data=payload, timeout=10)
            response.raise_for_status()
            raw_json = response.json()

            if "jsonResult" in raw_json and raw_json["jsonResult"].get("success") == "false":
                print(f"⚠️ [{name_str}] API 내부 오류 메시지: {raw_json['jsonResult'].get('message')}", flush=True)

            # 🟢 [핵심 가공 로직 연동] 받아온 JSON 데이터를 원하는 포맷으로 즉시 필터링 및 조립
            refined_result = process_and_transform(raw_json)

            file_path = os.path.join(output_dir, f"cur_2026.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(refined_result, f, ensure_ascii=False, indent=4)

            print(f"🟢 [{name_str}] 원본 파일 저장 완료 -> {file_path}", flush=True)
            success = True
            break # 요청 성공 시 재시도 루프 탈출
                
        except requests.exceptions.Timeout:
            print(f"🟡 [{name_str}] 요청 타임아웃 제한 시간(10초) 초과", flush=True)
        except Exception as e:
            print(f"🔴 [{name_str}] 에러 발생: {e}", flush=True)

        # 실패했고, 아직 재시도 기회가 남아있다면 잠시 쉬었다가 다음 회차로 진행
        if attempt < MAX_RETRIES:
            retry_delay = round(random.uniform(MIN_DELAY, MAX_DELAY), 2)
            print(f"⏳ {retry_delay}초 동안 랜덤 대기 후 다음 재시도를 수행합니다...", flush=True)
            time.sleep(retry_delay)

    if not success:
        print(f"❌ [{name_str}] 최종 수집 실패 (총 {MAX_RETRIES + 1}회 시도 모두 실패)", flush=True)

    print("\n모든 작업이 완료되었습니다.", flush=True)

if __name__ == "__main__":
    main()
