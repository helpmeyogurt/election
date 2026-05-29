import os
import json
import requests
from datetime import datetime

# 1. 고정 설정 및 경로 지정
TARGET_URL = "https://info.nec.go.kr/m/electioninfo/electionInfo_report.json"
FILE_PATH = "election/data/jibang/9/jibang_vote_9.js"

# 선관위 보안 차단 회피를 위한 최소한의 헤더 설정
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Origin": "https://info.nec.go.kr",
    "Referer": "https://info.nec.go.kr/m/main.xhtml"
}

def get_current_time_code():
    """현재 시각을 기반으로 선관위 timeCode 생성 (예: 오전 8시 -> '08')"""
    current_hour = datetime.now().hour
    # 오전 6시부터 오후 6시(18시)까지만 유효한 코드로 제한 보정
    if current_hour < 6:
        return "06"
    elif current_hour > 18:
        return "18"
    return f"{current_hour:02d}"

def fetch_nec_data(time_code):
    """선관위 API로부터 특정 시간대 투표율 데이터 추출"""
    payload = {
        "electionId": "0020260603",
        "secondMenuId": "VCAP01",
        "cityCode": "0",
        "dateCode": "1",
        "timeCode": time_code,
        "statementId": "VCAP01_#1",
        "prevoteDate1": "20260529",
        "prevoteDate2": "20260530"
    }
    
    try:
        # 선관위는 일반 JSON POST가 아닌 Form-Data 형식을 선호하므로 data= 파라미터 사용
        response = requests.post(TARGET_URL, headers=HEADERS, data=payload, timeout=10)
        response.raise_for_status()
        
        # 선관위 리턴 데이터 파싱 (구조가 유동적일 수 있으므로 json 안전 파싱)
        raw_json = response.json()
        
        # ⚠️ 중요: 선관위 JSON 내부의 실제 데이터 배열 필드명을 확인하셔야 합니다.
        # 일반적인 선관위 스펙에 맞춰 json 응답 내부 객체 추출 프로세스 배치
        # 만약 응답 바디 전체가 바로 배열 리스트라면 `return raw_json` 처리
        if "jsonResult" in raw_json and "model" in raw_json["jsonResult"]:
            return raw_json["jsonResult"]["model"]
        return raw_json
        
    except Exception as e:
        print(f"[{datetime.now()}] 선관위 API 통신 실패 (시간코드: {time_code}): {e}")
        return None

def load_existing_js_file():
    """기존에 저장된 .js 파일 로드 및 자바스크립트 전역 변수 기호 탈취 파싱"""
    if not os.path.exists(FILE_PATH):
        # 파일이 없을 경우 사장님이 쓰시던 초기 기본 뼈대 구조 생성 리턴
        return [{"0": [], "1": [], "2": []}]
        
    try:
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
            
            # 프론트엔드 연동용 JS 파일 특성상 앞뒤로 변수명이나 괄호가 붙어있을 수 있으므로 정제
            # 만약 순수 JSON 데이터가 아니라 자바스크립트 변수문 형식이면 정규식 처리가 필요할 수 있습니다.
            if content.startswith("[") or content.startswith("{"):
                return json.loads(content)
            else:
                # 'var data = [...];' 형태 방어 대책
                json_string = content[content.find("["):content.rfind("]")+1]
                return json.loads(json_string)
    except Exception as e:
        print(f"기존 파일 읽기 실패 (새 파일로 대체합니다): {e}")
        return [{"0": [], "1": [], "2": []}]

def save_js_file(data):
    """추출 합산된 파이썬 객체를 다시 프론트엔드 연동용 .js 포맷 파일로 변환 저장"""
    # 폴더가 없을 경우 자동 생성
    os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)
    
    try:
        with open(FILE_PATH, "w", encoding="utf-8") as f:
            # 사장님 차트 스크립트가 그대로 파싱할 수 있게 깔끔하게 들여쓰기 처리
            json_content = json.dumps(data, ensure_ascii=False, indent=2)
            f.write(json_content)
        print(f"[{datetime.now()}] 데이터 병합 및 자바스크립트 파일 업데이트 완료!")
    except Exception as e:
        print(f"파일 쓰기 실패: {e}")

def main():
    time_code = get_current_time_code()
    print(f"[{datetime.now()}] 투표율 데이터 수집 프로세스 가동 (타겟 시간: {time_code}시)")
    
    # 1. 새 데이터 수집
    new_hour_data = fetch_nec_data(time_code)
    if not new_hour_data or not isinstance(new_hour_data, list):
        print("유효한 데이터 리스트를 수집하지 못해 프로세스를 종료합니다.")
        return
        
    # 2. 기존 파일의 데이터 가져오기
    current_db = load_existing_js_file()
    
    # 3. 데이터 병합 자동화 (중복 수집 방어)
    # 현재 수집한 타겟 시간대 데이터가 이미 기존 리스트에 존재하는지 검증 처리
    # (각 시간대의 '서울특별시' 투표율 값을 비교 기준으로 판독)
    try:
        new_seoul_tuyul = next(item["TPR_SU"] for item in new_hour_data if item.get("WIWID") == 1100 or item.get("WIWNAME") == "서울특별시")
    except StopIteration:
        new_seoul_tuyul = None

    is_duplicated = False
    for existing_hour_list in current_db[0]["0"]:
        try:
            ex_seoul_tuyul = next(item["TPR_SU"] for item in existing_hour_list if item.get("WIWID") == 1100 or item.get("WIWNAME") == "서울특별시")
            if ex_seoul_tuyul == new_seoul_tuyul:
                is_duplicated = True
                break
        except StopIteration:
            continue

    if is_duplicated:
        print(f"{time_code}시 데이터는 이미 병합되어 있습니다. 추가하지 않습니다.")
        return

    # 중복이 아니면 사장님의 "0"번 키 배열 내부 차트 라인으로 새 배열 밀어넣기
    current_db[0]["0"].append(new_hour_data)
    
    # 4. 최종 저장
    save_js_file(current_db)

if __name__ == "__main__":
    main()
