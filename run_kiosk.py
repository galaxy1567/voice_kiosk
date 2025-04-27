from kiosk_module import main

def main_loop():
    while True:
        print("사용자 음성 대기중")
        recognized_text = main()

        if recognized_text is None:
            print("인식된 텍스트가 없습니다. 다시 대기합니다.\n")
            continue

        if "종료" in recognized_text or "끝내자" in recognized_text:
            print("종료 명령어 감지. 프로그램을 종료합니다.")
            break

        print("다시 대기 상태로 돌아갑니다.")

if __name__ == "__main__":
    main_loop()