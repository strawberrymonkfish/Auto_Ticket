import time
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import Select

# ==============================================================================
# 🎟️ Ticketing Macro (Local Time + Pre-Watch + Queue Handling + After CAPTCHA)
# ==============================================================================

# [필수] 여러 경기가 있는 예매 페이지 URL
TICKET_PAGE_URL = "https://tickets.interpark.com/special/sports/promotion/41"

# [필수] 티켓팅 시작 시간 (24시간 기준)
TARGET_TIME = datetime.datetime(2025, 10, 22, 20, 25, 40)

# [필수] 클릭하려는 버튼 XPath
MY_BUTTON_XPATH = "//*[@id='__next']/div/div/div/div[2]/div[3]/ul/li[5]/div/div[2]/button"

# ==============================================================================


def run_macro():
    """매크로 전체 실행"""
    driver = None
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)

        print("=" * 60)
        print("🎟️ 인터파크 티켓팅 매크로를 시작합니다.")
        print("=" * 60)

        driver.get(
            "https://accounts.yanolja.com/?clientId=ticket-pc&postProc=FULLSCREEN"
            "&origin=https%3A%2F%2Fnol.interpark.com%2Fticket&service=interpark-ticket"
            "&redirect=https%3A%2F%2Faccounts.interpark.com%2Flogin%2Fsuccess%2Fnol"
            "%3FpostProc%3DFULLSCREEN%26origin%3Dhttps%253A%252F%252Fnol.interpark.com%252Fticket"
        )

        input("✅ 브라우저에서 로그인 완료 후 터미널로 돌아와 Enter ▶ ")

        print("로그인 완료. 예매 페이지로 이동 중...")
        driver.get(TICKET_PAGE_URL)
        print(f"✅ 예매 페이지로 이동 완료: {TICKET_PAGE_URL}")

        wait_until_ready()

        print("\n🚀 예매 시작 2초 전! 버튼 활성화를 감시합니다...")
        wait_for_button_and_click(driver)

        handle_popup_window(driver)

        print("\n🎉 예매 프로세스 완료! 결제 단계 진입했습니다.")
        print("10분 후 브라우저가 자동 종료됩니다.")
        time.sleep(600)

    except Exception as e:
        print(f"\n🔴 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            print("\n브라우저를 닫습니다.")
            driver.quit()


# ==============================================================================


def wait_until_ready():
    """예매 시작 2초 전까지 대기"""
    print(f"\n⏰ 목표 시간: {TARGET_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    pre_watch_time = TARGET_TIME - datetime.timedelta(seconds=2)

    while True:
        now = datetime.datetime.now()
        if now >= pre_watch_time:
            break
        remaining = (pre_watch_time - now).total_seconds()
        if remaining > 1:
            print(f"\r⏳ 버튼 감시 시작까지 {remaining:,.2f}초 남음", end="")
            time.sleep(0.1)
        else:
            print(f"\r⏳ 버튼 감시 시작까지 {remaining:.3f}초 남음", end="")
            time.sleep(0.001)


# ==============================================================================


def wait_for_button_and_click(driver):
    """예매 버튼 클릭 감시"""
    try:
        wait_duration = 600
        start_time = time.monotonic()

        book_button = WebDriverWait(driver, wait_duration).until(
            EC.element_to_be_clickable((By.XPATH, MY_BUTTON_XPATH))
        )

        end_time = time.monotonic()
        print(
            f"\n✅ 예매 버튼 활성화 감지! 즉시 클릭 실행!"
            f" (반응: {end_time - start_time:.4f}초)"
        )
        book_button.click()

    except TimeoutException:
        print(f"\n🔴 10분 동안 버튼 활성화 안 됨.")
    except Exception as e:
        print(f"\n🔴 버튼 클릭 오류: {e}")


# ==============================================================================


def handle_popup_window(driver):
    """예매 버튼 클릭 후 새 창 전환 + 대기열 / 팝업 처리"""
    print("\n--- 예매 창 처리 시작 ---")

    try:
        original_window = driver.current_window_handle
        WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))

        for window_handle in driver.window_handles:
            if window_handle != original_window:
                driver.switch_to.window(window_handle)
                break
        print("✅ 예매 창으로 전환됨.")
    except Exception as e:
        print(f"🔴 새 창 전환 실패: {e}")
        return

    wait_for_queue_or_popup(driver)
    handle_after_popup(driver)


# ==============================================================================


