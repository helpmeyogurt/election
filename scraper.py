import json
import os
import requests

# 1. 선관위 API 주소 및 요청 파라미터 설정
URL = "https://info.nec.go.kr/m/electioninfo/electionInfo_report.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Referer": "https://info.nec.go.kr/",
}

DATA = {
    "electionId": "0000000000",
    "electionType": "4",
    "sgDivMenuId": "VCCP09",
    "electionName": "20220601",
    "electionCode": "3",
    "electionCodeId": "3",
    "electionNameSgType": "1",
    "cityCode": "1100",
    "oldElectionType": "1",
    "statementId": "VCCP09_#3",
}


def fetch_and_save():
    try:
        # 2. POST 요청 보내기
        print("선관위 서버에 데이터를 요청 중입니다...")
        response = requests.post(URL, headers=HEADERS, data=DATA)

        # 상태 코드 확인 (200이 아니면 에러 발생)
        response.raise_for_status()

        # 3. JSON 데이터 파싱
        # 선관위 응답이 이미 JSON 형태라면 .json()을 사용하고,
        # 만약 텍스트 내부의 특정 정제가 필요하다면 내부 로직을 추가해야 합니다.
        json_data = response.json()

        # 4. 파일로 저장
        output_dir = "data"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "election_result.json")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)

        print(f"성공적으로 데이터를 저장했습니다: {output_path}")

    except requests.exceptions.RequestException as e:
        print(f"네트워크 요청 중 에러 발생: {e}")
    except json.JSONDecodeError:
        print(
            "JSON 파싱 실패. 응답 데이터가 JSON 형식이 아닐 수 있습니다. (텍스트 확인 필요)"
        )
        print(response.text[:500])  # 에러 로그 확인용 앞부분 출력


if __name__ == "__main__":
    fetch_and_save()