import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

# Setup undetected Chrome with additional options
options = uc.ChromeOptions()
options.add_argument('--window-size=1920,1080')
options.add_argument('--no-first-run')
options.add_argument('--no-service-autorun')
options.add_argument('--password-store=basic')
driver = uc.Chrome(options=options)

try:
    # Access the ticker URL directly
    url = "https://dataviz.theanalyst.com/opta-football-predictions/?ticker=true"
    print(f"Attempting to access ticker URL: {url}")
    driver.get(url)
    print("Page loaded, waiting for content...")

    wait = WebDriverWait(driver, 5)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    # Print a portion of the page source for debugging
    print("\nPage source:")
    print(driver.page_source[:1000])

    print("\nLooking for match cards...")

    # Try different selectors with explicit wait
    selectors = [
        "[role='link']",
        "div[style*='background-color: rgb(255, 255, 255)']",
        ".match-card",
        "[class*='match']",
        "[class*='card']",
        "div > div > div"  # More generic selector
    ]

    cards = []
    for selector in selectors:
        try:
            found_cards = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector)))
            print(f"\nTrying selector '{selector}': found {len(found_cards)} elements")
            if found_cards:
                # Print first element found for debugging if available
                print("First element HTML:")
                print(found_cards[0].get_attribute('outerHTML'))
                cards = found_cards
                break
        except Exception as e:
            print(f"Error with selector '{selector}': {e}")

    if not cards:
        print("No match cards found using provided selectors.")

    data = []
    for card in cards:
        try:
            # Get HTML content
            card_html = card.get_attribute('outerHTML')
            print("\nProcessing card HTML:")
            print(card_html[:200])  # Print truncated HTML for debugging
            
            soup = BeautifulSoup(card_html, "html.parser")
            
            # Try multiple methods to find team names
            team_names = []
            
            # Method 1: Look for spans with specific style
            team_spans = soup.find_all("span", style=lambda x: x and "color: rgb(29, 10, 48)" in str(x))
            if len(team_spans) >= 2:
                team_names = [span.get_text().strip() for span in team_spans[:2]]
            
            # Method 2: Look for team badges or team names
            if not team_names:
                team_elements = soup.find_all("div", class_=lambda x: x and ("team" in str(x).lower() or "badge" in str(x).lower()))
                if len(team_elements) >= 2:
                    team_names = [elem.get_text().strip() for elem in team_elements[:2]]
            
            # Find probabilities (try multiple methods)
            percentages = []
            
            # Method 1: Look for specific percentage text
            prob_elements = soup.find_all(string=lambda text: text and '%' in str(text))
            if prob_elements:
                percentages = [elem.strip().strip('%') for elem in prob_elements if elem.strip().strip('%').replace('.', '').isdigit()]
            
            # Method 2: Look for probability divs
            if not percentages:
                prob_divs = soup.find_all("div", class_=lambda x: x and "prob" in str(x).lower())
                for div in prob_divs:
                    text = div.get_text().strip()
                    if '%' in text:
                        percentages.append(text.strip('%'))
            
            if team_names and len(team_names) >= 2:
                home_team, away_team = team_names[:2]
                print(f"Found teams: {home_team} vs {away_team}")
                
                if len(percentages) >= 3:
                    # Changed order to: home_prob, away_prob, draw_prob
                    # Looking at matches like MCI vs LIV where away and draw were swapped
                    home_prob, away_prob, draw_prob = percentages[:3]
                    print(f"Found probabilities: {home_prob}% - {away_prob}% - {draw_prob}%")
                    
                    # Get competition and date (if available) from meta content
                    meta_content = soup.find("div", class_=lambda x: x and "match-card-meta-content" in x)
                    competition = "Unknown"
                    date_time = "Unknown"
                    if meta_content:
                        meta_labels = meta_content.find_all("div", class_=lambda x: x and "match-card-right-label" in x)
                        if len(meta_labels) >= 2:
                            # Extract exactly 3 letters for competition
                            comp_text = meta_labels[0].get_text().strip()
                            if len(comp_text) >= 3:
                                competition = comp_text[:3]
                            else:
                                competition = comp_text
                            date_time = meta_labels[1].get_text().strip()
                    
                    match_data = [
                        competition,
                        date_time,
                        home_team,
                        away_team,
                        home_prob,
                        draw_prob,
                        away_prob
                    ]
                    data.append(match_data)
                    print(f"Added match: {home_team} vs {away_team}")
        
        except Exception as e:
            print(f"Error processing a match card: {e}")
            continue
    
    # Create DataFrame
    df = pd.DataFrame(data, columns=[
        "competition",
        "date_time",
        "home_team",
        "away_team",
        "home_win_%",
        "draw_%",
        "away_win_%"
    ])
    print("\nFinal DataFrame:")
    print(df)
    
    if len(df) > 0:
        output_file = 'opta_predictions.csv'
        df.to_csv(output_file, index=False)
        print(f"\nData saved to {output_file}")
    else:
        print("\nNo data was collected!")

except Exception as e:
    print(f"An error occurred: {e}")
    raise e

finally:
    print("\nClosing browser...")
    try:
        driver.quit()
    except:
        pass
