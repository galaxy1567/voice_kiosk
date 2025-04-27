from kiosk_module import main

if __name__ == "__main__":
    print("키오스크 대기 시작")

    while True:
        recognized_text = main()

        if recognized_text is None:
            continue

        if "종료" in recognized_text or "끝내자" in recognized_text:
            print("'종료' 명령어 감지. 프로그램을 종료합니다.")
            break

        print("다시 대기합니다\n")