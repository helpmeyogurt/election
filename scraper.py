import json
import os
import time
import requests

URL = "https://info.nec.go.kr/m/electioninfo/electionInfo_report.json"

# 안드로이드 모바일 크롬 브라우저 기준으로 헤더 전면 개편
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://info.nec.go.kr",
    "Referer": "https://info.nec.go.kr/m/main.xhtml", # 모바일 메인 주소 레퍼러
    "Connection": "keep-alive"
}

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

def get_party_color(party_name):
    cleaned_name = party_name.strip() if party_name else ""
    return PARTY_COLORS.get(cleaned_name, "#8b8b8b")

def parse_raw_data(raw_json, city_code, city_name):
    refined_list = []
    raw_items = raw_json.get("jsonResult", {}).get("data", [])
    if not raw_items:
        raw_items = raw_json if isinstance(raw_json, list) else [raw_json]

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
            hubo_name = item.get(f"HUBO{suffix}")
            party_name = item.get(f"JD{suffix}")
            dugsu_str = item.get(f"DUGSU{suffix}")
            dugyul = item.get(f"DUGYUL{suffix}")

            if not hubo_name:
                break
            hubo_count += 1

            try:
                val = int(dugsu_str.replace(",", ""))
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
    output_dir = os.path.join("data", "jibang", "8")
    os.makedirs(output_dir, exist_ok=True)

    print(f"총 {len(CITIES)}개 시도 선거 데이터 수집을 시작합니다.")

    for city in CITIES:
        code_str = str(city["CODE"])
        name_str = city["NAME"]

        print(f"[{name_str}] 데이터 요청 중 (코드: {code_str})...")

        payload = {
            "electionId": "0000000000", "electionType": "4", "sgDivMenuId": "VCCP09",
            "electionName": "20220601", "electionCode": "3", "electionCodeId": "3",
            "electionNameSgType": "1", "cityCode": code_str, "oldElectionType": "1",
            "statementId": "VCCP09_#3",
        }

        try:
            # timeout=10 추가 (선관위가 응답 안 주면 10초 뒤 강제 중단 및 다음 지역으로 패스)
            response = requests.post(URL, headers=HEADERS, data=payload, timeout=10)
            response.raise_for_status()
            raw_json = response.json()

            # 1. 원본 저장
            with open(os.path.join(output_dir, f"ori_{code_str}.json"), "w", encoding="utf-8") as f:
                json.dump(raw_json, f, ensure_ascii=False, indent=4)

            # 2. 정제 저장
            refined_json = parse_raw_data(raw_json, code_str, name_str)
            with open(os.path.join(output_dir, f"{code_str}.json"), "w", encoding="utf-8") as f:
                json.dump(refined_json, f, ensure_ascii=False, indent=4)

            print(f"🟢 [{name_str}] 저장 완료")

        except requests.exceptions.Timeout:
            print(f"🔴 [{name_str}] 요청 타임아웃 제한 시간(10초)을 초과하여 다음 지역으로 넘어갑니다.")
        except Exception as e:
            print(f"🔴 [{name_str}] 처리 중 오류 발생: {e}")

        # 안전 구동을 위해 대기 시간을 5초로 크게 늘림 (선관위 부하 방지)
        print("안전 조치를 위해 30초간 대기합니다...")
        time.sleep(30)

    print("모든 작업 시도가 완료되었습니다.")

if __name__ == "__main__":
    main()
