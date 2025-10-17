import time
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pytesseract
from PIL import Image, ImageEnhance

# ==============================================================================
# ⬇️ 1. 사용자 설정 영역: 이 부분을 직접 채워주셔야 합니다. ⬇️
# ==============================================================================

# [필수] 여러 경기가 있는 예매 페이지 URL을 입력하세요.
TICKET_PAGE_URL = "https://tickets.interpark.com/special/sports/promotion/41"

# [필수] 티켓팅 시작 시간을 정확하게 입력하세요. (24시간 기준)
TARGET_TIME = datetime.datetime(2025, 10, 16, 22, 51, 0)

# [필수] 클릭하려는 특정 버튼의 XPath 주소를 입력하세요.
MY_BUTTON_XPATH = "//*[@id='__next']/div/div/div/div[2]/div[3]/ul/li[3]/div/div[2]/button"

# [필수] Tesseract-OCR을 설치한 경로를 입력하세요.
TESSERACT_PATH = r'C:\Tesseract_OCR\tesseract.exe'

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

    # 보안문자 자동 완성
    solve_captcha(driver)


def solve_captcha(driver):
    """보안문자 이미지를 인식하여 자동으로 입력합니다."""
    print("\n--- 보안문자 처리 시작 ---")
    
    captcha_image_xpath = "//*[@id='imgCaptcha']"
    captcha_input_id = "txtCaptcha"
    confirm_button_xpath = "//*[@id='divRecaptcha']/div[1]/div[1]/a[1]"
    
    # 먼저 보안문자가 있는지 확인
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, captcha_image_xpath))
        )
        print("✅ 보안문자 화면 감지!")
    except Exception:
        print("🟡 보안문자가 없습니다. 다음 단계로 진행합니다.")
        return

    # 보안문자 입력에 성공할 때까지 최대 5회 시도
    for attempt in range(5):
        try:
            print(f"\n({attempt + 1}/5) 보안문자 인식 시도 중...")
            
            # 1. 보안문자 이미지 요소 찾기
            image_element = driver.find_element(By.XPATH, captcha_image_xpath)
            
            # 2. 이미지 스크린샷 및 저장
            image_element.screenshot('captcha.png')
            print("   > 이미지 캡처 완료")
            
            # 3. 이미지 전처리
            image = Image.open('captcha.png')
            
            # 크기 확대 (OCR 정확도 향상)
            image = image.resize((image.width * 2, image.height * 2), Image.LANCZOS)
            
            # 흑백 변환
            image = image.convert('L')
            
            # 대비 강화
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2)
            
            # 임계값 처리 (더 선명하게)
            threshold = 128
            image = image.point(lambda p: p > threshold and 255)
            
            image.save('captcha_processed.png')  # 전처리된 이미지 저장 (디버깅용)
            
            # 4. Tesseract OCR로 텍스트 추출
            # 숫자만 있으면 'eng' 또는 'kor+eng', 한글이면 'kor'
            text = pytesseract.image_to_string(
                image, 
                lang='eng',  # 또는 'kor' 또는 'kor+eng'
                config='--psm 7 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            ).strip()
            
            # 공백 제거
            text = text.replace(' ', '').replace('\n', '')
            
            print(f"   > 인식된 텍스트: '{text}' (길이: {len(text)})")
            
            # 텍스트가 비어있거나 너무 짧으면 건너뛰기
            if not text or len(text) < 3:
                print("   > 텍스트가 너무 짧습니다. 재시도...")
                raise Exception("텍스트 인식 실패")
            
            # 5. 입력창에 텍스트 입력
            input_box = driver.find_element(By.ID, captcha_input_id)
            input_box.clear()
            time.sleep(0.3)
            input_box.send_keys(text)
            print(f"   > 입력 완료: '{text}'")
            
            time.sleep(0.5)
            
            # 6. 확인 버튼 클릭
            confirm_button = driver.find_element(By.XPATH, confirm_button_xpath)
            confirm_button.click()
            print("   > 확인 버튼 클릭")
            
            # 7. 성공 여부 판단
            time.sleep(2)  # 페이지 반응 대기
            
            # 보안문자 입력창이 사라졌는지 확인
            try:
                driver.find_element(By.XPATH, captcha_image_xpath)
                # 아직 보안문자 화면이 있으면 실패
                print("   > ❌ 인식 실패. 재시도...")
                
                # 새로고침 버튼 클릭 (있다면)
                try:
                    refresh_button = driver.find_element(By.XPATH, "//*[@id='imgCaptcha']")
                    refresh_button.click()
                except:
                    pass
                    
            except Exception:
                # 보안문자 화면이 사라졌으면 성공
                print("   > ✅ 보안문자 입력 성공!")
                return

        except Exception as e:
            print(f"   > ❌ 오류 발생: {e}")
            
            # 새로고침 버튼 클릭 시도
            try:
                time.sleep(1)
                # 보안문자 새로고침 (이미지를 다시 클릭하면 새로고침되는 경우가 많음)
                image_element = driver.find_element(By.XPATH, captcha_image_xpath)
                image_element.click()
            except:
                pass
            
            time.sleep(1)
    
    print("\n🔴 보안문자 자동 입력에 최종 실패했습니다.")
    print("🔔 수동으로 보안문자를 입력해주세요!")
    
    # 수동 입력 대기
    input("\n보안문자를 직접 입력하고 확인을 누른 후, Enter 키를 눌러주세요...")


if __name__ == "__main__":
    run_macro()