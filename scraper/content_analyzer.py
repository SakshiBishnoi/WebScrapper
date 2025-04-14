import re
from bs4 import BeautifulSoup
from typing import Dict, Optional

class ContentAnalyzer:
    def __init__(self, html_content: str):
        self.soup = BeautifulSoup(html_content, 'html.parser')
        self.content_indicators = {
            'content': 8,
            'main': 7,
            'article': 7,
            'entry': 6,
            'post': 5,
            'body': 4,
            'section': 4,
            'primary': 6,
            'container': 5
        }

        self.semantic_elements = {
            'article', 'main', 'section', 'summary',
            'details', 'figure', 'dialog', 'header'
        }
        
    def _calculate_content_score(self, element) -> float:
        score = 0
        text_length = len(element.get_text(strip=True))
        
        # Add semantic element bonus
        if element.name in self.semantic_elements:
            score += 6

        # Check for common content attributes
        for attr in ['itemprop', 'role', 'aria-label']:
            if element.has_attr(attr):
                attr_value = element[attr]
                if any(keyword in attr_value for keyword in ['main', 'content', 'article']):
                    score += 4
        
        # Check class and id patterns
        for attr in ['class', 'id']:
            attr_value = element.get(attr, [])
            if isinstance(attr_value, list):
                attr_value = ' '.join(attr_value)
            
            for pattern, weight in self.content_indicators.items():
                if re.search(rf'\b{pattern}\b', attr_value):
                    score += weight
        
        # Text density heuristic
        element_html = str(element)
        tag_count = len(re.findall(r'<[^>]+>', element_html))
        if tag_count > 0:
            score += (text_length / tag_count) * 0.1
        
        return score

    def find_primary_container(self) -> Optional[Dict]:
        max_score = -1
        best_element = None
        candidates = []
        
        # First pass: calculate scores for all elements
        for element in self.soup.find_all(True):
            # Skip very small elements or those with no text
            if len(element.get_text(strip=True)) < 50 and element.name not in ['article', 'main', 'section']:
                continue
                
            current_score = self._calculate_content_score(element)
            
            # Add text length bonus for longer content
            text_length = len(element.get_text(strip=True))
            current_score += min(text_length / 1000, 10)  # Cap at 10 points
            
            # Add bonus for elements with many paragraph children
            p_count = len(element.find_all('p', recursive=False))
            current_score += min(p_count * 0.5, 5)  # Cap at 5 points
            
            # Add bonus for elements with heading tags (h1-h6)
            heading_count = len(element.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'], recursive=True))
            current_score += min(heading_count * 2, 10)  # Cap at 10 points
            
            # Add bonus for elements with list items
            list_item_count = len(element.find_all('li', recursive=True))
            current_score += min(list_item_count * 0.2, 5)  # Cap at 5 points
            
            # Store candidates with their scores
            candidates.append((element, current_score))
            
            if current_score > max_score:
                max_score = current_score
                best_element = element
        
        # If we found a good candidate
        if best_element:
            # Check if there are multiple good candidates with similar scores
            good_candidates = [c for c in candidates if c[1] > max_score * 0.8]
            
            # If multiple good candidates, prefer the one with better semantic meaning
            if len(good_candidates) > 1:
                for candidate, score in good_candidates:
                    if candidate.name in ['article', 'main', 'section'] and candidate != best_element:
                        if score > max_score * 0.9:  # If score is at least 90% of the best
                            best_element = candidate
                            max_score = score
            
            return {
                'selector': self._generate_css_selector(best_element),
                'element': best_element,
                'score': max_score
            }
        return None

    def _generate_css_selector(self, element):
        selector_parts = []
        while element.parent:
            if element.name == 'body':
                break
            siblings = element.find_previous_siblings() + element.find_next_siblings()
            if element.has_attr('id'):
                selector_parts.insert(0, f'#{element["id"]}')
                break
            elif element.has_attr('class'):
                classes = '.'.join(element['class'])
                selector_parts.insert(0, f'{element.name}.{classes}')
            else:
                same_type = [sib for sib in siblings if sib.name == element.name]
                if len(same_type) == 0:
                    selector_parts.insert(0, element.name)
                else:
                    index = len(same_type) + 1
                    selector_parts.insert(0, f'{element.name}:nth-of-type({index})')
            element = element.parent
        return ' > '.join(selector_parts)