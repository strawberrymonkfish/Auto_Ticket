import time
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ==============================================================================
# ⬇️ 1. 사용자 설정 영역: 이 부분을 직접 채워주셔야 합니다. ⬇️
# ==============================================================================

# [필수] 여러 경기가 있는 예매 페이지 URL을 입력하세요.
TICKET_PAGE_URL = "https://tickets.interpark.com/special/sports/promotion/41"

# [필수] 티켓팅 시작 시간을 정확하게 입력하세요. (24시간 기준)
TARGET_TIME = datetime.datetime(2025, 10, 16, 20, 40, 40)  # 예시: 오후 2시 30분

# [필수] 클릭하려는 특정 버튼의 XPath 주소를 입력하세요.
MY_BUTTON_XPATH = "//*[@id='__next']/div/div/div/div[2]/div[3]/ul/li[3]/div/div[2]/button"  # 예시: 3번째 경기

# ==============================================================================
# ⬆️ 사용자 설정 영역 끝 ⬆️
# ==============================================================================


def run_macro():
    """셀레니움 티켓팅 매크로를 실행합니다."""
    
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

        # 반응 시간 측정을 위해 시작 시간 기록
        reaction_start_time = time.monotonic()

        while True:
            try:
                book_button = WebDriverWait(driver, 0.5).until(
                    EC.element_to_be_clickable((By.XPATH, MY_BUTTON_XPATH)) 
                )
                
                # 반응 시간 측정 및 출력
                reaction_end_time = time.monotonic()
                reaction_time = reaction_end_time - reaction_start_time
                print(f"\n✅ 예매 버튼 활성화 감지! 즉시 클릭 실행! (반응 시간: {reaction_time:.4f}초)")

                book_button.click()
                break  # 클릭 성공 시 루프 탈출
            except Exception:
                driver.refresh()

        handle_popup_window(driver)

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
        
        # 남은 시간이 1초 이하일 때는 더 정밀하게 대기
        if remaining_time < 1:
            print(f"\r⏳ 예매 시작까지 {remaining_time:.3f}초 남았습니다...", end="")
            time.sleep(0.001)
        else:
            print(f"\r⏳ 예매 시작까지 {remaining_time:,.2f}초 남았습니다...", end="")
            time.sleep(0.1)


def handle_popup_window(driver):
    """'예매하기' 클릭 후 열리는 새 창으로 전환하고 대기열 통과 후 팝업을 닫습니다."""
    print("\n--- 예매 창 처리 시작 ---")
    
    # 1. 새로 열린 예매 창으로 제어권 전환
    try:
        original_window = driver.current_window_handle
        WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))  # 새 창이 열릴 때까지 대기
        
        for window_handle in driver.window_handles:
            if window_handle != original_window:
                driver.switch_to.window(window_handle)
                break
        print("✅ 예매 창으로 전환 성공.")
    except Exception as e:
        print(f"🔴 새 창으로 전환하는 데 실패했습니다: {e}")
        return  # 전환 실패 시 함수 종료

    # 2. 대기열 또는 팝업 감지 (동시에 체크)
    wait_for_queue_or_popup(driver)


def wait_for_queue_or_popup(driver):
    """대기열이 있으면 통과를 기다리고, 없으면 바로 팝업을 닫습니다."""
    
    queue_text_xpath = "//*[@id='__next']/div/div/div/div[2]/div[1]/div[1]/h3"
    popup_close_xpath = "//*[@id='divBookNoticeLayer']/div[2]/div[1]/a"
    
    max_wait_time = 600  # 최대 10분
    start_time = time.time()
    
    print("⏳ 대기열 또는 팝업을 감지하는 중...")
    
    # 1단계: 대기열이 있는지, 팝업이 바로 나타나는지 확인 (최대 5초)
    queue_detected = False
    popup_detected = False
    
    while time.time() - start_time < 5:
        # 대기열 체크
        try:
            queue_element = driver.find_element(By.XPATH, queue_text_xpath)
            if queue_element.is_displayed():
                print("\n✅ 대기열이 감지되었습니다!")
                queue_detected = True
                break
        except Exception:
            pass
        
        # 팝업 체크
        try:
            popup_element = driver.find_element(By.XPATH, popup_close_xpath)
            if popup_element.is_displayed():
                print("\n✅ 대기열 없이 바로 팝업이 나타났습니다!")
                popup_detected = True
                break
        except Exception:
            pass
        
        elapsed = int(time.time() - start_time)
        print(f"\r⏳ 페이지 로딩 중... ({elapsed}초)", end="", flush=True)
        time.sleep(0.1)
    
    # 2단계: 대기열이 감지된 경우 - 대기열 통과 대기
    if queue_detected:
        print("⏳ 대기열이 사라질 때까지 대기 중...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                queue_element = driver.find_element(By.XPATH, queue_text_xpath)
                
                if queue_element.is_displayed():
                    elapsed = int(time.time() - start_time)
                    print(f"\r⏳ 대기열 대기 중... ({elapsed}초 경과)", end="", flush=True)
                    time.sleep(0.1)
                else:
                    print("\n✅ 대기열 통과!")
                    time.sleep(0.1)
                    break
            except Exception:
                print("\n✅ 대기열 통과!")
                time.sleep(0.1)
                break
    
    # 3단계: 팝업 닫기 시도
    print("🔍 팝업 닫기 버튼을 찾는 중...")
    
    try:
        # iframe 전환 시도
        try:
            popup_iframe_name = "ifrmSeat"
            WebDriverWait(driver, 3).until(
                EC.frame_to_be_available_and_switch_to_it((By.NAME, popup_iframe_name))
            )
            print("✅ 공지 팝업 iframe으로 전환 성공.")
        except Exception:
            print("🟡 iframe이 없거나 전환 불필요.")
        
        # 팝업 닫기 버튼 클릭
        close_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, popup_close_xpath))
        )
        close_button.click()
        print("✅ 팝업 공지 '닫기' 버튼 클릭 성공.")
        
    except Exception as e:
        print(f"🟡 팝업 닫기 버튼을 찾지 못했습니다: {e}")
        print("   팝업이 없거나 수동으로 닫아주세요.")


if __name__ == "__main__":
    run_macro()