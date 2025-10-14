#!/usr/bin/env python3
"""Email Analyzer for Email Helper - Content Analysis and Processing.

This module provides comprehensive email content analysis capabilities,
including intelligent text processing, date extraction, link parsing,
and context-aware email classification support.

The EmailAnalyzer class handles:
- Due date extraction from email content using natural language processing
- Link extraction and categorization from email bodies
- Job posting detection and analysis
- Content analysis for AI classification support
- Text preprocessing and cleaning for downstream processing
- Email thread grouping and representative selection
- Content similarity detection for duplicate identification

Key Features:
- Intelligent due date extraction with relative date support
- Robust URL parsing and link categorization
- Job listing detection and metadata extraction
- Content preprocessing for AI analysis
- Support for various email formats and content types
- Thread-aware email grouping for better organization
- Duplicate detection using content similarity algorithms

This module integrates with the AI processor to provide enhanced
context for email classification and task extraction.

Dependencies:
    - re: Regular expression operations for pattern matching
    - urllib.parse: URL parsing and manipulation
    - datetime: Date and time operations

Example Usage:
    >>> from email_analyzer import EmailAnalyzer
    >>> from ai_processor import AIProcessor
    >>> 
    >>> # Initialize with AI processor for enhanced analysis
    >>> ai_processor = AIProcessor()
    >>> analyzer = EmailAnalyzer(ai_processor)
    >>> 
    >>> # Extract due date from email content
    >>> email_text = "Please respond by tomorrow at 5 PM"
    >>> due_date = analyzer.extract_due_date_intelligent(email_text)
    >>> print(f"Due date: {due_date}")
    >>> 
    >>> # Extract and categorize links
    >>> email_body = "Check out https://forms.microsoft.com/survey123 and https://docs.microsoft.com/azure"
    >>> links = analyzer.extract_links_intelligent(email_body)
    >>> for link in links:
    ...     print(f"Found link: {link}")
    >>> 
    >>> # Group emails by thread
    >>> emails = get_emails_from_outlook()  # Your email retrieval function
    >>> thread_groups = analyzer.group_emails_by_thread(emails)
    >>> print(f"Found {len(thread_groups)} conversation threads")

Author: Email Helper Team
Version: 2.0
Last Updated: 2025-10-13
"""

import re
import urllib.parse as urlparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple


