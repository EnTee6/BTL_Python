import pickle
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
options = Options()
options.add_argument('--headless')
options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
driver = webdriver.Chrome(options=options)
driver.get('https://fbref.com/en/squads/822bd0ba/2024-2025/Liverpool-Stats')
try:
    with open('output/fbref_cookies.pkl', 'rb') as f:
        cookies = pickle.load(f)
    for c in cookies: driver.add_cookie(c)
    driver.get('https://fbref.com/en/squads/822bd0ba/2024-2025/Liverpool-Stats')
    html = driver.page_source
    import re
    tables = re.findall(r'<table[^>]*id="([^"]+)"', html)
    print('Found tables:', tables)
except Exception as e:
    print('Error:', e)
finally:
    driver.quit()
