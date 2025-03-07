#!/usr/bin/env python
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
dr = uc.Chrome(options=options)

try:
    # Access Unibet URL
    url = 'https://valuebase.io/api/bestbacked/toppicks?market=www.unibet.nl'
    print(f'Accessing URL: {url}')
    dr.get(url)
    print('Page loaded, waiting for content...')

    wait = WebDriverWait(dr, 10)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
    
    # Wait until at least one odds element is populated in the bets section
    wait.until(lambda d: any(b.text.strip() for b in d.find_elements(By.CSS_SELECTOR, '.bets .bet')))
    
    # For debugging: print part of the page source
    page_source = dr.page_source
    print('\nPage source preview:')
    print(page_source[:1000])

    # Use BeautifulSoup to parse the HTML
    soup = BeautifulSoup(page_source, 'html.parser')

    # Find the container with match cards; based on provided html structure
    matches_list = soup.find('div', id='matches-list')
    if not matches_list:
        print('No matches list found.')
        data = []
    else:
        cards = matches_list.find_all('a')
        print(f'Found {len(cards)} match cards.')
        data = []
        
        for card in cards:
            try:
                # Extract competition from first .match-details.small-text block
                comp_container = card.find('div', class_='match-details')
                competition = 'Unknown'
                if comp_container:
                    path_div = comp_container.find('div', class_='match-details-path')
                    if path_div:
                        span = path_div.find('span')
                        if span and span.text.strip():
                            comp_text = span.text.strip()
                            competition = comp_text[:3] if len(comp_text) >= 3 else comp_text
                
                # Extract date and time from second .match-details.small-text block
                date_time = 'Unknown'
                details_blocks = card.find_all('div', class_='match-details')
                if len(details_blocks) >= 2:
                    clock_div = details_blocks[-1].find('div', class_='match-clock')
                    if clock_div and clock_div.text.strip():
                        date_time = clock_div.text.strip()
                
                # Extract team names from the live-match section
                home_team = 'Unknown'
                away_team = 'Unknown'
                live_match = card.find('div', class_='live-match')
                if live_match:
                    participants = live_match.find('div', class_='match-participants')
                    if participants:
                        team_divs = participants.find_all('div')
                        if len(team_divs) >= 2:
                            home_team = team_divs[0].text.strip()
                            away_team = team_divs[1].text.strip()
                
                # Extract odds from bet-button elements using data-odds-decimal attribute
                bets_div = card.find('div', class_='bets')
                if bets_div:
                    bet_divs = bets_div.find_all('div', class_='bet', recursive=False)
                    if len(bet_divs) >= 3:
                        def extract_odds(bet_div):
                            # Find any element within bet-div that has data-odds-decimal
                            odds_element = bet_div.find(attrs={'data-odds-decimal': True})
                            if odds_element:
                                odds_str = odds_element['data-odds-decimal']
                                try:
                                    return float(odds_str) if odds_str else ''
                                except (ValueError, AttributeError):
                                    return odds_str
                            return ''

                        home_odds = extract_odds(bet_divs[0])
                        draw_odds = extract_odds(bet_divs[1])
                        away_odds = extract_odds(bet_divs[2])
                    else:
                        home_odds = draw_odds = away_odds = ''
                else:
                    home_odds = draw_odds = away_odds = ''
                
                data.append([
                    competition,
                    date_time,
                    home_team,
                    away_team,
                    home_odds,
                    draw_odds, 
                    away_odds
                ])
                print(f"Added match: {home_team} vs {away_team} with odds H:{home_odds} D:{draw_odds} A:{away_odds}")
            except Exception as e:
                print(f'Error processing a match card: {e}')
                continue

    # Create DataFrame
    df = pd.DataFrame(data, columns=[
        'competition',
        'date_time',
        'home_team',
        'away_team',
        'home_odds',
        'draw_odds',
        'away_odds'
    ])
    print('\nFinal DataFrame:')
    print(df)

    # Save to CSV if data exists
    if not df.empty:
        output_file = 'unibet_predictions.csv'
        df.to_csv(output_file, index=False)
        print(f'Data saved to {output_file}')
    else:
        print('No data was collected!')

except Exception as e:
    print(f'An error occurred: {e}')
    raise e

finally:
    print('Closing browser...')
    try:
        dr.quit()
    except Exception as e:
        print('Error closing browser:', e)
