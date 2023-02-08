from concurrent.futures import ProcessPoolExecutor
import json
import os
from queue import Empty
import string
import time
from multiprocessing import Array, JoinableQueue, Process, Queue, cpu_count, freeze_support, set_start_method
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver import ActionChains
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager

def find_by_class(driver:webdriver, class_selector:string) -> webdriver:
    return driver.find_element(by=By.CLASS_NAME, value=class_selector)

def find_by_id(driver:webdriver, id:string) -> webdriver:
    return driver.find_element(value=id)

def open_symbol_search(driver:webdriver) -> None:
    find_by_id(driver, "header-toolbar-symbol-search").click()
    wait_for_load_end(driver)

def find_input(driver:webdriver) -> webdriver:
    return find_by_class(driver, "search-eYX5YvkT")

def clear_input(driver:webdriver) -> None:
    send_to_input(driver, Keys.CONTROL + "a" + Keys.DELETE, True)

def find_all_by_class(driver:webdriver, class_selector:string) -> list:
    return driver.find_elements(by=By.CLASS_NAME, value=class_selector)

def move_to(driver:webdriver, destination:webdriver) -> None:
    wait_till_attached_to_dom(driver, destination)
    ActionChains(driver).move_to_element(destination).perform()

def is_disabled(driver):
    return find_all_by_class(driver, "isDisabled-uO7HM85b")

def wait_till_not_disabled(driver):
    while True:
        if not is_disabled(driver):
            break

def wait_till_disabled(driver):
    while True:
        if is_disabled(driver):
            break

def send_to_input(driver:webdriver, keys:object, will_disable:bool) -> None:
    find_input(driver).send_keys(keys)
    wait_for_load_end(driver)
    # save_name = f"{os.getpid()}_{time.time()}"
    # driver.save_screenshot(f"debug\\{save_name}.png")
    # with open(f"debug\\{save_name}.html", "w", encoding="utf-8") as file:
    #     file.write(driver.page_source)
    # if will_disable:
    #     wait_till_disabled(driver)
    # else:
    #     wait_till_not_disabled(driver)
    # time.sleep(0.5)

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

def texts_from_elements(elements:list) -> list:
    return [el.text for el in elements]

def get_elements_with_symbols(driver:webdriver, em_tag_filter:bool) -> list:
    return driver.find_elements(by=By.XPATH, value=f"//div[contains(@class, 'actionHandleWrap-DPHbT8fH') and not(descendant::*)]/following-sibling::div/div/span[not(@class){' and descendant::em' if em_tag_filter else ''}]")

def go_back_from_sources(driver:webdriver) -> None:
    find_by_class(driver, "button-Ns7rA9vx").click()

class TextFromElements(Process):
    def __init__(self, elements:list) -> None:
        super().__init__()

        self.elements = elements
        self.texts = []

    def run(self):
        self.texts = [el.text for el in self.elements]

def is_spinner_not_visible(driver):
    return not find_all_by_class(driver, "spinnerContainer-vWG52QBW")

def load_rows(driver:webdriver, word:string, max_expand:int = 1000) -> None:
    rows_count_old = 0
    while rows_count_old < max_expand:
        if is_spinner_not_visible(driver):
            break

        rows = find_all_by_class(driver, "itemInfoCell-DPHbT8fH")
        rows_count_new = len(rows)
        loaded_rows_count = rows_count_new - rows_count_old
        any_loaded_row_startswith_word = any(row.text.startswith(word) for row in rows[-loaded_rows_count:])

        if any_loaded_row_startswith_word:
            move_to(driver, rows[-1])
            # Workaround for hang when loading new symbols
            move_to(driver, rows[-15])
        else:
            break

        rows_count_old = rows_count_new