def wait_for_queue_or_popup(driver):
    """대기열 / 안내 팝업 감시 및 닫기"""
    queue_xpath = "//*[@id='__next']/div/div/div/div[2]/div[1]/div[1]/h3"
    popup_close_xpath = "//*[@id='divBookNoticeLayer']/div[2]/div[1]/a"

    print("⏳ 대기열 또는 팝업 감지 중...")
    queue_detected = False
    start_time = time.time()

    while time.time() - start_time < 5:
        try:
            queue_el = driver.find_element(By.XPATH, queue_xpath)
            if queue_el.is_displayed():
                print("✅ 대기열 감지됨! 통과 대기...")
                queue_detected = True
                break
        except Exception:
            pass

        try:
            driver.switch_to.frame("ifrmSeat")
            popup_el = driver.find_element(By.XPATH, popup_close_xpath)
            if popup_el.is_displayed():
                print("✅ 팝업 감지됨! 닫기 실행.")
                driver.switch_to.default_content()
                break
            driver.switch_to.default_content()
        except Exception:
            driver.switch_to.default_content()
            pass

        time.sleep(0.1)

    if queue_detected:
        print("⏳ 대기열 통과 대기 중...")
        start_queue = time.time()
        while time.time() - start_queue < 600:
            try:
                q_el = driver.find_element(By.XPATH, queue_xpath)
                if not q_el.is_displayed():
                    print("\n✅ 대기열 통과!")
                    break
                print(f"\r⏳ 대기중... {int(time.time()-start_queue)}초", end="")
            except Exception:
                print("\n✅ 대기열 통과!")
                break
            time.sleep(0.1)

    print("\n🔍 팝업 닫기 시도 중...")

    try:
        try:
            WebDriverWait(driver, 3).until(
                EC.frame_to_be_available_and_switch_to_it((By.NAME, "ifrmSeat"))
            )
        except Exception:
            print("🟡 iframe 전환 불필요.")
        close_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, popup_close_xpath))
        )
        close_btn.click()
        print("✅ 안내 팝업 닫기 성공")
    except Exception as e:
        print(f"🟡 팝업 닫기 실패: {e}")
        print("   팝업이 없거나 이미 닫힘.")
    finally:
        driver.switch_to.default_content()


# ==============================================================================


def handle_after_popup(driver):
    """보안문자 입력 이후 단계 자동화"""
    print("\n🔐 안심예매(보안문자) 입력 후 Enter ▶ ")
    input()

    try:
        driver.switch_to.frame("ifrmSeat")
        print("✅ 좌석 선택 창 진입 완료")

        # 1루 응원석 클릭
        cheer_xpath = "/html/body/div[1]/div[3]/div[2]/div[1]/a[9]"
        auto_assign_xpath = "/html/body/div[1]/div[3]/div[2]/div[3]/a[1]/img"
        qty_xpath = "//*[@id='PriceRow000']/td[3]/select"
        next_btn_xpath = "//*[@id='SmallNextBtnImage']"

        click_safe(driver, cheer_xpath, "1루 응원석")
        click_safe(driver, auto_assign_xpath, "자동배정")

        qty_elem = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, qty_xpath))
        )
        Select(qty_elem).select_by_visible_text("1매")
        print("🎟️ 1매 선택 완료")

        click_safe(driver, next_btn_xpath, "다음단계")

        # 약관 동의 처리
        driver.switch_to.default_content()
        WebDriverWait(driver, 5).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, "ifrmBookStep"))
        )

        agree_xpath = "//*[@id='Agree']"
        save_xpath = "//*[@id='information']/div[2]/a[1]/img"

        try:
            agree = driver.find_element(By.XPATH, agree_xpath)
            if not agree.is_selected():
                agree.click()
                print("✅ 약관 동의 완료")
            driver.find_element(By.XPATH, save_xpath).click()
            print("💾 약관 저장 완료")
        except Exception:
            print("🟡 약관 영역 없음 (건너뜀)")

        # 결제단계 버튼
        driver.switch_to.default_content()
        driver.switch_to.frame("ifrmSeat")
        final_next_xpath = "//*[@id='SmallNextBtnImage']"
        click_safe(driver, final_next_xpath, "결제단계로 이동")

        print("🎉 모든 자동화 단계 완료 (결제창 도달)")

    except Exception as e:
        print(f"⚠️ 보안문자 이후 단계 오류: {e}")
    finally:
        driver.switch_to.default_content()


# ==============================================================================


def click_safe(driver, xpath, desc):
    """안전 클릭 함수"""
    try:
        btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", btn)
        btn.click()
        print(f"✅ {desc} 클릭 성공")
    except Exception as e:
        print(f"❌ {desc} 클릭 실패: {e}")

# ==============================================================================

if __name__ == "__main__":
    run_macro()
