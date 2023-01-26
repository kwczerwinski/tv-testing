import json
import os
import string
import threading
import time
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager

def append_to_list(array):
	for x in array:
		symbols.append(find_by_tag(x, "span").text)

def _main():
	driver = open_tv_widget()
	menu = open_symbol_search(driver)
	time.sleep(1)
	searchbox = find_searchbox(menu)
	clear_input(searchbox)
	time.sleep(1)
	loading_symbols(menu, '', 1000)

	# Get all symbols
	rows = find_all_by_class(menu, "itemRow-DPHbT8fH")

	start = time.time()
	# append_to_list(rows)
	thread = threading.Thread(target=append_to_list, args=rows)
	thread.start()
	thread.join()
	end = time.time()
	print(f"Getting all symbols in {end - start} s.")
	print(f"Rows: {len(rows)}, Symbols: {len(symbols)}")
	driver.quit()

def list_to_json_file(path:string, array:list) -> None:
	os.makedirs(os.path.dirname(path), exist_ok=True)
	with open(path, "w") as fp:
		json.dump(array, fp)

def open_tv_widget() -> webdriver:
	service = EdgeService(EdgeChromiumDriverManager().install())
	driver = webdriver.Edge(service=service)
	url = "https://s.tradingview.com/widgetembed/?symboledit=1&theme=dark&withdateranges=1&interval=12M"
	driver.get(url)
	return driver

def find_by_id(driver:webdriver, id:string) -> webdriver:
	return driver.find_element(by=By.ID, value=id)

def open_symbol_search(driver:webdriver) -> webdriver:
	find_by_id(driver, "header-toolbar-symbol-search").click()
	return find_by_id(driver, "overlap-manager-root")

def find_by_tag(driver:webdriver, tag:string) -> webdriver:
	return driver.find_element(by=By.TAG_NAME, value=tag)

def clear_input(driver:webdriver) -> None:
	driver.send_keys(Keys.CONTROL + "A" + Keys.BACKSPACE)

def generate_words() -> list:
	words = []
	for x in string.ascii_uppercase:
		for y in string.ascii_uppercase:
			words.add(f"{x}{y}")
	return words

def find_all_by_class(driver:webdriver, class_name:string) -> list:
	return driver.find_elements(by=By.CLASS_NAME, value=class_name)

def find_by_class(driver:webdriver, class_name:string) -> webdriver:
	return driver.find_element(by=By.CLASS_NAME, value=class_name)

def goto_sources(driver:webdriver) -> None:
	find_by_class(driver, class_name="exchange-KMA9DMBY").click()

def find_searchbox(driver:webdriver) -> webdriver:
	return find_by_tag(driver, tag="input")

def keydown(driver:webdriver) -> None:
	driver.send_keys(Keys.DOWN)
	time.sleep(0.2)

def get_source_code(driver:webdriver) -> string:
	clear_input(driver)
	keydown(driver)
	return driver.get_property("value").split(":")[0]

def fill_and_wait(driver:webdriver, word:string, seconds:float) -> None:
	clear_input(driver)
	driver.send_keys(word)
	time.sleep(seconds)

def is_list_empty(driver:webdriver) -> list:
	return find_all_by_class(driver, "noResultsDesktop-SVZTqWhV")

def get_rows(driver:webdriver) -> list:
	return find_all_by_class(driver, "itemInfoCell-DPHbT8fH")

def is_load_not_possible(driver:webdriver) -> bool:
	return not find_all_by_class(driver, "spinnerContainer-vWG52QBW")

def no_items_starswith_word(rows:list, word:string) -> bool:
	return not any(row.text.startswith(word) for row in rows)

def loading_symbols(driver:webdriver, word:string, max:int=10000) -> None:
	symbols_loaded = 0
	while True:
		if is_load_not_possible(driver):
			return

		rows = get_rows(driver)

		if len(rows) > max:
			return

		symbols_loaded = len(rows) - symbols_loaded
		if no_items_starswith_word(rows[-symbols_loaded:], word):
			return

		move_to(driver, rows[-1])
		# Workaround for hang when loading new symbols
		move_to(driver, rows[-symbols_loaded])

def move_to(driver:webdriver, destination:webdriver) -> None:
	ActionChains(driver).move_to_element(destination).perform()  # Need to change lines 91 & 97 in action_builder.py (".execute" to "._execute")

def move_and_click(driver:webdriver, element:webdriver) -> None:
	move_to(driver, element)
	element.click()

def find_handles(driver:webdriver) -> list:
	return find_all_by_class(driver, "expandHandle-DPHbT8fH")

def expand_dropdowns(driver:webdriver) -> None:
	starting_handles = find_handles(driver)

	if not starting_handles:
		return

	for i in range(len(starting_handles)):
		# Clicking handle generate new list - can't use 'for handle in handles:'
		handles = find_handles(driver)
		# Simple click() does not move list to appropriate position
		move_and_click(driver, handles[i])

	# Check if new handles appear
	assert len(handles) == len(find_handles(driver))

if __name__ == "__main__":
	_main()