def list_to_json_file(path:string, array:list) -> None:
    assert not os.path.exists(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fp:
        json.dump(array, fp)

def wait_for_load_end(driver:webdriver) -> None:
    while find_all_by_class(driver, "spinnerWrap-eYX5YvkT"):
        pass

def open_browser(rect=None) -> webdriver:
    service = EdgeService(EdgeChromiumDriverManager().install())
    driver = webdriver.Edge(service=service)
    if rect:
        driver.set_window_rect(rect['x'], rect['y'], rect['w'], rect['h'])
    url="https://www.tradingview-widget.com/widgetembed/?interval=12M&symboledit=1&saveimage=0&withdateranges=0&theme=dark&symbol="
    driver.get(url)

    return driver

def no_results(driver:webdriver) -> list:
    return find_all_by_class(driver, "container-CePxGLxr")

def get_source_code(driver:webdriver) -> string:
    clear_input(driver)
    if no_results(driver):
        send_to_input(driver, "A", False)
        clear_input(driver)
        send_to_input(driver, Keys.DOWN, False)
        if no_results(driver):
            return "!"
    send_to_input(driver, Keys.DOWN, False)
    code = find_input(driver).get_property("value").split(":")[0].replace("'", "")
    return code

def wait_till_attached_to_dom(driver:webdriver, element:webdriver) -> None:
    WebDriverWait(driver, timeout=10).until_not(expected_conditions.staleness_of(element))

def get_symbols_recursive(driver:webdriver, word:string = "", previous_first:string = "") -> list:
    clear_input(driver)
    send_to_input(driver, word, False)

    first_row = ""
    while first_row == previous_first:
        first_row = find_by_class(driver, "listContainer-vWG52QBW").text

    # goto_sources(driver)
    # go_back_from_sources(driver)
    elements = []
    
    if no_results(driver):
        pass
    elif is_spinner_not_visible(driver):
        expand_all_handles(driver)
        elements.extend(texts_from_elements(get_elements_with_symbols(driver, word != "")))
    else:
        for letter in string.ascii_uppercase:
            word += letter
            # send_to_input(driver, letter, False)
            elements.extend(get_symbols_recursive(driver, word, first_row))
            # send_to_input(driver, Keys.BACKSPACE, False)
            word = word[:-1]

    return elements

class Browser(Process):
    # def __init__(self, queue:JoinableQueue, rect:dict) -> None:
    def __init__(self, queue:JoinableQueue) -> None:
        super().__init__()

        self.daemon = True
        # self.rect = rect
        self.symbols = []
        self.queue = queue

    def run(self):
        driver = open_browser()
        # driver = open_browser(self.rect)
        open_symbol_search(driver)
        last_checked_element = 0

        while True:
            try:
                # source_description = self.arr
                source_description = self.queue.get(block=True, timeout=1)
            except Empty:
                break

            goto_sources(driver)
            sources = get_sources(driver)

            for i in range(last_checked_element,len(sources)):
                if sources[i].text == source_description:
                    sources[i].click()
                    last_checked_element = i
                    break

            source_code = get_source_code(driver)
            symbols = get_symbols_recursive(driver)
            # symbols = []

            list_to_json_file(f"symbols/{source_code}#{source_description.split(' — ')[-1]}.json",symbols)
            self.queue.task_done()
        # # x = driver.page_source
        # # driver.save_screenshot(f"screenshots/after_open_menu.png")
        # goto_sources(driver)


        # for word in words:
        #     clear_input(driver)
        #     send_to_input(driver, word)
        #     wait_until_spinner_hides(driver)
        #     send_to_input(driver, Keys.DOWN)
        #     load_rows(driver, word)
        #     expand_all_handles(driver)
        #     elements = get_elements_with_symbols(driver)
            
        #     # threads = []
        #     # divisions = 1
        #     # for n in range(divisions):
        #     #     t = TextFromElements(elements[n::divisions])
        #     #     threads.append(t)
        #     #     t.start()

        #     # for t in threads:
        #     #     t.join()
        #     #     self.symbols.extend(t.texts)
            
        #     self.symbols = elements
        driver.quit()

def get_sources(driver:webdriver) -> list:
    return find_all_by_class(driver, "description-jKCUPVoO")

def goto_sources(driver:webdriver) -> None:
    clear_input(driver)
    find_by_class(driver, "exchange-KMA9DMBY").click()

def text_from_element(element:webdriver):
    return element.text

def placeholder(*args) -> None:
    return args

if __name__ == "__main__":
    freeze_support()
    # set_start_method('spawn')
    start = time.time()
    driver = open_browser()
    driver.maximize_window()
    max_rect = driver.get_window_rect()
    h = max_rect['height'] // 2
    y1 = 0
    y2 = h
    w = max_rect['width'] // 3
    x1 =     0
    x2 =     w
    x3 = 2 * w
    open_symbol_search(driver)
    goto_sources(driver)

    # with ProcessPoolExecutor() as executor:
    #     for description in executor.map(None, sources):
    #         queue.put(description)

    sources_descriptions = [el.text for el in get_sources(driver)]
    queue = JoinableQueue()
    # queue = Queue()
    # with ProcessPoolExecutor() as executor:
    #     for description in executor.map(placeholder, sources_descriptions):
    #         queue.put(description)
    for sd in sources_descriptions:
        queue.put(sd)

    browser_rects = [
        {'w':w, 'h':h, 'x':x1, 'y':y1},
        {'w':w, 'h':h, 'x':x2, 'y':y1},
        {'w':w, 'h':h, 'x':x3, 'y':y1},
        {'w':w, 'h':h, 'x':x1, 'y':y2},
        {'w':w, 'h':h, 'x':x2, 'y':y2},
        {'w':w, 'h':h, 'x':x3, 'y':y2}
    ]
    threads = []
    division = cpu_count()
    division = 1

    # for n,rect in zip(range(division),browser_rects):
    #     t = Browser(queue=queue, rect=rect)
    #     threads.append(t)
    #     t.start()

    for n in range(division):
        t = Browser(queue=queue)
        threads.append(t)
        t.start()

    driver.quit()
    queue.join()

    symbols = []
    # for t in threads:
    #     t.join()
    #     symbols.extend(t.symbols)

    end = time.time()

    print(f"{len(symbols)} : {end - start}")