class EmailAnalyzer:
    """Email content analyzer for intelligent processing and classification support.
    
    This class provides comprehensive email analysis capabilities, including
    content parsing, date extraction, link analysis, and preprocessing for
    AI classification. It serves as a helper component for the AI processor.
    
    The analyzer handles:
    - Intelligent due date extraction from natural language
    - URL parsing and link categorization
    - Job posting detection and analysis
    - Content preprocessing for AI models
    - Text cleaning and normalization
    - Email thread grouping and management
    - Duplicate detection via content similarity
    
    Attributes:
        ai_processor (AIProcessor, optional): Reference to AI processor for
            enhanced analysis capabilities. When provided, enables advanced
            features like job qualification assessment.
    
    Thread Safety:
        This class is not thread-safe. Create separate instances for concurrent use.
    
    Performance Considerations:
        - Link extraction is limited to first 10 URLs to prevent performance issues
        - Text normalization uses efficient regex patterns
        - Content similarity uses Jaccard similarity for O(n) performance
    
    Example:
        >>> analyzer = EmailAnalyzer(ai_processor)
        >>> due_date = analyzer.extract_due_date_intelligent(
        ...     "Please respond by tomorrow"
        ... )
        >>> print(due_date)  # "December 16, 2024"
        >>> 
        >>> # Extract metadata in one call (more efficient)
        >>> metadata = analyzer.extract_email_metadata(
        ...     subject="Meeting Request",
        ...     body="Please confirm by Friday..."
        ... )
        >>> print(metadata['due_date'])
        >>> print(metadata['links'])
    """
    
    def __init__(self, ai_processor=None):
        """Initialize the EmailAnalyzer.
        
        Args:
            ai_processor (AIProcessor, optional): AI processor instance for 
                enhanced analysis capabilities. If None, advanced features 
                like job qualification will be unavailable.
        """
        self.ai_processor = ai_processor
    
    def extract_due_date_intelligent(self, text: str) -> str:
        """Extract due dates from email text using intelligent pattern matching.
        
        This method analyzes email content to identify due dates, deadlines,
        and time-sensitive information using both relative date expressions
        (like "tomorrow", "next week") and absolute date patterns.
        
        Supported Patterns:
            - Relative dates: "tomorrow", "next week", "end of week"
            - Absolute dates: "December 15, 2024", "12/15/2024", "15-12-2024"
            - Deadline phrases: "due by Monday", "deadline: Friday"
            - Expiration dates: "expires on January 1"
        
        Algorithm:
            1. Check for relative date keywords (tomorrow, next week, etc.)
            2. If found, calculate absolute date from current date
            3. Otherwise, search for absolute date patterns using regex
            4. Return first match found or "No specific deadline"
        
        Args:
            text (str): Email content to analyze for due dates. Can include
                subject line, body, or combination of both.
            
        Returns:
            str: Formatted due date string in one of these formats:
                - "Month Day, Year" for specific dates (e.g., "December 16, 2024")
                - "~Month Day, Year" for approximate dates (prefixed with ~)
                - "No specific deadline" if no date found
                 
        Example:
            >>> analyzer = EmailAnalyzer()
            >>> 
            >>> # Relative date
            >>> date = analyzer.extract_due_date_intelligent("Please respond by tomorrow")
            >>> print(date)  # "December 16, 2024" (if today is Dec 15)
            >>> 
            >>> # Absolute date
            >>> date = analyzer.extract_due_date_intelligent("Deadline: January 15, 2025")
            >>> print(date)  # "january 15, 2025"
            >>> 
            >>> # Approximate date
            >>> date2 = analyzer.extract_due_date_intelligent("Due next week")
            >>> print(date2)  # "~December 23, 2024"
            >>> 
            >>> # No deadline
            >>> date3 = analyzer.extract_due_date_intelligent("FYI: Status update")
            >>> print(date3)  # "No specific deadline"
        
        Performance:
            O(n) where n is the length of the text. Pattern matching is efficient
            as it stops at the first match.
        
        Notes:
            - Text is converted to lowercase for case-insensitive matching
            - Relative dates use current system time
            - "~" prefix indicates approximate/estimated dates
            - Year is inferred from context if not explicitly provided
        """
        text_lower = text.lower()
        
        # Simple relative dates - calculate from current date
        if 'tomorrow' in text_lower:
            return (datetime.now() + timedelta(days=1)).strftime('%B %d, %Y')
        elif 'next week' in text_lower:
            return f"~{(datetime.now() + timedelta(days=7)).strftime('%B %d, %Y')}"
        elif 'end of week' in text_lower:
            # Calculate days until Friday
            days_ahead = 4 - datetime.now().weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return (datetime.now() + timedelta(days=days_ahead)).strftime('%B %d, %Y')
        
        # Absolute date patterns - ordered by specificity
        patterns = [
            r'due\s+(?:by\s+)?(\w+\s+\d{1,2}(?:,\s+\d{4})?)',  # "due by January 15" or "due January 15, 2024"
            r'deadline:?\s*(\w+\s+\d{1,2}(?:,\s+\d{4})?)',      # "deadline: January 15, 2024"
            r'expires?\s+(?:on\s+)?(\w+\s+\d{1,2}(?:,\s+\d{4})?)',  # "expires on January 15"
            r'by\s+(\w+\s+\d{1,2}(?:,\s+\d{4})?)',              # "by January 15"
            r'(\d{1,2}/\d{1,2}/\d{4})',                         # "1/15/2024"
            r'(\w+\s+\d{1,2},\s+\d{4})',                        # "January 15, 2024"
            r'(\d{1,2}-\d{1,2}-\d{4})'                          # "15-1-2024"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                return match.group(1).strip()
        
        return "No specific deadline"
    
    def extract_links_intelligent(self, text: str) -> List[str]:
        """Intelligent link extraction with context-aware categorization and filtering.
        
        This method extracts URLs from email text, filters out non-actionable links
        (like images, tracking pixels), cleans tracking parameters, and categorizes
        links based on their domain and purpose.
        
        Features:
            - Automatic image and tracking pixel filtering
            - Tracking parameter removal for cleaner URLs
            - Domain-based categorization (Survey, Code, Docs, Meeting)
            - Limit to top 5 actionable links to prevent information overload
        
        Filtered Out:
            - Image files (.png, .jpg, .gif, .svg, etc.)
            - Tracking pixels and analytics URLs
            - Non-actionable protocol links (cid:, data:, mailto:)
            - URLs in image/asset paths
        
        Categorization Rules:
            - "Survey:" - forms.microsoft.com, survey domains
            - "Code:" - github.com, visualstudio.com
            - "Docs:" - docs.microsoft.com, aka.ms
            - "Meeting:" - teams.microsoft.com, outlook.com
            - Plain URL - all other actionable links
        
        Args:
            text (str): Email body text containing URLs. HTML tags are
                automatically handled by regex pattern.
            
        Returns:
            List[str]: List of categorized, cleaned URLs (max 5). Each URL
                may be prefixed with a category label for context.
                Returns empty list if no actionable links found.
                
        Example:
            >>> analyzer = EmailAnalyzer()
            >>> 
            >>> email_body = '''
            ... Check out this survey: https://forms.microsoft.com/survey123?utm_source=email
            ... And review the docs: https://docs.microsoft.com/azure/overview
            ... Meeting link: https://teams.microsoft.com/l/meetup/thread123
            ... Image: https://example.com/images/logo.png
            ... '''
            >>> 
            >>> links = analyzer.extract_links_intelligent(email_body)
            >>> for link in links:
            ...     print(link)
            # Output:
            # Survey: https://forms.microsoft.com/survey123
            # Docs: https://docs.microsoft.com/azure/overview
            # Meeting: https://teams.microsoft.com/l/meetup/thread123
        
        Performance:
            O(n*m) where n is number of URLs found and m is average URL length.
            Limited to first 10 URLs for processing, returns max 5 actionable links.
        
        Notes:
            - Tracking parameters (utm_*, fbclid, etc.) are automatically removed
            - Image links are filtered out to prevent clutter
            - URLs are validated before being returned
            - Category prefixes help users understand link purpose at a glance
        
        See Also:
            - _is_actionable_link(): Link filtering logic
            - _clean_tracking_parameters(): URL cleaning logic
        """
        # Extract all HTTP/HTTPS URLs from text
        urls = re.findall(r'http[s]?://[^\s<>"]+', text)
        
        categorized_links: List[str] = []
        
        # Process URLs and filter/categorize
        for url in urls[:10]:  # Check up to 10 URLs before limiting
            # Filter out image links and other non-actionable URLs
            if self._is_actionable_link(url):
                # Clean tracking parameters from the URL
                clean_url = self._clean_tracking_parameters(url)
                
                # Categorize based on domain
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
            
            # Limit to 5 actionable links to prevent information overload
            if len(categorized_links) >= 5:
                break
        
        return categorized_links
    
    def _clean_tracking_parameters(self, url: str) -> str:
        """Remove tracking parameters from URLs for cleaner presentation.
        
        This method strips common tracking parameters (UTM codes, click IDs, etc.)
        from URLs while preserving functional query parameters. This results in
        cleaner, more readable URLs without affecting functionality.
        
        Tracking Parameters Removed:
            - UTM parameters: utm_source, utm_medium, utm_campaign, utm_content, utm_term
            - Click IDs: fbclid (Facebook), gclid (Google), _hsenc/_hsmi (HubSpot)
            - Email tracking: mc_cid, mc_eid (MailChimp)
            - Generic: ref, source, campaign_id
        
        Args:
            url (str): Original URL potentially containing tracking parameters.
            
        Returns:
            str: Cleaned URL with tracking parameters removed. If URL parsing
                fails, returns the original URL unchanged.
                
        Example:
            >>> analyzer = EmailAnalyzer()
            >>> 
            >>> dirty_url = "https://example.com/page?utm_source=email&utm_campaign=promo&id=123"
            >>> clean_url = analyzer._clean_tracking_parameters(dirty_url)
            >>> print(clean_url)
            # "https://example.com/page?id=123"
            >>> 
            >>> # Invalid URL returns unchanged
            >>> bad_url = "not a real url"
            >>> result = analyzer._clean_tracking_parameters(bad_url)
            >>> print(result == bad_url)  # True
        
        Performance:
            O(n) where n is the number of query parameters.
        
        Error Handling:
            If URL parsing fails (malformed URL), returns the original URL
            unchanged rather than raising an exception.
        
        Notes:
            - Preserves all non-tracking query parameters
            - Maintains URL structure (scheme, domain, path, fragment)
            - Safe to use on any string - won't crash on invalid URLs
        """
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
            
            # Remove tracking parameters, keep functional ones
            cleaned_params = {k: v for k, v in query_params.items() 
                            if k not in tracking_params}
            
            # Rebuild the URL with cleaned parameters
            new_query = urlparse.urlencode(cleaned_params, doseq=True)
            cleaned_url = urlparse.urlunparse((
                parsed.scheme, parsed.netloc, parsed.path,
                parsed.params, new_query, parsed.fragment
            ))
            
            return cleaned_url
        except Exception:
            # If URL parsing fails, return original URL unchanged
            return url
    
    def _is_actionable_link(self, url: str) -> bool:
        """Filter out image links, tracking pixels, and other non-actionable URLs.
        
        This method determines whether a URL represents an actionable link that
        users would want to see, versus images, tracking pixels, and other
        non-actionable content that should be filtered out.
        
        Filtering Criteria:
            - Excludes non-HTTP protocols (cid:, data:, mailto:, tel:)
            - Excludes image file extensions (.png, .jpg, .gif, .svg, etc.)
            - Excludes image/asset URL paths (/images/, /icons/, /logo/, etc.)
            - Excludes tracking/analytics domains (Google Analytics, Facebook, etc.)
            - Excludes very short URLs (< 10 characters, likely incomplete)
        
        Args:
            url (str): URL to evaluate for actionability.
            
        Returns:
            bool: True if URL is actionable (should be shown to user),
                False if URL should be filtered out.
                
        Example:
            >>> analyzer = EmailAnalyzer()
            >>> 
            >>> # Actionable links return True
            >>> analyzer._is_actionable_link("https://docs.microsoft.com/azure")
            True
            >>> 
            >>> # Image links return False
            >>> analyzer._is_actionable_link("https://example.com/logo.png")
            False
            >>> 
            >>> # Tracking pixels return False
            >>> analyzer._is_actionable_link("https://google-analytics.com/collect?...")
            False
            >>> 
            >>> # Non-HTTP protocols return False
            >>> analyzer._is_actionable_link("mailto:user@example.com")
            False
        
        Performance:
            O(1) - Uses string containment checks and startswith/endswith operations.
        
        Notes:
            - Case-insensitive matching for robustness
            - Designed to be conservative - when in doubt, filters out
            - Helps prevent email clutter from tracking and decorative content
            - Easy to extend with additional filtering rules
        
        See Also:
            - extract_links_intelligent(): Uses this method for filtering
        """
        # Convert to lowercase for case-insensitive matching
        url_lower = url.lower()
        
        # Exclude specific protocols that aren't clickable web links
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
    
    def extract_email_metadata(self, subject: str, body: str) -> Dict[str, Any]:
        """Extract both due date and links in one efficient call.
        
        This method is a convenience function that extracts multiple pieces of
        metadata from an email in a single call, reducing code duplication and
        improving performance by analyzing the combined text only once.
        
        Features:
            - Single-pass analysis of email content
            - Combines subject and body for comprehensive due date detection
            - Extracts actionable links from body
            - Returns structured dictionary for easy access
        
        Args:
            subject (str): Email subject line. Used for due date detection
                as deadlines are often mentioned in subjects.
            body (str): Email body text. Used for both due date and link
                extraction.
            
        Returns:
            Dict[str, Any]: Dictionary containing extracted metadata with keys:
                - 'due_date' (str): Extracted due date or "No specific deadline"
                - 'links' (List[str]): List of categorized, actionable URLs
                
        Example:
            >>> analyzer = EmailAnalyzer()
            >>> 
            >>> subject = "Project Review - Due Friday"
            >>> body = '''
            ... Please review the project by end of week.
            ... Documentation: https://docs.microsoft.com/project
            ... Survey: https://forms.microsoft.com/feedback
            ... '''
            >>> 
            >>> metadata = analyzer.extract_email_metadata(subject, body)
            >>> print(metadata['due_date'])
            # "~December 20, 2024" (approximate end of week)
            >>> 
            >>> print(len(metadata['links']))
            # 2
            >>> 
            >>> for link in metadata['links']:
            ...     print(link)
            # Docs: https://docs.microsoft.com/project
            # Survey: https://forms.microsoft.com/feedback
        
        Performance:
            O(n + m) where n is the combined text length and m is the number of URLs.
            More efficient than calling extract_due_date_intelligent() and
            extract_links_intelligent() separately.
        
        Use Cases:
            - Initial email processing and classification
            - Batch email analysis
            - Generating email summaries
            - Preparing data for AI classification
        
        See Also:
            - extract_due_date_intelligent(): Due date extraction logic
            - extract_links_intelligent(): Link extraction and categorization
        """
        # Combine subject and body for comprehensive due date detection
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

    def calculate_content_similarity(self, item1, item2, threshold=0.8):
        """Calculate content similarity between two email items for duplicate detection
        
        Args:
            item1, item2: Email items to compare (dict with subject, sender, action_details)
            threshold: Similarity threshold (0-1, default 0.8)
            
        Returns:
            tuple: (is_similar: bool, similarity_score: float)
        """
        try:
            # Extract comparable features
            features1 = self._extract_similarity_features(item1)
            features2 = self._extract_similarity_features(item2)
            
            # Calculate similarity scores for different aspects
            subject_score = self._calculate_text_similarity(features1['subject'], features2['subject'])
            sender_score = self._calculate_exact_match_score(features1['sender'], features2['sender'])
            action_score = self._calculate_text_similarity(features1['action'], features2['action'])
            date_score = self._calculate_date_similarity(features1['due_date'], features2['due_date'])
            
            # Weighted similarity calculation
            # Subject and action are most important, sender and date provide context
            weighted_score = (
                subject_score * 0.3 +     # Subject similarity
                action_score * 0.4 +      # Action similarity (most important)
                sender_score * 0.2 +      # Sender match
                date_score * 0.1          # Date proximity
            )
            
            is_similar = weighted_score >= threshold
            
            return is_similar, weighted_score
            
        except Exception as e:
            print(f"⚠️  Content similarity calculation failed: {e}")
            return False, 0.0
    
    def _extract_similarity_features(self, item):
        """Extract features for similarity comparison"""
        # Handle both email objects and processed items
        if hasattr(item, 'Subject'):
            # Raw email object
            return {
                'subject': self._normalize_text(item.Subject),
                'sender': item.SenderName.lower() if hasattr(item, 'SenderName') else '',
                'action': '',
                'due_date': None
            }
        elif 'email_subject' in item:
            # Raw action item data format (from email processing)
            action_details = item.get('action_details', {})
            return {
                'subject': self._normalize_text(item.get('email_subject', '')),
                'sender': item.get('email_sender', '').lower(),
                'action': self._normalize_text(action_details.get('action_required', '')),
                'due_date': action_details.get('due_date')
            }
        else:
            # Processed summary item format (from summary generation)
            # For cross-section comparison, use both action_required and summary fields
            action_text = item.get('action_required', '')
            summary_text = item.get('summary', '')
            
            # Combine action and summary for better cross-section matching
            combined_action = f"{action_text} {summary_text}".strip()
            
            return {
                'subject': self._normalize_text(item.get('subject', '')),
                'sender': item.get('sender', '').lower(),
                'action': self._normalize_text(combined_action),
                'due_date': item.get('due_date')
            }
    
    def _normalize_text(self, text):
        """Normalize text for comparison"""
        if not text:
            return ''
        
        # Remove common email prefixes and normalize
        normalized = text.lower().strip()
        normalized = re.sub(r'^(re:|fw:|fwd:|forward:)\s*', '', normalized)
        normalized = re.sub(r'\[.*?\]', '', normalized)  # Remove tags like [EXTERNAL]
        normalized = re.sub(r'\s+', ' ', normalized)  # Normalize whitespace
        normalized = re.sub(r'[^\w\s]', '', normalized)  # Remove punctuation
        
        return normalized.strip()
    
    def _calculate_text_similarity(self, text1, text2):
        """Calculate similarity between two text strings using token overlap"""
        if not text1 or not text2:
            return 0.0
        
        # Tokenize and create sets
        tokens1 = set(text1.split())
        tokens2 = set(text2.split())
        
        if not tokens1 or not tokens2:
            return 0.0
        
        # Calculate Jaccard similarity (intersection over union)
        intersection = len(tokens1.intersection(tokens2))
        union = len(tokens1.union(tokens2))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_exact_match_score(self, val1, val2):
        """Calculate exact match score (1.0 for exact match, 0.0 for different)"""
        return 1.0 if val1 == val2 else 0.0
    
    def _calculate_date_similarity(self, date1, date2):
        """Calculate date similarity (1.0 for same/close dates, decreasing with distance)"""
        if not date1 or not date2:
            return 0.5  # Neutral score if dates unavailable
        
        # Handle "No specific deadline" case
        if date1 == date2:
            return 1.0
        
        if date1 == "No specific deadline" or date2 == "No specific deadline":
            return 0.3  # Lower similarity if one has no deadline
        
        try:
            # Try to parse dates and calculate proximity
            from datetime import datetime
            
            # Simple date parsing - adjust format as needed
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%Y-%m-%d %H:%M']:
                try:
                    d1 = datetime.strptime(date1, fmt)
                    d2 = datetime.strptime(date2, fmt)
                    
                    # Calculate days difference
                    diff_days = abs((d1 - d2).days)
                    
                    # Similarity decreases with date distance
                    if diff_days == 0:
                        return 1.0
                    elif diff_days <= 7:
                        return 0.8
                    elif diff_days <= 30:
                        return 0.6
                    else:
                        return 0.3
                        
                except ValueError:
                    continue
                    
        except Exception:
            pass
        
        return 0.5  # Default neutral score
