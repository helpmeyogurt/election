import json
import os
import requests

URL = "https://info.nec.go.kr/m/electioninfo/electionInfo_report.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Referer": "https://info.nec.go.kr/",
}

# 요청할 시도 코드 설정 (예: 서울은 1100)
CITY_CODE = "1100"
CITY_NAME = "서울"  # 결과 JSON의 키값으로 사용

DATA = {
    "electionId": "0000000000",
    "electionType": "4",
    "sgDivMenuId": "VCCP09",
    "electionName": "20220601",
    "electionCode": "3",
    "electionCodeId": "3",
    "electionNameSgType": "1",
    "cityCode": CITY_CODE,
    "oldElectionType": "1",
    "statementId": "VCCP09_#3",
}

# 주요 정당 컬러 매핑 가이드 (필요시 수정 가능)
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
    """정당명에 맞는 색상을 반환하며, 딕셔너리에 없으면 기본값(#8b8b8b)을 사용합니다."""
    # 양끝 공백 제거 후 매핑
    cleaned_name = party_name.strip() if party_name else ""
    return PARTY_COLORS.get(cleaned_name, "#8b8b8b")


def parse_raw_data(raw_json):
    """선관위 원본 JSON 데이터를 요청하신 포맷으로 정제합니다."""
    # 선관위 데이터 구조에 따라 딕셔너리 키 명칭은 실제 응답에 맞춰 파싱해야 합니다.
    # 아래는 예시 구조(정형화된 형태)를 바탕으로 데이터 재조립을 수행하는 로직입니다.

    # 실제 선관위 데이터의 리스트 추출 (예시 파싱 구조 분석 필요)
    # 여기서는 원본 내 데이터 배열 형식을 'json_results'라 가정하고 가공 프로세스를 진행합니다.
    # 제공해주신 예시 형태로 결과물 객체를 빌드합니다.

    refined_list = []

    # [주의] 선관위에서 넘어오는 내부 raw 구조 배열을 순회해야 합니다.
    # 아래 코드는 제공해주신 원본 템플릿 구조를 역산하여 매핑하는 자동화 로직입니다.
    raw_items = raw_json.get("jsonResult", {}).get("data", [])
    if not raw_items:
        # 만약 전체 구조가 리스트 형태 등으로 넘어올 경우의 예외 처리
        raw_items = raw_json if isinstance(raw_json, list) else [raw_json]

    for item in raw_items:
        # 기본 정보 매핑
        refined_item = {
            "SDID": int(CITY_CODE),
            "SDNAME": item.get("SDNAME", "서울특별시"),
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

        # 후보자 데이터 파싱 및 조립 (최대 15명 선까지 동적 추적 가능)
        hubo_count = 0
        for i in range(1, 16):
            suffix = f"{i:02d}"  # 01, 02, 03...
            hubo_name = item.get(f"HUBO{suffix}")
            party_name = item.get(f"JD{suffix}")
            dugsu_str = item.get(f"DUGSU{suffix}")
            dugyul = item.get(f"DUGYUL{suffix}")

            if not hubo_name:  # 더 이상 후보자가 없으면 정지
                break

            hubo_count += 1

            # 득표수 숫자 변환 (콤마 제거)
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

    # 최종 래핑 형식인 {"서울": [...]} 데이터 리턴
    return {CITY_NAME: refined_list}


def main():
    output_dir = os.path.join("data", "jibang", "8")
    os.makedirs(output_dir, exist_ok=True)

    try:
        print("선관위 API 데이터 수집 시작...")
        response = requests.post(URL, headers=HEADERS, data=DATA)
        response.raise_for_status()
        raw_json = response.json()

        # 1. 원본 데이터 저장 (ori_1100.json)
        ori_path = os.path.join(output_dir, f"ori_{CITY_CODE}.json")
        with open(ori_path, "w", encoding="utf-8") as f:
            json.dump(raw_json, f, ensure_ascii=False, indent=4)
        print(f"원시 데이터 저장 완료: {ori_path}")

        # 2. 정제 데이터 처리 및 저장 (1100.json)
        refined_json = parse_raw_data(raw_json)
        refined_path = os.path.join(output_dir, f"{CITY_CODE}.json")
        with open(refined_path, "w", encoding="utf-8") as f:
            json.dump(refined_json, f, ensure_ascii=False, indent=4)
        print(f"정제된 데이터 가공 완료: {refined_path}")

    except Exception as e:
        print(f"오류 발생: {e}")


if __name__ == "__main__":
    main()
