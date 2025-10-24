import time
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager


# ==============================================================================
# ⚙️ 사용자 설정
# ==============================================================================

TICKET_PAGE_URL = "https://tickets.interpark.com/special/sports/promotion/41"
TARGET_TIME = datetime.datetime(2025, 10, 21, 21, 39, 0)
MY_BUTTON_XPATH = "//*[@id='__next']/div/div/div/div[2]/div[3]/ul/li[5]/div/div[2]/button"

# ==============================================================================


def run_macro():
    driver = None
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
        driver.maximize_window()

        print("=" * 60)
        print("🎟️ 인터파크 티켓팅 매크로 시작")
        print("=" * 60)

        # 로그인 페이지
        driver.get(
            "https://accounts.yanolja.com/?clientId=ticket-pc&postProc=FULLSCREEN"
            "&origin=https%3A%2F%2Fnol.interpark.com%2Fticket&service=interpark-ticket"
            "&redirect=https%3A%2F%2Faccounts.interpark.com%2Flogin%2Fsuccess%2Fnol"
            "%3FpostProc%3DFULLSCREEN%26origin%3Dhttps%253A%252F%252Fnol.interpark.com%252Fticket"
        )

        input("✅ 로그인 완료 후 터미널에서 Enter ▶ ")

        driver.get(TICKET_PAGE_URL)
        print(f"✅ 예매페이지 이동 완료: {TICKET_PAGE_URL}")

        wait_until_ready()
        wait_for_button_and_click(driver)
        handle_popup_window(driver)

        print("\n🎯 팝업 닫기 완료. 보안문자 입력 후 '입력완료' 클릭 → 터미널에 Enter ▶")
        input()
        handle_after_popup(driver)
        print("\n🎉 예매 자동화 완료 (결제단계 진입!).")

        time.sleep(600)

    except Exception as e:
        print(f"🔴 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()


# ==============================================================================
# ⏱️ 대기/기초 부분
# ==============================================================================

def wait_until_ready():
    print(f"\n⏰ 목표 시간: {TARGET_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    pre_watch = TARGET_TIME - datetime.timedelta(seconds=2)
    while True:
        now = datetime.datetime.now()
        if now >= pre_watch:
            print("\n🚀 예매 감시 시작!")
            break
        remain = (pre_watch - now).total_seconds()
        print(f"\r⏳ 시작까지 {remain:.2f}초 남음", end="")
        time.sleep(0.1)


def wait_for_button_and_click(driver):
    start = time.monotonic()
    try:
        btn = WebDriverWait(driver, 600).until(
            EC.element_to_be_clickable((By.XPATH, MY_BUTTON_XPATH))
        )
        reaction = time.monotonic() - start
        print(f"\n✅ 예매버튼 활성화 감지 (반응 {reaction:.4f}s) → 클릭!")
        btn.click()
    except TimeoutException:
        print("🔴 10분 내 버튼 활성화 실패")
    except Exception as e:
        print(f"⚠️ 클릭 오류: {e}")


def handle_popup_window(driver):
    print("\n--- 예매창 처리 시작 ---")
    try:
        original = driver.current_window_handle
        WebDriverWait(driver, 15).until(EC.number_of_windows_to_be(2))
        for win in driver.window_handles:
            if win != original:
                driver.switch_to.window(win)
                break
        print("✅ 새 예매창 전환 완료")
    except Exception as e:
        print(f"⚠️ 창 전환 실패: {e}")
        return

    wait_for_queue_or_popup(driver)


def wait_for_queue_or_popup(driver):
    popup_btn = "//*[@id='divBookNoticeLayer']/div[2]/div[1]/a"
    queue_msg = "//*[@id='__next']/div/div/div/div[2]/div[1]/div[1]/h3"

    print("⏳ 대기열/팝업 감시 중...")
    queue = False
    start = time.time()

    while time.time() - start < 10:
        try:
            if driver.find_element(By.XPATH, queue_msg).is_displayed():
                print("✅ 대기열 감지됨")
                queue = True
                break
        except Exception:
            pass
        try:
            driver.switch_to.frame("ifrmSeat")
            if driver.find_element(By.XPATH, popup_btn).is_displayed():
                print("✅ 안내 팝업 감지됨")
                driver.switch_to.default_content()
                break
            driver.switch_to.default_content()
        except Exception:
            driver.switch_to.default_content()
        time.sleep(0.2)

    if queue:
        print("⏳ 대기열 통과 대기중...")
        while True:
            try:
                if not driver.find_element(By.XPATH, queue_msg).is_displayed():
                    print("\n✅ 대기열 통과!")
                    break
                time.sleep(0.2)
            except Exception:
                print("\n✅ 대기열 사라짐 감지. 통과 완료.")
                break

    print("🔍 팝업 닫기 시도 중...")
    try:
        WebDriverWait(driver, 5).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, "ifrmSeat"))
        )
        close_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, popup_btn))
        )
        close_btn.click()
        print("✅ 팝업 닫기 완료")
    except Exception:
        print("🟡 팝업 닫기 실패 (없거나 이미 닫힘)")
    finally:
        driver.switch_to.default_content()


