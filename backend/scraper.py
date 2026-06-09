import requests
from bs4 import BeautifulSoup
import re
import time
import random
from datetime import datetime
from urllib.parse import urljoin
import traceback

class JobScraper:
    def __init__(self, debug=False):
        self.session = requests.Session()
        self.debug = debug
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        ]
        
        # Known companies in Tanzania for fallback
        self.known_companies = [
            'NMB Bank', 'Vodacom', 'CRDB Bank', 'Selcom', 'Huawei', 'Tigo', 'Airtel',
            'World Vision', 'Action Against Hunger', 'Marie Stopes', 'Bolt', 'Tembo Nickel',
            'Tanzania Football Federation', 'TFF', 'NBC Bank', 'Braeburn', 'St. Constantine',
            'Milvik', 'Glory New Building', 'Jerusalem Mbezi', 'World Bank', 'UNICEF',
            'UNDP', 'WHO', 'Oxfam', 'Save the Children', 'Plan International',
            'KPMG', 'Deloitte', 'PwC', 'EY', 'Serengeti Breweries', 'Tanzania Breweries',
            'Bakhresa', 'Muhimbili Hospital', 'Aga Khan Hospital', 'Suma JKT', 'TANESCO'
        ]
        
        print("🤖 GRAFAN JOB SCRAPER READY (Keyword-based)")
        print("   Using smart keyword matching for job detection")
    
    def log(self, message):
        if self.debug:
            print(f"  [DEBUG] {message}")
    
    def get_headers(self):
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
    
    def is_job(self, text):
        """Check if text looks like a job posting"""
        if not text:
            return False
        
        text_lower = text.lower()
        job_keywords = [
            'job', 'vacancy', 'ajira', 'nafasi', 'kazi', 'position', 
            'opportunity', 'hiring', 'career', 'employ', 'recruit',
            'officer', 'manager', 'engineer', 'developer', 'specialist',
            'consultant', 'analyst', 'coordinator', 'supervisor',
            'director', 'assistant', 'associate', 'intern'
        ]
        
        return any(kw in text_lower for kw in job_keywords)
    
    def extract_company(self, text):
        """Extract company name from job title or description - IMPROVED"""
        text_clean = text.replace('\n', ' ').strip()
        
        # Pattern 1: "at Company Name"
        match = re.search(r'at\s+([A-Za-z0-9\s&\.]+?)(?:\s+-|\s+\(|$|\s+is|\s+in|\s+–)', text_clean, re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            if len(company) > 2 and len(company) < 60:
                return company
        
        # Pattern 2: "Company Name is hiring"
        match = re.search(r'^([A-Za-z0-9\s&\.]+?)\s+(?:is hiring|announces|seeks|wants|looking for)', text_clean, re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            if len(company) > 2 and len(company) < 60:
                return company
        
        # Pattern 3: "- Company Name" at end
        match = re.search(r'-\s+([A-Za-z0-9\s&\.]+?)$', text_clean, re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            if len(company) > 2 and len(company) < 60:
                return company
        
        # Pattern 4: "Job at Company Name"
        match = re.search(r'job\s+at\s+([A-Za-z0-9\s&\.]+?)(?:\s+\(|$)', text_clean, re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            if len(company) > 2 and len(company) < 60:
                return company
        
        # Pattern 5: "Company Name Vacancy"
        match = re.search(r'^([A-Za-z0-9\s&\.]+?)\s+(?:Vacancy|Job|Opportunity)', text_clean, re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            if len(company) > 2 and len(company) < 60:
                return company
        
        # Check known companies
        for company in self.known_companies:
            if company.lower() in text_clean.lower():
                return company
        
        return 'Various'
    
    def scrape_any_url(self, url, source_name=None):
        """Scrape jobs from any URL"""
        jobs = []
        source = source_name or f"Scraped-{url[:40]}"
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        print(f"\n🔍 Scraping: {url}")
        print(f"   Source: {source}")
        
        try:
            print(f"   📡 Fetching page...")
            response = self.session.get(url, headers=self.get_headers(), timeout=30)
            print(f"   📡 HTTP Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"   ❌ Failed to fetch page")
                return jobs
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove noise
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            
            found_jobs = {}
            
            # Method 1: Look at headings
            print(f"   🔍 Searching for job headings...")
            for heading in soup.find_all(['h1', 'h2', 'h3', 'h4']):
                text = heading.get_text(strip=True)
                if 15 < len(text) < 200 and self.is_job(text):
                    if text not in found_jobs:
                        found_jobs[text] = {
                            'title': text[:200],
                            'company': self.extract_company(text),
                            'job_type': self.classify_job_type(text),
                            'location': self.extract_location(text),
                            'salary': self.extract_salary(text)
                        }
                        self.log(f"Found job: {text[:50]}... (Company: {found_jobs[text]['company']})")
            
            # Method 2: Look at links
            print(f"   🔍 Searching for job links...")
            for link in soup.find_all('a'):
                text = link.get_text(strip=True)
                if 15 < len(text) < 200 and self.is_job(text):
                    if text not in found_jobs:
                        found_jobs[text] = {
                            'title': text[:200],
                            'company': self.extract_company(text),
                            'job_type': self.classify_job_type(text),
                            'location': self.extract_location(text),
                            'salary': self.extract_salary(text)
                        }
                        self.log(f"Found job link: {text[:50]}... (Company: {found_jobs[text]['company']})")
            
            print(f"   📊 Found {len(found_jobs)} potential jobs")
            
            for title, job_data in list(found_jobs.items())[:50]:
                jobs.append({
                    'title': job_data['title'],
                    'company': job_data['company'] if job_data['company'] != 'Various' else self.extract_company(title),
                    'job_type': job_data['job_type'],
                    'location': job_data['location'] or 'Tanzania',
                    'salary': job_data['salary'],
                    'source': source,
                    'url': url,
                    'scraped_at': datetime.now().isoformat()
                })
            
            print(f"   ✅ Successfully scraped {len(jobs)} jobs")
            return jobs
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return jobs
    
    def scrape_mabumbe(self):
        print("\n" + "=" * 50)
        print("📌 SCRAPING: Mabumbe")
        print("=" * 50)
        return self.scrape_any_url('https://mabumbe.com', 'Mabumbe')
    
    def scrape_ajirayako(self):
        print("\n" + "=" * 50)
        print("📌 SCRAPING: Ajirayako")
        print("=" * 50)
        return self.scrape_any_url('https://ajirayako.co.tz', 'Ajirayako')
    
    def scrape_kaziconnect(self):
        print("\n" + "=" * 50)
        print("📌 SCRAPING: Kaziconnect")
        print("=" * 50)
        return self.scrape_any_url('https://kaziconnect.co.tz', 'Kaziconnect')
    
    def scrape_dproz(self):
        print("\n" + "=" * 50)
        print("📌 SCRAPING: Dproz")
        print("=" * 50)
        return self.scrape_any_url('https://www.dproz.com', 'Dproz')
    
    def scrape_custom_url(self, url):
        return self.scrape_any_url(url, f"Custom")
    
    def get_ajira_portal(self):
        return {
            'title': 'Government Jobs - Ajira Portal',
            'company': 'Government of Tanzania',
            'job_type': 'onsite',
            'location': 'Tanzania',
            'salary': 'See portal',
            'source': 'Ajira Portal',
            'url': 'https://portal.ajira.go.tz',
        }
    
    def classify_job_type(self, text):
        text_lower = text.lower()
        if any(kw in text_lower for kw in ['remote', 'work from home', 'wfh']):
            return 'remote'
        elif any(kw in text_lower for kw in ['hybrid', 'flexible']):
            return 'hybrid'
        elif any(kw in text_lower for kw in ['contract', 'freelance', 'gig']):
            return 'gig'
        else:
            return 'onsite'
    
    def extract_location(self, text):
        locations = ['Dar es Salaam', 'Arusha', 'Mwanza', 'Dodoma', 'Tanga', 'Mbeya', 'Zanzibar', 
                     'Kilimanjaro', 'Morogoro', 'Tabora', 'Kigoma', 'Singida', 'Rukwa', 'Mtwara']
        for loc in locations:
            if loc.lower() in text.lower():
                return loc
        return 'Tanzania'
    
    def extract_salary(self, text):
        patterns = [r'(?:TSh|TZS|TSH)\s*[\d,]+', r'[\d,]+(?:\s*-\s*[\d,]+)?\s*(?:TSh|TZS|TSH)']
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None
    
    def scrape_all_sources(self):
        print("\n" + "=" * 60)
        print("📌 GRAFAN JOB SCRAPER (Keyword-based)")
        print("=" * 60)
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        all_jobs = []
        
        all_jobs.extend(self.scrape_mabumbe())
        time.sleep(2)
        
        all_jobs.extend(self.scrape_ajirayako())
        time.sleep(2)
        
        all_jobs.extend(self.scrape_kaziconnect())
        time.sleep(2)
        
        all_jobs.extend(self.scrape_dproz())
        
        all_jobs.append(self.get_ajira_portal())
        
        # Remove duplicates
        seen = set()
        unique_jobs = []
        for job in all_jobs:
            key = f"{job['title']}_{job['company']}"
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        print("\n" + "=" * 60)
        print("📊 SCRAPING SUMMARY")
        print("=" * 60)
        
        sources = ['Mabumbe', 'Ajirayako', 'Kaziconnect', 'Dproz', 'Ajira Portal']
        for source in sources:
            count = len([j for j in unique_jobs if j.get('source') == source])
            print(f"  {source:15} : {count:3} jobs")
        
        print("-" * 60)
        print(f"  {'TOTAL':15} : {len(unique_jobs):3} jobs")
        print("=" * 60)
        
        return unique_jobs