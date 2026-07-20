"""
Helper script to take a dashboard screenshot.
Run this after the dashboard is running.
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def take_screenshot():
    """Take a screenshot of the running dashboard"""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=options)
    driver.get('http://127.0.0.1:8050')
    time.sleep(2)  # Wait for page to load
    
    driver.save_screenshot('plots/dashboard.png')
    driver.quit()
    print("✓ Saved: dashboard.png")

if __name__ == '__main__':
    take_screenshot()