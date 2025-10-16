import time
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pytesseract
from PIL import Image

# ==============================================================================
# ⬇️ 1. 사용자 설정 영역: 이 부분을 직접 채워주셔야 합니다. ⬇️
# ==============================================================================

# [필수] 여러 경기가 있는 예매 페이지 URL을 입력하세요.
TICKET_PAGE_URL = "https://tickets.interpark.com/special/sports/promotion/41"

# [필수] 티켓팅 시작 시간을 정확하게 입력하세요. (24시간 기준)
TARGET_TIME = datetime.datetime(2025, 10, 16, 22, 10, 0) # 예시

# [필수] 클릭하려는 특정 버튼의 XPath 주소를 입력하세요.
MY_BUTTON_XPATH = "//*[@id='__next']/div/div/div/div[2]/div[3]/ul/li[3]/div/div[2]/button"  # 예시: 3번째 경기

# [필수] Tesseract-OCR을 설치한 경로를 입력하세요.
# 예시: r'C:\Program Files\Tesseract-OCR\tesseract.exe'
TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# ==============================================================================
# ⬆️ 사용자 설정 영역 끝 ⬆️
# ==============================================================================


def run_macro():
    """셀레니움 티켓팅 매크로를 실행합니다."""
    
    # Tesseract 경로 설정
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
    
    driver = None
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
        
        print("="*50)
        print("🎟️ 인터파크 티켓팅 매크로를 시작합니다.")
        print("="*50)
        
        driver.get("https://accounts.yanolja.com/?clientId=ticket-pc&postProc=FULLSCREEN&origin=https%3A%2F%2Fnol.interpark.com%2Fticket&service=interpark-ticket&redirect=https%3A%2F%2Faccounts.interpark.com%2Flogin%2Fsuccess%2Fnol%3FpostProc%3DFULLSCREEN%26origin%3Dhttps%253A%252F%252Fnol.interpark.com%252Fticket&nol_device_id=176059140467330604")
        
        input("✅ 브라우저에서 로그인을 완료하신 후, 이 터미널로 돌아와 Enter 키를 누르세요...")
        
        print("로그인 완료. 예매 페이지로 이동합니다.")
        driver.get(TICKET_PAGE_URL)
        print(f"예매 페이지로 이동 완료: {TICKET_PAGE_URL}")
        
        wait_until_ready()

        print("\n🚀 예매 시작 10초 전! 예매 버튼이 활성화되기를 기다립니다...")

        reaction_start_time = time.monotonic()

        while True:
            try:
                book_button = WebDriverWait(driver, 0.5).until(
                    EC.element_to_be_clickable((By.XPATH, MY_BUTTON_XPATH)) 
                )
                
                reaction_end_time = time.monotonic()
                reaction_time = reaction_end_time - reaction_start_time
                print(f"\n✅ 예매 버튼 활성화 감지! 즉시 클릭 실행! (반응 시간: {reaction_time:.4f}초)")

                book_button.click()
                break
            except Exception:
                driver.refresh()

        handle_booking_process(driver)

        print("\n🎉 예매 프로세스 완료! 이제 브라우저에서 다음 단계를 진행하세요.")
        print("10분 후 브라우저가 자동으로 종료됩니다.")
        time.sleep(600)

    except Exception as e:
        print(f"\n🔴 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            print("\n브라우저를 닫습니다.")
            driver.quit()


def wait_until_ready():
    """지정된 예매 시작 10초 전까지 대기하는 함수입니다 (로컬 시간 기준)."""
    print(f"\n⏰ 목표 시간: {TARGET_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    
    while True:
        now = datetime.datetime.now()
        remaining_time = (TARGET_TIME - now).total_seconds()
        
        if remaining_time <= 10:
            break
        
        if remaining_time < 1:
            print(f"\r⏳ 예매 시작까지 {remaining_time:.3f}초 남았습니다...", end="")
            time.sleep(0.001)
        else:
            print(f"\r⏳ 예매 시작까지 {remaining_time:,.2f}초 남았습니다...", end="")
            time.sleep(0.1)


def handle_booking_process(driver):
    """'예매하기' 클릭 후 새 창 전환, 대기열, 팝업, 보안문자를 순서대로 처리합니다."""
    print("\n--- 예매 창 처리 시작 ---")
    
    try:
        original_window = driver.current_window_handle
        WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
        
        for window_handle in driver.window_handles:
            if window_handle != original_window:
                driver.switch_to.window(window_handle)
                break
        print("✅ 예매 창으로 전환 성공.")
    except Exception as e:
        print(f"🔴 새 창으로 전환하는 데 실패했습니다: {e}")
        return

    # 대기열 처리
    try:
        queue_element_xpath = "//*[@id='ifrmWait']"
        print("⏳ 대기열 페이지 확인 중...")
        WebDriverWait(driver, 600).until(
            EC.invisibility_of_element_located((By.XPATH, queue_element_xpath))
        )
        print("✅ 대기열 통과!")
    except Exception:
        print("🟡 대기열이 없거나 이미 통과했습니다.")

    # 팝업 공지 닫기
    try:
        popup_iframe_name = "ifrmSeat"
        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, popup_iframe_name))
        )
        print("✅ 공지 팝업 iframe으로 전환 성공.")

        close_button_xpath = "//*[@id='divBookNoticeLayer']/div[2]/div[1]/a"
        close_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, close_button_xpath))
        )
        close_button.click()
        print("✅ 팝업 공지 '닫기' 버튼 클릭 성공.")
    except Exception:
        print("🟡 팝업 공지가 없거나 이미 닫혔습니다.")

    # --- [추가] 보안문자 자동 완성 ---
    solve_captcha(driver)


