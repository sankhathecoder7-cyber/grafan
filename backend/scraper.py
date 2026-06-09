import requests
from bs4 import BeautifulSoup
import re
import time
import random
from datetime import datetime
from urllib.parse import urljoin, urlparse
import numpy as np
import traceback

# AI Libraries
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("⚠️ Run: pip install sentence-transformers scikit-learn")

class JobScraper:
    def __init__(self, debug=False):
        self.session = requests.Session()
        self.debug = debug
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        ]
        
        # Load AI model for job detection
        self.ai_model = None
        if AI_AVAILABLE:
            try:
                print("🧠 Loading AI model for job detection...")
                self.ai_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', device='cpu')
                print("✅ AI model loaded successfully!")
            except Exception as e:
                print(f"⚠️ AI model loading failed: {e}")
                print("   Continuing with keyword-based detection...")
        
        # Training data for job classification
        self.job_titles = [
            'software engineer', 'developer', 'data scientist', 'product manager',
            'marketing manager', 'sales executive', 'hr manager', 'accountant',
            'financial analyst', 'project manager', 'business analyst',
            'system administrator', 'network engineer', 'ux designer',
            'graphic designer', 'content writer', 'digital marketer',
            'customer service', 'office manager', 'procurement officer',
            'logistics coordinator', 'quality assurance', 'research assistant',
            'nurse', 'doctor', 'pharmacist', 'civil engineer',
            'electrical engineer', 'mechanical engineer', 'architect',
            'teacher', 'lecturer', 'professor', 'driver', 'security',
            'sales representative', 'store keeper', 'receptionist'
        ]
        
        # Create embeddings for job titles
        if self.ai_model:
            try:
                self.job_embeddings = self.ai_model.encode(self.job_titles)
                print(f"✅ Created embeddings for {len(self.job_titles)} job titles")
            except Exception as e:
                print(f"⚠️ Embedding creation failed: {e}")
                self.ai_model = None
    
    def log(self, message):
        if self.debug:
            print(f"  [DEBUG] {message}")
    
    def get_headers(self):
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def is_job_with_ai(self, text):
        """Use AI to detect if text is a job posting"""
        if not text:
            return False
            
        text_lower = text.lower()
        
        # Quick keyword check first (faster)
        job_keywords = ['job', 'vacancy', 'ajira', 'nafasi', 'kazi', 'position', 
                       'opportunity', 'hiring', 'career', 'employ', 'recruit',
                       'officer', 'manager', 'engineer', 'developer', 'specialist',
                       'consultant', 'analyst', 'coordinator', 'supervisor',
                       'director', 'assistant', 'associate']
        
        keyword_match = any(kw in text_lower for kw in job_keywords)
        
        if not keyword_match:
            return False
        
        # If AI is available, use it for better accuracy
        if self.ai_model and len(text) > 20:
            try:
                text_embedding = self.ai_model.encode([text[:500]])[0]
                similarities = cosine_similarity([text_embedding], self.job_embeddings)[0]
                max_similarity = np.max(similarities)
                self.log(f"Similarity score: {max_similarity:.2f} for '{text[:50]}...'")
                return max_similarity > 0.3
            except Exception as e:
                self.log(f"AI error: {e}")
                return keyword_match
        
        return keyword_match
    
    def scrape_any_url(self, url, source_name=None):
        """AI-powered scraping from any URL"""
        jobs = []
        source = source_name or f"Scraped-{url[:40]}"
        
        # Ensure URL has protocol
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        print(f"\n🧠 AI Scraping: {url}")
        print(f"   Source: {source}")
        
        try:
            # Fetch the page
            print(f"   📡 Fetching page...")
            response = self.session.get(url, headers=self.get_headers(), timeout=30)
            print(f"   📡 HTTP Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"   ❌ Failed to fetch page. Status code: {response.status_code}")
                return jobs
            
            print(f"   📄 Page size: {len(response.text)} bytes")
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            print(f"   📄 Page title: {soup.title.string if soup.title else 'No title'}")
            
            # Remove non-content elements
            for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
                tag.decompose()
            
            found_jobs = {}
            
            # Method 1: Look at headings (most reliable)
            print(f"   🔍 Searching for job headings...")
            for heading in soup.find_all(['h1', 'h2', 'h3', 'h4']):
                text = heading.get_text(strip=True)
                if 15 < len(text) < 200 and self.is_job_with_ai(text):
                    if text not in found_jobs:
                        company = self.extract_company(text)
                        if company == 'Various':
                            parent = heading.find_parent(['div', 'article', 'li', 'section'])
                            if parent:
                                parent_text = parent.get_text(strip=True)[:500]
                                company = self.extract_company(parent_text) or company
                        
                        found_jobs[text] = {
                            'title': text[:200],
                            'company': company,
                            'job_type': self.classify_job_type(text),
                            'location': self.extract_location(text),
                            'salary': self.extract_salary(text)
                        }
                        self.log(f"Found job: {text[:50]}...")
            
            # Method 2: Look at links with job indicators
            print(f"   🔍 Searching for job links...")
            for link in soup.find_all('a'):
                text = link.get_text(strip=True)
                if 15 < len(text) < 200 and self.is_job_with_ai(text):
                    if text not in found_jobs:
                        company = self.extract_company(text)
                        found_jobs[text] = {
                            'title': text[:200],
                            'company': company,
                            'job_type': self.classify_job_type(text),
                            'location': self.extract_location(text),
                            'salary': self.extract_salary(text)
                        }
                        self.log(f"Found job link: {text[:50]}...")
            
            # Method 3: Look at article/list elements
            print(f"   🔍 Searching for job articles...")
            selectors = ['article', '.job', '.post', '.listing', '.vacancy', '.position', '.career', '.opportunity']
            for selector in selectors:
                for elem in soup.find_all(selector):
                    text = elem.get_text(strip=True)
                    if 30 < len(text) < 500 and self.is_job_with_ai(text[:200]):
                        title_elem = elem.find(['h2', 'h3', 'h4', 'strong', 'a'])
                        title = title_elem.get_text(strip=True) if title_elem else text[:100]
                        if 15 < len(title) < 200 and self.is_job_with_ai(title):
                            if title not in found_jobs:
                                company = self.extract_company(title)
                                if company == 'Various':
                                    company = self.extract_company(text)
                                found_jobs[title] = {
                                    'title': title[:200],
                                    'company': company,
                                    'job_type': self.classify_job_type(title),
                                    'location': self.extract_location(text),
                                    'salary': self.extract_salary(text)
                                }
                                self.log(f"Found job article: {title[:50]}...")
            
            # Convert to job objects
            print(f"   📊 Found {len(found_jobs)} potential jobs")
            
            for title, job_data in list(found_jobs.items())[:50]:
                jobs.append({
                    'title': job_data['title'],
                    'company': job_data['company'] or 'Various',
                    'job_type': job_data['job_type'],
                    'location': job_data['location'] or 'Tanzania',
                    'salary': job_data['salary'],
                    'source': source,
                    'url': url,
                    'scraped_at': datetime.now().isoformat()
                })
            
            print(f"   ✅ Successfully scraped {len(jobs)} jobs")
            return jobs
            
        except requests.exceptions.Timeout:
            print(f"   ❌ Request timeout for {url}")
            return jobs
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection error for {url}")
            return jobs
        except Exception as e:
            print(f"   ❌ Error scraping {url}: {str(e)}")
            if self.debug:
                traceback.print_exc()
            return jobs
    
    # ============ SOURCE-SPECIFIC SCRAPING ============
    
    def scrape_mabumbe(self):
        print("\n" + "=" * 50)
        print("🧠 AI SCRAPING: Mabumbe")
        print("=" * 50)
        return self.scrape_any_url('https://mabumbe.com', 'Mabumbe')
    
    def scrape_ajirayako(self):
        print("\n" + "=" * 50)
        print("🧠 AI SCRAPING: Ajirayako")
        print("=" * 50)
        return self.scrape_any_url('https://ajirayako.co.tz', 'Ajirayako')
    
    def scrape_kaziconnect(self):
        print("\n" + "=" * 50)
        print("🧠 AI SCRAPING: Kaziconnect")
        print("=" * 50)
        return self.scrape_any_url('https://kaziconnect.co.tz', 'Kaziconnect')
    
    def scrape_dproz(self):
        print("\n" + "=" * 50)
        print("🧠 AI SCRAPING: Dproz")
        print("=" * 50)
        return self.scrape_any_url('https://www.dproz.com', 'Dproz')
    
    def scrape_custom_url(self, url):
        """Scrape any custom URL provided by user"""
        return self.scrape_any_url(url, f"Custom")
    
    def get_ajira_portal(self):
        return {
            'title': 'Government Jobs - Ajira Portal',
            'company': 'Government of Tanzania',
            'job_type': 'onsite',
            'location': 'Tanzania',
            'salary': 'See official portal',
            'source': 'Ajira Portal',
            'url': 'https://portal.ajira.go.tz',
            'scraped_at': datetime.now().isoformat()
        }
    
    # ============ HELPER FUNCTIONS ============
    
    def classify_job_type(self, text):
        text_lower = text.lower()
        if any(kw in text_lower for kw in ['remote', 'work from home', 'wfh', 'anywhere', 'virtual', 'home based', 'online']):
            return 'remote'
        elif any(kw in text_lower for kw in ['hybrid', 'flexible', 'mix', 'partially remote', 'partial remote']):
            return 'hybrid'
        elif any(kw in text_lower for kw in ['contract', 'freelance', 'gig', 'temporary', 'part-time', 'consultant']):
            return 'gig'
        else:
            return 'onsite'
    
    def extract_company(self, text):
        patterns = [
            r'at\s+([A-Za-z0-9\s&\.]+?)(?:\s+-|\s+\(|$|\s+is|\s+are|\s+in)',
            r'-\s+([A-Za-z0-9\s&\.]+?)(?:\s+-|\s+\(|$|\s+is)',
            r'with\s+([A-Za-z0-9\s&\.]+?)(?:\s+-|\s+\(|$)',
            r'for\s+([A-Za-z0-9\s&\.]+?)(?:\s+-|\s+\(|$)',
            r'by\s+([A-Za-z0-9\s&\.]+?)(?:\s+-|\s+\(|$)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                company = re.sub(r'\s+(is hiring|announces|seeks|wants|looking for)$', '', company, flags=re.I)
                company = re.sub(r'\s+\(.*?\)$', '', company)
                if len(company) > 2 and len(company) < 60:
                    return company
        return 'Various'
    
    def extract_location(self, text):
        locations = [
            'Dar es Salaam', 'Arusha', 'Mwanza', 'Dodoma', 'Tanga', 'Mbeya', 
            'Zanzibar', 'Kilimanjaro', 'Morogoro', 'Tabora', 'Kigoma', 
            'Singida', 'Rukwa', 'Ruvuma', 'Shinyanga', 'Simiyu', 'Kagera', 
            'Mara', 'Manyara', 'Njombe', 'Katavi', 'Geita', 'Lindi', 'Mtwara', 'Pwani'
        ]
        for loc in locations:
            if loc.lower() in text.lower():
                return loc
        return 'Tanzania'
    
    def extract_salary(self, text):
        patterns = [
            r'(?:TSh|TZS|TSH|Tsh|Tshs)\s*[\d,]+(?:\s*[-–]\s*[\d,]+)?',
            r'[\d,]+(?:\s*[-–]\s*[\d,]+)?\s*(?:TSh|TZS|TSH|Tsh|shillings)',
            r'(?:salary|mshahara):?\s*[\d,]+',
            r'up to\s*[\d,]+',
            r'[\d,]+(?:,\d{3})*(?:\s*[-–]\s*[\d,]+)?\s*\/\s*(?:month|week)'
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None
    
    # ============ MAIN AI ENGINE ============
    
    def scrape_all_sources(self):
        print("\n" + "=" * 60)
        print("🧠 GRAFAN AI JOB SCRAPING ENGINE")
        print("=" * 60)
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🤖 AI Model: {'ACTIVE' if self.ai_model else 'DISABLED'}")
        print("=" * 60)
        
        all_jobs = []
        
        # Scrape all predefined sources
        all_jobs.extend(self.scrape_mabumbe())
        time.sleep(2)
        
        all_jobs.extend(self.scrape_ajirayako())
        time.sleep(2)
        
        all_jobs.extend(self.scrape_kaziconnect())
        time.sleep(2)
        
        all_jobs.extend(self.scrape_dproz())
        
        # Add Ajira Portal link
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
        print("📊 AI SCRAPING SUMMARY")
        print("=" * 60)
        
        sources = ['Mabumbe', 'Ajirayako', 'Kaziconnect', 'Dproz', 'Ajira Portal']
        for source in sources:
            count = len([j for j in unique_jobs if j.get('source') == source])
            print(f"  {source:15} : {count:3} jobs")
        
        print("-" * 60)
        print(f"  {'TOTAL':15} : {len(unique_jobs):3} jobs")
        print("=" * 60)
        
        return unique_jobs


# For testing
if __name__ == '__main__':
    import sys
    
    scraper = JobScraper(debug=True)
    
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    else:
        test_url = input("Enter a job website URL to scrape: ")
    
    jobs = scraper.scrape_custom_url(test_url)
    
    print(f"\n✅ Found {len(jobs)} jobs:")
    for i, job in enumerate(jobs[:10]):
        print(f"{i+1}. {job['title']}")
        print(f"   Company: {job['company']} | Type: {job['job_type']} | Location: {job['location']}")
        if job['salary']:
            print(f"   Salary: {job['salary']}")
        print()