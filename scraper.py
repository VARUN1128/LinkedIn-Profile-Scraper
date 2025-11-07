"""
LinkedIn Profile Scraper
Scrapes profile data from multiple LinkedIn URLs and saves to CSV.
"""

import os
import sys
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

# Suppress harmless cleanup warnings from undetected-chromedriver
warnings.filterwarnings("ignore", category=UserWarning)

# Load environment variables - try explicit path first
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    # Fallback to default location
    load_dotenv()

class LinkedInScraper:
    def __init__(self, headless=True):
        """
        Initialize the LinkedIn scraper.
        
        Args:
            headless (bool): Run browser in headless mode
        """
        self.headless = headless
        self.driver = None
        self.ua = UserAgent()
        
        # Get the directory where the script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        env_path = os.path.join(script_dir, '.env')
        
        # Check if .env file exists
        if not os.path.exists(env_path):
            raise ValueError(
                "\n❌ ERROR: .env file not found!\n\n"
                f"Expected location: {env_path}\n\n"
                "Please create a .env file in the project directory with the following format:\n\n"
                "LINKEDIN_EMAIL=your_email@example.com\n"
                "LINKEDIN_PASSWORD=your_password\n\n"
                "Make sure to replace 'your_email@example.com' and 'your_password' with your actual LinkedIn credentials."
            )
        
        # Reload .env file explicitly
        load_dotenv(env_path, override=True)
        
        # Get credentials
        self.email = os.getenv('LINKEDIN_EMAIL', '').strip()
        self.password = os.getenv('LINKEDIN_PASSWORD', '').strip()
        
        # Debug: Show what was loaded (mask password)
        print(f"\n📋 Debug Info:")
        print(f"   .env file path: {env_path}")
        print(f"   .env file exists: {os.path.exists(env_path)}")
        print(f"   LINKEDIN_EMAIL loaded: {'Yes' if self.email else 'No'} ({'***' if self.email else 'Empty'})")
        print(f"   LINKEDIN_PASSWORD loaded: {'Yes' if self.password else 'No'} ({'***' if self.password else 'Empty'})")
        
        # Check if credentials are missing or still placeholders
        if not self.email or not self.password:
            # Try to read the file directly to show what's in it
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"\n   .env file content preview (first 100 chars): {content[:100]}")
            except Exception as e:
                print(f"\n   Could not read .env file: {e}")
            
            raise ValueError(
                "\n❌ ERROR: LinkedIn credentials not found or incomplete in .env file!\n\n"
                f"File location: {env_path}\n\n"
                "Please make sure your .env file contains EXACTLY these two lines (no quotes, no spaces around =):\n\n"
                "LINKEDIN_EMAIL=your_actual_email@example.com\n"
                "LINKEDIN_PASSWORD=your_actual_password\n\n"
                "Common issues:\n"
                "  - Missing LINKEDIN_EMAIL or LINKEDIN_PASSWORD line\n"
                "  - Extra spaces around the = sign\n"
                "  - Quotes around the values (don't use quotes)\n"
                "  - Empty values\n\n"
                "⚠️  Important: Replace the placeholder values with your actual LinkedIn test account credentials."
            )
        
        # Check if credentials are still placeholders
        if 'your_email' in self.email.lower() or 'your_password' in self.password.lower() or 'here' in self.password.lower():
            raise ValueError(
                "\n❌ ERROR: Please update your .env file with actual LinkedIn credentials!\n\n"
                "Your .env file currently contains placeholder values. Please replace them with:\n\n"
                "LINKEDIN_EMAIL=your_actual_email@example.com\n"
                "LINKEDIN_PASSWORD=your_actual_password\n\n"
                "⚠️  Use a test LinkedIn account, not your personal account."
            )
        
        print("✅ Credentials loaded successfully!\n")
    
    def setup_driver(self):
        """Setup Chrome driver with undetected-chromedriver."""
        options = uc.ChromeOptions()
        
        if self.headless:
            options.add_argument('--headless=new')
        
        # Use random user agent
        try:
            user_agent = self.ua.random
            options.add_argument(f'--user-agent={user_agent}')
        except:
            # Fallback user agent if fake-useragent fails
            pass
        
        # Basic options to avoid detection (keep it simple)
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Create driver - undetected-chromedriver handles most stealth features automatically
        print("Setting up Chrome driver...")
        try:
            self.driver = uc.Chrome(options=options, use_subprocess=True)
        except Exception as e:
            print(f"Warning: Error with use_subprocess, trying without: {e}")
            try:
                self.driver = uc.Chrome(options=options)
            except Exception as e2:
                print(f"Error creating Chrome driver: {e2}")
                raise
        
        self.driver.maximize_window()
        
        # Execute script to remove webdriver property (optional, UC handles this)
        try:
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                '''
            })
        except Exception as e:
            # This is optional, undetected-chromedriver already handles this
            pass
    
    def login(self):
        """Login to LinkedIn."""
        print("Logging in to LinkedIn...")
        self.driver.get("https://www.linkedin.com/login")
        
        # Wait for login page to load
        time.sleep(random.uniform(2, 4))
        
        try:
            # Find and fill email
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_field.send_keys(self.email)
            
            # Find and fill password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.send_keys(self.password)
            
            # Click login button
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait for navigation after login
            time.sleep(random.uniform(3, 5))
            
            # Check if login was successful (check for feed or profile)
            if "feed" in self.driver.current_url or "linkedin.com/in/" in self.driver.current_url:
                print("Login successful!")
                return True
            else:
                print("Login may have failed. Please check credentials.")
                return False
                
        except TimeoutException:
            print("Timeout while trying to login.")
            return False
        except Exception as e:
            print(f"Error during login: {str(e)}")
            return False
    
    def extract_profile_data(self, url):
        """
        Extract profile data from a LinkedIn profile URL.
        
        Args:
            url (str): LinkedIn profile URL
            
        Returns:
            dict: Extracted profile data
        """
        print(f"Scraping profile: {url}")
        
        try:
            self.driver.get(url)
            time.sleep(random.uniform(3, 6))  # Random delay to mimic human behavior
            
            profile_data = {
                'Name': '',
                'Headline': '',
                'Company': '',
                'Location': '',
                'About': ''
            }
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Extract Name - multiple selector strategies
            name_selectors = [
                "h1.text-heading-xlarge",
                "h1.pv-text-details__left-panel h1",
                "h1[data-generated-suggestion-target]",
                "main section h1",
                "h1"
            ]
            for selector in name_selectors:
                try:
                    name_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if name_element.text.strip():
                        profile_data['Name'] = name_element.text.strip()
                        break
                except NoSuchElementException:
                    continue
            
            # Extract Headline - multiple selector strategies
            headline_selectors = [
                ".text-body-medium.break-words",
                ".pv-text-details__left-panel .text-body-medium",
                ".ph5.pb5 .text-body-medium",
                "[data-generated-suggestion-target] + .text-body-medium",
                ".text-body-medium"
            ]
            for selector in headline_selectors:
                try:
                    headline_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if headline_element.text.strip():
                        profile_data['Headline'] = headline_element.text.strip()
                        break
                except NoSuchElementException:
                    continue
            
            # Extract Location - multiple selector strategies
            location_selectors = [
                ".text-body-small.inline.t-black--light.break-words",
                ".pv-text-details__left-panel .text-body-small",
                ".ph5.pb5 .text-body-small",
                "[data-test-id='location']",
                ".text-body-small"
            ]
            for selector in location_selectors:
                try:
                    location_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in location_elements:
                        text = elem.text.strip()
                        if text and ('•' not in text or len(text) > 5):  # Filter out separators
                            profile_data['Location'] = text
                            break
                    if profile_data['Location']:
                        break
                except NoSuchElementException:
                    continue
            
            # Extract Current Position / Company
            # Strategy 1: Try to find from experience section
            try:
                experience_selectors = [
                    "#experience ~ .pvs-list",
                    "section[data-section='experience']",
                    "#experience",
                    "[data-section='experience']",
                    "section[id*='experience']",
                    ".pvs-list[data-section='experience']"
                ]
                for exp_selector in experience_selectors:
                    try:
                        experience_section = self.driver.find_element(By.CSS_SELECTOR, exp_selector)
                        first_position = experience_section.find_element(
                            By.CSS_SELECTOR,
                            ".pvs-list__item:first-child, li:first-child, .pvs-entity:first-child, .pvs-list__outer-container:first-child"
                        )
                        company_text = first_position.text.strip()
                        if company_text:
                            # Extract company name (usually the second or last meaningful line)
                            lines = [line.strip() for line in company_text.split('\n') if line.strip() and len(line.strip()) > 2]
                            if len(lines) >= 2:
                                # Usually: Position title, Company name, Location/Duration
                                profile_data['Company'] = lines[1]  # Second line is usually company
                            elif len(lines) == 1:
                                profile_data['Company'] = lines[0]
                            else:
                                profile_data['Company'] = company_text
                            break
                    except NoSuchElementException:
                        continue
            except:
                pass
            
            # Strategy 2: Extract from headline if not found (get first company only)
            if not profile_data['Company'] and profile_data['Headline']:
                headline = profile_data['Headline']
                # Handle multiple companies separated by || or |
                if ' || ' in headline:
                    # Get the first part before ||
                    headline = headline.split(' || ')[0]
                elif ' | ' in headline:
                    headline = headline.split(' | ')[0]
                
                # Extract company from headline
                if ' at ' in headline:
                    parts = headline.split(' at ')
                    if len(parts) > 1:
                        company = parts[-1].strip()
                        # Clean up common suffixes
                        if company.endswith(' ||') or company.endswith(' |'):
                            company = company[:-3].strip()
                        profile_data['Company'] = company
                elif ' @ ' in headline:
                    parts = headline.split(' @ ')
                    if len(parts) > 1:
                        company = parts[-1].strip()
                        if company.endswith(' ||') or company.endswith(' |'):
                            company = company[:-3].strip()
                        profile_data['Company'] = company
                elif 'Intern' in headline or 'Developer' in headline or 'Engineer' in headline:
                    # Try to extract company after common job titles
                    for separator in [' @ ', ' at ', ' - ']:
                        if separator in headline:
                            parts = headline.split(separator, 1)
                            if len(parts) > 1:
                                company = parts[1].split(' ||')[0].split(' |')[0].strip()
                                if company:
                                    profile_data['Company'] = company
                                    break
            
            # Extract About section
            try:
                # Scroll to About section to ensure it's loaded
                try:
                    about_section_header = self.driver.find_element(By.XPATH, "//h2[contains(text(), 'About')] | //h2[@id='about'] | //span[contains(text(), 'About')]")
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", about_section_header)
                    time.sleep(1)
                except:
                    pass
                
                # Click "Show more" if it exists (multiple strategies)
                show_more_xpaths = [
                    "//button[contains(@aria-label, 'Show more')]",
                    "//button[contains(@aria-label, 'see more')]",
                    "//button[contains(@aria-label, 'See more')]",
                    "//span[contains(text(), 'Show more')]/ancestor::button",
                    "//span[contains(text(), 'see more')]/ancestor::button",
                    "//button[.//span[contains(text(), 'more')]]"
                ]
                for xpath in show_more_xpaths:
                    try:
                        show_more_buttons = self.driver.find_elements(By.XPATH, xpath)
                        for button in show_more_buttons:
                            if button.is_displayed():
                                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", button)
                                time.sleep(0.5)
                                self.driver.execute_script("arguments[0].click();", button)
                                time.sleep(1.5)
                                break
                    except:
                        continue
                
                # Try to find About section with multiple strategies
                about_selectors = [
                    "section[data-section='summary'] .inline-show-more-text",
                    "section[data-section='summary'] .pv-shared-text-with-see-more",
                    "#about ~ .display-flex .inline-show-more-text",
                    "#about ~ .pv-shared-text-with-see-more",
                    "section[id='about'] .inline-show-more-text",
                    "section[id='about'] .pv-shared-text-with-see-more",
                    "[data-section='summary'] .inline-show-more-text",
                    "[data-section='summary']",
                    "#about",
                    "section[id*='about']"
                ]
                for selector in about_selectors:
                    try:
                        about_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for elem in about_elements:
                            about_text = elem.text.strip()
                            # Filter out section headers and get actual content
                            if about_text and len(about_text) > 20 and 'About' not in about_text[:10]:
                                profile_data['About'] = about_text
                                break
                        if profile_data['About']:
                            break
                    except NoSuchElementException:
                        continue
                
                # Alternative: Try to find by text content near "About" header
                if not profile_data['About']:
                    try:
                        about_header = self.driver.find_element(By.XPATH, "//h2[contains(text(), 'About')] | //h2[@id='about']")
                        # Get the next sibling or parent's next sibling
                        about_content = self.driver.execute_script("""
                            var header = arguments[0];
                            var parent = header.parentElement;
                            var nextSibling = parent.nextElementSibling;
                            if (nextSibling) {
                                var text = nextSibling.innerText || nextSibling.textContent;
                                return text ? text.trim() : '';
                            }
                            return '';
                        """, about_header)
                        if about_content and len(about_content) > 20:
                            profile_data['About'] = about_content
                    except:
                        pass
            except Exception as e:
                pass
            
            print(f"Successfully scraped: {profile_data['Name']}")
            return profile_data
            
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return {
                'Name': '',
                'Headline': '',
                'Company': '',
                'Location': '',
                'About': ''
            }
    
    def read_urls_from_file(self, filename='linkedin_urls.txt'):
        """
        Read LinkedIn URLs from a text file.
        
        Args:
            filename (str): Path to the file containing URLs
            
        Returns:
            list: List of URLs
        """
        urls = []
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                for line in f:
                    url = line.strip()
                    if url and url.startswith('http'):
                        urls.append(url)
            print(f"Loaded {len(urls)} URLs from {filename}")
            return urls
        except FileNotFoundError:
            print(f"File {filename} not found. Please create it with LinkedIn profile URLs.")
            return []
    
    def save_to_csv(self, profiles_data, filename='profiles.csv'):
        """
        Save scraped profiles to CSV file.
        
        Args:
            profiles_data (list): List of dictionaries containing profile data
            filename (str): Output CSV filename
        """
        if not profiles_data:
            print("No data to save.")
            return
        
        fieldnames = ['Name', 'Headline', 'Company', 'Location', 'About']
        
        # Check if file exists to determine if we need to write headers
        file_exists = os.path.exists(filename)
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(profiles_data)
        
        print(f"Saved {len(profiles_data)} profiles to {filename}")
    
    def scrape_profiles(self, urls_file='linkedin_urls.txt', output_file='profiles.csv'):
        """
        Main method to scrape all profiles.
        
        Args:
            urls_file (str): File containing LinkedIn URLs
            output_file (str): Output CSV filename
        """
        try:
            # Setup driver
            self.setup_driver()
            
            # Login
            if not self.login():
                print("Failed to login. Exiting.")
                return
            
            # Read URLs
            urls = self.read_urls_from_file(urls_file)
            if not urls:
                return
            
            # Scrape each profile
            profiles_data = []
            for i, url in enumerate(urls, 1):
                print(f"\nProcessing profile {i}/{len(urls)}")
                profile_data = self.extract_profile_data(url)
                profiles_data.append(profile_data)
                
                # Random delay between profiles
                if i < len(urls):
                    delay = random.uniform(5, 10)
                    print(f"Waiting {delay:.1f} seconds before next profile...")
                    time.sleep(delay)
            
            # Save to CSV
            self.save_to_csv(profiles_data, output_file)
            
        except Exception as e:
            print(f"Error during scraping: {str(e)}")
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    print("\nBrowser closed.")
                except Exception:
                    # Ignore cleanup errors (harmless - happens during garbage collection)
                    pass
                finally:
                    # Explicitly set to None to help with cleanup
                    self.driver = None


def main():
    """Main function to run the scraper."""
    scraper = LinkedInScraper(headless=True)
    scraper.scrape_profiles()


if __name__ == "__main__":
    main()

