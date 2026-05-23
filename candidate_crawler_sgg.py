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

MAX_RETRIES = 3
MIN_DELAY = 15.0  # 서버 보호를 위한 무작위 대기 최소 시간
MAX_DELAY = 30.0  # 서버 보호를 위한 무작위 대기 최대 시간

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

# 🚨 SGG_CODE.json의 키값과 매핑하기 위해 "KEY" 필드를 보완했습니다.
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
    """지정한 시간만큼 점을 찍으며 안전 대기합니다."""
    print(f"⏱️ 방화벽 차단 회피 대기 ({delay_time:.2f}초): ", end="")
    sys.stdout.flush()
    for _ in range(int(delay_time)):
        time.sleep(1)
        print(".", end="")
        sys.stdout.flush()
    print(" [대기 종료]")

def load_local_sgg_codes():
    """가상 서버 환경과 로컬 환경 어디서든 SGG_CODE.json 파일을 유연하게 탐색합니다."""
    # 탐색할 후보 경로 리스트 목록 정의
    possible_paths = [
        # 1순위: 깃허브 액션 최상위 워크스페이스 기준 표준 경로
        os.path.join("election", "data", "jibang", "SGG_CODE.json"),
        
        # 2순위: 현재 실행 중인 스크립트 파일 위치 기준 경로
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "election", "data", "jibang", "SGG_CODE.json"),
        
        # 3순위: 만약 레포지토리 자체가 최상위 루트일 경우의 직접 경로
        os.path.join("data", "jibang", "SGG_CODE.json"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "jibang", "SGG_CODE.json")
    ]
    
    sgg_json_path = None
    
    # 순고하게 매핑 후보를 순회하며 실제 물리적으로 존재하는 경로를 채택합니다.
    for path in possible_paths:
        print(f"🔍 [경로 탐색망 체크]: {path}")
        if os.path.exists(path):
            sgg_json_path = path
            print(f"🟢 [매칭 성공] 파일을 찾았습니다! 최종 채택 경로 ➡️ {sgg_json_path}")
            break

    if not sgg_json_path:
        print(f"🔴 [치명적 오류] 제공된 모든 후보 경로에서 SGG_CODE.json 파일을 찾지 못했습니다.")
        # 디버깅을 돕기 위해 현재 스크립트 실행 위치의 폴더 트리 상태를 출력합니다.
        try:
            print(f"📂 현재 스크립트 실행 작업 디렉터리(CWD): {os.getcwd()}")
            print(f"📂 현재 폴더 내 파일 목록 구조: {os.listdir('.')}")
        except Exception:
            pass
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

    # 🚨 1단계: 로컬에 저장해두신 시군구 코드북 파일 로드
    print("📂 로컬 SGG_CODE.json 명세를 메모리에 로드합니다.")
    sgg_codebook = load_local_sgg_codes()
    
    if not sgg_codebook:
        print("🔴 시군구 데이터베이스 로드 실패로 스크립트를 종료합니다.")
        return

    print(f"🔄 제9회 지선 [시군구청장(코드:{ELEC_CODE})] 로컬 매핑 크롤링을 개시합니다.")

    for city in CITIES:
        city_code_str = str(city["CODE"])
        city_name_str = city["NAME"]
        city_key = city["KEY"]

        # 로컬 파일에서 현재 시도 키(예: "서울")에 해당하는 배열 추출
        sgg_list = sgg_codebook.get(city_key, [])
        
        if not sgg_list:
            print(f"⚠️ [{city_name_str}] 로컬 매핑 데이터 구조에 하위 시군구가 없어 건너뜁니다.")
            continue

        print(f"\n=======================================================")
        print(f"📊 [{city_name_str}] 데이터베이스 기준 총 {len(sgg_list)}개 자치구/시군 매핑 시작.")
        
        city_combined_candidates = {}

        for sgg in sgg_list:
            # 🚨 제공해주신 대문자 명세인 CODE와 NAME 필드 사용
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
                "sggCityCode": sgg_code  # 로컬 파일에서 가져온 코드가 주입됩니다.
            }

            success = False
            attempt = 1

            while not success and attempt <= MAX_RETRIES:
                try:
                    response = requests.post(URL_CANDIDATE, headers=HEADERS, data=payload, timeout=15)
                    response.raise_for_status()
                    raw_json = response.json()

                    # 시군구 이름을 키로 삼아 통계 원본 바인딩
                    city_combined_candidates[sgg_name] = raw_json
                    success = True

                except Exception as e:
                    print(f"	⚠️ [{sgg_name}] 에러 발생: {e}. {attempt}/{MAX_RETRIES}회차 재시도 대기...")
                    attempt += 1
                    time.sleep(10)

            if not success:
                print(f"	🔴 [{sgg_name}] 최종 수집 실패.")

            # 서버 보호를 위한 무작위 대기 텀 작동
            random_delay = random.uniform(MIN_DELAY, MAX_DELAY)
            sleep_with_dots(random_delay)

        # 시도 통합 원본 파일 쓰기 (예: data/jibang/9/candidate_ori_4_1100.json)
        if city_combined_candidates:
            file_name = f"candidate_ori_{ELEC_CODE}_{city_code_str}.json"
            file_path = os.path.join(output_dir, file_name)
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(city_combined_candidates, f, ensure_ascii=False, indent=4)
            print(f"🟢 [{city_name_str}] 로컬 매핑 기반 통합 후보자 파일 저장 완료 -> {file_name}")

    print("\n✨ 모든 시도의 시군구청장 후보자 로컬 최적화 수집이 종료되었습니다.")

if __name__ == "__main__":
    main()
