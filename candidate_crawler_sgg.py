import json
import os
import random
import time
import requests
import sys

# 선관위 원본 API 주소 명세
URL_SGG_LIST = "https://info.nec.go.kr/m/bizcommon/selectbox/selectbox_getSggCityCodeJson.json"
URL_CANDIDATE = "https://info.nec.go.kr/m/electioninfo/electionInfo_report.json"

# 🚨 시군구청장 선거 종류 코드 고정
ELEC_CODE = "4"

MAX_RETRIES = 3
MIN_DELAY = 15.0  # 시군구별로 요청이 많아지므로 딜레이 범위를 15~30초로 미세 조율했습니다.
MAX_DELAY = 25.0

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
    {"CODE": 1100, "NAME": "서울특별시"}, {"CODE": 2600, "NAME": "부산광역시"},
    {"CODE": 2700, "NAME": "대구광역시"}, {"CODE": 2800, "NAME": "인천광역시"},
    {"CODE": 2900, "NAME": "광주광역시"}, {"CODE": 3000, "NAME": "대전광역시"},
    {"CODE": 3100, "NAME": "울산광역시"}, {"CODE": 5100, "NAME": "세종특별자치시"},
    {"CODE": 4100, "NAME": "경기도"},    {"CODE": 4200, "NAME": "강원도"},
    {"CODE": 4300, "NAME": "충청북도"},  {"CODE": 4400, "NAME": "충청남도"},
    {"CODE": 4500, "NAME": "전라북도"},  {"CODE": 4600, "NAME": "전라남도"},
    {"CODE": 4700, "NAME": "경상북도"},  {"CODE": 4800, "NAME": "경상남도"},
    {"CODE": 4900, "NAME": "제주특별자치도"}
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

def get_sgg_city_codes(city_code, city_name):
    """해당 시도 하위의 자치구/시군 코드 목록을 받아옵니다."""
    payload = {
        "electionId": "0020260603",
        "secondMenuId": "CPRI03",
        "electionCode": ELEC_CODE,
        "cityCode": str(city_code),
        "statementId": f"CPRI03_#{ELEC_CODE}",
        "dateCode": "0"
    }
    try:
        response = requests.post(URL_SGG_LIST, headers=HEADERS, data=payload, timeout=15)
        response.raise_for_status()
        # 선관위 리턴 구조에서 jsonResult 또는 내부 리스트 추출
        res_data = response.json()
        sgg_items = res_data.get("jsonResult", {}).get("data", []) if isinstance(res_data, dict) else []
        if not sgg_items and isinstance(res_data, list):
            sgg_items = res_data
            
        return sgg_items
    except Exception as e:
        print(f"🔴 [{city_name}] 시군구 목록 코드 조회 실패: {e}")
        return []

def main():
    output_dir = os.path.join("data", "jibang", "9")
    os.makedirs(output_dir, exist_ok=True)

    print(f"🔄 제9회 지선 [시군구청장(코드:{ELEC_CODE})] 2단계 레이어 수집을 시작합니다.")

    for city in CITIES:
        city_code_str = str(city["CODE"])
        city_name_str = city["NAME"]

        print(f"\n=======================================================")
        print(f"🔎 [{city_name_str}] 하위 시군구 목록을 먼저 확보합니다.")
        sgg_list = get_sgg_city_codes(city_code_str, city_name_str)
        
        if not sgg_list:
            print(f"⚠️ [{city_name_str}] 조회된 하위 자치구/시군이 없거나 실패하여 건너뜁니다.")
            continue

        print(f"📊 [{city_name_str}] 총 {len(sgg_list)}개의 자치구/시군 감지 완료.")
        
        # 각 시도별 수집된 개별 시군구의 후보자 데이터를 하나로 모으기 위한 그릇
        city_combined_candidates = {}

        for sgg in sgg_list:
            # 선관위 selectbox 반환 필드명 매핑 (일반적으로 CODE / NAME 구조)
            sgg_code = str(sgg.get("CODE", ""))
            sgg_name = str(sgg.get("NAME", "")).strip()

            if not sgg_code or sgg_name == "선택": 
                continue

            print(f"📡 ├─ [{sgg_name} (코드:{sgg_code})] 후보자 명부 수집 중...")

            payload = {
                "electionId": "0020260603",
                "secondMenuId": "CPRI03",
                "electionCode": ELEC_CODE,
                "cityCode": city_code_str,
                "statementId": f"CPRI03_#{ELEC_CODE}",
                "dateCode": "0",
                "sggCityCode": sgg_code  # 🚨 요구하신 핵심 인자 동적 매핑
            }

            success = False
            attempt = 1

            while not success and attempt <= MAX_RETRIES:
                try:
                    response = requests.post(URL_CANDIDATE, headers=HEADERS, data=payload, timeout=15)
                    response.raise_for_status()
                    raw_json = response.json()

                    # 시군구 명을 키값으로 하여 데이터를 합산 저장 구조화합니다.
                    city_combined_candidates[sgg_name] = raw_json
                    success = True

                except Exception as e:
                    print(f"	⚠️ [{sgg_name}] 에러 발생: {e}. {attempt}/{MAX_RETRIES}회차 재시도 대기...")
                    attempt += 1
                    time.sleep(10)

            if not success:
                print(f"	🔴 [{sgg_name}] 최종 수집 실패.")

            # 선관위 DDoS 방화벽 타겟팅 우회를 위한 짧은 텀 대기
            random_delay = random.uniform(MIN_DELAY, MAX_DELAY)
            sleep_with_dots(random_delay)

        # 🚨 [안정적인 저장] 시도 단위 파일(예: candidate_ori_4_4100.json) 하나로 통합 저장하여
        # 파일 개수가 너무 파편화되어 깃허브 액션 트래픽이 무거워지는 현상을 예방합니다.
        if city_combined_candidates:
            file_name = f"candidate_ori_{ELEC_CODE}_{city_code_str}.json"
            file_path = os.path.join(output_dir, file_name)
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(city_combined_candidates, f, ensure_ascii=False, indent=4)
            print(f"🟢 [{city_name_str}] 통합 시군구청장 후보자 파일 빌드 성공 -> {file_name}")

    print("\n✨ 모든 시도의 시군구청장 후보자 2단계 통합 원본 수집이 종료되었습니다.")

if __name__ == "__main__":
    main()
