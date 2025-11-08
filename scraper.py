import os
import time
import random
import csv
import warnings
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from fake_useragent import UserAgent

warnings.filterwarnings("ignore", category=UserWarning)

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path if os.path.exists(env_path) else None)

EMPTY_PROFILE = {'Name': '', 'Headline': '', 'Company': '', 'Location': '', 'About': ''}

class LinkedInScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        self.ua = UserAgent()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        env_path = os.path.join(script_dir, '.env')
        
        if not os.path.exists(env_path):
            raise ValueError(f"[ERROR] .env file not found at {env_path}\nCreate .env with LINKEDIN_EMAIL and LINKEDIN_PASSWORD")
        
        load_dotenv(env_path, override=True)
        self.email = os.getenv('LINKEDIN_EMAIL', '').strip()
        self.password = os.getenv('LINKEDIN_PASSWORD', '').strip()
        
        if not self.email or not self.password or any(x in self.email.lower() or x in self.password.lower() 
                                                      for x in ['your_email', 'your_password', 'here']):
            raise ValueError(f"[ERROR] Invalid credentials in .env file at {env_path}")
        
        print("[OK] Credentials loaded successfully!\n")
    
    def _find_element(self, selectors, by=By.CSS_SELECTOR, multiple=False):
        """Helper to find element using multiple selector strategies."""
        for selector in selectors:
            try:
                elements = self.driver.find_elements(by, selector) if multiple else [self.driver.find_element(by, selector)]
                for elem in elements:
                    text = elem.text.strip()
                    if text and (not multiple or len(text) > 5):
                        return elem if not multiple else text
            except NoSuchElementException:
                continue
        return None
    
    def _find_text(self, selectors, filter_func=None):
        """Helper to extract text using multiple selector strategies."""
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    text = elem.text.strip()
                    if text and (not filter_func or filter_func(text)):
                        return text
            except NoSuchElementException:
                continue
        return ''
    
    def setup_driver(self):
        """Setup Chrome driver with undetected-chromedriver."""
        options = uc.ChromeOptions()
        if self.headless:
            options.add_argument('--headless=new')
        try:
            options.add_argument(f'--user-agent={self.ua.random}')
        except:
            pass
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        print("Setting up Chrome driver...")
        try:
            self.driver = uc.Chrome(options=options, use_subprocess=True)
        except:
            self.driver = uc.Chrome(options=options)
        
        self.driver.maximize_window()
        try:
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
            })
        except:
            pass
    
    def login(self):
        """Login to LinkedIn."""
        print("Logging in to LinkedIn...")
        self.driver.get("https://www.linkedin.com/login")
        time.sleep(random.uniform(2, 4))
        
        try:
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(self.email)
            self.driver.find_element(By.ID, "password").send_keys(self.password)
            self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
            time.sleep(random.uniform(3, 5))
            
            success = "feed" in self.driver.current_url or "linkedin.com/in/" in self.driver.current_url
            print("Login successful!" if success else "Login may have failed. Please check credentials.")
            return success
        except (TimeoutException, Exception) as e:
            print(f"Error during login: {str(e)}")
            return False
    
    def _extract_company_from_headline(self, headline):
        """Extract company name from headline."""
        for sep in [' || ', ' | ']:
            headline = headline.split(sep)[0]
        for sep in [' at ', ' @ ', ' - ']:
            if sep in headline:
                company = headline.split(sep, 1)[1].split(' ||')[0].split(' |')[0].strip()
                if company:
                    return company
        return ''
    
    def extract_profile_data(self, url):
        """Extract profile data from a LinkedIn profile URL."""
        print(f"Scraping profile: {url}")
        try:
            self.driver.get(url)
            time.sleep(random.uniform(3, 6))
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            profile_data = EMPTY_PROFILE.copy()
            
            # Extract Name
            name_elem = self._find_element(["h1.text-heading-xlarge", "h1.pv-text-details__left-panel h1", 
                                           "h1[data-generated-suggestion-target]", "main section h1", "h1"])
            if name_elem:
                profile_data['Name'] = name_elem.text.strip()
            
            # Extract Headline
            headline_elem = self._find_element([".text-body-medium.break-words", ".pv-text-details__left-panel .text-body-medium",
                                               ".ph5.pb5 .text-body-medium", "[data-generated-suggestion-target] + .text-body-medium",
                                               ".text-body-medium"])
            if headline_elem:
                profile_data['Headline'] = headline_elem.text.strip()
            
            # Extract Location
            profile_data['Location'] = self._find_text([".text-body-small.inline.t-black--light.break-words",
                                                        ".pv-text-details__left-panel .text-body-small", ".ph5.pb5 .text-body-small",
                                                        "[data-test-id='location']", ".text-body-small"],
                                                       filter_func=lambda t: '•' not in t or len(t) > 5)
            
            # Extract Company from experience section
            try:
                exp_selectors = ["#experience ~ .pvs-list", "section[data-section='experience']", "#experience",
                               "[data-section='experience']", "section[id*='experience']", ".pvs-list[data-section='experience']"]
                for exp_sel in exp_selectors:
                    try:
                        exp_section = self.driver.find_element(By.CSS_SELECTOR, exp_sel)
                        first_pos = exp_section.find_element(By.CSS_SELECTOR, 
                                                            ".pvs-list__item:first-child, li:first-child, .pvs-entity:first-child")
                        lines = [l.strip() for l in first_pos.text.strip().split('\n') if l.strip() and len(l.strip()) > 2]
                        if lines:
                            profile_data['Company'] = lines[1] if len(lines) >= 2 else lines[0]
                            break
                    except NoSuchElementException:
                        continue
            except:
                pass
            
            # Extract Company from headline if not found
            if not profile_data['Company'] and profile_data['Headline']:
                profile_data['Company'] = self._extract_company_from_headline(profile_data['Headline'])
            
            # Extract About section
            try:
                try:
                    about_header = self.driver.find_element(By.XPATH, "//h2[contains(text(), 'About')] | //h2[@id='about']")
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", about_header)
                    time.sleep(1)
                except:
                    pass
                
                # Click "Show more" if exists
                for xpath in ["//button[contains(@aria-label, 'Show more')]", "//button[contains(@aria-label, 'see more')]",
                             "//span[contains(text(), 'Show more')]/ancestor::button", "//button[.//span[contains(text(), 'more')]]"]:
                    try:
                        for btn in self.driver.find_elements(By.XPATH, xpath):
                            if btn.is_displayed():
                                self.driver.execute_script("arguments[0].click();", btn)
                                time.sleep(1.5)
                                break
                    except:
                        continue
                
                # Find About text
                about_selectors = ["section[data-section='summary'] .inline-show-more-text",
                                 "section[data-section='summary'] .pv-shared-text-with-see-more",
                                 "#about ~ .display-flex .inline-show-more-text", "#about ~ .pv-shared-text-with-see-more",
                                 "section[id='about'] .inline-show-more-text", "[data-section='summary']", "#about"]
                profile_data['About'] = self._find_text(about_selectors, 
                                                        filter_func=lambda t: len(t) > 20 and 'About' not in t[:10])
                
                # Alternative: Get content near About header
                if not profile_data['About']:
                    try:
                        about_header = self.driver.find_element(By.XPATH, "//h2[contains(text(), 'About')] | //h2[@id='about']")
                        about_content = self.driver.execute_script("""
                            var header = arguments[0], parent = header.parentElement, next = parent.nextElementSibling;
                            return next ? (next.innerText || next.textContent || '').trim() : '';
                        """, about_header)
                        if about_content and len(about_content) > 20:
                            profile_data['About'] = about_content
                    except:
                        pass
            except:
                pass
            
            print(f"Successfully scraped: {profile_data['Name']}")
            return profile_data
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return EMPTY_PROFILE.copy()
    
    def read_urls_from_file(self, filename='linkedin_urls.txt'):
        """Read LinkedIn URLs from a text file."""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip().startswith('http')]
            print(f"Loaded {len(urls)} URLs from {filename}")
            return urls
        except FileNotFoundError:
            print(f"File {filename} not found. Please create it with LinkedIn profile URLs.")
            return []
    
    def save_to_csv(self, profiles_data, filename='profiles.csv'):
        """Save scraped profiles to CSV file."""
        if not profiles_data:
            print("[WARNING] No data to save.")
            return
        
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        fieldnames = ['Name', 'Headline', 'Company', 'Location', 'About']
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(profiles_data)
                csvfile.flush()
                os.fsync(csvfile.fileno())
            
            if os.path.exists(file_path):
                print(f"[SUCCESS] Saved {len(profiles_data)} profiles to {file_path}")
            else:
                raise FileNotFoundError(f"CSV file was not created at {file_path}")
        except Exception as e:
            print(f"[ERROR] Error saving to CSV: {str(e)}")
            raise
    
    def scrape_profiles(self, urls_file='linkedin_urls.txt', output_file='profiles.csv'):
        """Main method to scrape all profiles."""
        try:
            self.setup_driver()
            if not self.login():
                print("Failed to login. Exiting.")
                return
            
            urls = self.read_urls_from_file(urls_file)
            if not urls:
                return
            
            profiles_data = []
            for i, url in enumerate(urls, 1):
                print(f"\nProcessing profile {i}/{len(urls)}")
                try:
                    profile_data = self.extract_profile_data(url)
                    profiles_data.append(profile_data)
                    print(f"   [OK] Collected data for: {profile_data.get('Name', 'Unknown')}")
                except Exception as e:
                    print(f"   [ERROR] Error scraping profile {i}: {str(e)}")
                    profiles_data.append(EMPTY_PROFILE.copy())
                
                if i < len(urls):
                    delay = random.uniform(5, 10)
                    print(f"Waiting {delay:.1f} seconds before next profile...")
                    time.sleep(delay)
            
            print(f"\n[INFO] Scraping complete! Total profiles collected: {len(profiles_data)}")
            if profiles_data:
                self.save_to_csv(profiles_data, output_file)
            else:
                print("[WARNING] No profile data to save. Check if scraping was successful.")
        except Exception as e:
            print(f"Error during scraping: {str(e)}")
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    print("\nBrowser closed.")
                except:
                    pass
                finally:
                    self.driver = None

def main():
    """Main function to run the scraper."""
    scraper = LinkedInScraper(headless=True)
    scraper.scrape_profiles()

if __name__ == "__main__":
    main()
