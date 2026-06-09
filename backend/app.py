from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import threading
import time
from werkzeug.utils import secure_filename

from scraper import JobScraper
from cv_parser import CVParser
from email_sender import EmailSender

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///grafan.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# ============ MODELS ============
class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(100))
    job_type = db.Column(db.String(50))
    location = db.Column(db.String(100))
    salary = db.Column(db.String(100))
    description = db.Column(db.Text)
    source = db.Column(db.String(100))
    recruiter_email = db.Column(db.String(100))  # ← ADDED for recruiter emails
    posted_date = db.Column(db.DateTime, default=datetime.utcnow)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer)
    applicant_name = db.Column(db.String(100))
    applicant_email = db.Column(db.String(100))
    applicant_phone = db.Column(db.String(20))
    cv_filename = db.Column(db.String(200))
    cover_letter = db.Column(db.Text)
    applied_date = db.Column(db.DateTime, default=datetime.utcnow)

# Initialize database
with app.app_context():
    db.create_all()
    
    # Add sample jobs if empty
    if Job.query.count() == 0:
        sample_jobs = [
            Job(title='Software Engineer', company='NMB Bank', job_type='hybrid', location='Dar es Salaam', salary='TSh 1,500,000 - 2,500,000', source='Sample', recruiter_email='careers@nmb.co.tz'),
            Job(title='Web Developer', company='Vodacom', job_type='remote', location='Tanzania', salary='TSh 1,200,000 - 1,800,000', source='Sample', recruiter_email='hr@vodacom.co.tz'),
            Job(title='Data Scientist', company='CRDB Bank', job_type='onsite', location='Dar es Salaam', salary='TSh 2,000,000 - 3,000,000', source='Sample', recruiter_email='recruitment@crdb.com'),
            Job(title='UI/UX Designer', company='Selcom', job_type='hybrid', location='Dar es Salaam', salary='TSh 1,000,000 - 1,500,000', source='Sample', recruiter_email='jobs@selcom.com'),
            Job(title='DevOps Engineer', company='Huawei', job_type='remote', location='Tanzania', salary='TSh 2,500,000 - 3,500,000', source='Sample', recruiter_email='hr@huawei.co.tz'),
        ]
        db.session.add_all(sample_jobs)
        db.session.commit()
        print(f"✅ {len(sample_jobs)} sample jobs added!")

scraper = JobScraper()
cv_parser = CVParser()
email_sender = EmailSender()

# ============ AUTOMATIC SCHEDULED SCRAPING ============
def scheduled_auto_scrape():
    while True:
        try:
            print("\n" + "=" * 60)
            print("⏰ [SCHEDULER] Running automatic AI scraping...")
            print("=" * 60)
            
            with app.app_context():
                scraped = scraper.scrape_all_sources()
                new_count = 0
                for job_data in scraped:
                    existing = Job.query.filter_by(
                        title=job_data['title'], 
                        source=job_data.get('source', 'Scraped')
                    ).first()
                    if not existing:
                        job = Job(
                            title=job_data['title'],
                            company=job_data.get('company', 'Various'),
                            job_type=job_data.get('job_type', 'onsite'),
                            location=job_data.get('location', 'Tanzania'),
                            salary=job_data.get('salary'),
                            source=job_data.get('source', 'AI-Scraped'),
                            posted_date=datetime.now()
                        )
                        db.session.add(job)
                        new_count += 1
                db.session.commit()
                print(f"✅ [SCHEDULER] Scraping complete! Added {new_count} new jobs.")
                print(f"📊 Total jobs in database: {Job.query.count()}")
        except Exception as e:
            print(f"❌ [SCHEDULER] Error: {e}")
        time.sleep(21600)

scheduler_thread = threading.Thread(target=scheduled_auto_scrape, daemon=True)
scheduler_thread.start()
print("🕐 Automatic scraping scheduler started (every 6 hours)")

# ============ API ROUTES ============

@app.route('/')
def home():
    return jsonify({
        'name': 'Grafan AI Job Platform',
        'version': '4.0',
        'features': ['AI Scraping', 'CV Builder', 'Email notifications', 'Auto-scheduling']
    })

@app.route('/api/jobs')
def get_jobs():
    job_type = request.args.get('type', 'all')
    search = request.args.get('search', '')
    
    query = Job.query
    if job_type != 'all':
        query = query.filter_by(job_type=job_type)
    if search:
        query = query.filter(
            (Job.title.contains(search)) | 
            (Job.company.contains(search))
        )
    
    jobs = query.order_by(Job.posted_date.desc()).limit(100).all()
    
    return jsonify({
        'success': True,
        'count': len(jobs),
        'jobs': [{
            'id': j.id, 'title': j.title, 'company': j.company,
            'job_type': j.job_type, 'location': j.location,
            'salary': j.salary, 'source': j.source
        } for j in jobs]
    })

@app.route('/api/scrape', methods=['POST'])
def trigger_scrape():
    def scrape_bg():
        with app.app_context():
            print("\n🤖 Manual AI scraping triggered...")
            scraped = scraper.scrape_all_sources()
            new_count = 0
            for job_data in scraped:
                existing = Job.query.filter_by(
                    title=job_data['title'], 
                    source=job_data.get('source', 'Scraped')
                ).first()
                if not existing:
                    job = Job(
                        title=job_data['title'],
                        company=job_data.get('company', 'Various'),
                        job_type=job_data.get('job_type', 'onsite'),
                        location=job_data.get('location', 'Tanzania'),
                        salary=job_data.get('salary'),
                        source=job_data.get('source', 'AI-Scraped'),
                        posted_date=datetime.now()
                    )
                    db.session.add(job)
                    new_count += 1
            db.session.commit()
            print(f"✅ Manual scrape complete! Added {new_count} new jobs. Total: {Job.query.count()}")
    
    thread = threading.Thread(target=scrape_bg)
    thread.start()
    return jsonify({'success': True, 'message': 'AI scraping started!'})