def solve_captcha(driver):
    """보안문자 이미지를 인식하여 자동으로 입력합니다."""
    print("\n--- 보안문자 처리 시작 ---")
    
    # ⭐️ 중요: 실제 보안문자 관련 요소들의 XPath 또는 ID로 수정해야 합니다.
    captcha_image_xpath = "//*[@id='imgCaptcha']" # 예시
    captcha_input_id = "txtCaptcha" # 예시
    confirm_button_xpath = "//*[@id='btnNext']" # 예시

    # 보안문자 입력에 성공할 때까지 최대 5회 시도
    for attempt in range(5):
        try:
            print(f"({attempt + 1}/5) 보안문자 인식 시도...")
            
            # 1. 보안문자 이미지 요소 찾기
            image_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, captcha_image_xpath))
            )
            
            # 2. 이미지 스크린샷 및 저장
            image_element.screenshot('captcha.png')
            
            # 3. 이미지 처리 (흑백 변환 및 대비 강화)
            image = Image.open('captcha.png')
            image = image.convert('L') # 흑백으로 변환
            
            # 4. Tesseract OCR로 텍스트 추출
            # lang='kor' 또는 'eng' 등 사이트에 맞게 설정
            text = pytesseract.image_to_string(image, lang='kor', config='--psm 6').strip()
            print(f"   > 인식된 텍스트: {text}")

            # 5. 입력창에 텍스트 입력 및 확인 버튼 클릭
            input_box = driver.find_element(By.ID, captcha_input_id)
            input_box.clear()
            input_box.send_keys(text)
            
            driver.find_element(By.XPATH, confirm_button_xpath).click()
            
            # 성공 여부 판단 (예: 다음 페이지로 넘어갔는지, 오류 메시지가 없는지)
            # 여기서는 다음 단계(좌석 선택)의 iframe이 나타나는 것으로 성공을 가정
            time.sleep(1) # 페이지 전환 대기
            WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.NAME, "ifrmSeatDetail")))
            
            print("✅ 보안문자 입력 성공!")
            return # 성공 시 함수 종료

        except Exception as e:
            print(f"   > 보안문자 처리 실패. 새로고침 후 재시도... 오류: {e}")
            try:
                # 보안문자 새로고침 버튼이 있다면 클릭, 없다면 페이지 새로고침
                driver.find_element(By.XPATH, "//*[@id='btnRefresh']").click() # 예시
            except:
                driver.refresh()
            time.sleep(1)
            
    print("🔴 보안문자 자동 입력에 최종 실패했습니다. 수동으로 진행해주세요.")


if __name__ == "__main__":
    run_macro()