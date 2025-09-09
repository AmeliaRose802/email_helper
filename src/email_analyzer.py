#!/usr/bin/env python3
"""
Email Analyzer - Handles email analysis (job matching, date extraction, links, etc.)
"""

import re
from datetime import datetime, timedelta


class EmailAnalyzer:
    def __init__(self, ai_processor=None):
        self.ai_processor = ai_processor
    
    def extract_due_date_intelligent(self, text):
        """Intelligent due date extraction"""
        text_lower = text.lower()
        
        # Simple relative dates
        if 'tomorrow' in text_lower:
            return (datetime.now() + timedelta(days=1)).strftime('%B %d, %Y')
        elif 'next week' in text_lower:
            return f"~{(datetime.now() + timedelta(days=7)).strftime('%B %d, %Y')}"
        elif 'end of week' in text_lower:
            days_ahead = 4 - datetime.now().weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return (datetime.now() + timedelta(days=days_ahead)).strftime('%B %d, %Y')
        
        # Date patterns
        patterns = [
            r'due\s+(?:by\s+)?(\w+\s+\d{1,2}(?:,\s+\d{4})?)',
            r'deadline:?\s*(\w+\s+\d{1,2}(?:,\s+\d{4})?)',
            r'expires?\s+(?:on\s+)?(\w+\s+\d{1,2}(?:,\s+\d{4})?)',
            r'by\s+(\w+\s+\d{1,2}(?:,\s+\d{4})?)',
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\w+\s+\d{1,2},\s+\d{4})',
            r'(\d{1,2}-\d{1,2}-\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                return match.group(1).strip()
        
        return "No specific deadline"
    
    def extract_links_intelligent(self, text):
        """Intelligent link extraction with context and image filtering"""
        urls = re.findall(r'http[s]?://[^\s<>"]+', text)
        
        categorized_links = []
        for url in urls[:10]:  # Check more URLs before limiting
            # Filter out image links and other non-actionable URLs
            if self._is_actionable_link(url):
                # Clean tracking parameters from the URL
                clean_url = self._clean_tracking_parameters(url)
                
                if 'forms.' in clean_url or 'survey' in clean_url:
                    categorized_links.append(f"Survey: {clean_url}")
                elif 'github.com' in clean_url or 'visualstudio.com' in clean_url:
                    categorized_links.append(f"Code: {clean_url}")
                elif 'docs.microsoft.com' in clean_url or 'aka.ms' in clean_url:
                    categorized_links.append(f"Docs: {clean_url}")
                elif 'teams.microsoft.com' in clean_url or 'outlook.com' in clean_url:
                    categorized_links.append(f"Meeting: {clean_url}")
                else:
                    categorized_links.append(clean_url)
            
            # Limit to 5 actionable links
            if len(categorized_links) >= 5:
                break
        
        return categorized_links
    
    def _clean_tracking_parameters(self, url):
        """Remove tracking parameters from URLs"""
        import urllib.parse as urlparse
        
        try:
            parsed = urlparse.urlparse(url)
            
            # Common tracking parameters to remove
            tracking_params = [
                'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term',
                'fbclid', 'gclid', '_hsenc', '_hsmi', 'mc_cid', 'mc_eid',
                'ref', 'source', 'campaign_id'
            ]
            
            # Parse query parameters
            query_params = urlparse.parse_qs(parsed.query)
            
            # Remove tracking parameters
            cleaned_params = {k: v for k, v in query_params.items() 
                            if k not in tracking_params}
            
            # Rebuild the URL
            new_query = urlparse.urlencode(cleaned_params, doseq=True)
            cleaned_url = urlparse.urlunparse((
                parsed.scheme, parsed.netloc, parsed.path,
                parsed.params, new_query, parsed.fragment
            ))
            
            return cleaned_url
        except Exception:
            # If URL parsing fails, return original URL
            return url
    
    def _is_actionable_link(self, url):
        """Filter out image links, tracking pixels, and other non-actionable URLs"""
        # Convert to lowercase for case-insensitive matching
        url_lower = url.lower()
        
        # Exclude specific protocols
        if url_lower.startswith(('cid:', 'data:', 'mailto:', 'tel:')):
            return False
        
        # Exclude image file extensions
        image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico', '.bmp', '.tif', '.tiff']
        if any(url_lower.endswith(ext) for ext in image_extensions):
            return False
        
        # Exclude common image/asset paths
        asset_paths = ['/images/', '/img/', '/icons/', '/logo/', '/assets/', '/static/']
        if any(path in url_lower for path in asset_paths):
            return False
        
        # Exclude tracking and analytics URLs
        tracking_domains = ['google-analytics.com', 'googletagmanager.com', 'doubleclick.net', 
                          'facebook.com/tr', 'linkedin.com/px', 'twitter.com/i/adsct']
        if any(domain in url_lower for domain in tracking_domains):
            return False
        
        # Exclude very short URLs that are likely not actionable
        if len(url) < 10:
            return False
        
        return True
    
    def extract_email_metadata(self, subject, body):
        """Extract both due date and links in one call to reduce duplication"""
        text_combined = f"{subject} {body}"
        return {
            'due_date': self.extract_due_date_intelligent(text_combined),
            'links': self.extract_links_intelligent(body)
        }
    
    def assess_job_qualification(self, email_subject, email_body):
        """AI-powered job qualification assessment"""
        if not self.ai_processor:
            return "Assessment unavailable - AI processor not initialized"
            
        subject = email_subject.lower()
        body = email_body.lower()
        
        try:
            skills_profile = self.ai_processor.get_job_skills()
            my_skills = self.parse_skills_from_profile(skills_profile)
            job_requirements = self.extract_job_requirements(subject, body)
            
            match_analysis = self.calculate_skill_match(my_skills, job_requirements)
            match_score = match_analysis['score']
            
            # Determine match level
            if match_score >= 85:
                level = "🟢 EXCELLENT MATCH"
            elif match_score >= 70:
                level = "🟢 STRONG MATCH"  
            elif match_score >= 50:
                level = "🟡 GOOD MATCH"
            elif match_score >= 30:
                level = "🟠 PARTIAL MATCH"
            else:
                level = "🔴 LIMITED MATCH"
            
            # Build assessment
            assessment_parts = [level]
            
            if match_analysis['key_matches']:
                top_matches = match_analysis['key_matches'][:3]
                assessment_parts.append(f"Strong in: {', '.join(top_matches)}")
            
            seniority = self.assess_seniority_match(subject, body)
            if seniority:
                assessment_parts.append(f"Level: {seniority}")
            
            if match_analysis['domain_strengths']:
                assessment_parts.append(f"Domain fit: {', '.join(match_analysis['domain_strengths'])}")
            
            if match_analysis['skill_gaps']:
                gaps = match_analysis['skill_gaps'][:2]
                assessment_parts.append(f"Gaps: {', '.join(gaps)}")
            
            return " | ".join(assessment_parts)
            
        except Exception as e:
            print(f"⚠️  Job qualification assessment failed: {e}")
            return "🔴 ASSESSMENT FAILED - Could not analyze job requirements"
    
    def parse_skills_from_profile(self, profile):
        """Parse skills from job skills profile"""
        profile_lower = profile.lower()
        
        skills = {
            'languages': [],
            'domains': [],
            'experience_years': 4,
            'level': 'Software Engineer II'
        }
        
        # Extract languages
        for lang in ['c++', 'rust', 'python', 'powershell', 'javascript', 'java', 'c#']:
            if lang in profile_lower:
                skills['languages'].append(lang)
        
        # Extract domains  
        for domain in ['azure', 'backend', 'security', 'cloud', 'frontend', 'devops']:
            if domain in profile_lower:
                skills['domains'].append(domain)
        
        # Extract experience level
        if 'senior' in profile_lower or 'lead' in profile_lower:
            skills['experience_years'] = 6
            skills['level'] = 'Senior Software Engineer'
        elif 'principal' in profile_lower:
            skills['experience_years'] = 8
            skills['level'] = 'Principal Software Engineer'
        elif 'junior' in profile_lower or 'entry' in profile_lower:
            skills['experience_years'] = 2
            skills['level'] = 'Junior Software Engineer'
        
        return skills
    
    def extract_job_requirements(self, subject, body):
        """Extract job requirements from posting"""
        text = f"{subject} {body}".lower()
        
        requirements = {
            'languages': [],
            'experience_level': 'mid',
            'domains': []
        }
        
        # Languages
        for lang in ['c++', 'rust', 'python', 'java', 'javascript', 'c#', 'go']:
            if lang in text:
                requirements['languages'].append(lang)
        
        # Experience level
        if any(term in text for term in ['senior', 'sr.', 'lead', 'principal']):
            requirements['experience_level'] = 'senior'
        elif any(term in text for term in ['junior', 'entry', 'new grad', 'graduate']):
            requirements['experience_level'] = 'junior'
        
        # Domains
        for domain in ['azure', 'cloud', 'security', 'backend', 'frontend', 'devops', 'machine learning', 'ai']:
            if domain in text:
                requirements['domains'].append(domain)
        
        return requirements
    
    def calculate_skill_match(self, my_skills, requirements):
        """Calculate detailed skill match analysis"""
        analysis = {
            'score': 0,
            'key_matches': [],
            'domain_strengths': [],
            'skill_gaps': []
        }
        
        score = 0
        
        # Language matches (30 points possible)
        language_matches = set(my_skills['languages']) & set(requirements['languages'])
        if language_matches:
            score += min(30, len(language_matches) * 15)
            analysis['key_matches'].extend(language_matches)
        
        # Domain matches (40 points possible)  
        domain_matches = set(my_skills['domains']) & set(requirements['domains'])
        if domain_matches:
            score += min(40, len(domain_matches) * 20)
            analysis['domain_strengths'].extend(domain_matches)
        
        # Experience level match (30 points possible)
        if requirements['experience_level'] == 'mid' and my_skills['experience_years'] >= 3:
            score += 30
        elif requirements['experience_level'] == 'senior' and my_skills['experience_years'] >= 5:
            score += 30
        elif requirements['experience_level'] == 'junior' and my_skills['experience_years'] >= 1:
            score += 25
        elif requirements['experience_level'] == 'senior' and my_skills['experience_years'] >= 3:
            score += 20  # Stretch opportunity
        elif requirements['experience_level'] == 'junior':
            score += 15  # Overqualified but still valid
        
        # Identify gaps
        language_gaps = set(requirements['languages']) - set(my_skills['languages'])
        analysis['skill_gaps'].extend(language_gaps)
        analysis['score'] = score
        
        return analysis
    
    def assess_seniority_match(self, subject, body):
        """Assess seniority level match"""
        text = f"{subject} {body}".lower()
        
        if any(term in text for term in ['senior', 'sr.', 'lead', 'principal']):
            return "Stretch role - senior level opportunity"
        elif any(term in text for term in ['software engineer ii', 'engineer ii', 'mid-level']):
            return "Perfect fit - matches current level"
        elif any(term in text for term in ['junior', 'entry', 'associate']):
            return "Below current level - overqualified"
        elif any(term in text for term in ['2-5 years', '3-5 years', '4+ years']):
            return "Experience range matches"
        
        return "Experience level unclear"
    
    def group_emails_by_thread(self, emails):
        """Group emails by conversation thread using subject and participants"""
        thread_groups = {}
        
        for email in emails:
            # Create thread key based on normalized subject and core participants
            thread_key = self._get_thread_key(email)
            
            if thread_key not in thread_groups:
                thread_groups[thread_key] = []
            
            thread_groups[thread_key].append(email)
        
        return thread_groups
    
    def _get_thread_key(self, email):
        """Generate a thread key for grouping related emails"""
        # Normalize subject by removing Re:, FW:, etc.
        subject = email.Subject.lower()
        subject = re.sub(r'^(re:|fw:|fwd:|forward:)\s*', '', subject).strip()
        subject = re.sub(r'\[.*?\]', '', subject).strip()  # Remove tags like [EXTERNAL]
        subject = re.sub(r'\s+', ' ', subject).strip()  # Normalize whitespace
        
        # Use only the normalized subject as the thread key
        # This allows proper grouping of conversation threads regardless of sender
        return subject
    
    def select_thread_representatives(self, thread_groups, max_emails):
        """Select the most representative email from each thread"""
        representatives = []
        
        # Sort thread groups by latest email date (most recent conversations first)
        sorted_threads = sorted(
            thread_groups.items(), 
            key=lambda x: max(email.ReceivedTime for email in x[1]),
            reverse=True
        )
        
        for thread_key, thread_emails in sorted_threads[:max_emails]:
            if len(thread_emails) == 1:
                # Single email - use as is
                representatives.append({
                    'representative': thread_emails[0],
                    'thread_count': 1,
                    'participants': [thread_emails[0].SenderName],
                    'latest_date': thread_emails[0].ReceivedTime,
                    'thread_emails': thread_emails
                })
            else:
                # Multiple emails in thread - select best representative
                representative_email = self.choose_best_representative(thread_emails)
                participants = list(set(email.SenderName for email in thread_emails))
                latest_date = max(email.ReceivedTime for email in thread_emails)
                
                representatives.append({
                    'representative': representative_email,
                    'thread_count': len(thread_emails),
                    'participants': participants,
                    'latest_date': latest_date,
                    'thread_emails': thread_emails
                })
        
        return representatives
    
    def choose_best_representative_email(self, thread_emails, purpose="general"):
        """Unified method to choose the best email from a thread for different purposes
        
        Args:
            thread_emails: List of emails in the thread
            purpose: 'general', 'actionable', or 'latest' to optimize selection
        """
        if len(thread_emails) == 1:
            return thread_emails[0]
        
        # Sort emails by date (newest first)
        sorted_emails = sorted(thread_emails, key=lambda x: x.ReceivedTime, reverse=True)
        
        if purpose == "actionable":
            return self._get_most_actionable_from_sorted(sorted_emails)
        elif purpose == "latest":
            return sorted_emails[0]
        else:  # general purpose
            return self._get_best_representative_from_sorted(sorted_emails)
    
    def _get_best_representative_from_sorted(self, sorted_emails):
        """Helper method for general representative selection"""
        # Strategy: Prefer the latest email that's not just "Thanks" or "Got it"
        for email in sorted_emails:
            try:
                body = email.Body[:5000] if hasattr(email, 'Body') and email.Body else ""
                body_lower = body.lower()
                subject = email.Subject.lower()
                
                # Skip very short responses
                if len(body) < 50 and any(phrase in body_lower for phrase in ['thanks', 'got it', 'received', 'ok']):
                    continue
                    
                # Skip auto-replies
                if 'auto' in subject or 'out of office' in body_lower:
                    continue
                    
                return email
            except:
                # If there's any error accessing properties, just use this email
                return email
        
        # Fallback: return the latest email
        return sorted_emails[0]
    
    def _get_most_actionable_from_sorted(self, sorted_emails):
        """Helper method for actionable email selection"""
        # Score emails based on actionable content indicators
        scored_emails = []
        
        for email in sorted_emails:
            body = email.Body[:5000] if email.Body else ""
            body_lower = body.lower()
            subject = email.Subject.lower()
            score = 0
            
            # Higher score for action keywords
            action_keywords = ['need', 'required', 'deadline', 'due', 'please', 'action', 'review', 'feedback', 'respond', 'complete']
            score += sum(2 for keyword in action_keywords if keyword in body_lower)
            
            # Higher score for dates and deadlines
            date_patterns = [r'\d{1,2}[/-]\d{1,2}', r'(monday|tuesday|wednesday|thursday|friday)', r'(january|february|march|april|may|june|july|august|september|october|november|december)']
            for pattern in date_patterns:
                if re.search(pattern, body_lower):
                    score += 1
            
            # Higher score for longer content (more context)
            if len(body) > 200:
                score += 1
            if len(body) > 500:
                score += 2
                
            # Lower score for auto-replies and acknowledgments
            if any(phrase in body_lower for phrase in ['thanks', 'received', 'got it', 'auto-reply']):
                score -= 2
                
            # Prefer more recent emails (slight bias)
            days_old = (datetime.now() - email.ReceivedTime.replace(tzinfo=None)).days
            if days_old < 1:
                score += 1
                
            scored_emails.append((email, score))
        
        # Return email with highest score
        return max(scored_emails, key=lambda x: x[1])[0]