# ==============================================================================
# 🎟️ 보안문자 이후 자동화 (ifrmSeat 전용)
# ==============================================================================

def handle_after_popup(driver):
    """보안문자 수동 입력 후 Enter → 자동 좌석/결제"""
    try:
        print("\n🔁 ifrmSeat 프레임 접근 중...")

        # 1️⃣ 현재 활성탭 전환
        for w in driver.window_handles:
            driver.switch_to.window(w)
            if "BookMain" in driver.current_url:
                print(f"✅ 활성 예매창: {driver.current_url}")
                break

        # 2️⃣ ifrmSeat 프레임 진입
        WebDriverWait(driver, 30).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, "ifrmSeat"))
        )
        print("✅ ifrmSeat 프레임 진입 완료")

        # 3️⃣ 좌석 선택 (3루 1층 내야지정석)
        seat_xpath = "/html/body/div[1]/div[3]/div[2]/div[1]/a[8]"
        click_safe(driver, seat_xpath, "3루 1층 내야지정석")

        # 4️⃣ 자동배정 클릭
        auto_assign_xpath = "/html/body/div[1]/div[3]/div[2]/div[3]/a[1]/img"
        click_safe(driver, auto_assign_xpath, "자동배정")

        # 5️⃣ 매수 선택 (2매)
        qty_xpath = "//*[@id='PriceRow000']/td[3]/select"
        qty_elem = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, qty_xpath))
        )
        Select(qty_elem).select_by_visible_text("2매")
        print("🎟️ 매수 2매 선택 완료")

        # 6️⃣ 다음단계 클릭
        next_btn = "//*[@id='SmallNextBtnImage']"
        click_safe(driver, next_btn, "다음단계 이동")

        # 7️⃣ 약관 처리
        driver.switch_to.default_content()
        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, "ifrmBookStep"))
        )
        agree_xpath = "//*[@id='Agree']"
        save_xpath = "//*[@id='information']/div[2]/a[1]/img"

        try:
            agree = driver.find_element(By.XPATH, agree_xpath)
            if not agree.is_selected():
                agree.click()
                print("✅ 약관 전체 동의 완료")
            driver.find_element(By.XPATH, save_xpath).click()
            print("💾 약관 저장 완료")
        except Exception:
            print("🟡 약관 생략됨 / 이미 선택됨")

        # 8️⃣ 결제단계 클릭
        driver.switch_to.default_content()
        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, "ifrmSeat"))
        )
        click_safe(driver, next_btn, "결제단계 이동")
        print("🎉 결제단계 진입 완료!")

    except Exception as e:
        print(f"⚠️ handle_after_popup 중 오류: {e}")
    finally:
        driver.switch_to.default_content()


# ==============================================================================
# 🖱️ 안전 클릭 헬퍼
# ==============================================================================

def click_safe(driver, xpath, desc):
    try:
        elm = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", elm)
        elm.click()
        print(f"✅ {desc} 클릭 성공")
    except Exception as e:
        print(f"❌ {desc} 클릭 실패: {e}")


# ==============================================================================

if __name__ == "__main__":
    run_macro()
