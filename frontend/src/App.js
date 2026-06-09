import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = 'http://localhost:5000/api';

function App() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [showPostForm, setShowPostForm] = useState(false);
  const [showApplyModal, setShowApplyModal] = useState(null);
  const [showCVBuilder, setShowCVBuilder] = useState(false);
  const [showUrlScraper, setShowUrlScraper] = useState(false);
  const [targetUrl, setTargetUrl] = useState('');
  const [scrapingUrl, setScrapingUrl] = useState(false);
  const [cvData, setCvData] = useState(null);
  const [stats, setStats] = useState({});

  useEffect(() => {
    loadJobs();
    loadStats();
  }, [filter, search]);

  const loadJobs = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_URL}/jobs?type=${filter}&search=${search}`);
      setJobs(res.data.jobs);
    } catch (error) {
      console.error('Error:', error);
    }
    setLoading(false);
  };

  const loadStats = async () => {
    try {
      const res = await axios.get(`${API_URL}/stats`);
      setStats(res.data);
    } catch (error) {
      console.error('Stats error:', error);
    }
  };

  const handleScrape = async () => {
    try {
      await axios.post(`${API_URL}/scrape`);
      alert('✅ AI Scraping started! Jobs will appear soon.');
      setTimeout(loadJobs, 5000);
    } catch (error) {
      alert('❌ Scraping failed');
    }
  };

  const handleUrlScrape = async () => {
    if (!targetUrl) {
      alert('Please enter a website URL');
      return;
    }
    
    setScrapingUrl(true);
    try {
      await axios.post(`${API_URL}/scrape-url`, { url: targetUrl });
      alert(`✅ AI scraping started for:\n${targetUrl}\n\nJobs will appear soon.`);
      setShowUrlScraper(false);
      setTargetUrl('');
      setTimeout(loadJobs, 8000);
    } catch (error) {
      alert('❌ Scraping failed. Make sure the URL is valid.');
    }
    setScrapingUrl(false);
  };

  const handlePostJob = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      await axios.post(`${API_URL}/jobs`, {
        title: fd.get('title'),
        company: fd.get('company'),
        job_type: fd.get('job_type'),
        location: fd.get('location'),
        salary: fd.get('salary')
      });
      alert('✅ Job posted!');
      setShowPostForm(false);
      loadJobs();
      loadStats();
    } catch (error) {
      alert('❌ Failed to post job');
    }
  };

  const handleApply = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      await axios.post(`${API_URL}/apply`, fd);
      alert('✅ Application submitted! Check your email for confirmation.');
      setShowApplyModal(null);
      loadStats();
    } catch (error) {
      alert('❌ Failed to submit application');
    }
  };

  const handleCVUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const res = await axios.post(`${API_URL}/cv/parse`, formData);
      setCvData(res.data.extracted);
      alert('✅ CV parsed successfully! Your information has been extracted.');
    } catch (error) {
      alert('❌ Failed to parse CV');
    }
  };

  const getTypeBadge = (type) => {
    const badges = { remote: '🏠 Remote', hybrid: '💻 Hybrid', onsite: '🏢 On-job', gig: '⚡ Gig' };
    return badges[type] || type;
  };

  const getSourceDisplay = (source) => {
    if (!source) return '📌 Source: Direct Post';
    if (source === 'Mabumbe') return '📌 Source: Mabumbe';
    if (source === 'Ajirayako') return '📌 Source: Ajirayako';
    if (source === 'Sample') return '📌 Source: GRAFAN (Sample)';
    if (source.startsWith('Scraped')) return `📌 Source: ${source}`;
    return `📌 Source: ${source}`;
  };

  return (
    <div className="app">
      {/* Main Layout - 2 columns */}
      <div className="main-layout">
        
        {/* LEFT COLUMN - Job Listings */}
        <div className="left-column">
          <header>
            <h1>🛠️ GRAFAN</h1>
            <p>AI-Powered Job Platform - Scrape ANY Website, Build CV, Apply with AI</p>
            <div className="stats-bar">
              <span>📋 {stats.total_jobs || 0} Jobs</span>
              <span>🏠 {stats.jobs_by_type?.remote || 0} Remote</span>
              <span>💻 {stats.jobs_by_type?.hybrid || 0} Hybrid</span>
              <span>🏢 {stats.jobs_by_type?.onsite || 0} On-job</span>
              <span>⚡ {stats.jobs_by_type?.gig || 0} Gig</span>
            </div>
            <div className="buttons">
              <button onClick={handleScrape} className="btn-ai">🤖 AI Scrape All</button>
              <button onClick={() => setShowUrlScraper(true)} className="btn-url">🌐 Scrape Any URL</button>
              <button onClick={() => setShowPostForm(true)} className="btn-post">📝 Post a Job</button>
              <button onClick={() => setShowCVBuilder(true)} className="btn-cv">📄 Build CV</button>
            </div>
          </header>

          <div className="search-filter">
            <input 
              type="text" 
              placeholder="🔍 Search jobs by title or company..." 
              value={search} 
              onChange={(e) => setSearch(e.target.value)} 
            />
            <div className="filters">
              {['all', 'remote', 'hybrid', 'onsite', 'gig'].map(t => (
                <button key={t} className={filter === t ? 'active' : ''} onClick={() => setFilter(t)}>
                  {t === 'all' ? '📋 All' : getTypeBadge(t)}
                </button>
              ))}
            </div>
          </div>

          <div className="jobs">
            {loading ? (
              <div className="loading">🔄 Loading jobs...</div>
            ) : jobs.length === 0 ? (
              <div className="empty">
                <p>😔 No jobs found</p>
                <button onClick={() => setShowUrlScraper(true)} className="link-btn">
                  🌐 Click here to scrape jobs from any website
                </button>
              </div>
            ) : (
              jobs.map(job => (
                <div key={job.id} className="job-card">
                  <h3>{job.title}</h3>
                  <p className="company">{job.company}</p>
                  <span className={`badge ${job.job_type}`}>{getTypeBadge(job.job_type)}</span>
                  {job.location && <p className="location">📍 {job.location}</p>}
                  {job.salary && <p className="salary">💰 {job.salary}</p>}
                  
                  {/* SOURCE DISPLAY - Shows where the job came from */}
                  <div className="job-source">
                    <span className="source-icon">📌</span>
                    <span className="source-text">{getSourceDisplay(job.source)}</span>
                  </div>
                  
                  <button onClick={() => setShowApplyModal(job)} className="apply-btn">📧 Apply Now</button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* RIGHT COLUMN - ADS SPACE */}
        <div className="right-column">
          <div className="ads-container">
            <div className="ad-card">
              <div className="ad-label">ADVERTISEMENT</div>
              <div className="ad-content">
                <div className="ad-space">
                  <p>📢</p>
                  <p className="ad-title">Advertise Here</p>
                  <p className="ad-text">Reach thousands of job seekers daily</p>
                  <button className="ad-btn">Contact Us</button>
                </div>
              </div>
            </div>

            <div className="ad-card sponsored">
              <div className="ad-label">SPONSORED</div>
              <div className="ad-content">
                <div className="ad-space">
                  <p>🏆</p>
                  <p className="ad-title">Featured Employers</p>
                  <p className="ad-text">Post your jobs and find top talent</p>
                  <button className="ad-btn">Post a Job</button>
                </div>
              </div>
            </div>

            <div className="ad-card">
              <div className="ad-label">PROMOTION</div>
              <div className="ad-content">
                <div className="ad-space">
                  <p>📚</p>
                  <p className="ad-title">CV Writing Services</p>
                  <p className="ad-text">Professional CV from TSh 50,000</p>
                  <button className="ad-btn">Learn More</button>
                </div>
              </div>
            </div>

            <div className="ad-card">
              <div className="ad-label">PARTNER</div>
              <div className="ad-content">
                <div className="ad-space">
                  <p>🎓</p>
                  <p className="ad-title">Online Courses</p>
                  <p className="ad-text">Upskill with top certifications</p>
                  <button className="ad-btn">View Courses</button>
                </div>
              </div>
            </div>

            <div className="ad-card">
              <div className="ad-label">INFO</div>
              <div className="ad-content">
                <div className="ad-space">
                  <p>🤖</p>
                  <p className="ad-title">AI Scraping</p>
                  <p className="ad-text">Scrape jobs from ANY website</p>
                  <button className="ad-btn" onClick={() => setShowUrlScraper(true)}>Try Now</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ============ MODALS ============ */}

      {/* URL Scraper Modal */}
      {showUrlScraper && (
        <div className="modal" onClick={() => setShowUrlScraper(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <button className="close" onClick={() => setShowUrlScraper(false)}>×</button>
            <h2>🌐 AI Job Scraper</h2>
            <p>Enter any website URL with job listings - AI will extract all jobs automatically</p>
            <input 
              type="url" 
              placeholder="https://example.com/jobs" 
              value={targetUrl}
              onChange={(e) => setTargetUrl(e.target.value)}
              className="url-input"
            />
            <button onClick={handleUrlScrape} disabled={scrapingUrl}>
              {scrapingUrl ? '🤖 AI Scraping in progress...' : '🚀 Start AI Scraping'}
            </button>
            <small>Examples: mabumbe.com, ajirayako.co.tz, dproz.com, brighterMonday.co.tz</small>
          </div>
        </div>
      )}

      {/* Post Job Modal */}
      {showPostForm && (
        <div className="modal" onClick={() => setShowPostForm(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <button className="close" onClick={() => setShowPostForm(false)}>×</button>
            <h2>📝 Post a Job</h2>
            <form onSubmit={handlePostJob}>
              <input name="title" placeholder="Job Title*" required />
              <input name="company" placeholder="Company Name*" required />
              <select name="job_type" required>
                <option value="onsite">🏢 On-job</option>
                <option value="remote">🏠 Remote</option>
                <option value="hybrid">💻 Hybrid</option>
                <option value="gig">⚡ Gig</option>
              </select>
              <input name="location" placeholder="Location" />
              <input name="salary" placeholder="Salary" />
              <button type="submit">Post Job</button>
            </form>
          </div>
        </div>
      )}

      {/* Apply Modal */}
      {showApplyModal && (
        <div className="modal" onClick={() => setShowApplyModal(null)}>
          <div className="modal-content large" onClick={e => e.stopPropagation()}>
            <button className="close" onClick={() => setShowApplyModal(null)}>×</button>
            <h2>📧 Apply for {showApplyModal.title}</h2>
            <p><strong>{showApplyModal.company}</strong></p>
            <form onSubmit={handleApply} encType="multipart/form-data">
              <input name="job_id" type="hidden" value={showApplyModal.id} />
              <input name="name" placeholder="Your Full Name*" required defaultValue={cvData?.name || ''} />
              <input name="email" type="email" placeholder="Your Email*" required defaultValue={cvData?.email || ''} />
              <input name="phone" placeholder="Your Phone" defaultValue={cvData?.phone || ''} />
              <div className="cv-upload">
                <label>Upload your CV (PDF):</label>
                <input name="cv" type="file" accept=".pdf" required />
              </div>
              <textarea name="message" placeholder="Cover Letter / Why you're a good fit..." rows="4" required />
              <button type="submit">Submit Application</button>
            </form>
            <p className="note">✨ You will receive a confirmation email after submitting.</p>
          </div>
        </div>
      )}

      {/* CV Builder Modal */}
      {showCVBuilder && (
        <div className="modal" onClick={() => setShowCVBuilder(false)}>
          <div className="modal-content large" onClick={e => e.stopPropagation()}>
            <button className="close" onClick={() => setShowCVBuilder(false)}>×</button>
            <h2>📄 Build Your CV</h2>
            <p>Upload your certificates or existing CV - AI will extract your information</p>
            <div className="cv-upload-area">
              <input type="file" accept=".pdf" onChange={handleCVUpload} />
              <small>Supported: PDF files (Degree, Diploma, CV, Certificates)</small>
            </div>
            {cvData && (
              <div className="cv-preview">
                <h3>Extracted Information:</h3>
                <p><strong>Name:</strong> {cvData.name || 'Not detected'}</p>
                <p><strong>Email:</strong> {cvData.email || 'Not detected'}</p>
                <p><strong>Phone:</strong> {cvData.phone || 'Not detected'}</p>
                <p><strong>Skills:</strong> {cvData.skills?.join(', ') || 'Not detected'}</p>
                <p><strong>Experience:</strong> {cvData.experience?.join(', ') || 'Not detected'}</p>
                <p><strong>Education:</strong> {cvData.education?.join(', ') || 'Not detected'}</p>
                <button onClick={() => alert('CV saved! Use it when applying for jobs.')}>Save CV</button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;