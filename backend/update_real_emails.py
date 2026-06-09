from app import app, db, Job

with app.app_context():
    # REAL recruiter emails
    updates = [
        ('NMB Bank', 'recruitment@nmb.co.tz'),
        ('CRDB Bank', 'recruitment@crdbbank.co.tz'),
        ('Selcom', 'hr@selcom.net'),
        ('Action Against Hunger', 'vacancies-hl@af-actionagainsthunger.org'),
        ('Tanzania Football Federation', 'tanfootball@tff.or.tz'),
        ('TFF', 'tanfootball@tff.or.tz'),
        ('Sotta Mining', 'hr.tanzania@perseusmining.com'),
        ('Sotta Mining Corporation', 'hr.tanzania@perseusmining.com'),
    ]
    
    count = 0
    for company, email in updates:
        jobs = Job.query.filter(Job.company.contains(company)).all()
        for job in jobs:
            job.recruiter_email = email
            count += 1
            print(f"✓ {job.title[:50]}... -> {email}")
    
    db.session.commit()
    print(f"\n✅ Updated {count} jobs with REAL recruiter emails!")
    print("\n📋 JOBS WITH REAL EMAILS:")
    
    for job in Job.query.filter(Job.recruiter_email.isnot(None)).all():
        if job.recruiter_email not in ['jobs@grafan.com', 'hr@securiport.com', 'hr@vodacom.co.tz', 'hr@huawei.co.tz', 'jobs@selcom.com']:
            print(f"   • {job.title} ({job.company}) -> {job.recruiter_email}")