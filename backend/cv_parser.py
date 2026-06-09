import pdfplumber
import re
import os

class CVParser:
    def parse_pdf(self, file_path):
        """Extract text from PDF"""
        text = ""
        try:
            print(f"📄 Parsing PDF: {file_path}")
            print(f"📄 File size: {os.path.getsize(file_path)} bytes")
            
            with pdfplumber.open(file_path) as pdf:
                print(f"📄 Number of pages: {len(pdf.pages)}")
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text() or ""
                    text += page_text
                    print(f"📄 Page {i+1}: {len(page_text)} characters")
            
            print(f"📄 Total extracted text: {len(text)} characters")
            print(f"📄 First 200 chars: {text[:200]}")
            
        except Exception as e:
            print(f"❌ PDF parsing error: {e}")
            import traceback
            traceback.print_exc()
        
        return text
    
    def extract_info(self, text):
        """Extract personal info from CV text"""
        info = {
            'name': self.extract_name(text),
            'email': self.extract_email(text),
            'phone': self.extract_phone(text),
            'skills': self.extract_skills(text),
            'experience': self.extract_experience(text),
            'education': self.extract_education(text)
        }
        
        print(f"📊 Extracted: Name={info['name']}, Email={info['email']}, Phone={info['phone']}")
        
        return info
    
    def extract_name(self, text):
        # Try to find name at the beginning of CV
        lines = text.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if len(line) > 3 and len(line) < 50 and not any(kw in line.lower() for kw in ['email', 'phone', 'address', 'cv', 'resume', 'curriculum']):
                # Check if it looks like a name (contains letters and maybe spaces)
                if re.match(r'^[A-Za-z\s\.\'-]+$', line):
                    return line
        return ""
    
    def extract_email(self, text):
        match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        return match.group(0) if match else ""
    
    def extract_phone(self, text):
        # Tanzanian phone numbers
        patterns = [
            r'(\+255|0)[0-9]{9}',
            r'\(?\+255\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{6}',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return ""
    
    def extract_skills(self, text):
        skills_keywords = [
            'python', 'java', 'javascript', 'react', 'node', 'sql', 'aws', 'docker',
            'html', 'css', 'php', 'laravel', 'django', 'flask', 'mongodb', 'postgresql',
            'git', 'linux', 'excel', 'word', 'powerpoint', 'communication', 'leadership'
        ]
        found = []
        text_lower = text.lower()
        for skill in skills_keywords:
            if skill in text_lower:
                found.append(skill)
        return found[:10]  # Return top 10 skills
    
    def extract_experience(self, text):
        exp = []
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if re.search(r'\b(20\d{2})\s*[-–]\s*(20\d{2}|present)\b', line.lower()):
                if i+1 < len(lines):
                    exp.append(lines[i+1].strip()[:100])
                exp.append(line.strip())
        return exp[:5]  # Return top 5 experiences
    
    def extract_education(self, text):
        edu = []
        edu_keywords = [
            'bachelor', 'master', 'degree', 'diploma', 'university', 'college',
            'school', 'certificate', 'certification', 'bsc', 'msc', 'phd'
        ]
        lines = text.split('\n')
        for line in lines:
            line_lower = line.lower()
            if any(kw in line_lower for kw in edu_keywords):
                if len(line) > 10 and len(line) < 200:
                    edu.append(line.strip())
        return edu[:5]  # Return top 5 education entries