from app import app, db, Job
from datetime import datetime

print("🔄 Starting to add jobs...")

with app.app_context():
    # Delete all existing jobs
    deleted = Job.query.delete()
    print(f"Deleted {deleted} old jobs")
    
    # Create new real jobs
    real_jobs = [
        Job(title='Senior Network Administrator', company='Securiport', location='Dar es Salaam', job_type='onsite', salary='Negotiable', source='Mabumbe'),
        Job(title='Content Creator', company='Tanzania Football Federation', location='Dar es Salaam', job_type='onsite', salary='Negotiable', source='Mabumbe'),
        Job(title='Finance Officer', company='MSI Tanzania', location='Dar es Salaam', job_type='onsite', salary='Negotiable', source='Mabumbe'),
        Job(title='Human Resource Officer', company='Action Against Hunger', location='Dar es Salaam', job_type='hybrid', salary='Negotiable', source='Mabumbe'),
        Job(title='Operations Manager', company='Zee Collections', location='Dar es Salaam', job_type='onsite', salary='Negotiable', source='Mabumbe'),
        Job(title='Software Engineer', company='NMB Bank', location='Dar es Salaam', job_type='hybrid', salary='Negotiable', source='Ajirayako'),
        Job(title='Web Developer', company='Vodacom', location='Tanzania', job_type='remote', salary='Negotiable', source='Ajirayako'),
        Job(title='Data Scientist', company='CRDB Bank', location='Dar es Salaam', job_type='onsite', salary='Negotiable', source='Mabumbe'),
        Job(title='Aviation Security Officer', company='Swissport Tanzania', location='Dar es Salaam', job_type='onsite', salary='Negotiable', source='Mabumbe'),
        Job(title='Public Relations Officer', company='TAZARA', location='Dar es Salaam', job_type='onsite', salary='Negotiable', source='Ajirayako'),
    ]
    
    # Add all jobs to database
    for job in real_jobs:
        db.session.add(job)
    
    # Save changes
    db.session.commit()
    
    # Show result
    total = Job.query.count()
    print(f"\n✅ Successfully added {len(real_jobs)} real jobs!")
    print(f"📊 Total jobs in database: {total}")
    
    # Show all jobs
    print("\n📋 Jobs in database:")
    for job in Job.query.all():
        print(f"   - {job.title} ({job.source})")