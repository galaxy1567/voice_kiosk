import serial
import time


PORT = 'COM3'
BAUD = 9600
TIMEOUT = 1

al_list = [[163, 77, 233, 16],[106, 156, 241, 91]]

def main():

    ser = serial.Serial(PORT, BAUD, timeout=TIMEOUT)
    time.sleep(2)

    print(f"Listening on {PORT} @ {BAUD}bps...")

    try:
        while True:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if not line:
                continue

            parts = line.split()
            try:
                uid = [int(x) for x in parts]
                print("Detected UID (decimal):", uid)
                if uid == al_list[0]:
                    print("땅콩알러지")
                elif uid == al_list[1]:
                    print("육류 알러지")
                break
            except ValueError:
                print("Invalid data:", line)
    except KeyboardInterrupt:
        print("종료합니다.")
    finally:
        ser.close()

if __name__ == '__main__':
    main()
