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
TARGET_TIME = datetime.datetime(2025, 10, 17, 14, 51, 40)

# [필수] 클릭하려는 특정 버튼의 XPath 주소를 입력하세요.
MY_BUTTON_XPATH = "//*[@id='__next']/div/div/div/div[2]/div[3]/ul/li[3]/div/div[2]/button"

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
        WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
        
        for window_handle in driver.window_handles:
            if window_handle != original_window:
                driver.switch_to.window(window_handle)
                break
        print("✅ 예매 창으로 전환 성공.")
    except Exception as e:
        print(f"🔴 새 창으로 전환하는 데 실패했습니다: {e}")
        return

    # 2. 대기열 또는 팝업 감지 (동시에 체크)
    wait_for_queue_or_popup(driver)
    
    # 3. 보안문자 수동 입력 대기
    handle_captcha_manual(driver)
    
    # 4. 좌석 선택 자동화
    auto_select_seats(driver)


def wait_for_queue_or_popup(driver):
    """대기열이 있으면 통과를 기다리고, 없으면 바로 팝업을 닫습니다."""
    
    queue_text_xpath = "//*[@id='__next']/div/div/div/div[2]/div[1]/div[1]/h3"
    popup_close_xpath = "//*[@id='divBookNoticeLayer']/div[2]/div[1]/a"
    
    max_wait_time = 600
    start_time = time.time()
    
    print("⏳ 대기열 또는 팝업을 감지하는 중...")
    
    # 1단계: 대기열이 있는지, 팝업이 바로 나타나는지 확인
    queue_detected = False
    
    while time.time() - start_time < 3:
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
                    time.sleep(0.5)
                    break
            except Exception:
                print("\n✅ 대기열 통과!")
                time.sleep(0.5)
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
        time.sleep(1)
        
    except Exception as e:
        print(f"🟡 팝업 닫기 버튼을 찾지 못했습니다: {e}")


def handle_captcha_manual(driver):
    """보안문자 수동 입력을 기다리고, 완료되면 자동으로 다음 단계 진행"""
    print("\n--- 보안문자 확인 중 ---")
    
    # 보안문자 관련 요소들
    captcha_selectors = [
        (By.XPATH, "//*[@id='imgCaptcha']"),
        (By.ID, "imgCaptcha"),
        (By.XPATH, "//*[contains(@id, 'Captcha') or contains(@id, 'captcha')]"),
    ]
    
    captcha_found = False
    
    # 보안문자가 있는지 확인
    for selector_type, selector_value in captcha_selectors:
        try:
            captcha_element = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((selector_type, selector_value))
            )
            if captcha_element.is_displayed():
                print(f"✅ 보안문자 발견!")
                captcha_found = True
                break
        except Exception:
            continue
    
    if not captcha_found:
        print("🟡 보안문자가 없습니다. 다음 단계로 진행합니다.")
        return
    
    # 보안문자 발견 - 수동 입력 안내
    print("\n" + "="*60)
    print("🔐 보안문자가 나타났습니다!")
    print("="*60)
    print("📌 보안문자를 직접 입력하고 확인 버튼을 눌러주세요.")
    print("📌 매크로가 자동으로 다음 단계를 감지합니다...")
    print("="*60)
    
    # 알림음 재생
    try:
        import winsound
        for _ in range(3):
            winsound.Beep(1000, 300)
            time.sleep(0.2)
    except:
        pass
    
    # 보안문자가 사라질 때까지 대기 (사용자가 입력 완료할 때까지)
    print("\n⏳ 보안문자 입력을 기다리는 중...")
    
    max_wait = 300  # 최대 5분 대기
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            # 보안문자 이미지가 아직 있는지 확인
            captcha_still_exists = False
            for selector_type, selector_value in captcha_selectors:
                try:
                    element = driver.find_element(selector_type, selector_value)
                    if element.is_displayed():
                        captcha_still_exists = True
                        break
                except:
                    continue
            
            if not captcha_still_exists:
                print("\n✅ 보안문자 통과 감지! 다음 단계로 진행합니다.")
                time.sleep(1)
                return
            
            elapsed = int(time.time() - start_time)
            print(f"\r⏳ 대기 중... ({elapsed}초)", end="", flush=True)
            time.sleep(0.5)
            
        except Exception:
            print("\n✅ 보안문자 통과!")
            return
    
    print("\n⚠️ 보안문자 대기 시간 초과. 수동으로 진행해주세요.")


