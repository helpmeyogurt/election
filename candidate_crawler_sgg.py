import json
import os
import random
import time
import requests
import sys

# 선관위 후보자 명부 조회 API 주소
URL_CANDIDATE = "https://info.nec.go.kr/m/electioninfo/electionInfo_report.json"

# 가공하고자 하는 선거 종류 코드 (4: 시군구청장)
ELEC_CODE = "4"

# 🚨 [테스트 타겟 필터 시스템 적용]
# 테스트하고 싶으신 시도의 KEY를 적으세요. (예: "부산", "서울", "경기")
# 만약 "전체"라고 적으면 기존처럼 전국 17개 시도를 다 돕니다.
TARGET_CITY_KEY = "울산" 

MAX_RETRIES = 3
MIN_DELAY = 10.0  # 단일 지역 테스트이므로 빠른 피드백을 위해 대기 텀을 10~15초로 낮췄습니다.
MAX_DELAY = 15.0

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
    {"CODE": 1100, "NAME": "서울특별시", "KEY": "서울"},
    {"CODE": 2600, "NAME": "부산광역시", "KEY": "부산"},
    {"CODE": 2700, "NAME": "대구광역시", "KEY": "대구"},
    {"CODE": 2800, "NAME": "인천광역시", "KEY": "인천"},
    {"CODE": 2900, "NAME": "광주광역시", "KEY": "광주"},
    {"CODE": 3000, "NAME": "대전광역시", "KEY": "대전"},
    {"CODE": 3100, "NAME": "울산광역시", "KEY": "울산"},
    {"CODE": 5100, "NAME": "세종특별자치시", "KEY": "세종"},
    {"CODE": 4100, "NAME": "경기도", "KEY": "경기"},
    {"CODE": 4200, "NAME": "강원도", "KEY": "강원"},
    {"CODE": 4300, "NAME": "충청북도", "KEY": "충북"},
    {"CODE": 4400, "NAME": "충청남도", "KEY": "충남"},
    {"CODE": 4500, "NAME": "전라북도", "KEY": "전북"},
    {"CODE": 4600, "NAME": "전라남도", "KEY": "전남"},
    {"CODE": 4700, "NAME": "경상북도", "KEY": "경북"},
    {"CODE": 4800, "NAME": "경상남도", "KEY": "경남"},
    {"CODE": 4900, "NAME": "제주특별자치도", "KEY": "제주"}
]

def sleep_with_dots(delay_time):
    print(f"⏱️ 방화벽 차단 회피 대기 ({delay_time:.2f}초): ", end="")
    sys.stdout.flush()
    for _ in range(int(delay_time)):
        time.sleep(1)
        print(".", end="")
        sys.stdout.flush()
    print(" [대기 종료]")

def load_local_sgg_codes():
    """가상 서버 환경과 로컬 환경 어디서든 SGG_CODE.json 파일을 유연하게 탐색합니다."""
    possible_paths = [
        os.path.join("data", "jibang", "SGG_CODE.json"),
        os.path.join("election", "data", "jibang", "SGG_CODE.json"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "election", "data", "jibang", "SGG_CODE.json"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "jibang", "SGG_CODE.json")
    ]
    
    sgg_json_path = None
    for path in possible_paths:
        if os.path.exists(path):
            sgg_json_path = path
            print(f"🟢 [코드북 로드 성공] 경로 채택 ➡️ {sgg_json_path}")
            break

    if not sgg_json_path:
        print(f"🔴 [치명적 오류] SGG_CODE.json 파일을 찾지 못했습니다.")
        return None
    
    try:
        with open(sgg_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "SGG_CODE" in data and isinstance(data["SGG_CODE"], list) and len(data["SGG_CODE"]) > 0:
            return data["SGG_CODE"][0]
        return data
    except Exception as e:
        print(f"🔴 로컬 시군구 코드 파싱 오류: {e}")
        return None

def main():
    output_dir = os.path.join("data", "jibang", "9")
    os.makedirs(output_dir, exist_ok=True)

    print("📂 로컬 SGG_CODE.json 명세를 메모리에 로드합니다.")
    sgg_codebook = load_local_sgg_codes()
    
    if not sgg_codebook:
        return

    print(f"🔄 제9회 지선 [시군구청장(코드:{ELEC_CODE})] 타겟 지역 크롤링 모드를 작동합니다.")
    if TARGET_CITY_KEY != "전체":
        print(f"🎯 현재 조준 타겟 시도: [{TARGET_CITY_KEY}]")

    for city in CITIES:
        city_code_str = str(city["CODE"])
        city_name_str = city["NAME"]
        city_key = city["KEY"]

        # 🚨 [필터링 작동 부] 설정한 타겟 지역이 아니면 연산을 통째로 건너뜁니다.
        if TARGET_CITY_KEY != "전체" and city_key != TARGET_CITY_KEY:
            continue

        sgg_list = sgg_codebook.get(city_key, [])
        if not sgg_list:
            print(f"⚠️ [{city_name_str}] 데이터베이스 구조에 하위 시군구가 없어 패스합니다.")
            continue

        print(f"\n=======================================================")
        print(f"📊 [{city_name_str}] 타겟 분석 개시! 하위 총 {len(sgg_list)}개 자치구/시군 감지.")
        
        city_combined_candidates = {}

        for sgg in sgg_list:
            sgg_code = str(sgg.get("CODE", "")).strip()
            sgg_name = str(sgg.get("NAME", "")).strip()

            if not sgg_code or not sgg_name: 
                continue

            print(f"📡 ├─ [{sgg_name} (코드:{sgg_code})] 후보자 명부 수집 중...")

            payload = {
                "electionId": "0020260603",
                "secondMenuId": "CPRI03",
                "electionCode": ELEC_CODE,
                "cityCode": city_code_str,
                "statementId": f"CPRI03_#{ELEC_CODE}",
                "dateCode": "0",
                "sggCityCode": sgg_code
            }

            success = False
            attempt = 1

            while not success and attempt <= MAX_RETRIES:
                try:
                    response = requests.post(URL_CANDIDATE, headers=HEADERS, data=payload, timeout=15)
                    response.raise_for_status()
                    raw_json = response.json()

                    city_combined_candidates[sgg_name] = raw_json
                    success = True

                except Exception as e:
                    print(f"	⚠️ [{sgg_name}] 에러: {e}. {attempt}/{MAX_RETRIES}회차 재시도...")
                    attempt += 1
                    time.sleep(5)

            if not success:
                print(f"	🔴 [{sgg_name}] 최종 수집 실패.")

            random_delay = random.uniform(MIN_DELAY, MAX_DELAY)
            sleep_with_dots(random_delay)

        if city_combined_candidates:
            file_name = f"candidate_ori_{ELEC_CODE}_{city_code_str}.json"
            file_path = os.path.join(output_dir, file_name)
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(city_combined_candidates, f, ensure_ascii=False, indent=4)
            print(f"🟢 [{city_name_str}] 단일 타겟 통합 후보자 파일 저장 완료 -> {file_name}")

    print("\n✨ 설정된 타겟 시도의 시군구청장 후보자 테스트 수집이 종료되었습니다.")

if __name__ == "__main__":
    main()
