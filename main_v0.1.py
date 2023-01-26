import json
import os
import string
import time
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager

# Check if chart use candles
# TO DO if chart can be candles - change chart type
def is_candles(elements: list) -> bool:
	for el in elements:
		el.click()
		menu = driver.find_element(
			by=By.CLASS_NAME, value="menuWrap-biWYdsXC"
		)
		if menu.text.startswith("Bars"):
			active_chart_type = menu.find_element(
				by=By.CLASS_NAME, value="isActive-RhC5uhZw"
			)
			return active_chart_type.text == "Candles"

	return False


driver = webdriver.Edge(
	service=EdgeService(EdgeChromiumDriverManager().install())
)
# driver.implicitly_wait(2)

driver.get(
	"https://s.tradingview.com/widgetembed/" +
	"?symboledit=1&theme=dark&withdateranges=1&interval=12M"
)

# Open 'Symbol Search' menu
btn_change_symbol = driver.find_element(
	by=By.ID, value="header-toolbar-symbol-search"
)
btn_change_symbol.click()
opened_menu = driver.find_element(
	by=By.ID, value="overlap-manager-root"
)
opened_menu.find_element(by=By.TAG_NAME, value="input").clear()

# Get all sources
opened_menu.find_element(
	by=By.CLASS_NAME, value="exchange-KMA9DMBY"
).click()
sources = opened_menu.find_elements(
	by=By.CLASS_NAME, value="description-jKCUPVoO"
)

ltr_comb = []
for x in string.ascii_uppercase:
	for y in string.ascii_uppercase:
		ltr_comb.append(f"{x}{y}")

# Get all symbols
while True:
	# Select next source
	sources = opened_menu.find_elements(
		by=By.CLASS_NAME, value="container-jKCUPVoO"
	)
	selected_source = opened_menu.find_element(
		by=By.CLASS_NAME, value="selected-jKCUPVoO"
	)
	next_index = sources.index(selected_source) + 1

	if next_index >= len(sources):
		break  # No more sources

	sources[next_index].click()
	time.sleep(0.2)

	# Clear symbols list
	symbols = []

	# Get source code
	input_search = opened_menu.find_element(
		by=By.TAG_NAME, value="input"
	)
	input_search.send_keys(Keys.CONTROL + "A" + Keys.BACKSPACE)
	input_search.send_keys(Keys.DOWN)
	time.sleep(0.2)
	source_code = input_search.get_property("value").split(":")[0]

	# Omit dumped sources
	if source_code in os.listdir('symbols'):
		# Go to sources list
		opened_menu.\
			find_element(by=By.CLASS_NAME, value="exchange-KMA9DMBY").\
			click()
		continue

	for letters in ltr_comb:
		# Filtering by source and letters should omit max length of
		#   list (10000); there are several problems when list is 
		#   empty (ex. changing markets)
		# Sometimes menu does not react on input_search.clear() when 
		#   list is empty
		input_search.send_keys(Keys.CONTROL + "A" + Keys.BACKSPACE)
		input_search.send_keys(letters)
		# In some cases it is possible that symbols will not appear 
		#   fast enough
		time.sleep(0.7)

		if opened_menu.find_elements(
			by=By.CLASS_NAME, value="noResultsDesktop-SVZTqWhV"
		):
			continue

		# Move down for loading more symbols; max 50 lines per load
		# Since not all symbols starting with specific letters are on top
		#   there is small chance that some symbols might not be catched
		while True:
			spinner_visible = opened_menu.find_elements(
				by=By.CLASS_NAME, value="spinnerContainer-vWG52QBW"
			)

			if not spinner_visible:
				break

			rows = opened_menu.find_elements(
				by=By.CLASS_NAME, value="itemInfoCell-DPHbT8fH"
			)
			any_row_startswith_letters = any(
				row.text.startswith(letters) for row in rows[-50:]
			)

			if any_row_startswith_letters:
				ActionChains(opened_menu).\
					move_to_element(rows[-1]).\
					perform()  # Need to change lines 91 & 97 in action_builder.py (".execute" to "._execute")
				# Workaround for hang when loading new symbols
				ActionChains(opened_menu).\
					move_to_element(rows[-50]).\
					perform()  # as above
			else:
				break

		# Expand all dropdowns that could appear
		handles = opened_menu.find_elements(
			by=By.CLASS_NAME, value="expandHandle-DPHbT8fH"
		)

		if handles:
			for i in range(len(handles)):
				# Clicking handle generate new list and therefore we cannot use simple 'for handle in handles:'
				handles = opened_menu.find_elements(
					by=By.CLASS_NAME, value="expandHandle-DPHbT8fH"
				)
				# Simple click does not move list to appropriate position
				ActionChains(opened_menu).\
					move_to_element(handles[i]).\
					click(handles[i]).\
					perform()

			# Check if new handles appear
			new_handles = opened_menu.find_elements(
				by=By.CLASS_NAME, value="expandHandle-DPHbT8fH"
			)
			assert len(handles) == len(new_handles)

		# Get all symbols
		rows = opened_menu.find_elements(
			by=By.CLASS_NAME, value="itemRow-DPHbT8fH"
		)
		assert len(rows) < 10000  # Need to adjust filters if false

		if rows:
			for row in rows:
				if not row.text.startswith(letters):
					continue
				
				if row.find_elements(
					by=By.CLASS_NAME, value="expandHandle-DPHbT8fH"
				):
					continue

				symbols.append(row.\
					find_element(by=By.TAG_NAME, value="span").\
					text)

	# 'for letters in ltr_comb:' end

	# Dump to file as json
	path = f"symbols/{source_code}"
	os.makedirs(os.path.dirname(path), exist_ok=True)
	with open(path, "w") as fp:
		json.dump(symbols, fp)

	# Go to sources list
	opened_menu.\
		find_element(by=By.CLASS_NAME, value="exchange-KMA9DMBY").\
		click()

# 'while True:' end

# while True:
# 	btn_change_symbol = driver.find_element(
# 		by=By.ID, value="header-toolbar-symbol-search"
# 	)

# 	menu_symbol_search = driver.find_element(by=By.ID, value="overlap-manager-root")

# 	btn_arrows = [
# 		el
# 		for el in driver.find_elements(by=By.CLASS_NAME, value="arrow-reABrhVR")
# 		if el.aria_role == "generic"
# 	]
# 	if not is_candles(btn_arrows):
# 		continue

driver.quit()