@app.route('/api/scrape-url', methods=['POST'])
def scrape_custom_url():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    def scrape_bg():
        with app.app_context():
            print(f"\n🌐 AI Scraping custom URL: {url}")
            scraped = scraper.scrape_custom_url(url)
            new_count = 0
            for job_data in scraped:
                existing = Job.query.filter_by(title=job_data['title']).first()
                if not existing:
                    job = Job(
                        title=job_data['title'],
                        company=job_data.get('company', 'Various'),
                        job_type=job_data.get('job_type', 'onsite'),
                        location=job_data.get('location', 'Tanzania'),
                        salary=job_data.get('salary'),
                        source=f"Scraped: {url[:40]}",
                        posted_date=datetime.now()
                    )
                    db.session.add(job)
                    new_count += 1
            db.session.commit()
            print(f"✅ Added {new_count} jobs from {url}")
    
    thread = threading.Thread(target=scrape_bg)
    thread.start()
    return jsonify({'success': True, 'message': f'AI scraping started for {url}'})

@app.route('/api/cv/parse', methods=['POST'])
def parse_cv():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    text = cv_parser.parse_pdf(filepath)
    info = cv_parser.extract_info(text)
    
    return jsonify({'success': True, 'extracted': info})

# ============ APPLY WITH EMAIL TO RECRUITER ============
@app.route('/api/apply', methods=['POST'])
def apply_job():
    cv_filename = None
    cv_path = None
    
    # Handle CV upload
    if 'cv' in request.files:
        file = request.files['cv']
        if file and file.filename:
            cv_filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
            cv_path = os.path.join(app.config['UPLOAD_FOLDER'], cv_filename)
            file.save(cv_path)
    
    data = request.form
    job_id = data.get('job_id')
    job = Job.query.get(job_id)
    
    if not job:
        return jsonify({'success': False, 'message': 'Job not found'}), 404
    
    # Save application to database
    application = Application(
        job_id=job_id,
        applicant_name=data.get('name'),
        applicant_email=data.get('email'),
        applicant_phone=data.get('phone', ''),
        cv_filename=cv_filename,
        cover_letter=data.get('message', '')
    )
    db.session.add(application)
    db.session.commit()
    
    # Get recruiter email (use default if not set)
    recruiter_email = job.recruiter_email if job.recruiter_email else 'jobs@grafan.com'
    
    print(f"\n📧 Sending application email to recruiter: {recruiter_email}")
    print(f"   Job: {job.title} at {job.company}")
    print(f"   Applicant: {data.get('name')} ({data.get('email')})")
    
    # Send email to recruiter
    email_sender.send_application_email(
        to_email=recruiter_email,
        job_title=job.title,
        company=job.company,
        applicant_name=data.get('name'),
        applicant_email=data.get('email'),
        applicant_phone=data.get('phone', ''),
        cover_letter=data.get('message', ''),
        cv_path=cv_path
    )
    
    # Send confirmation email to applicant
    email_sender.send_confirmation_email(
        to_email=data.get('email'),
        applicant_name=data.get('name'),
        job_title=job.title,
        company=job.company
    )
    
    return jsonify({
        'success': True, 
        'message': 'Application submitted! Check your email for confirmation.',
        'application_id': application.id
    })

@app.route('/api/stats')
def get_stats():
    return jsonify({
        'total_jobs': Job.query.count(),
        'total_applications': Application.query.count(),
        'jobs_by_type': {
            'remote': Job.query.filter_by(job_type='remote').count(),
            'hybrid': Job.query.filter_by(job_type='hybrid').count(),
            'onsite': Job.query.filter_by(job_type='onsite').count(),
            'gig': Job.query.filter_by(job_type='gig').count()
        }
    })

@app.route('/api/sources')
def get_sources():
    sources = [
        {'name': 'Mabumbe', 'url': 'https://mabumbe.com', 'status': 'active'},
        {'name': 'Ajirayako', 'url': 'https://ajirayako.co.tz', 'status': 'active'},
        {'name': 'Kaziconnect', 'url': 'https://kaziconnect.co.tz', 'status': 'inactive'},
        {'name': 'Dproz', 'url': 'https://www.dproz.com', 'status': 'inactive'},
        {'name': 'Ajira Portal', 'url': 'https://portal.ajira.go.tz', 'status': 'link_only'}
    ]
    return jsonify({'success': True, 'sources': sources})

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 GRAFAN AI JOB PLATFORM v4.0")
    print("=" * 60)
    print(f"📍 API URL: http://localhost:5000")
    print(f"📋 Jobs API: http://localhost:5000/api/jobs")
    print(f"📊 Stats API: http://localhost:5000/api/stats")
    print(f"🤖 AI Scrape API: POST http://localhost:5000/api/scrape")
    print(f"🌐 Custom URL Scrape: POST http://localhost:5000/api/scrape-url")
    print(f"📧 Email notifications: ENABLED (sends to recruiters!)")
    print("=" * 60)
    print(f"📦 Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"📎 Uploads folder: {app.config['UPLOAD_FOLDER']}")
    print("=" * 60)
    print("✅ Server is running... Press CTRL+C to stop")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)