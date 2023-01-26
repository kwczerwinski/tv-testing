import os
import string
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager

def find_by_class(driver:webdriver, class_selector:string) -> webdriver:
    return driver.find_element(by=By.CLASS_NAME, value=class_selector)

def find_by_id(driver:webdriver, id:string) -> webdriver:
    return driver.find_element(value=id)

def open_symbol_search(driver:webdriver) -> None:
    find_by_id(driver, "header-toolbar-symbol-search").click()

def find_input(driver:webdriver) -> webdriver:
    return find_by_class(driver, "search-eYX5YvkT")

def clear_input(driver:webdriver) -> None:
    find_input(driver).send_keys(Keys.CONTROL + "a" + Keys.DELETE)

def find_all_by_class(driver:webdriver, class_selector:string) -> list:
    return driver.find_elements(by=By.CLASS_NAME, value=class_selector)

def move_to(driver:webdriver, destination:webdriver) -> None:
    ActionChains(driver).move_to_element(destination).perform()

def fill_input(driver:webdriver, word:string) -> None:
    find_input(driver).send_keys(word)

def expand_all_handles(driver:webdriver) -> None:
    while True:
        all_handles = find_all_by_class(driver, "expandHandle-DPHbT8fH")
        expanded_handles = find_all_by_class(driver, "expanded-DPHbT8fH")
        if all_handles == expanded_handles:
            break
        for handle in all_handles:
            if handle not in expanded_handles:
                move_to(driver, handle)
                handle.click()
                break

if __name__ == "__main__":
    service = EdgeService(EdgeChromiumDriverManager().install())
    driver = webdriver.Edge(service=service)
    url="https://www.tradingview-widget.com/widgetembed/?interval=12M&symboledit=1&saveimage=0&withdateranges=0&theme=dark&symbol="
    driver.get(url)
    driver.implicitly_wait(1)

    open_symbol_search(driver)
    clear_input(driver)
    fill_input(driver, "NQ")
    
    rows = []
    while len(rows) < 1000:
        expand_all_handles(driver)
        rows = find_all_by_class(driver, "itemInfoCell-DPHbT8fH")
        move_to(driver, rows[-1])

    expand_all_handles(driver)
    start = time.time()
    symbols = [el.text for el in driver.find_elements(by=By.XPATH, value="//div[contains(@class, 'actionHandleWrap-DPHbT8fH') and not(descendant::*)]/following-sibling::div/div/span[not(@class) and descendant::em]")]
    end = time.time()
    print(f"{len(symbols)} : {end - start}")

    time.sleep(5)
    driver.quit()
