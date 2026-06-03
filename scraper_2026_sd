import json
import os
import time
import requests

URL = "https://info.nec.go.kr/m/electioninfo/electionInfo_report.json"

# ==========================================
# [설정 변수] 원하시는 대기 시간을 초 단위로 설정하세요.
# ==========================================
DELAY_SECONDS = 10  # 예: 20초 텀을 두고 싶다면 20으로 설정

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
    {"CODE": 5200, "NAME": "강원특별자치도"},
    {"CODE": 4300, "NAME": "충청북도"},
    {"CODE": 4400, "NAME": "충청남도"},
    {"CODE": 5300, "NAME": "전북특별자치도"},
    {"CODE": 4700, "NAME": "경상북도"},
    {"CODE": 4800, "NAME": "경상남도"},
    {"CODE": 4900, "NAME": "제주특별자치도"},
]

def main():
    output_dir = os.path.join("data", "jibang", "9")
    os.makedirs(output_dir, exist_ok=True)

    print(f"총 {len(CITIES)}개 시도 선거 원본 데이터 수집을 시작합니다. (요청 텀: {DELAY_SECONDS}초)")

    for idx, city in enumerate(CITIES):
        code_str = str(city["CODE"])
        name_str = city["NAME"]

        print(f"[{name_str}] 데이터 요청 중 (코드: {code_str})...")

        payload = {
            "electionId": "0020260603",
            "secondMenuId": "VCCP09",
            "electionCode": "3",
            "cityCode": code_str,
            "statementId": "VCCP09_#3",
        }

        try:
            response = requests.post(URL, headers=HEADERS, data=payload, timeout=10)
            response.raise_for_status()
            raw_json = response.json()

            if "jsonResult" in raw_json and raw_json["jsonResult"].get("success") == "false":
                print(f"⚠️ [{name_str}] API 내부 오류 메시지: {raw_json['jsonResult'].get('message')}")

            file_path = os.path.join(output_dir, f"ori_{code_str}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(raw_json, f, ensure_ascii=False, indent=4)

            print(f"🟢 [{name_str}] 원본 파일 저장 완료 -> {file_path}")

        except requests.exceptions.Timeout:
            print(f"🔴 [{name_str}] 요청 타임아웃 제한 시간 초과")
        except Exception as e:
            print(f"🔴 [{name_str}] 에러 발생: {e}")

        # 마지막 루프가 아니라면 대기 시간을 적용합니다.
        if idx < len(CITIES) - 1:
            print(f"⏳ 다음 요청까지 {DELAY_SECONDS}초 대기 중...")
            time.sleep(DELAY_SECONDS)

    print("모든 작업이 완료되었습니다.")

if __name__ == "__main__":
    main()
