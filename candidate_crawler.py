import json
import os
import random
import time
import requests
import sys

URL = "https://info.nec.go.kr/m/electioninfo/electionInfo_report.json"

# 🚨 가공하고자 하는 선거 종류 코드 (3: 시도지사, 4: 시군구청장)
ELEC_CODE = "3"

# 🚨 실패 시 최대 재시도 횟수 지정
MAX_RETRIES = 3

# 🚨 서버 보호를 위한 무작위 대기 시간 범위 (초 단위)
MIN_DELAY = 30.0
MAX_DELAY = 50.0

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

# 전국 17개 시도 코드 매핑 배열
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

def main():
    elec_code = ELEC_CODE
    output_dir = os.path.join("data", "jibang", "8")
    os.makedirs(output_dir, exist_ok=True)

    elec_name = "시도지사" if elec_code == "3" else "시군구청장"
    print(f"🔄 총 {len(CITIES)}개 시도의 [{elec_name}(코드:{elec_code})] '후보자 명부' 크롤링을 시작합니다.")
    print(f"⏱️ 안전 제어 모드: {MIN_DELAY}초 ~ {MAX_DELAY}초 랜덤 대기 및 Actions 강제종료 방지 활성화")

    for city in CITIES:
        code_str = str(city["CODE"])
        name_str = city["NAME"]

        # 🚨 전달해주신 후보자 조회용 인자 명세 반영
        payload = {
            "electionId": "0020260603",       # 제9회 지선 고유 선거 ID
            "secondMenuId": "CPRI03",         # 후보자 명부 메뉴 고유 식별자
            "electionCode": elec_code,         # 3 또는 4
            "cityCode": code_str,             # 시도 코드 (예: 1100)
            "statementId": f"CPRI03_#{elec_code}", # 명세 ID 동적 결합
            "dateCode": "0"
        }

        success = False
        attempt = 1

        while not success and attempt <= MAX_RETRIES:
            print(f"📡 [{name_str} 후보자 정보] 선관위 원본 API 요청 중... (시도 {attempt}/{MAX_RETRIES}회차)")

            try:
                response = requests.post(URL, headers=HEADERS, data=payload, timeout=15)
                response.raise_for_status()
                raw_json = response.json()

                # 기존 개표 데이터 파일명과 충돌하지 않도록 candidate_ori_ 규칙 적용
                file_name = f"candidate_ori_{elec_code}_{code_str}.json"
                file_path = os.path.join(output_dir, file_name)
                
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(raw_json, f, ensure_ascii=False, indent=4)

                print(f"🟢 [{name_str}] 후보자 원본 다운로드 완료 -> {file_name}")
                success = True 

            except Exception as e:
                print(f"⚠️ [{name_str}] 요청 실패 에러: {e}. 20초 대기 후 재시도합니다.")
                attempt += 1
                time.sleep(20)

        if not success:
            print(f"🔴 [{name_str}] 후보자 명부 최종 획득 실패. 다음 지역으로 건너뜁니다.")

        # GitHub Actions 무응답 서버 다운(Hang) 현상 방지용 점 찍기 루프
        random_delay = random.uniform(MIN_DELAY, MAX_DELAY)
        print(f"⏱️ 방화벽 차단 회피 보호 대기 ({random_delay:.2f}초): ", end="")
        sys.stdout.flush()

        seconds_to_sleep = int(random_delay)
        for _ in range(seconds_to_sleep):
            time.sleep(1)
            print(".", end="")
            sys.stdout.flush()
        print(" [대기 종료]\n")

    print(f"✨ 모든 시도의 {elec_name} 후보자 원본 데이터 JSON 다운로드 프로세스가 종료되었습니다.")

if __name__ == "__main__":
    main()
