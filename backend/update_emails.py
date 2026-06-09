from app import app, db, Job

with app.app_context():
    # Update recruiter emails for scraped jobs
    updates = [
        ('Securiport', 'hr@securiport.com'),
        ('Tanzania Football Federation', 'info@tff.or.tz'),
        ('MSI Tanzania', 'hr@msi.or.tz'),
        ('Action Against Hunger', 'hr@actionagainsthunger.org'),
        ('Zee Collections', 'hr@zeecollections.com'),
        ('Sotta Mining', 'hr@rottamining.com'),
        ('Swissport Tanzania', 'hr@swissport.co.tz'),
        ('TAZARA', 'hr@tazara.com'),
        ('CRDB Bank', 'recruitment@crdb.com'),
        ('NMB Bank', 'careers@nmb.co.tz'),
        ('Vodacom', 'hr@vodacom.co.tz'),
        ('Selcom', 'jobs@selcom.com'),
        ('Huawei', 'hr@huawei.co.tz'),
    ]
    
    count = 0
    for company, email in updates:
        jobs = Job.query.filter(Job.company.contains(company)).all()
        for job in jobs:
            job.recruiter_email = email
            count += 1
            print(f"✓ {job.title} -> {email}")
    
    db.session.commit()
    print(f"\n✅ Updated {count} jobs with recruiter emails!")