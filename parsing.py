import re
import logging
from typing import List
from urllib.parse import urlparse, unquote
import json
from pydantic import ValidationError
from state_management import LearningPath, ResearchQuality, ResearchResource

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResearchDataParser:
    """
    Robust parser for academic research data with fallback mechanisms.
    Handles malformed LLM outputs with production-ready error handling.
    """
    
    def __init__(self):
        """Initialize parser with compiled regex patterns for performance."""
        
        # Quality assessment heuristics
        self.QUALITY_INDICATORS = {
            'high_impact_journals': {
                'Nature', 'Science', 'Cell', 'PNAS', 'Nature Neuroscience', 
                'Neuron', 'Nature Methods', 'Nature Communications', 'Brain',
                'NeuroImage', 'Journal of Neuroscience', 'Current Biology'
            },
            'github_star_thresholds': {'high': 1000, 'medium': 100, 'low': 10},
            'educational_platforms': {
                'Coursera', 'edX', 'Khan Academy', 'MIT OpenCourseWare',
                'Udacity', 'Udemy', 'YouTube', 'Medium', 'Towards Data Science'
            },
            'difficulty_keywords': {
                'beginner': ['tutorial', 'introduction', 'getting started', 'basics', 'primer', 'fundamentals'],
                'intermediate': ['implementation', 'application', 'practice', 'hands-on', 'workshop'],
                'advanced': ['research', 'novel', 'state-of-the-art', 'cutting-edge', 'expert', 'advanced']
            }
        }
        
        # Compiled regex patterns for performance
        self._compile_patterns()
        
    def _compile_patterns(self):
        """Compile all regex patterns for better performance."""
        
        # Title extraction patterns (multiple fallbacks)
        self.title_patterns = [
            re.compile(r'"([^"]+)"', re.IGNORECASE),  # Quoted titles
            re.compile(r'\*\*([^*]+)\*\*', re.IGNORECASE),  # Bold markdown
            re.compile(r'\*([^*]+)\*', re.IGNORECASE),  # Italic markdown
            re.compile(r'^\d+\.\s*([^\n\r]+)', re.MULTILINE),  # Numbered lists
            re.compile(r'^-\s*([^\n\r]+)', re.MULTILINE),  # Bullet points
            re.compile(r'Title:\s*([^\n\r]+)', re.IGNORECASE),  # Explicit title labels
            re.compile(r'Paper:\s*([^\n\r]+)', re.IGNORECASE),  # Paper labels
            re.compile(r'([A-Z][^.!?]*[.!?])', re.MULTILINE),  # Sentence-like titles
        ]
        
        # URL extraction patterns with validation
        self.url_patterns = [
            # DOI patterns
            re.compile(r'(?:doi:|DOI:)\s*(10\.\d{4,}/[^\s]+)', re.IGNORECASE),
            re.compile(r'https?://(?:dx\.)?doi\.org/(10\.\d{4,}/[^\s]+)', re.IGNORECASE),
            # PubMed patterns
            re.compile(r'https?://(?:www\.)?ncbi\.nlm\.nih\.gov/pubmed/\d+', re.IGNORECASE),
            re.compile(r'https?://pubmed\.ncbi\.nlm\.nih\.gov/\d+/?', re.IGNORECASE),
            # ArXiv patterns
            re.compile(r'https?://arxiv\.org/(?:abs|pdf)/\d{4}\.\d{4,5}(?:v\d+)?', re.IGNORECASE),
            # GitHub patterns
            re.compile(r'https?://github\.com/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+/?', re.IGNORECASE),
            # General academic URLs
            re.compile(r'https?://[a-zA-Z0-9.-]+/[^\s]+', re.IGNORECASE),
        ]
        
        # Description extraction patterns
        self.description_patterns = [
            re.compile(r'Abstract:\s*([^\n\r]+(?:\n[^\n\r]+)*?)(?:\n\s*\n|$)', re.IGNORECASE | re.DOTALL),
            re.compile(r'Description:\s*([^\n\r]+(?:\n[^\n\r]+)*?)(?:\n\s*\n|$)', re.IGNORECASE | re.DOTALL),
            re.compile(r'Summary:\s*([^\n\r]+(?:\n[^\n\r]+)*?)(?:\n\s*\n|$)', re.IGNORECASE | re.DOTALL),
        ]
        
        # GitHub repository metadata patterns
        self.github_patterns = {
            'stars': re.compile(r'(\d+)\s*stars?', re.IGNORECASE),
            'forks': re.compile(r'(\d+)\s*forks?', re.IGNORECASE),
            'language': re.compile(r'Language:\s*([A-Za-z+#]+)', re.IGNORECASE),
            'license': re.compile(r'License:\s*([^\n\r]+)', re.IGNORECASE),
        }
        
        # Time estimation patterns
        self.time_patterns = [
            re.compile(r'(\d+)\s*(?:hours?|hrs?)', re.IGNORECASE),
            re.compile(r'(\d+)\s*(?:minutes?|mins?)', re.IGNORECASE),
            re.compile(r'(\d+)\s*(?:days?)', re.IGNORECASE),
            re.compile(r'(\d+)\s*(?:weeks?)', re.IGNORECASE),
            re.compile(r'(\d+)\s*(?:months?)', re.IGNORECASE),
        ]

    def _extract_text_between_markers(self, text: str, start_markers: List[str], 
                                     end_markers: List[str] = None) -> List[str]:
        """Extract text between various markdown/formatting markers."""
        extracted = []
        
        for start_marker in start_markers:
            if end_markers:
                for end_marker in end_markers:
                    pattern = re.compile(f'{re.escape(start_marker)}(.*?){re.escape(end_marker)}', 
                                       re.DOTALL | re.IGNORECASE)
                    matches = pattern.findall(text)
                    extracted.extend([match.strip() for match in matches])
            else:
                # Single marker extraction (e.g., after a colon)
                pattern = re.compile(f'{re.escape(start_marker)}\\s*([^\\n\\r]+)', re.IGNORECASE)
                matches = pattern.findall(text)
                extracted.extend([match.strip() for match in matches])
        
        return extracted

    def _normalize_url(self, url: str) -> str:
        """Normalize and validate URLs."""
        if not url:
            return ""
            
        # Remove common markdown formatting
        url = re.sub(r'[\[\]()]', '', url).strip()
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            if any(domain in url.lower() for domain in ['github.com', 'arxiv.org', 'doi.org']):
                url = 'https://' + url
            else:
                url = 'http://' + url
        
        # Clean up common URL issues
        url = unquote(url)  # Decode URL encoding
        url = re.sub(r'\s+', '', url)  # Remove whitespace
        
        return url

    def _assess_quality(self, title: str, url: str, description: str, 
                       resource_type: str) -> ResearchQuality:
        """Assess quality based on heuristics and content analysis."""
        
        try:
            # Academic rigor assessment
            academic_score = 1
            title_lower = title.lower()
            desc_lower = description.lower()
            
            # Check for high-impact journals in title/description
            for journal in self.QUALITY_INDICATORS['high_impact_journals']:
                if journal.lower() in title_lower or journal.lower() in desc_lower:
                    academic_score = 5
                    break
            
            # Check for academic keywords
            academic_keywords = ['peer-reviewed', 'published', 'journal', 'conference', 'research']
            if any(keyword in desc_lower for keyword in academic_keywords):
                academic_score = max(academic_score, 4)
            
            academic_score = max(1, min(5, academic_score))
            
            # Implementation quality (based on platform and indicators)
            impl_score = 3
            if 'github.com' in url:
                # Extract GitHub metrics if available
                stars_match = self.github_patterns['stars'].search(description)
                if stars_match:
                    stars = int(stars_match.group(1))
                    if stars >= self.QUALITY_INDICATORS['github_star_thresholds']['high']:
                        impl_score = 5
                    elif stars >= self.QUALITY_INDICATORS['github_star_thresholds']['medium']:
                        impl_score = 4
                    elif stars >= self.QUALITY_INDICATORS['github_star_thresholds']['low']:
                        impl_score = 3
                    else:
                        impl_score = 2
            
            impl_score = max(1, min(5, impl_score))
            
            # Educational value
            edu_score = 3
            parsed_url = urlparse(url)
            if any(platform.lower() in parsed_url.netloc.lower() 
                  for platform in self.QUALITY_INDICATORS['educational_platforms']):
                edu_score = 5
            elif any(keyword in desc_lower 
                    for keyword in ['tutorial', 'guide', 'howto', 'explanation']):
                edu_score = 4
            
            edu_score = max(1, min(5, edu_score))
            
            # Relevance score (based on neuroscience keywords)
            relevance_score = 3
            neuro_keywords = [
                'neuroscience', 'brain', 'neural', 'neuron', 'cognitive', 'fmri', 'eeg',
                'neuroimaging', 'connectivity', 'signal processing', 'machine learning'
            ]
            
            relevance_count = sum(1 for keyword in neuro_keywords 
                                if keyword in title_lower or keyword in desc_lower)
            
            if relevance_count >= 3:
                relevance_score = 5
            elif relevance_count >= 2:
                relevance_score = 4
            elif relevance_count >= 1:
                relevance_score = 3
            else:
                relevance_score = 2
                
            relevance_score = max(1, min(5, relevance_score))
            
            # Overall score calculation
            overall_score = (
                academic_score * 0.3 +
                impl_score * 0.25 +
                edu_score * 0.25 +
                relevance_score * 0.2
            )
            overall_score = max(1.0, min(5.0, overall_score))
            
            # Create and validate ResearchQuality using Pydantic
            return ResearchQuality(
                academic_rigor=academic_score,
                implementation_quality=impl_score,
                educational_value=edu_score,
                relevance_score=relevance_score,
                overall_score=overall_score
            )
            
        except (ValidationError, Exception) as e:
            logger.warning(f"Error in quality assessment: {e}")
            # Return default quality if assessment fails
            return ResearchQuality(
                academic_rigor=3,
                implementation_quality=3,
                educational_value=3,
                relevance_score=3,
                overall_score=3.0
            )

    def _determine_difficulty(self, title: str, description: str) -> str:
        """Determine difficulty level based on content analysis."""
        
        text_combined = (title + " " + description).lower()
        
        # Score each difficulty level
        scores = {'beginner': 0, 'intermediate': 0, 'advanced': 0}
        
        for level, keywords in self.QUALITY_INDICATORS['difficulty_keywords'].items():
            for keyword in keywords:
                scores[level] += text_combined.count(keyword)
        
        # Additional heuristics
        if any(word in text_combined for word in ['phd', 'research', 'novel', 'cutting-edge']):
            scores['advanced'] += 2
        
        if any(word in text_combined for word in ['application', 'implementation', 'practical']):
            scores['intermediate'] += 1
            
        if any(word in text_combined for word in ['intro', 'basic', 'start', 'begin']):
            scores['beginner'] += 2
        
        # Return highest scoring difficulty
        return max(scores.items(), key=lambda x: x[1])[0]

    def _parse_literature_output(self, raw_output: str) -> List[ResearchResource]:
        """
        Parse academic literature from potentially unstructured LLM output.
        Tries JSON extraction first, then falls back to text parsing.
        
        Args:
            raw_output: Raw text output from LLM containing literature references
            
        Returns:
            List of ResearchResource objects representing academic papers
        """
        
        resources = []
        
        if not raw_output or not raw_output.strip():
            logger.warning("Empty input provided to literature parser")
            return resources
        
        try:
            # First, try to extract JSON blocks
            json_pattern = r'```json\s*(.*?)\s*```'
            json_matches = re.findall(json_pattern, raw_output, re.DOTALL)
            
            if json_matches:
                for match in json_matches:
                    try:
                        data = json.loads(match)
                        if isinstance(data, list):
                            for item in data:
                                resources.append(self._parse_single_literature_resource(item))
                        elif isinstance(data, dict):
                            resources.append(self._parse_single_literature_resource(data))
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse JSON in literature output: {e}")
                        continue
            
            # If no JSON found or JSON parsing failed, try structured text parsing
            if not resources:
                resources = self._parse_literature_from_text(raw_output)
                
        except Exception as e:
            logger.error(f"Critical error in literature parsing: {e}")
            
        logger.info(f"Successfully parsed {len(resources)} literature resources")
        return resources[:10]  # Reasonable limit

    def _parse_single_literature_resource(self, data: dict) -> ResearchResource:
        """Parse a single literature resource from dict data with robust fallbacks"""
        try:
            # Extract basic fields with multiple fallback keys
            title = (data.get('title') or data.get('paper_title') or 
                    data.get('name') or 'Unknown Paper')
            
            url = (data.get('url') or data.get('doi') or data.get('link') or 
                  data.get('pubmed_url') or 'https://unknown-paper.com')
            
            description = (data.get('description') or data.get('abstract') or 
                         data.get('summary') or 'No description available')
            
            # Create quality assessment with defaults and validation
            quality_data = data.get('quality', {})
            try:
                quality = ResearchQuality(
                    academic_rigor=max(1, min(5, quality_data.get('academic_rigor', 4))),
                    implementation_quality=max(1, min(5, quality_data.get('implementation_quality', 3))),
                    educational_value=max(1, min(5, quality_data.get('educational_value', 4))),
                    relevance_score=max(1, min(5, quality_data.get('relevance_score', 4))),
                    overall_score=max(1.0, min(5.0, quality_data.get('overall_score', 3.8)))
                )
            except ValidationError:
                quality = ResearchQuality(
                    academic_rigor=4, implementation_quality=3,
                    educational_value=4, relevance_score=4, overall_score=3.8
                )
            
            # Extract prerequisites with validation
            prerequisites = data.get('prerequisites', [])
            if isinstance(prerequisites, str):
                prerequisites = [p.strip() for p in prerequisites.split(',')]
            prerequisites = prerequisites[:5] if isinstance(prerequisites, list) else []
            
            return ResearchResource(
                title=title[:200],  # Reasonable limit
                url=self._normalize_url(url),
                resource_type="paper",
                description=description[:500],  # Reasonable limit
                quality=quality,
                prerequisites=prerequisites,
                difficulty_level=data.get('difficulty_level', 'intermediate')
            )
        except ValidationError as e:
            logger.warning(f"Pydantic validation error parsing literature resource: {e}")
            # Return a minimal valid resource if parsing fails
            return ResearchResource(
                title="Failed to Parse Paper",
                url="https://unknown.com",
                resource_type="paper",
                description="Error parsing this resource",
                quality=ResearchQuality(
                    academic_rigor=2, implementation_quality=2, 
                    educational_value=2, relevance_score=2, overall_score=2.0
                ),
                difficulty_level="unknown"
            )
        except Exception as e:
            logger.warning(f"Error parsing single literature resource: {e}")
            # Return a minimal valid resource if parsing fails
            return ResearchResource(
                title="Failed to Parse Paper",
                url="https://unknown.com",
                resource_type="paper",
                description="Error parsing this resource",
                quality=ResearchQuality(
                    academic_rigor=2, implementation_quality=2, 
                    educational_value=2, relevance_score=2, overall_score=2.0
                ),
                difficulty_level="unknown"
            )

    def _parse_literature_from_text(self, text: str) -> List[ResearchResource]:
        """Parse literature resources from unstructured text with enhanced patterns"""
        resources = []
        
        try:
            # Enhanced patterns for academic papers
            title_patterns = [
                r'(?:Title|Paper):\s*([^\n]+)',
                r'\"([^\"]+)\"(?:\s*\([^)]*\))?',  # Quoted titles
                r'^\d+\.\s*([^\n]+)',              # Numbered lists
                r'\*\*([^*]+)\*\*',                # Bold markdown
                r'(?:^|\n)([A-Z][^.!?]*[.!?])',    # Sentence-like titles
            ]
            
            # Split text into potential paper sections
            sections = re.split(r'\n\s*\n|\n\d+\.\s+|---|\*\*\*', text)
            sections = [s.strip() for s in sections if len(s.strip()) > 20]
            
            for section in sections[:10]:  # Limit to first 10 sections
                try:
                    # Extract title using multiple patterns
                    title = None
                    for pattern in title_patterns:
                        match = re.search(pattern, section, re.MULTILINE)
                        if match:
                            title = match.group(1).strip()
                            break
                    
                    if not title:
                        # Use first meaningful sentence as title
                        sentences = re.split(r'[.!?]+', section)
                        if sentences:
                            title = sentences[0].strip()[:100]
                    
                    # Find URLs with preference for academic sources
                    urls = []
                    for pattern in self.url_patterns:
                        urls.extend(pattern.findall(section))
                    
                    # Prioritize academic URLs
                    url = "https://unknown-paper.com"
                    for found_url in urls:
                        normalized = self._normalize_url(str(found_url))
                        if any(domain in normalized.lower() 
                              for domain in ['doi.org', 'pubmed', 'arxiv.org']):
                            url = normalized
                            break
                    
                    if url == "https://unknown-paper.com" and urls:
                        url = self._normalize_url(str(urls[0]))
                    
                    # Extract description
                    description = ""
                    for pattern in self.description_patterns:
                        match = pattern.search(section)
                        if match:
                            description = match.group(1).strip()
                            break
                    
                    if not description:
                        # Use cleaned section as description
                        description = re.sub(r'\s+', ' ', section[:300]).strip()
                    
                    # Only add if we have a reasonable title
                    if title and len(title) > 5:
                        try:
                            resource = ResearchResource(
                                title=title,
                                url=url,
                                resource_type="paper",
                                description=description,
                                quality=self._assess_quality(title, url, description, "paper"),
                                difficulty_level=self._determine_difficulty(title, description)
                            )
                            resources.append(resource)
                        except ValidationError as e:
                            logger.warning(f"Pydantic validation failed for literature resource: {e}")
                            continue
                        
                except Exception as e:
                    logger.warning(f"Error parsing literature section: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error in literature text parsing: {e}")
        
        return resources

    def _parse_code_output(self, raw_output: str) -> List[ResearchResource]:
        """
        Parse code repositories and programming resources from LLM output.
        Tries JSON extraction first, then falls back to text parsing.
        
        Args:
            raw_output: Raw text output containing code repositories and tutorials
            
        Returns:
            List of ResearchResource objects representing code resources
        """
        
        resources = []
        
        if not raw_output or not raw_output.strip():
            logger.warning("Empty input provided to code parser")
            return resources
        
        try:
            # Try JSON extraction first
            json_pattern = r'```json\s*(.*?)\s*```'
            json_matches = re.findall(json_pattern, raw_output, re.DOTALL)
            
            if json_matches:
                for match in json_matches:
                    try:
                        data = json.loads(match)
                        if isinstance(data, list):
                            for item in data:
                                resources.append(self._parse_single_code_resource(item))
                        elif isinstance(data, dict):
                            resources.append(self._parse_single_code_resource(data))
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse JSON in code output: {e}")
                        continue
            
            # If no JSON found, parse from text
            if not resources:
                resources = self._parse_code_from_text(raw_output)
                
        except Exception as e:
            logger.error(f"Critical error in code parsing: {e}")
            
        logger.info(f"Successfully parsed {len(resources)} code resources")
        return resources[:10]  # Reasonable limit

    def _parse_single_code_resource(self, data: dict) -> ResearchResource:
        """Parse a single code resource from dict data with robust fallbacks"""
        try:
            title = (data.get('title') or data.get('name') or 
                    data.get('repository_name') or 'Unknown Repository')
            
            url = (data.get('url') or data.get('github_url') or 
                  data.get('repository_url') or data.get('link') or 
                  'https://github.com/unknown')
            
            description = (data.get('description') or data.get('readme') or 
                         data.get('summary') or 'No description available')
            
            # Validate and create quality assessment
            quality_data = data.get('quality', {})
            try:
                quality = ResearchQuality(
                    academic_rigor=max(1, min(5, quality_data.get('academic_rigor', 3))),
                    implementation_quality=max(1, min(5, quality_data.get('implementation_quality', 4))),
                    educational_value=max(1, min(5, quality_data.get('educational_value', 3))),
                    relevance_score=max(1, min(5, quality_data.get('relevance_score', 4))),
                    overall_score=max(1.0, min(5.0, quality_data.get('overall_score', 3.5)))
                )
            except ValidationError:
                quality = ResearchQuality(
                    academic_rigor=3, implementation_quality=4,
                    educational_value=3, relevance_score=4, overall_score=3.5
                )
            
            # Handle prerequisites
            prerequisites = data.get('prerequisites', ['Python', 'Basic programming'])
            if isinstance(prerequisites, str):
                prerequisites = [p.strip() for p in prerequisites.split(',')]
            prerequisites = prerequisites[:5] if isinstance(prerequisites, list) else ['Python']
            
            return ResearchResource(
                title=title[:200],
                url=self._normalize_url(url),
                resource_type="repository",
                description=description[:500],
                quality=quality,
                prerequisites=prerequisites,
                difficulty_level=data.get('difficulty_level', 'intermediate')
            )
        except ValidationError as e:
            logger.warning(f"Pydantic validation error parsing code resource: {e}")
            return ResearchResource(
                title="Failed to Parse Repository",
                url="https://github.com/unknown",
                resource_type="repository",
                description="Error parsing this repository",
                quality=ResearchQuality(
                    academic_rigor=2, implementation_quality=3,
                    educational_value=2, relevance_score=2, overall_score=2.3
                ),
                prerequisites=['Python'],
                difficulty_level="unknown"
            )
        except Exception as e:
            logger.warning(f"Error parsing single code resource: {e}")
            return ResearchResource(
                title="Failed to Parse Repository",
                url="https://github.com/unknown",
                resource_type="repository",
                description="Error parsing this repository",
                quality=ResearchQuality(
                    academic_rigor=2, implementation_quality=3,
                    educational_value=2, relevance_score=2, overall_score=2.3
                ),
                prerequisites=['Python'],
                difficulty_level="unknown"
            )

    def _parse_code_from_text(self, text: str) -> List[ResearchResource]:
        """Parse code resources from unstructured text with enhanced GitHub detection"""
        resources = []
        
        try:
            # Enhanced GitHub URL pattern
            github_pattern = r'https://github\.com/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+/?'
            github_urls = re.findall(github_pattern, text)
            
            # Repository name patterns
            repo_patterns = [
                r'(?:Repository|Repo|GitHub):\s*([^\n]+)',
                r'github\.com/[^/]+/([^/\s\)\]\}]+)',
                r'(?:^|\n)\d+\.\s*([^\n]*(?:repository|repo|github)[^\n]*)',
                r'\*\*([^*]+)\*\*.*?github',  # Bold titles near GitHub
            ]
            
            # Split into sections
            sections = re.split(r'\n\s*\n|\n\d+\.\s+|---|\*\*\*', text)
            sections = [s.strip() for s in sections if len(s.strip()) > 15]
            
            for section in sections[:8]:  # Limit to 8 sections
                try:
                    # Look for GitHub URLs in this section
                    github_match = re.search(github_pattern, section)
                    github_url = github_match.group() if github_match else None
                    
                    # Extract repository name/title
                    title = None
                    for pattern in repo_patterns:
                        match = re.search(pattern, section, re.IGNORECASE | re.MULTILINE)
                        if match:
                            title = match.group(1).strip()
                            # Clean up common patterns
                            title = re.sub(r'^[\d\.\-\*\s]+', '', title)
                            break
                    
                    if not title and github_url:
                        # Extract name from GitHub URL
                        url_match = re.search(r'github\.com/[^/]+/([^/\s\)\]\}]+)', github_url)
                        if url_match:
                            repo_name = url_match.group(1).replace('-', ' ').replace('_', ' ')
                            title = repo_name.title()
                    
                    if not title:
                        # Use first meaningful line as title
                        lines = [line.strip() for line in section.split('\n') if line.strip()]
                        if lines:
                            title = lines[0][:60]
                    
                    # Extract description
                    description = ""
                    for pattern in self.description_patterns:
                        match = pattern.search(section)
                        if match:
                            description = match.group(1).strip()
                            break
                    
                    if not description:
                        description = re.sub(r'\s+', ' ', section[:250]).strip()
                    
                    url = github_url or "https://github.com/unknown-repo"
                    
                    # Extract programming language
                    lang_match = self.github_patterns['language'].search(section)
                    prerequisites = ['Basic programming']
                    if lang_match:
                        lang = lang_match.group(1)
                        prerequisites = [f"{lang} programming"]
                    elif any(lang in section.lower() for lang in ['python', 'pytorch', 'tensorflow']):
                        prerequisites = ['Python programming']
                    
                    if title and len(title) > 3:
                        try:
                            resource = ResearchResource(
                                title=title,
                                url=url,
                                resource_type="repository", 
                                description=description,
                                quality=self._assess_quality(title, url, description, "repository"),
                                prerequisites=prerequisites,
                                difficulty_level=self._determine_difficulty(title, description)
                            )
                            resources.append(resource)
                        except ValidationError as e:
                            logger.warning(f"Pydantic validation failed for code resource: {e}")
                            continue
                        
                except Exception as e:
                    logger.warning(f"Error parsing code section: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error in code text parsing: {e}")
        
        return resources

    def _parse_educational_output(self, raw_output: str) -> List[ResearchResource]:
        """
        Parse educational content and tutorials from LLM output.
        Tries JSON extraction first, then falls back to text parsing.
        
        Args:
            raw_output: Raw text containing educational resources
            
        Returns:
            List of ResearchResource objects representing educational content
        """
        
        resources = []
        
        if not raw_output or not raw_output.strip():
            logger.warning("Empty input provided to educational parser")
            return resources
        
        try:
            # Try JSON extraction first
            json_pattern = r'```json\s*(.*?)\s*```'
            json_matches = re.findall(json_pattern, raw_output, re.DOTALL)
            
            if json_matches:
                for match in json_matches:
                    try:
                        data = json.loads(match)
                        if isinstance(data, list):
                            for item in data:
                                resources.append(self._parse_single_educational_resource(item))
                        elif isinstance(data, dict):
                            resources.append(self._parse_single_educational_resource(data))
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse JSON in educational output: {e}")
                        continue
            
            # Parse from text if no JSON
            if not resources:
                resources = self._parse_educational_from_text(raw_output)
                
        except Exception as e:
            logger.error(f"Critical error in educational parsing: {e}")
            
        logger.info(f"Successfully parsed {len(resources)} educational resources")
        return resources[:10]  # Reasonable limit

    def _parse_single_educational_resource(self, data: dict) -> ResearchResource:
        """Parse a single educational resource from dict data with robust fallbacks"""
        try:
            title = (data.get('title') or data.get('course_title') or 
                    data.get('name') or 'Unknown Educational Resource')
            
            url = (data.get('url') or data.get('link') or data.get('course_url') or 
                  'https://unknown-tutorial.com')
            
            description = (data.get('description') or data.get('summary') or 
                         data.get('overview') or 'No description available')
            
            resource_type = (data.get('resource_type') or data.get('type') or 
                           data.get('category') or 'tutorial')
            
            # Validate and create quality assessment
            quality_data = data.get('quality', {})
            try:
                quality = ResearchQuality(
                    academic_rigor=max(1, min(5, quality_data.get('academic_rigor', 3))),
                    implementation_quality=max(1, min(5, quality_data.get('implementation_quality', 3))),
                    educational_value=max(1, min(5, quality_data.get('educational_value', 4))),
                    relevance_score=max(1, min(5, quality_data.get('relevance_score', 4))),
                    overall_score=max(1.0, min(5.0, quality_data.get('overall_score', 3.5)))
                )
            except ValidationError:
                quality = ResearchQuality(
                    academic_rigor=3, implementation_quality=3,
                    educational_value=4, relevance_score=4, overall_score=3.5
                )
            
            # Handle prerequisites
            prerequisites = data.get('prerequisites', [])
            if isinstance(prerequisites, str):
                prerequisites = [p.strip() for p in prerequisites.split(',')]
            prerequisites = prerequisites[:5] if isinstance(prerequisites, list) else []
            
            return ResearchResource(
                title=title[:200],
                url=self._normalize_url(url),
                resource_type=resource_type,
                description=description[:500],
                quality=quality,
                prerequisites=prerequisites,
                difficulty_level=data.get('difficulty_level', 'beginner')
            )
        except ValidationError as e:
            logger.warning(f"Pydantic validation error parsing educational resource: {e}")
            return ResearchResource(
                title="Failed to Parse Educational Resource",
                url="https://unknown.com",
                resource_type="tutorial",
                description="Error parsing this resource",
                quality=ResearchQuality(
                    academic_rigor=2, implementation_quality=2,
                    educational_value=3, relevance_score=2, overall_score=2.3
                ),
                difficulty_level="unknown"
            )
        except Exception as e:
            logger.warning(f"Error parsing single educational resource: {e}")
            return ResearchResource(
                title="Failed to Parse Educational Resource",
                url="https://unknown.com",
                resource_type="tutorial",
                description="Error parsing this resource",
                quality=ResearchQuality(
                    academic_rigor=2, implementation_quality=2,
                    educational_value=3, relevance_score=2, overall_score=2.3
                ),
                difficulty_level="unknown"
            )

    def _parse_educational_from_text(self, text: str) -> List[ResearchResource]:
        """Parse educational resources from unstructured text with enhanced detection"""
        resources = []
        
        try:
            # Enhanced educational resource patterns
            title_patterns = [
                r'(?:Title|Tutorial|Course|Guide|Lesson):\s*([^\n]+)',
                r'(?:^|\n)\d+\.\s*([^\n]+)',
                r'\"([^\"]+)\"',
                r'\*\*([^*]+)\*\*',  # Bold markdown
            ]
            
            # Resource type detection
            resource_type_patterns = {
                'course': r'\b(course|class|lesson|module)\b',
                'video': r'\b(video|youtube|watch|tutorial video)\b',
                'blog': r'\b(blog|article|post|medium)\b',
                'tutorial': r'\b(tutorial|guide|howto|walkthrough)\b',
                'book': r'\b(book|ebook|pdf|manual)\b',
                'documentation': r'\b(documentation|docs|reference)\b'
            }
            
            # Split into sections
            sections = re.split(r'\n\s*\n|\n\d+\.\s+|---|\*\*\*', text)
            sections = [s.strip() for s in sections if len(s.strip()) > 20]
            
            for section in sections[:10]:
                try:
                    # Extract title
                    title = None
                    for pattern in title_patterns:
                        match = re.search(pattern, section, re.MULTILINE)
                        if match:
                            title = match.group(1).strip()
                            # Clean up common patterns
                            title = re.sub(r'^[\d\.\-\*\s]+', '', title)
                            break
                    
                    if not title:
                        lines = [line.strip() for line in section.split('\n') if line.strip()]
                        if lines:
                            title = lines[0][:80]
                    
                    # Extract URL
                    urls = []
                    for pattern in self.url_patterns:
                        urls.extend(pattern.findall(section))
                    
                    # Prioritize educational platform URLs
                    edu_platforms = ['coursera.org', 'edx.org', 'udacity.com', 'khanacademy.org', 
                                   'youtube.com', 'medium.com']
                    url = "https://unknown-tutorial.com"
                    
                    for found_url in urls:
                        normalized = self._normalize_url(str(found_url))
                        if any(platform in normalized.lower() for platform in edu_platforms):
                            url = normalized
                            break
                    
                    if url == "https://unknown-tutorial.com" and urls:
                        url = self._normalize_url(str(urls[0]))
                    
                    # Determine resource type
                    resource_type = "tutorial"  # default
                    section_lower = section.lower()
                    
                    for r_type, pattern in resource_type_patterns.items():
                        if re.search(pattern, section_lower):
                            resource_type = r_type
                            break
                    
                    # Extract description
                    description = ""
                    for pattern in self.description_patterns:
                        match = pattern.search(section)
                        if match:
                            description = match.group(1).strip()
                            break
                    
                    if not description:
                        description = re.sub(r'\s+', ' ', section[:300]).strip()
                    
                    # Extract duration/time estimates
                    estimated_time = ""
                    for pattern in self.time_patterns:
                        match = pattern.search(section)
                        if match:
                            time_value = match.group(1)
                            time_unit = pattern.pattern.split('\\s*(?:')[1].split('|')[0]
                            estimated_time = f"{time_value} {time_unit}"
                            break
                    
                    # Extract prerequisites
                    prerequisites = []
                    prereq_patterns = [
                        r'(?:Prerequisites?|Requirements?|Before starting):\s*([^\n\r]+)',
                        r'(?:You should know|Assumed knowledge):\s*([^\n\r]+)',
                    ]
                    
                    for pattern in prereq_patterns:
                        match = re.search(pattern, section, re.IGNORECASE)
                        if match:
                            prerequisites = [p.strip() for p in match.group(1).split(',')][:5]
                            break
                    
                    if title and len(title) > 5:
                        try:
                            resource = ResearchResource(
                                title=title,
                                url=url,
                                resource_type=resource_type,
                                description=description,
                                quality=self._assess_quality(title, url, description, resource_type),
                                prerequisites=prerequisites,
                                difficulty_level=self._determine_difficulty(title, description)
                            )
                            resources.append(resource)
                        except ValidationError as e:
                            logger.warning(f"Pydantic validation failed for educational resource: {e}")
                            continue
                        
                except Exception as e:
                    logger.warning(f"Error parsing educational section: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error in educational text parsing: {e}")
        
        return resources

    def _parse_synthesis_output(self, raw_output: str) -> LearningPath:
        """
        Parse comprehensive learning recommendations into a structured learning path.
        Tries JSON extraction first, then falls back to text parsing.
        
        Args:
            raw_output: Raw text containing learning path recommendations
            
        Returns:
            LearningPath object with structured learning progression
        """
        
        if not raw_output or not raw_output.strip():
            logger.warning("Empty input provided to synthesis parser")
            return self._create_default_learning_path()
        
        try:
            # Try to extract JSON first
            json_pattern = r'```json\s*(.*?)\s*```'
            json_match = re.search(json_pattern, raw_output, re.DOTALL)
            
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                    return self._parse_learning_path_from_dict(data)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON in synthesis output: {e}")
            
            # Fall back to text parsing
            return self._parse_learning_path_from_text(raw_output)
            
        except Exception as e:
            logger.error(f"Critical error in synthesis parsing: {e}")
            return self._create_default_learning_path()

    def _parse_learning_path_from_dict(self, data: dict) -> LearningPath:
        """Parse learning path from dictionary data with robust fallbacks"""
        try:
            topic = (data.get('topic') or data.get('subject') or 
                    data.get('learning_path') or 'Unknown Topic')
            
            # Parse resources
            resources = []
            resource_data = data.get('resources', [])
            for res in resource_data:
                if isinstance(res, dict):
                    try:
                        resources.append(self._parse_single_educational_resource(res))
                    except Exception as e:
                        logger.warning(f"Failed to parse resource in learning path: {e}")
                        continue
            
            # Extract sequence with multiple fallback keys
            sequence = (data.get('sequence') or data.get('order') or 
                       data.get('steps') or data.get('progression') or [])
            
            if isinstance(sequence, str):
                # Handle string-based sequence
                sequence = [s.strip() for s in sequence.split(',')]
            
            # If no sequence or resources, create defaults
            if not sequence and resources:
                sequence = [res.title for res in resources[:6]]
            
            estimated_time = (data.get('estimated_time') or data.get('duration') or 
                            data.get('time_required') or '4-6 weeks')
            
            learning_objectives = data.get('learning_objectives', 
                                         data.get('objectives', 
                                         data.get('goals', [])))
            
            if isinstance(learning_objectives, str):
                learning_objectives = [obj.strip() for obj in learning_objectives.split(',')]
            
            # Ensure we have default objectives if none provided
            if not learning_objectives:
                learning_objectives = [
                    f'Understand theoretical foundations of {topic}',
                    f'Implement practical solutions for {topic}',
                    f'Apply {topic} knowledge to real problems'
                ]
            
            return LearningPath(
                topic=topic[:200],
                resources=resources[:10],  # Reasonable limit
                sequence=sequence[:10],    # Reasonable limit
                estimated_time=estimated_time,
                learning_objectives=learning_objectives[:8]  # Reasonable limit
            )
        except ValidationError as e:
            logger.warning(f"Pydantic validation error parsing learning path from dict: {e}")
            return self._create_default_learning_path()
        except Exception as e:
            logger.warning(f"Error parsing learning path from dict: {e}")
            return self._create_default_learning_path()

    def _parse_learning_path_from_text(self, text: str) -> LearningPath:
        """Parse learning path from unstructured text with enhanced extraction"""
        try:
            # Extract main topic/theme with multiple patterns
            topic_patterns = [
                r'(?:Topic|Subject|Theme|Learning path for):\s*([^\n\r]+)',
                r'(?:Learning|Studying|Mastering)\s+([^\n\r]+)',
                r'^([^\n\r]+?)(?:\s+Learning Path|\s+Study Guide)',
                r'# ([^\n\r]+)',  # Markdown header
            ]
            
            topic = ""
            for pattern in topic_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    topic = match.group(1).strip()
                    # Clean up common prefixes
                    topic = re.sub(r'^(?:Learning Path|Study Guide|Course):\s*', 
                                 '', topic, flags=re.IGNORECASE)
                    break
            
            if not topic:
                # Fallback: extract from first meaningful line
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                if lines:
                    topic = lines[0][:100]
            
            # Extract learning objectives with enhanced patterns
            objectives = []
            obj_patterns = [
                r'(?:Learning Objectives?|Goals?|Outcomes?):\s*\n(.*?)(?:\n\n|\n[A-Z]|\Z)',
                r'(?:By the end|Upon completion).*?:\s*\n(.*?)(?:\n\n|\n[A-Z]|\Z)',
                r'(?:You will learn|Skills? (?:gained?|acquired?)):\s*\n(.*?)(?:\n\n|\n[A-Z]|\Z)',
                r'(?:^|\n)\d+\.\s*([^\n]*(?:learn|understand|implement|apply)[^\n]*)',
                r'[•\-]\s*([^\n]*(?:learn|understand|implement|apply)[^\n]*)',
            ]
            
            for pattern in obj_patterns:
                matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
                for match in matches:
                    if isinstance(match, str):
                        # Split by bullet points or numbered items
                        items = re.split(r'\n[-•*]\s*|\n\d+\.\s*', match)
                        objectives.extend([item.strip() for item in items 
                                         if item.strip() and len(item.strip()) > 10])
            
            # Extract estimated time with multiple patterns
            time_patterns = [
                r'(?:Time|Duration|Estimated time):\s*([^\n]+)',
                r'(?:Takes?|Requires?):\s*([^\n]*(?:weeks?|months?|hours?|days?)[^\n]*)',
                r'(\d+[-\s]*(?:weeks?|months?|hours?|days?))',
            ]
            
            estimated_time = "4-6 weeks"  # default
            for pattern in time_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    estimated_time = match.group(1).strip()
                    break
            
            # Extract sequence/order with enhanced patterns
            sequence_patterns = [
                r'(?:Sequence|Order|Steps?):\s*\n(.*?)(?:\n\n|\n[A-Z]|\Z)',
                r'(?:Phase|Stage|Step|Week|Month)\s*(\d+)[:\.]?\s*([^\n\r]+)',
                r'(?:^|\n)\d+\.\s*([^\n]+)',
                r'(?:First|Second|Third|Fourth|Fifth|Finally)[:\.]?\s*([^\n\r]+)',
            ]
            
            sequence = []
            for pattern in sequence_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                for match in matches:
                    if len(match.groups()) == 2:
                        # Pattern with step number and content
                        step_content = match.group(2).strip()
                        if len(step_content) > 5:
                            sequence.append(step_content[:100])
                    elif len(match.groups()) == 1:
                        # Single content group
                        content = match.group(1).strip()
                        if len(content) > 5:
                            sequence.append(content[:100])
            
            # Extract referenced resources from URLs
            resources = []
            url_matches = []
            for pattern in self.url_patterns:
                url_matches.extend(pattern.findall(text))
            
            # Create simple resource objects for referenced materials
            for i, url in enumerate(set(url_matches[:8])):  # Limit and deduplicate
                try:
                    resource = ResearchResource(
                        title=f"Referenced Resource {i+1}",
                        url=self._normalize_url(str(url)),
                        resource_type="reference",
                        description="Resource referenced in learning path",
                        quality=ResearchQuality(
                            academic_rigor=3, implementation_quality=3,
                            educational_value=3, relevance_score=3, overall_score=3.0
                        ),
                        difficulty_level="intermediate"
                    )
                    resources.append(resource)
                except ValidationError as e:
                    logger.warning(f"Failed to create referenced resource: {e}")
                    continue
            
            # Set defaults if extraction failed
            if not objectives:
                objectives = [
                    f'Understand theoretical foundations of {topic or "the topic"}',
                    f'Implement practical solutions',
                    f'Apply knowledge to real-world problems'
                ]
            
            if not sequence:
                sequence = [
                    'Review theoretical foundations',
                    'Study practical implementations',
                    'Complete hands-on exercises',
                    'Apply to real projects'
                ]
            
            return LearningPath(
                topic=topic[:200] or "Learning Path",
                resources=resources,
                sequence=sequence[:10],
                estimated_time=estimated_time,
                learning_objectives=objectives[:8]
            )
            
        except Exception as e:
            logger.error(f"Error parsing learning path from text: {e}")
            return self._create_default_learning_path()

    def _create_default_learning_path(self) -> LearningPath:
        """Create a default learning path when parsing fails completely"""
        return LearningPath(
            topic="General Learning Path",
            resources=[],
            sequence=[
                "Review foundational concepts",
                "Study core implementations", 
                "Practice with examples",
                "Apply to projects"
            ],
            estimated_time="4-6 weeks",
            learning_objectives=[
                "Understand theoretical foundations",
                "Implement practical solutions",
                "Apply knowledge to real problems"
            ]
        )