def auto_select_seats(driver):
    """좌석 자동 선택 및 예매 완료"""
    print("\n--- 좌석 선택 자동화 시작 ---")
    
    try:
        # 좌석 선택 iframe으로 전환 (필요한 경우)
        try:
            seat_iframe = "ifrmSeatDetail"
            WebDriverWait(driver, 5).until(
                EC.frame_to_be_available_and_switch_to_it((By.NAME, seat_iframe))
            )
            print("✅ 좌석 선택 iframe으로 전환 성공.")
        except Exception:
            print("🟡 좌석 선택 iframe 없음 또는 이미 전환됨.")
        
        # 1. 잔여석 확인 및 선택 가능한 좌석 찾기
        print("🔍 선택 가능한 좌석을 찾는 중...")
        
        # 좌석 선택 가능한 요소들 (실제 XPath는 페이지 구조에 맞게 수정 필요)
        seat_selectors = [
            "//map[@name='imgMap']//area[@class='map']",  # 클릭 가능한 구역
            "//td[contains(@class, 'seat') and not(contains(@class, 'disable'))]",  # 좌석 td
            "//*[contains(@onclick, 'SelectSeat')]",  # SelectSeat 함수가 있는 요소
        ]
        
        seat_found = False
        for selector in seat_selectors:
            try:
                seats = driver.find_elements(By.XPATH, selector)
                if seats:
                    print(f"✅ {len(seats)}개의 선택 가능한 좌석 발견!")
                    # 첫 번째 좌석 클릭
                    seats[0].click()
                    print("✅ 첫 번째 좌석 클릭 완료!")
                    seat_found = True
                    time.sleep(1)
                    break
            except Exception as e:
                continue
        
        if not seat_found:
            print("🟡 자동 좌석 선택 실패. 수동으로 좌석을 선택해주세요.")
            input("좌석 선택 완료 후 Enter를 누르세요...")
        
        # 2. 다음 단계 버튼 찾기 및 클릭
        print("\n🔍 다음 단계 버튼을 찾는 중...")
        
        next_button_selectors = [
            (By.XPATH, "//*[@id='NextStepBtn']"),
            (By.XPATH, "//a[contains(text(), '다음단계')]"),
            (By.XPATH, "//button[contains(text(), '다음')]"),
            (By.XPATH, "//*[contains(@onclick, 'NextStep')]"),
        ]
        
        for selector_type, selector_value in next_button_selectors:
            try:
                next_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((selector_type, selector_value))
                )
                next_button.click()
                print("✅ 다음 단계 버튼 클릭 성공!")
                time.sleep(2)
                break
            except Exception:
                continue
        
        # 3. 가격/티켓 정보 확인 및 다음 단계
        print("\n🔍 가격 확인 페이지 처리 중...")
        
        # 최종 예매하기 버튼
        final_button_selectors = [
            (By.XPATH, "//*[@id='SmallNextStepBtn']"),
            (By.XPATH, "//a[contains(text(), '예매하기')]"),
            (By.XPATH, "//button[contains(text(), '결제')]"),
        ]
        
        for selector_type, selector_value in final_button_selectors:
            try:
                final_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((selector_type, selector_value))
                )
                print("✅ 최종 예매 버튼 발견!")
                print("\n⚠️ 최종 결제는 직접 확인 후 진행해주세요!")
                break
            except Exception:
                continue
        
        print("\n🎉 좌석 선택 자동화 완료!")
        print("💡 이제 결제 정보를 확인하고 수동으로 결제를 완료해주세요.")
        
    except Exception as e:
        print(f"\n🔴 좌석 선택 중 오류 발생: {e}")
        print("💡 수동으로 좌석 선택을 진행해주세요.")


if __name__ == "__main__":
    run_macro()