REDMINE TO YONA
===============

# 기존 redmine setting 변경
  * 모든 로드맵 (version) 의 공유설정을 "공유없음" 으로 변경합니다.

# 설정
config.yml 파일에서 redmine, yona의 url, token을 설정하세요.

	pip install -r requirements.txt


# 테스트
	$ pytest test
## 테스트 시 표준출력 포함
	$ python -m pytest test/ -s
