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
TARGET_TIME = datetime.datetime(2025, 10, 25, 13, 35, 30)
MY_BUTTON_XPATH = "//*[@id='__next']/div/div/div/div[2]/div[3]/ul/li[4]/div/div[2]/button"

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
    """
    개선된 버튼 활성화 감지:
    - 버튼 텍스트에 '예매' 관련 문구가 포함되는지 확인
    - element.is_enabled()와 aria-disabled/disabled 속성 검사
    - (선택) computed backgroundColor로 시각적 활성화 여부 보조검사
    """
    start = time.monotonic()
    xpath = MY_BUTTON_XPATH

    def _is_really_ready(drv):
        try:
            el = drv.find_element(By.XPATH, xpath)
            text = (el.text or "").strip()
            enabled = el.is_enabled()
            aria_disabled = (el.get_attribute("aria-disabled") or "").lower()
            disabled_attr = el.get_attribute("disabled")
            # computed style (보조): 예매 버튼은 보통 배경색이 채워짐 — 필요시 조건 강화
            try:
                bg = drv.execute_script("return window.getComputedStyle(arguments[0]).backgroundColor;", el) or ""
            except Exception:
                bg = ""

            # debug: 필요하면 주석 해제해서 상태 확인
            # print(f"[DEBUG] text={text!r}, enabled={enabled}, aria={aria_disabled!r}, disabled={disabled_attr!r}, bg={bg!r}")

            text_ok = ("예매하기" in text) or ("예매" in text and "예매예정" not in text)  # 유연한 텍스트 매칭
            aria_ok = (aria_disabled == "" or aria_disabled == "false")
            disabled_ok = (disabled_attr is None)

            # 최종 조건: 텍스트 신호 + enable 관련 체크
            if text_ok and enabled and aria_ok and disabled_ok:
                return el
            # 보조: 텍스트가 정확하지 않더라도 bg 색상으로 판단하려면 아래처럼 허용
            # if enabled and "rgb" in bg and not bg.startswith("rgba(0, 0, 0, 0)"):
            #     return el

            return False
        except Exception:
            return False

    try:
        btn = WebDriverWait(driver, 600, poll_frequency=0.2).until(_is_really_ready)
        reaction = time.monotonic() - start
        print(f"\n✅ 예매버튼 실활성화 감지 (반응 {reaction:.4f}s) → 클릭!")
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
    """보안문자 수동 입력 후 Enter → 매수 1매 선택 + 다음단계 버튼"""
    try:
        print("\n🔁 ifrmSeat 프레임 접근 중...")

        # 1️⃣ 활성 예매창 전환
        for w in driver.window_handles:
            driver.switch_to.window(w)
            if "BookMain" in driver.current_url:
                print(f"✅ 활성 예매창 확인: {driver.current_url}")
                break

        # 2️⃣ ifrmSeat 프레임 진입
        WebDriverWait(driver, 30).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, "ifrmSeat"))
        )
        print("✅ ifrmSeat 프레임 진입 완료")

        # 3️⃣ 좌석 구역 → 선택버튼 → 좌석 → 좌석완료 를 그대로 실행
        zone = "/html/body/div[1]/div[3]/div[2]/div[1]/a[7]"
        pick_btn = "/html/body/div[1]/div[3]/div[2]/div[3]/a[1]/img"
        next_btn = "//*[@id='NextStepImage']"

        click_safe(driver, zone, "구역 선택 (a[7])")
        click_safe(driver, pick_btn, "자동배정 클릭")
        

        # 4️⃣ 가격/할인 페이지 프레임 전환 (ifrmBookStep)
        driver.switch_to.default_content()
        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, "ifrmBookStep"))
        )
        print("✅ 가격/할인 선택 프레임 진입 완료")

        # 5️⃣ 매수 select → 2매 선택
        qty_xpath = "//*[@id='PriceRow000']/td[3]/select"
        qty_elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, qty_xpath))
        )
        Select(qty_elem).select_by_visible_text("2매")
        print("🎟️ 매수 2매 선택 완료")

        # 6️⃣ 다음단계 버튼 클릭
        next_btn_xpath = "//*[@id='SmallNextBtnImage']"
        click_safe(driver, next_btn_xpath, "다음단계 클릭")
        print("🚀 다음단계 이동 완료")

    except Exception as e:
        print(f"⚠️ handle_after_popup 오류: {e}")
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