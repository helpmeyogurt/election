import json
import os
import time
import requests

URL = "https://info.nec.go.kr/m/electioninfo/electionInfo_report.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Referer": "https://info.nec.go.kr/",
}

# 요청하신 시도 명칭 그대로 반영
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

# 정당 컬러 매핑 가이드
PARTY_COLORS = {
    "더불어민주당": "#152484",
    "국민의힘": "#E61E2B",
    "더불어민주연합": "#152484",
    "국민의미래": "#E61E2B",
    "녹색정의당": "#007C36",
    "새로운미래": "#46bbbd",
    "개혁신당": "#FF7920",
    "진보당": "#D6001C",
    "자유통일당": "#E24A49",
    "조국혁신당": "#004099",
    "기본소득당": "#00D2C3",
    "무소속": "#8b8b8b",
    "국민의당": "#EA5504",
    "미래통합당": "#EF426F",
    "미래한국당": "#EF426F",
    "더불어시민당": "#006CB7",
    "정의당": "#ffca05",
    "열린민주당": "#003E98",
    "소나무당": "#1A246B",
    "우리공화당": "#009944",
    "한국국민당": "#013588",
    "새진보연합": "#00d2c3",
    "없음": "#8b8b8b",
}


def get_party_color(party_name):
    """정당명에 맞는 색상을 반환합니다."""
    cleaned_name = party_name.strip() if party_name else ""
    return PARTY_COLORS.get(cleaned_name, "#8b8b8b")


def parse_raw_data(raw_json, city_code, city_name):
    """선관위 원본 JSON 데이터를 요청하신 포맷으로 정제합니다."""
    refined_list = []

    raw_items = raw_json.get("jsonResult", {}).get("data", [])
    if not raw_items:
        raw_items = raw_json if isinstance(raw_json, list) else [raw_json]

    for item in raw_items:
        # 기본 정보 매핑 (전달받은 정식 시도 명칭을 SDNAME 기본값으로 활용)
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

        # 후보자 데이터 파싱 및 조립 (최대 15명 동적 추적)
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

            # data 내부 리스트 구조 채우기
            refined_item["data"].append(
                {
                    "value": val,
                    "name": hubo_name,
                    "itemStyle": {"color": get_party_color(party_name)},
                }
            )

            # 상위 레벨 후보 정보 복사
            refined_item[f"HUBO{suffix}"] = hubo_name
            refined_item[f"JD{suffix}"] = party_name
            refined_item[f"DUGSU{suffix}"] = dugsu_str
            refined_item[f"DUGYUL{suffix}"] = dugyul

        refined_item["HUBOSU"] = str(hubo_count)
        refined_list.append(refined_item)

    # 지정하신 "서울특별시", "부산광역시" 등의 명칭이 그대로 키값(Key)이 됩니다.
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
            "electionId": "0000000000",
            "electionType": "4",
            "sgDivMenuId": "VCCP09",
            "electionName": "20220601",
            "electionCode": "3",
            "electionCodeId": "3",
            "electionNameSgType": "1",
            "cityCode": code_str,
            "oldElectionType": "1",
            "statementId": "VCCP09_#3",
        }

        try:
            response = requests.post(URL, headers=HEADERS, data=payload)
            response.raise_for_status()
            raw_json = response.json()

            # 1. 원본 데이터 저장 (예: ori_1100.json)
            ori_path = os.path.join(output_dir, f"ori_{code_str}.json")
            with open(ori_path, "w", encoding="utf-8") as f:
                json.dump(raw_json, f, ensure_ascii=False, indent=4)

            # 2. 정제 데이터 처리 및 저장 (예: 1100.json)
            refined_json = parse_raw_data(raw_json, code_str, name_str)
            refined_path = os.path.join(output_dir, f"{code_str}.json")
            with open(refined_path, "w", encoding="utf-8") as f:
                json.dump(refined_json, f, ensure_ascii=False, indent=4)

            print(f"🟢 [{name_str}] 저장 완료")

        except Exception as e:
            print(f"🔴 [{name_str}] 처리 중 오류 발생: {e}")

        # 딜레이 부하 방지 (1초 쉬기)
        time.sleep(1)

    print("모든 작업이 완료되었습니다.")


if __name__ == "__main__":
    main()
