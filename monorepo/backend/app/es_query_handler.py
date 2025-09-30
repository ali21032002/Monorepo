"""
Advanced Elasticsearch Query Handler
Handles intelligent parsing and execution of ES queries from natural language
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import json

from .es import get_client

logger = logging.getLogger(__name__)


class QueryType(Enum):
    COUNT = "count"
    FETCH = "fetch" 
    SEARCH = "search"
    AGGREGATE = "aggregate"
    LIST_INDICES = "list_indices"
    UNKNOWN = "unknown"


@dataclass
class QueryParams:
    """Extracted parameters from natural language query"""
    query_type: QueryType
    index_pattern: Optional[str] = None
    size: int = 10
    search_terms: List[str] = None
    filters: Dict[str, Any] = None
    sort_field: Optional[str] = None
    sort_order: str = "desc"
    aggregation_field: Optional[str] = None
    date_range: Optional[Dict[str, str]] = None
    specific_fields: List[str] = None
    message: str = ""  # Add original message for context
    
    def __post_init__(self):
        if self.search_terms is None:
            self.search_terms = []
        if self.filters is None:
            self.filters = {}
        if self.specific_fields is None:
            self.specific_fields = []


class ESQueryHandler:
    """Intelligent Elasticsearch Query Handler"""
    
    def __init__(self):
        self.es = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ES client with error handling"""
        try:
            self.es = get_client()
            if self.es:
                logger.info("✅ ES Query Handler initialized successfully")
            else:
                logger.warning("⚠️ ES client not available")
        except Exception as e:
            logger.error(f"❌ Failed to initialize ES client: {e}")
            self.es = None
    
    def is_enabled(self) -> bool:
        """Check if ES is available"""
        return self.es is not None
    
    def parse_query(self, message: str) -> QueryParams:
        """Parse natural language query into structured parameters"""
        message = message.strip()
        
        # Detect query type
        query_type = self._detect_query_type(message)
        
        # Extract index pattern
        index_pattern = self._extract_index_pattern(message)
        
        # Extract size/limit
        size = self._extract_size(message)
        
        # Extract search terms
        search_terms = self._extract_search_terms(message)
        
        # Extract filters
        filters = self._extract_filters(message)
        
        # Extract specific fields user wants to see
        specific_fields = self._extract_specific_fields(message)
        if specific_fields:
            filters['_source'] = specific_fields
        
        # Extract conditions for filtering
        conditions = self._extract_conditions(message)
        if conditions:
            filters['conditions'] = conditions
        
        # Extract sorting
        sort_field, sort_order = self._extract_sorting(message)
        
        # Extract aggregation field
        aggregation_field = self._extract_aggregation_field(message)
        
        # Extract date range
        date_range = self._extract_date_range(message)
        
        return QueryParams(
            query_type=query_type,
            index_pattern=index_pattern,
            size=size,
            search_terms=search_terms,
            filters=filters,
            sort_field=sort_field,
            sort_order=sort_order,
            aggregation_field=aggregation_field,
            date_range=date_range,
            specific_fields=specific_fields,
            message=message  # Add original message for context
        )
    
    def _detect_query_type(self, message: str) -> QueryType:
        """Universal query type detection for any index structure"""
        message_lower = message.lower()
        
        # List indices queries - check this FIRST
        list_indices_patterns = [
            r'به\s+چه\s+ایندکس.*دسترسی\s+داری',
            r'لیست\s+ایندکس.*ها',
            r'فهرست\s+ایندکس.*ها',
            r'چه\s+ایندکس.*هایی\s+داری',
            r'ایندکس.*های\s+موجود',
            r'what\s+indices.*do\s+you\s+have',
            r'list.*indices',
            r'show.*indices',
            r'available\s+indices'
        ]
        
        if any(re.search(pattern, message_lower) for pattern in list_indices_patterns):
            return QueryType.LIST_INDICES
        
        # Aggregation/Statistical queries - Check BEFORE count for better detection
        agg_patterns = [
            # Mathematical operations
            r'جمع.*فیلد',
            r'مجموع.*فیلد',
            r'میانگین.*فیلد',
            r'حداکثر.*فیلد',
            r'حداقل.*فیلد',
            r'sum.*field',
            r'average.*field',
            r'avg.*field',
            r'max.*field',
            r'min.*field',
            r'total.*field',
            
            # Complex aggregations with filtering
            r'جمع.*در.*رکورد',
            r'مجموع.*در.*رکورد',
            r'میانگین.*در.*رکورد',
            r'sum.*in.*records?',
            r'total.*in.*records?',
            r'average.*in.*records?',
            
            # Traditional aggregation patterns
            r'گروه.*بندی',
            r'تجمیع.*داده',
            r'آمار.*بر.*اساس',
            r'میانگین.*از',
            r'مجموع.*بر.*اساس',
            r'نمودار.*از',
            r'چارت.*از',
            r'گراف.*از',
            r'توزیع.*داده',
            r'آنالیز.*داده',
            r'group.*by',
            r'aggregate.*by',
            r'statistics.*by',
            r'average.*by',
            r'sum.*by',
            r'chart.*data',
            r'graph.*data',
            r'analyze.*data',
            r'distribution.*of'
        ]
        
        if any(re.search(pattern, message_lower) for pattern in agg_patterns):
            return QueryType.AGGREGATE
        
        # Count queries (including conditional counts)
        count_patterns = [
            r'تعداد.*رکورد',
            r'چند.*رکورد',
            r'کل.*رکورد',
            r'مجموع.*رکورد',
            r'تعداد.*که.*دارای',
            r'چند.*که.*شامل',
            r'تعداد.*هایی.*که',
            r'count.*record',
            r'how many.*record',
            r'total.*record',
            r'number.*record',
            r'count.*where',
            r'count.*that.*contain'
        ]
        
        if any(re.search(pattern, message_lower) for pattern in count_patterns):
            return QueryType.COUNT
        
        # Search queries - Look for specific search terms
        search_patterns = [
            r'جستجو.*در',
            r'پیدا.*کن.*که',
            r'دنبال.*می.*گردم',
            r'search.*for',
            r'find.*in.*where',
            r'looking.*for.*that',
            r'filter.*by',
            r'فیلتر.*بر.*اساس'
        ]
        
        if any(re.search(pattern, message_lower) for pattern in search_patterns):
            return QueryType.SEARCH
        
        # Fetch/List queries - DEFAULT for data retrieval
        fetch_patterns = [
            r'\d+\s*رکورد.*بده',
            r'\d+\s*رکورد.*از.*ایندکس',
            r'رکورد.*از.*ایندکس.*بده',
            r'لیست.*رکورد',
            r'لیست.*داده',
            r'نمایش.*رکورد',
            r'آخرین.*رکورد',
            r'اولین.*رکورد',
            r'رکورد.*ها.*بده',
            r'داده.*های.*داخل.*ایندکس',
            r'داده.*های.*ایندکس',
            r'محتویات.*ایندکس',
            r'نمونه.*از.*ایندکس',
            r'.*رکورد.*را.*بده',
            r'.*داده.*را.*بده',
            r'.*رو.*بده',
            r'show.*record',
            r'list.*record',
            r'get.*record',
            r'fetch.*record',
            r'latest.*record',
            r'first.*record',
            r'data.*from.*index',
            r'documents.*from.*index',
            r'contents.*of.*index',
            r'\d+.*records?.*from',
            # Universal patterns for any data request
            r'بده.*از.*ایندکس',
            r'نشان.*بده.*از',
            r'show.*me.*from',
            r'give.*me.*from'
        ]
        
        if any(re.search(pattern, message_lower) for pattern in fetch_patterns):
            return QueryType.FETCH
        
        # If mentions an index, probably wants to fetch data
        if re.search(r'ایندکس\s+[a-zA-Z0-9_\-\.]+', message_lower):
            return QueryType.FETCH
        
        return QueryType.UNKNOWN
    
    def _extract_index_pattern(self, message: str) -> Optional[str]:
        """Universal index pattern extraction supporting multiple indices"""
        
        # First priority: explicit index mentions (single or multiple)
        # Support both quoted and unquoted index names
        explicit_patterns = [
            # Quoted patterns (with single or double quotes)
            r'ایندکس\s+[\'"]([^\'\"]+)[\'"]',
            r'از\s+ایندکس\s+[\'"]([^\'\"]+)[\'"]',
            r'در\s+ایندکس\s+[\'"]([^\'\"]+)[\'"]',
            r'داخل\s+ایندکس\s+[\'"]([^\'\"]+)[\'"]',
            r'index\s+[\'"]([^\'\"]+)[\'"]',
            r'from\s+index\s+[\'"]([^\'\"]+)[\'"]',
            r'in\s+index\s+[\'"]([^\'\"]+)[\'"]',
            
            # Unquoted patterns (until space, comma, or end of string)
            r'ایندکس\s+([a-zA-Z0-9_\-\.]+(?:\-[0-9]{4}\.[0-9]{2}\.[0-9]{2})?)',
            r'از\s+ایندکس\s+([a-zA-Z0-9_\-\.]+(?:\-[0-9]{4}\.[0-9]{2}\.[0-9]{2})?)',
            r'در\s+ایندکس\s+([a-zA-Z0-9_\-\.]+(?:\-[0-9]{4}\.[0-9]{2}\.[0-9]{2})?)',
            r'داخل\s+ایندکس\s+([a-zA-Z0-9_\-\.]+(?:\-[0-9]{4}\.[0-9]{2}\.[0-9]{2})?)',
            r'ایندکس‌های\s+([a-zA-Z0-9_\-\.]+(?:\-[0-9]{4}\.[0-9]{2}\.[0-9]{2})?)',
            r'از\s+ایندکس‌های\s+([a-zA-Z0-9_\-\.]+(?:\-[0-9]{4}\.[0-9]{2}\.[0-9]{2})?)',
            r'index\s+([a-zA-Z0-9_\-\.]+(?:\-[0-9]{4}\.[0-9]{2}\.[0-9]{2})?)',
            r'indices\s+([a-zA-Z0-9_\-\.]+(?:\-[0-9]{4}\.[0-9]{2}\.[0-9]{2})?)',
            r'from\s+index\s+([a-zA-Z0-9_\-\.]+(?:\-[0-9]{4}\.[0-9]{2}\.[0-9]{2})?)',
            r'from\s+indices\s+([a-zA-Z0-9_\-\.]+(?:\-[0-9]{4}\.[0-9]{2}\.[0-9]{2})?)',
            r'in\s+index\s+([a-zA-Z0-9_\-\.]+(?:\-[0-9]{4}\.[0-9]{2}\.[0-9]{2})?)'
        ]
        
        for pattern in explicit_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                index_name = match.group(1).strip()
                # If index name looks complete (has date pattern), use it as-is
                if re.search(r'\d{4}\.\d{2}\.\d{2}', index_name):
                    return index_name  # Exact match for date-based indices
                # Add wildcard if not present
                if not any(ch in index_name for ch in '*?[]'):
                    return f"*{index_name}*"
                return index_name
        
        # Second priority: conditional patterns
        conditional_patterns = [
            r'ایندکسی\s+که\s+با\s+([a-zA-Z0-9_\-\.]+)\s+شروع\s+می\s*[شس]ود',
            r'ایندکسی\s+که\s+داخل\s+اسمش\s+([a-zA-Z0-9_\-\.]+)\s+وجود\s+دارد'
        ]
        
        for pattern in conditional_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                index_name = match.group(1).strip()
                if 'شروع می' in message:
                    return f"{index_name}*"
                else:
                    return f"*{index_name}*"
        
        # Third priority: look for index-like tokens but exclude values from conditions
        # First extract condition values to exclude them
        condition_values = set()
        condition_patterns = [
            r'دارای\s+کلمه\s+([^\s]+)',
            r'شامل\s+([^\s]+)',
            r'برابر\s+([^\s]+)'
        ]
        
        for pattern in condition_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            for match in matches:
                condition_values.add(match.strip().strip('"').strip("'").lower())
        
        # Now find potential index names, excluding condition values
        tokens = re.findall(r'[a-zA-Z][a-zA-Z0-9_\-\.]{3,}', message)  # At least 4 chars for index names
        if tokens:
            excluded_words = {
                'username', 'email', 'user', 'name', 'field', 'record', 'data', 'document',
                'است', 'هست', 'دارای', 'کلمه', 'شامل', 'برابر'
            }
            excluded_words.update(condition_values)
            
            # Filter out excluded words and condition values
            filtered_tokens = []
            for token in tokens:
                if token.lower() not in excluded_words and len(token) >= 4:
                    # Additional check: looks like an index name (contains numbers or underscores)
                    if any(c.isdigit() or c in '_-.' for c in token):
                        filtered_tokens.append(token)
            
            if filtered_tokens:
                # Return the longest filtered token as likely index name
                longest = max(filtered_tokens, key=len)
                # If token has date pattern, use it as-is (exact match)
                if re.search(r'\d{4}\.\d{2}\.\d{2}', longest):
                    return longest
                # Otherwise add wildcards
                return f"*{longest}*"
        
        # If no index found, return None (will be handled by caller)
        return None
    
    def _extract_size(self, message: str) -> int:
        """Extract size/limit from message"""
        # Persian numbers
        persian_numbers = {
            'یک': 1, 'دو': 2, 'سه': 3, 'چهار': 4, 'پنج': 5,
            'شش': 6, 'هفت': 7, 'هشت': 8, 'نه': 9, 'ده': 10,
            'بیست': 20, 'سی': 30, 'چهل': 40, 'پنجاه': 50,
            'صد': 100, 'هزار': 1000
        }
        
        # Look for explicit numbers near "رکورد" or "record"
        patterns = [
            r'(\d+)\s*(?:رکورد|record|docs?|داده|سند)',
            r'(?:رکورد|record|docs?|داده|سند)\s*(\d+)',
            r'(?:اول|first|latest|last|آخرین|اولین)\s*(\d+)',
            r'(\d+)\s*(?:تا|عدد|مورد|نمونه)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                try:
                    return min(int(match.group(1)), 1000)  # Cap at 1000
                except ValueError:
                    continue
        
        # Check for Persian number words
        for word, num in persian_numbers.items():
            if word in message:
                return num
        
        # Default size based on query type and keywords
        if 'همه' in message or 'all' in message.lower():
            return 100  # More reasonable for "all"
        elif 'آخرین' in message or 'latest' in message.lower():
            return 10
        elif any(word in message.lower() for word in ['لیست', 'نمایش', 'محتویات', 'داده', 'کاربران']):
            return 20  # More for general data requests
        
        return 10  # Default
    
    def _is_simple_count_query(self, message: str) -> bool:
        """Check if this is a simple count query without search conditions"""
        message_lower = message.lower()
        
        # Must be a count query
        if not any(word in message_lower for word in ['تعداد', 'count', 'چندتا', 'چند تا']):
            return False
            
        # Should mention records/documents/data
        if not any(word in message_lower for word in ['رکورد', 'داده', 'سند', 'record', 'document', 'data']):
            return False
        
        # Should have index mention
        if not any(word in message_lower for word in ['ایندکس', 'index']):
            return False
        
        # Should NOT have search conditions - more comprehensive check
        search_indicators = [
            'که در', 'که شامل', 'که دارای', 'که برابر',  # conditional patterns
            'کلمه', 'عبارت', 'متن', 'نام کاربری',  # field/value patterns
            'contains', 'includes', 'equals', 'with', 'having', 'where'
        ]
        
        if any(indicator in message_lower for indicator in search_indicators):
            return False
        
        # Additional check: if message contains "که" followed by field names, it's conditional
        conditional_patterns = [
            r'که.*(?:نام کاربری|username|email|user_id|name)',
            r'که.*(?:شامل|دارای|برابر|contains|includes|equals)'
        ]
        
        for pattern in conditional_patterns:
            if re.search(pattern, message_lower):
                return False
            
        return True
    
    def _extract_search_terms(self, message: str) -> List[str]:
        """Extract search terms from message"""
        # For simple count queries (without search conditions), don't extract search terms
        if self._is_simple_count_query(message):
            return []
            
        # Remove common query structure words
        stop_words = {
            'که', 'از', 'در', 'با', 'را', 'به', 'و', 'یا', 'این', 'آن', 'تا', 'بده',
            'the', 'in', 'on', 'at', 'by', 'for', 'with', 'from', 'to', 'give', 'show',
            'ایندکس', 'رکورد', 'داده', 'index', 'record', 'data', 'document', 'docs',
            'لیست', 'هایی', 'میخوام', 'توش', 'استفاده', 'شده', 'باشه', 'فقط', 'نمی', 'خوام',
            'کن', 'بقیه', 'رو', 'کلمه', 'تعداد', 'کل', 'های', 'count', 'total', 'all'
        }
        
        # Extract quoted terms first
        quoted_terms = re.findall(r'["\']([^"\']+)["\']', message)
        
        # Look for specific search value patterns
        search_value_patterns = [
            r'کلمه\s+([a-zA-Z0-9_\-\.]+)',  # "کلمه ali"
            r'عبارت\s+([a-zA-Z0-9_\-\.]+)',  # "عبارت ali"
            r'متن\s+([a-zA-Z0-9_\-\.]+)',   # "متن ali"
            r'شامل\s+([a-zA-Z0-9_\-\.]+)',  # "شامل ali"
            r'contains\s+([a-zA-Z0-9_\-\.]+)',  # "contains ali"
        ]
        
        search_values = []
        for pattern in search_value_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            search_values.extend(matches)
        
        # Extract other meaningful terms (minimum length 2 for names like 'ali')
        words = re.findall(r'[a-zA-Z\u0600-\u06FF]+', message)
        meaningful_terms = [w for w in words if len(w) >= 2 and w.lower() not in stop_words]
        
        # Combine all terms, prioritize search values
        all_terms = quoted_terms + search_values + meaningful_terms
        
        # Remove duplicates while preserving order
        seen = set()
        result = []
        for term in all_terms:
            if term.lower() not in seen:
                seen.add(term.lower())
                result.append(term)
        
        return result[:5]  # Limit to avoid noise
    
    def _extract_specific_fields(self, message: str) -> List[str]:
        """Extract specific field names that user wants to see"""
        fields = []
        
        # Persian patterns for specific field requests
        persian_patterns = [
            r'فقط\s+(\w+)\s+رو',  # "فقط username رو"
            r'فقط\s+([\w\s]+)\s+رو.*لیست\s+کن',  # "فقط نام کاربری رو لیست کن"
            r'(\w+)\s+رو\s+لیست\s+کن.*بقیه\s+رو\s+نمی\s*خوام',  # "username رو لیست کن بقیه رو نمی‌خوام"
            r'(\w+)\s*رو.*بده.*بقیه.*نمی\s*خوام',  # "username رو بده بقیه رو نمی‌خوام"
        ]
        
        # English patterns
        english_patterns = [
            r'only\s+(\w+)',
            r'just\s+(\w+)',
            r'show\s+only\s+(\w+)',
            r'get\s+only\s+(\w+)'
        ]
        
        all_patterns = persian_patterns + english_patterns
        
        for pattern in all_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            for match in matches:
                # Clean up the match
                field_name = match.strip()
                fields.append(field_name)
        
        # Map Persian field names to English
        field_mapping = {
            'نام کاربری': 'username',
            'نام_کاربری': 'username', 
            'کاربری': 'username',
            'ایمیل': 'email',
            'نام': 'name',
            'عنوان': 'title',
            'شناسه': 'id',
            'تاریخ': 'timestamp',
            'وضعیت': 'status'
        }
        
        # Apply mapping
        mapped_fields = []
        for field in fields:
            if field in field_mapping:
                mapped_fields.append(field_mapping[field])
            else:
                mapped_fields.append(field)
        
        # If no specific fields found but user mentions common fields, add them
        if not mapped_fields:
            common_fields = ['username', 'user_id', 'email', 'name', 'title', 'id', 'timestamp', 'date', 'status']
            for field in common_fields:
                if field in message.lower():
                    mapped_fields.append(field)
        
        return list(set(mapped_fields))  # Remove duplicates
    
    def _extract_conditions(self, message: str) -> Dict[str, Any]:
        """Extract filtering conditions from message"""
        conditions = {}
        message_lower = message.lower()
        
        # Pattern: "username آن دارای کلمه X است"
        # Pattern: "username شامل X است"
        # Pattern: "field contains value"
        condition_patterns = [
            r'(\w+)\s+آن\s+دارای\s+کلمه\s+[\'"]?([^\s\'"]+)[\'"]?\s*(?:است|هست)',
            r'(\w+)\s+آنها\s+دارای\s+کلمه\s+[\'"]?([^\s\'"]+)[\'"]?\s*(?:است|هست)',
            r'(\w+)\s+انها\s+دارای\s+کلمه\s+[\'"]?([^\s\'"]+)[\'"]?\s*(?:است|هست)',
            r'نام\s+کاربری\s+انها\s+دارای\s+کلمه\s+[\'"]?([^\s\'"]+)[\'"]?\s*(?:است|هست)',
            r'(\w+)\s+دارای\s+[\'"]?([^\s\'"]+)[\'"]?',
            r'(\w+)\s+شامل\s+[\'"]?([^\s\'"]+)[\'"]?',
            r'(\w+)\s+برابر\s+[\'"]?([^\s\'"]+)[\'"]?',
            r'(\w+)\s+equals?\s+[\'"]?([^\s\'"]+)[\'"]?',
            r'(\w+)\s+contains?\s+[\'"]?([^\s\'"]+)[\'"]?',
            r'(\w+)\s+is\s+[\'"]?([^\s\'"]+)[\'"]?',
            r'که\s+(\w+)\s+آن\s+[\'"]?([^\s\'"]+)[\'"]?',
            r'که\s+(\w+)\s+دارای\s+[\'"]?([^\s\'"]+)[\'"]?'
        ]
        
        # Special handling for common Persian patterns first
        special_patterns = [
            # "در نام کاربری کلمه X دارند"
            r'در\s+نام\s+کاربری\s+کلمه\s+([^\s]+)\s+دارند',
            # "که در نام کاربری کلمه X دارند"
            r'که\s+در\s+نام\s+کاربری\s+کلمه\s+([^\s]+)\s+دارند',
            # "تعداد رکورد هایی که username آن دارای کلمه X است"
            r'که\s+(\w+)\s+آن\s+دارای\s+کلمه\s+([^\s]+)\s+است',
            # "نام کاربری انها دارای کلمه X"
            r'نام\s+کاربری\s+انها\s+دارای\s+کلمه\s+[\'"]?([^\s\'"]+)[\'"]?\s*(?:است|هست)?',
            # "username آن دارای کلمه X"
            r'(\w+)\s+آن\s+دارای\s+کلمه\s+([^\s]+)',
        ]
        
        for pattern in special_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) == 2:
                    field, value = groups
                elif len(groups) == 1:
                    # For patterns like "در نام کاربری کلمه X دارند"
                    field = 'username'  # Default for نام کاربری patterns
                    value = groups[0]
                else:
                    continue
                    
                value = value.strip().strip('"').strip("'")
                conditions[field] = {
                    'type': 'contains',
                    'value': value
                }
                return conditions  # Return early to avoid other patterns
        
        # Only process other patterns if special pattern didn't match
        for pattern in condition_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            for match in matches:
                if len(match) == 2:
                    field, value = match
                    # Remove Persian articles and conjunctions
                    value = value.strip('است').strip('می‌باشد').strip().strip('"').strip("'")
                    
                    # Skip common Persian words that are not field names
                    if field in ['نام', 'کاربری', 'انها', 'آنها', 'که', 'دارای', 'کلمه']:
                        continue
                        
                    conditions[field] = {
                        'type': 'contains' if 'دارای' in message or 'شامل' in message or 'contains' in message else 'equals',
                        'value': value
                    }
        
        return conditions
    
    def _build_condition_query(self, field: str, condition: Dict[str, Any]) -> Dict[str, Any]:
        """Build a robust condition query that works with different field mappings"""
        if condition['type'] == 'contains':
            # Try both field.keyword and field, let ES choose what exists
            return {
                "bool": {
                    "should": [
                        {"wildcard": {f"{field}.keyword": f"*{condition['value']}*"}},
                        {"wildcard": {field: f"*{condition['value']}*"}},
                        {"match": {field: {"query": condition['value'], "fuzziness": "AUTO"}}}
                    ],
                    "minimum_should_match": 1
                }
            }
        elif condition['type'] == 'equals':
            # Try both field.keyword and field
            return {
                "bool": {
                    "should": [
                        {"term": {f"{field}.keyword": condition['value']}},
                        {"term": {field: condition['value']}},
                        {"match": {field: condition['value']}}
                    ],
                    "minimum_should_match": 1
                }
            }
        else:
            # Fallback to simple match
            return {"match": {field: condition['value']}}
    
    def _extract_filters(self, message: str) -> Dict[str, Any]:
        """Extract filters from message"""
        filters = {}
        
        # Date filters
        date_patterns = [
            r'تاریخ\s+([0-9\-/]+)',
            r'date\s+([0-9\-/]+)',
            r'روز\s+([0-9\-/]+)',
            r'امروز|today',
            r'دیروز|yesterday',
            r'هفته\s+گذشته|last\s+week',
            r'ماه\s+گذشته|last\s+month'
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                # This would need more sophisticated date parsing
                filters['date_filter'] = True
                break
        
        # Status filters
        status_patterns = [
            r'وضعیت\s+([a-zA-Z\u0600-\u06FF]+)',
            r'status\s+([a-zA-Z]+)',
            r'حالت\s+([a-zA-Z\u0600-\u06FF]+)'
        ]
        
        for pattern in status_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                filters['status'] = match.group(1)
                break
        
        return filters
    
    def _extract_sorting(self, message: str) -> Tuple[Optional[str], str]:
        """Extract sorting information"""
        sort_field = None
        sort_order = "desc"  # Default to newest first
        
        # Sort field patterns - only use fields that commonly exist
        if 'تاریخ' in message or 'date' in message.lower():
            sort_field = '@timestamp'
        # Don't automatically sort by name as it may not exist
        # elif 'نام' in message or 'name' in message.lower():
        #     sort_field = 'name.keyword'
        elif 'اندازه' in message or 'size' in message.lower():
            sort_field = 'size'
        
        # Sort order patterns
        if any(word in message for word in ['قدیمی', 'اول', 'ascending', 'asc', 'oldest']):
            sort_order = "asc"
        elif any(word in message for word in ['جدید', 'آخرین', 'descending', 'desc', 'latest', 'newest']):
            sort_order = "desc"
        
        return sort_field, sort_order
    
    def _extract_aggregation_field(self, message: str) -> Optional[str]:
        """Extract field name for aggregation with enhanced patterns"""
        
        # Enhanced field patterns for mathematical operations
        field_patterns = [
            # Persian patterns with quotes
            r'فیلد\s+[\'"]([^\'\"]+)[\'"]',
            r'جمع\s+فیلد\s+[\'"]([^\'\"]+)[\'"]',
            r'مجموع\s+فیلد\s+[\'"]([^\'\"]+)[\'"]',
            r'میانگین\s+فیلد\s+[\'"]([^\'\"]+)[\'"]',
            
            # Persian patterns without quotes
            r'فیلد\s+([a-zA-Z0-9_\.]+)',
            r'جمع\s+فیلد\s+([a-zA-Z0-9_\.]+)',
            r'مجموع\s+فیلد\s+([a-zA-Z0-9_\.]+)',
            r'میانگین\s+فیلد\s+([a-zA-Z0-9_\.]+)',
            r'حداکثر\s+فیلد\s+([a-zA-Z0-9_\.]+)',
            r'حداقل\s+فیلد\s+([a-zA-Z0-9_\.]+)',
            
            # Traditional patterns
            r'بر\s+اساس\s+([a-zA-Z\u0600-\u06FF_]+)',
            r'گروه.*بندی\s+([a-zA-Z0-9_\.]+)',
            
            # English patterns
            r'field\s+[\'"]([^\'\"]+)[\'"]',
            r'sum\s+field\s+[\'"]([^\'\"]+)[\'"]',
            r'avg\s+field\s+[\'"]([^\'\"]+)[\'"]',
            r'field\s+([a-zA-Z0-9_\.]+)',
            r'sum\s+field\s+([a-zA-Z0-9_\.]+)',
            r'avg\s+field\s+([a-zA-Z0-9_\.]+)',
            r'group\s+by\s+([a-zA-Z_]+)',
            r'تجمیع\s+([a-zA-Z\u0600-\u06FF_]+)',
            r'آمار\s+([a-zA-Z\u0600-\u06FF_]+)'
        ]
        
        for pattern in field_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_aggregation_operation(self, message: str) -> str:
        """Extract the type of mathematical operation requested"""
        
        # Operation patterns
        operation_patterns = {
            'sum': [r'جمع', r'مجموع', r'sum', r'total'],
            'avg': [r'میانگین', r'average', r'avg', r'mean'],
            'max': [r'حداکثر', r'بیشترین', r'max', r'maximum', r'highest'],
            'min': [r'حداقل', r'کمترین', r'min', r'minimum', r'lowest'],
            'count': [r'تعداد', r'شمارش', r'count']
        }
        
        message_lower = message.lower()
        
        for operation, patterns in operation_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return operation
        
        return 'sum'  # default
    
    def _extract_date_range(self, message: str) -> Optional[Dict[str, str]]:
        """Extract date range from message"""
        # This would need more sophisticated implementation
        # For now, just detect if date range is mentioned
        if any(word in message for word in ['از', 'تا', 'between', 'from', 'to']):
            return {"has_range": True}
        return None
    
    def _index_exists(self, index_pattern: str) -> bool:
        """Check if index exists in Elasticsearch"""
        try:
            # For exact index names (no wildcards), use direct exists check
            if not any(c in index_pattern for c in '*?[]'):
                result = self.es.indices.exists(index=index_pattern)
                logger.info(f"🔍 Direct index check '{index_pattern}': {result}")
                return result
            else:
                # For patterns with wildcards, try to resolve them
                try:
                    response = self.es.indices.get(
                        index=index_pattern, 
                        ignore_unavailable=True,
                        allow_no_indices=True
                    )
                    result = bool(response)
                    logger.info(f"🔍 Pattern index check '{index_pattern}': {result}")
                    return result
                except Exception:
                    logger.warning(f"⚠️ Pattern index check failed for '{index_pattern}'")
                    return False
        except Exception as e:
            logger.error(f"❌ Index existence check failed for '{index_pattern}': {e}")
            return False
    
    def _find_similar_indices(self, index_pattern: str) -> List[str]:
        """Find indices similar to the given pattern"""
        try:
            # Get all available indices
            indices_response = self.es.cat.indices(format="json", h="index")
            if not indices_response:
                return []
            
            all_indices = [idx.get("index", "") for idx in indices_response 
                          if not idx.get("index", "").startswith('.')]
            
            # Remove wildcards from pattern for similarity matching
            clean_pattern = index_pattern.strip('*')
            
            # Find indices that contain the pattern
            similar = []
            for idx in all_indices:
                if clean_pattern.lower() in idx.lower():
                    similar.append(idx)
            
            # Sort by length (shorter names first, likely more relevant)
            similar.sort(key=len)
            return similar
            
        except Exception:
            return []
    
    def execute_query(self, params: QueryParams) -> Dict[str, Any]:
        """Execute the parsed query"""
        if not self.is_enabled():
            return {"enabled": False, "error": "Elasticsearch غیرفعال است"}
        
        try:
            if params.query_type == QueryType.COUNT:
                return self._execute_count_query(params)
            elif params.query_type == QueryType.FETCH:
                return self._execute_fetch_query(params)
            elif params.query_type == QueryType.SEARCH:
                return self._execute_search_query(params)
            elif params.query_type == QueryType.AGGREGATE:
                return self._execute_aggregate_query(params)
            elif params.query_type == QueryType.LIST_INDICES:
                return self._execute_list_indices_query(params)
            else:
                return {"enabled": True, "error": "نوع سؤال شناسایی نشد"}
        
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return {"enabled": True, "error": f"خطا در اجرای کوئری: {str(e)}"}
    
    def _execute_count_query(self, params: QueryParams) -> Dict[str, Any]:
        """Execute count query"""
        if not params.index_pattern:
            return {"enabled": True, "error": "ایندکس مشخص نشده است. لطفاً نام ایندکس را در سؤال ذکر کنید، مثل: 'در ایندکس instagram تعداد...'"}
        
        # Check if index pattern is too generic or might be wrong
        if params.index_pattern in ['*ali*', '*است*', '*که*', '*دارای*']:
            return {"enabled": True, "error": "نام ایندکس نامشخص است. لطفاً نام صحیح ایندکس را ذکر کنید."}
        
        # Check if the exact index exists (for better error messages)
        if not self._index_exists(params.index_pattern):
            # Try to find similar indices
            similar_indices = self._find_similar_indices(params.index_pattern)
            if similar_indices:
                suggestions = ', '.join(similar_indices[:3])  # Show top 3 suggestions
                return {"enabled": True, "error": f"ایندکس '{params.index_pattern}' یافت نشد. آیا منظورتان یکی از این‌ها است؟ {suggestions}"}
            else:
                return {"enabled": True, "error": f"ایندکس '{params.index_pattern}' یافت نشد. برای مشاهده لیست ایندکس‌های موجود بپرسید: 'لیست ایندکس‌ها'"}
        
        try:
            # For simple count queries, use match_all
            # For search queries, build complex query
            must_clauses = []
            filter_clauses = []
            
            # Add search terms if present
            if params.search_terms:
                must_clauses.append({
                    "multi_match": {
                        "query": " ".join(params.search_terms),
                        "fields": ["*"]
                    }
                })
            
            # Add conditions from message
            if params.filters and 'conditions' in params.filters:
                conditions = params.filters['conditions']
                for field, condition in conditions.items():
                    must_clauses.append(self._build_condition_query(field, condition))
            
            # Add date range filter
            if params.date_range:
                filter_clauses.append({
                    "range": {"@timestamp": {"gte": "now-1d"}}
                })
            
            # Build final query
            if must_clauses or filter_clauses:
                query = {"bool": {}}
                if must_clauses:
                    query["bool"]["must"] = must_clauses
                if filter_clauses:
                    query["bool"]["filter"] = filter_clauses
            else:
                # No conditions, count all documents
                query = {"match_all": {}}
            
            # Execute count
            response = self.es.count(
                index=params.index_pattern,
                body={"query": query},
                ignore_unavailable=True,
                allow_no_indices=True
            )
            
            count = response.get('count', 0)
            result = {
                "enabled": True,
                "query_type": "count",
                "index_pattern": params.index_pattern,
                "count": count,
                "took": response.get('took', 0)
            }
            
            # Add conditions to result for display
            if params.filters and 'conditions' in params.filters:
                result["conditions"] = params.filters['conditions']
            
            return result
        
        except Exception as e:
            return {"enabled": True, "error": f"خطا در شمارش: {str(e)}"}
    
    def _execute_fetch_query(self, params: QueryParams) -> Dict[str, Any]:
        """Execute fetch query"""
        if not params.index_pattern:
            return {"enabled": True, "error": "ایندکس مشخص نشده است. لطفاً نام ایندکس را در سؤال ذکر کنید، مثل: 'در ایندکس instagram لیست...'"}
        
        # Check if index pattern is too generic or might be wrong
        if params.index_pattern in ['*ali*', '*است*', '*که*', '*دارای*']:
            return {"enabled": True, "error": "نام ایندکس نامشخص است. لطفاً نام صحیح ایندکس را ذکر کنید."}
        
        # SKIP index existence check for now - it's causing issues with crypto_data-2025.09.29
        # Let Elasticsearch handle the error if index doesn't exist
        
        try:
            # Build query with conditions
            must_clauses = []
            
            # Add search terms
            if params.search_terms:
                must_clauses.append({
                    "multi_match": {
                        "query": " ".join(params.search_terms),
                        "fields": ["*"]
                    }
                })
            
            # Add conditions from message
            if params.filters and 'conditions' in params.filters:
                conditions = params.filters['conditions']
                for field, condition in conditions.items():
                    must_clauses.append(self._build_condition_query(field, condition))
            
            # Build final query
            if must_clauses:
                query = {"bool": {"must": must_clauses}}
            else:
                query = {"match_all": {}}
            
            # Build sort - avoid sorting on non-existent fields
            sort = []
            if params.sort_field:
                # Only sort on common fields that likely exist
                safe_sort_fields = ['@timestamp', '_score', '_doc']
                if params.sort_field in safe_sort_fields:
                    sort.append({params.sort_field: {"order": params.sort_order}})
                else:
                    # Default to _doc for unknown fields
                    sort.append({"_doc": {"order": params.sort_order}})
            else:
                sort.append({"_doc": {"order": params.sort_order}})
            
            # Build search body
            search_body = {
                "query": query,
                "sort": sort,
                "size": params.size
            }
            
            # Add field selection if specified
            if params.filters and '_source' in params.filters:
                search_body["_source"] = params.filters['_source']
            
            # Execute search
            logger.info(f"🔍 Executing search on index: {params.index_pattern}")
            logger.info(f"📋 Search body: {search_body}")
            
            response = self.es.search(
                index=params.index_pattern,
                body=search_body,
                ignore_unavailable=True,
                allow_no_indices=True
            )
            
            logger.info(f"📊 ES Response keys: {list(response.keys())}")
            
            hits = response.get('hits', {}).get('hits', [])
            total = response.get('hits', {}).get('total', {})
            total_value = total.get('value') if isinstance(total, dict) else total
            
            logger.info(f"📊 Found {len(hits)} hits, total: {total_value}")
            
            # Format documents
            docs = []
            for hit in hits:
                source = hit.get("_source", {})
                
                # If specific fields were requested, show only those
                if params.filters and '_source' in params.filters:
                    filtered_source = {}
                    for field in params.filters['_source']:
                        if field in source:
                            filtered_source[field] = source[field]
                    source = filtered_source
                
                doc = {
                    "_index": hit.get("_index"),
                    "_id": hit.get("_id"),
                    "_score": hit.get("_score"),
                    "_source": source
                }
                docs.append(doc)
            
            result = {
                "enabled": True,
                "query_type": "fetch",
                "index_pattern": params.index_pattern,
                "docs": docs,
                "returned": len(docs),
                "total": total_value,
                "took": response.get('took', 0)
            }
            
            # Add conditions to result for display
            if params.filters and 'conditions' in params.filters:
                result["conditions"] = params.filters['conditions']
            
            return result
        
        except Exception as e:
            return {"enabled": True, "error": f"خطا در دریافت داده: {str(e)}"}
    
    def _execute_search_query(self, params: QueryParams) -> Dict[str, Any]:
        """Execute search query with highlighting"""
        if not params.index_pattern:
            return {"enabled": True, "error": "الگوی ایندکس مشخص نشده"}
        
        if not params.search_terms:
            return {"enabled": True, "error": "عبارت جستجو مشخص نشده"}
        
        try:
            # Build advanced search query
            query = {
                "multi_match": {
                    "query": " ".join(params.search_terms),
                    "fields": ["*"],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            }
            
            # Build search body
            search_body = {
                "query": query,
                "size": params.size,
                "highlight": {
                    "fields": {"*": {}},
                    "pre_tags": ["<mark>"],
                    "post_tags": ["</mark>"]
                }
            }
            
            # Add sorting
            if params.sort_field:
                search_body["sort"] = [{params.sort_field: {"order": params.sort_order}}]
            
            # Execute search
            response = self.es.search(
                index=params.index_pattern,
                body=search_body,
                ignore_unavailable=True,
                allow_no_indices=True
            )
            
            hits = response.get('hits', {}).get('hits', [])
            total = response.get('hits', {}).get('total', {})
            total_value = total.get('value') if isinstance(total, dict) else total
            
            # Format results with highlights
            results = []
            for hit in hits:
                result = {
                    "_index": hit.get("_index"),
                    "_id": hit.get("_id"),
                    "_score": hit.get("_score"),
                    "_source": hit.get("_source", {}),
                    "highlight": hit.get("highlight", {})
                }
                results.append(result)
            
            return {
                "enabled": True,
                "query_type": "search",
                "index_pattern": params.index_pattern,
                "search_terms": params.search_terms,
                "results": results,
                "returned": len(results),
                "total": total_value,
                "took": response.get('took', 0)
            }
        
        except Exception as e:
            return {"enabled": True, "error": f"خطا در جستجو: {str(e)}"}
    
    def _execute_aggregate_query(self, params: QueryParams) -> Dict[str, Any]:
        """Universal aggregation query for any index structure"""
        if not params.index_pattern:
            return {"enabled": True, "error": "الگوی ایندکس مشخص نشده"}
        
        try:
            # First, get sample documents to understand field structure
            sample_response = self.es.search(
                index=params.index_pattern,
                body={"query": {"match_all": {}}, "size": 1},
                ignore_unavailable=True,
                allow_no_indices=True
            )
            
            sample_fields = []
            if sample_response.get('hits', {}).get('hits'):
                sample_doc = sample_response['hits']['hits'][0].get('_source', {})
                sample_fields = list(sample_doc.keys())
            
            # Auto-detect aggregation field if not specified
            agg_field = params.aggregation_field
            if not agg_field:
                # Smart field detection for aggregation (case-insensitive)
                priority_fields = ['@timestamp', 'timestamp', 'date', 'created_at', 'status', 'type', 'category', 'price_usd', 'price', 'amount', 'value']
                for priority_field in priority_fields:
                    for actual_field in sample_fields:
                        if actual_field.lower() == priority_field.lower():
                            agg_field = actual_field
                            break
                    if agg_field:
                        break
                
                # If no priority field found, use first suitable field
                if not agg_field and sample_fields:
                    for field in sample_fields:
                        if not field.startswith('_') and isinstance(sample_doc.get(field), (str, int, float)):
                            agg_field = field
                            break
            else:
                # Case-insensitive field matching for user-specified fields
                if agg_field not in sample_fields:
                    for field in sample_fields:
                        if field.lower() == agg_field.lower():
                            agg_field = field  # Use the actual field name from the index
                            break
            
            if not agg_field:
                return {"enabled": True, "error": "فیلد مناسب برای تجمیع یافت نشد"}
            
            # Detect mathematical operation
            operation = self._extract_aggregation_operation(params.message if hasattr(params, 'message') else "")
            
            # Check if this is a filtered aggregation (e.g., "sum in last 10 records")
            limit = self._extract_size(params.message if hasattr(params, 'message') else "")
            has_limit_filter = any(pattern in params.message.lower() if hasattr(params, 'message') else "" 
                                 for pattern in ['در', 'رکورد', 'in', 'records', 'last', 'اخر', 'آخر'])
            
            logger.info(f"🔍 Aggregation detection: field='{agg_field}', operation='{operation}', limit={limit}, has_limit_filter={has_limit_filter}")
            logger.info(f"📝 Original message: {params.message if hasattr(params, 'message') else 'No message'}")
            
            # Build smart aggregation based on operation and context
            search_body = {}
            
            # If this is a filtered aggregation (e.g., "sum in last 10 records")
            if has_limit_filter and limit > 0:
                logger.info(f"🎯 Executing filtered aggregation: {operation} on {agg_field} for last {limit} records")
                # First get the records, then aggregate
                search_body = {
                    "query": {"match_all": {}},
                    "size": limit,
                    "sort": [{"@timestamp": {"order": "desc"}}] if "@timestamp" in sample_fields else [{"_id": {"order": "desc"}}]
                }
                
                # Get the records first
                records_response = self.es.search(
                    index=params.index_pattern,
                    body=search_body,
                    ignore_unavailable=True,
                    allow_no_indices=True
                )
                
                # Calculate the aggregation manually from the records
                hits = records_response.get('hits', {}).get('hits', [])
                if hits and operation in ['sum', 'avg', 'max', 'min']:
                    values = []
                    for hit in hits:
                        source = hit.get('_source', {})
                        if agg_field in source and isinstance(source[agg_field], (int, float)):
                            values.append(source[agg_field])
                    
                    if values:
                        if operation == 'sum':
                            result_value = sum(values)
                        elif operation == 'avg':
                            result_value = sum(values) / len(values)
                        elif operation == 'max':
                            result_value = max(values)
                        elif operation == 'min':
                            result_value = min(values)
                        
                        logger.info(f"✅ Filtered aggregation result: {operation}({agg_field}) = {result_value} from {len(hits)} records")
                        return {
                            "enabled": True,
                            "query_type": "aggregate",
                            "index_pattern": params.index_pattern,
                            "aggregation_field": agg_field,
                            "operation": operation,
                            "limit": limit,
                            "result_value": result_value,
                            "total_records": len(hits),
                            "sample_fields": sample_fields,
                            "took": records_response.get('took', 0)
                        }
            
            # Traditional aggregation without record limit
            aggs = {}
            
            # Build aggregation based on operation
            if operation in ['sum', 'avg', 'max', 'min'] and isinstance(sample_doc.get(agg_field), (int, float)):
                aggs[f"{operation}_agg"] = {
                    operation: {
                        "field": agg_field
                    }
                }
            else:
                # Terms aggregation for categorical data
                aggs["terms_agg"] = {
                    "terms": {
                        "field": f"{agg_field}.keyword" if isinstance(sample_doc.get(agg_field), str) else agg_field,
                        "size": 20
                    }
                }
            
            # Date histogram for date fields
            if any(date_word in agg_field.lower() for date_word in ['timestamp', 'date', 'time', 'created', 'updated']):
                aggs["date_histogram"] = {
                    "date_histogram": {
                        "field": agg_field,
                        "calendar_interval": "day"
                    }
                }
            
            # Statistics for numeric fields
            if isinstance(sample_doc.get(agg_field), (int, float)):
                aggs["stats"] = {
                    "stats": {
                        "field": agg_field
                    }
                }
            
            # Execute aggregation
            response = self.es.search(
                index=params.index_pattern,
                body={
                    "size": 0,
                    "aggs": aggs
                },
                ignore_unavailable=True,
                allow_no_indices=True
            )
            
            aggregations = response.get('aggregations', {})
            
            # Prepare chart data if applicable
            chart_data = self._prepare_chart_data(aggregations, agg_field)
            
            return {
                "enabled": True,
                "query_type": "aggregate",
                "index_pattern": params.index_pattern,
                "aggregation_field": agg_field,
                "aggregations": aggregations,
                "sample_fields": sample_fields,
                "chart_data": chart_data,
                "took": response.get('took', 0)
            }
        
        except Exception as e:
            return {"enabled": True, "error": f"خطا در تجمیع: {str(e)}"}
    
    def _prepare_chart_data(self, aggregations: Dict[str, Any], field_name: str) -> Optional[Dict[str, Any]]:
        """Prepare chart data from aggregations for visualization"""
        try:
            chart_data = None
            
            # Terms aggregation -> Bar chart
            if "terms_agg" in aggregations:
                buckets = aggregations["terms_agg"].get("buckets", [])
                if buckets:
                    labels = [bucket.get("key", "") for bucket in buckets[:10]]
                    values = [bucket.get("doc_count", 0) for bucket in buckets[:10]]
                    
                    chart_data = {
                        "type": "bar",
                        "title": f"توزیع {field_name}",
                        "labels": labels,
                        "datasets": [{
                            "label": "تعداد",
                            "data": values,
                            "backgroundColor": ["rgba(54, 162, 235, 0.6)"] * len(values)
                        }]
                    }
            
            # Date histogram -> Line chart
            elif "date_histogram" in aggregations:
                buckets = aggregations["date_histogram"].get("buckets", [])
                if buckets:
                    labels = [bucket.get("key_as_string", bucket.get("key", "")) for bucket in buckets]
                    values = [bucket.get("doc_count", 0) for bucket in buckets]
                    
                    chart_data = {
                        "type": "line",
                        "title": f"روند زمانی {field_name}",
                        "labels": labels,
                        "datasets": [{
                            "label": "تعداد",
                            "data": values,
                            "borderColor": ["rgba(75, 192, 192, 1)"] * len(values),
                            "backgroundColor": ["rgba(75, 192, 192, 0.2)"] * len(values)
                        }]
                    }
            
            return chart_data
            
        except Exception as e:
            logger.error(f"Error preparing chart data: {e}")
            return None
    
    def _execute_list_indices_query(self, params: QueryParams) -> Dict[str, Any]:
        """Execute list indices query"""
        try:
            # Get all indices from cluster
            indices_response = self.es.cat.indices(format="json", h="index,docs.count,store.size")
            
            if not indices_response:
                return {"enabled": True, "indices": [], "total_indices": 0}
            
            # Format indices info
            indices_info = []
            for idx in indices_response:
                index_name = idx.get("index", "")
                doc_count = idx.get("docs.count", "0")
                size = idx.get("store.size", "0b")
                
                # Skip system indices (starting with .)
                if not index_name.startswith('.'):
                    indices_info.append({
                        "name": index_name,
                        "doc_count": doc_count,
                        "size": size
                    })
            
            return {
                "enabled": True,
                "query_type": "list_indices",
                "indices": indices_info,
                "total_indices": len(indices_info)
            }
        
        except Exception as e:
            return {"enabled": True, "error": f"خطا در دریافت فهرست ایندکس‌ها: {str(e)}"}
    
    def format_response(self, result: Dict[str, Any], params: QueryParams) -> str:
        """Format query result into user-friendly response"""
        if not result.get("enabled"):
            return "🔌 Elasticsearch غیرفعال است"
        
        if result.get("error"):
            return f"❌ {result['error']}"
        
        query_type = result.get("query_type", params.query_type.value)
        
        if query_type == "count":
            count = result.get("count", 0)
            pattern = result.get("index_pattern", "نامشخص")
            conditions = result.get("conditions", {})
            
            if conditions:
                condition_text = []
                for field, condition in conditions.items():
                    if condition['type'] == 'contains':
                        condition_text.append(f"{field} شامل '{condition['value']}'")
                    elif condition['type'] == 'equals':
                        condition_text.append(f"{field} برابر '{condition['value']}'")
                
                condition_str = " و ".join(condition_text)
                return f"📊 تعداد رکوردهایی که {condition_str} در '{pattern}': {count:,}"
            else:
                return f"📊 تعداد رکوردها در '{pattern}': {count:,}"
        
        elif query_type == "fetch":
            docs = result.get("docs", [])
            total = result.get("total", 0)
            pattern = result.get("index_pattern", "نامشخص")
            conditions = result.get("conditions", {})
            
            if not docs:
                if conditions:
                    condition_text = []
                    for field, condition in conditions.items():
                        if condition['type'] == 'contains':
                            condition_text.append(f"{field} شامل '{condition['value']}'")
                        elif condition['type'] == 'equals':
                            condition_text.append(f"{field} برابر '{condition['value']}'")
                    
                    condition_str = " و ".join(condition_text)
                    return f"📄 هیچ رکوردی که {condition_str} در '{pattern}' یافت نشد"
                else:
                    return f"📄 هیچ رکوردی در '{pattern}' یافت نشد"
            
            # Prepare table data
            table_data = []
            all_fields = ["_index", "_id"]  # Start with basic fields
            
            for i, doc in enumerate(docs[:10], 1):
                index = doc.get("_index", "")
                doc_id = doc.get("_id", "")
                source = doc.get("_source", {})
                
                # Add to table data instead of creating preview
                if isinstance(source, dict) and source:
                    # Collect all unique field names for table headers
                    for field_name in source.keys():
                        if field_name not in all_fields:
                            all_fields.append(field_name)
                    table_data.append({
                        "_index": index,
                        "_id": doc_id,
                        **source
                    })
                else:
                    # If no source data, show basic info
                    table_data.append({
                        "_index": index,
                        "_id": doc_id,
                        "data": "فیلد مورد نظر یافت نشد" if not source else str(source)[:100]
                    })
            
            # Create table format
            if table_data:
                if conditions:
                    condition_text = []
                    for field, condition in conditions.items():
                        if condition['type'] == 'contains':
                            condition_text.append(f"{field} شامل '{condition['value']}'")
                        elif condition['type'] == 'equals':
                            condition_text.append(f"{field} برابر '{condition['value']}'")
                    
                    condition_str = " و ".join(condition_text)
                    title = f"📄 {len(docs)} رکورد که {condition_str} از '{pattern}' (کل: {total:,})"
                else:
                    title = f"📄 {len(docs)} رکورد از '{pattern}' (کل: {total:,})"
                
                return self._format_as_table(table_data, all_fields, title)
            else:
                return f"📄 هیچ رکوردی در '{pattern}' یافت نشد"
        
        elif query_type == "search":
            results = result.get("results", [])
            total = result.get("total", 0)
            search_terms = result.get("search_terms", [])
            pattern = result.get("index_pattern", "نامشخص")
            
            if not results:
                return f"🔍 نتیجه‌ای برای '{' '.join(search_terms)}' در '{pattern}' یافت نشد"
            
            # Prepare table data for search results
            table_data = []
            all_fields = ["_index", "_id", "_score"]
            
            for result_item in results[:10]:
                index = result_item.get("_index", "")
                doc_id = result_item.get("_id", "")
                score = result_item.get("_score", 0)
                source = result_item.get("_source", {})
                highlight = result_item.get("highlight", {})
                
                # Add source fields to table
                row_data = {
                    "_index": index,
                    "_id": doc_id,
                    "_score": f"{score:.2f}",
                    **source
                }
                
                # Add highlight as a special field if available
                if highlight:
                    highlight_text = ""
                    for field, highlights in highlight.items():
                        highlight_text = " | ".join(highlights[:2])
                        break
                    if highlight_text:
                        row_data["highlight"] = highlight_text
                        if "highlight" not in all_fields:
                            all_fields.append("highlight")
                
                # Collect field names
                for field_name in source.keys():
                    if field_name not in all_fields:
                        all_fields.append(field_name)
                
                table_data.append(row_data)
            
            if table_data:
                return self._format_as_table(table_data, all_fields, f"🔍 {len(results)} نتیجه برای '{' '.join(search_terms)}' در '{pattern}' (کل: {total:,})")
            else:
                return f"🔍 نتیجه‌ای برای '{' '.join(search_terms)}' در '{pattern}' یافت نشد"
        
        elif query_type == "aggregate":
            aggs = result.get("aggregations", {})
            field = result.get("aggregation_field", "نامشخص")
            pattern = result.get("index_pattern", "نامشخص")
            sample_fields = result.get("sample_fields", [])
            operation = result.get("operation", "")
            result_value = result.get("result_value")
            limit = result.get("limit", 0)
            total_records = result.get("total_records", 0)
            
            # Handle filtered aggregation results (e.g., sum in last 10 records)
            if result_value is not None:
                operation_persian = {
                    'sum': 'جمع',
                    'avg': 'میانگین', 
                    'max': 'حداکثر',
                    'min': 'حداقل'
                }.get(operation, operation)
                
                lines = [f"🧮 نتیجه محاسبه '{operation_persian}' فیلد '{field}' در ایندکس '{pattern}':"]
                lines.append(f"📊 {operation_persian} فیلد '{field}' در {total_records} رکورد اخر: {result_value:,.2f}")
                
                if limit > 0:
                    lines.append(f"🔢 تعداد رکوردهای بررسی شده: {total_records}")
                
                return "\n".join(lines)
            
            # Handle traditional aggregation results
            if not aggs:
                return f"📈 آماری برای '{field}' در '{pattern}' یافت نشد"
            
            lines = [f"📈 تحلیل داده‌های '{pattern}' بر اساس '{field}':"]
            
            # Process terms aggregation
            if "terms_agg" in aggs:
                buckets = aggs["terms_agg"].get("buckets", [])
                if buckets:
                    lines.append(f"\n🏷️ توزیع مقادیر '{field}':")
                    for bucket in buckets[:15]:  # Show top 15
                        key = bucket.get("key", "نامشخص")
                        count = bucket.get("doc_count", 0)
                        lines.append(f"  • {key}: {count:,}")
            
            # Process date histogram
            if "date_histogram" in aggs:
                buckets = aggs["date_histogram"].get("buckets", [])
                if buckets:
                    lines.append(f"\n📅 توزیع زمانی '{field}':")
                    for bucket in buckets[-10:]:  # Last 10 periods
                        date = bucket.get("key_as_string", bucket.get("key", "نامشخص"))
                        count = bucket.get("doc_count", 0)
                        lines.append(f"  • {date}: {count:,}")
            
            # Process statistics
            if "stats" in aggs:
                stats = aggs["stats"]
                lines.append(f"\n📊 آمار عددی '{field}':")
                lines.append(f"  • تعداد: {stats.get('count', 0):,}")
                lines.append(f"  • مجموع: {stats.get('sum', 0):,.2f}")
                lines.append(f"  • میانگین: {stats.get('avg', 0):,.2f}")
                lines.append(f"  • کمینه: {stats.get('min', 0):,.2f}")
                lines.append(f"  • بیشینه: {stats.get('max', 0):,.2f}")
            
            # Show available fields for future queries
            if sample_fields:
                lines.append(f"\n💡 فیلدهای موجود در این ایندکس:")
                field_preview = ', '.join(sample_fields[:10])
                if len(sample_fields) > 10:
                    field_preview += f" و {len(sample_fields) - 10} فیلد دیگر"
                lines.append(f"  {field_preview}")
            
            # Add chart data to response if available
            chart_data = result.get("chart_data")
            if chart_data:
                lines.append(f"\n📊 نمودار داده‌ها آماده نمایش است")
            
            return "\n".join(lines)
        
        elif query_type == "list_indices":
            indices = result.get("indices", [])
            total = result.get("total_indices", 0)
            
            if not indices:
                return "📚 هیچ ایندکسی در کلاستر یافت نشد"
            
            lines = [f"📚 فهرست ایندکس‌های موجود ({total} ایندکس):"]
            
            for idx in indices:
                name = idx.get("name", "نامشخص")
                doc_count = idx.get("doc_count", "0")
                size = idx.get("size", "0b")
                
                # Format numbers
                try:
                    doc_num = int(doc_count) if doc_count != "-" else 0
                    doc_formatted = f"{doc_num:,}" if doc_num > 0 else "خالی"
                except:
                    doc_formatted = doc_count
                
                lines.append(f"• {name}: {doc_formatted} سند ({size})")
            
            return "\n".join(lines)
        
        return "❓ نتیجه قابل تفسیر نیست"
    
    def _format_as_table(self, data: List[Dict], fields: List[str], title: str) -> str:
        """Format data as HTML table"""
        if not data or not fields:
            return title + "\n(داده‌ای برای نمایش وجود ندارد)"
        
        # Filter fields that actually exist in data
        existing_fields = []
        for field in fields:
            if any(field in row for row in data):
                existing_fields.append(field)
        
        if not existing_fields:
            return title + "\n(فیلد قابل نمایشی وجود ندارد)"
        
        # Dynamic field translations - only translate common system fields
        # Let user field names remain as-is to support any data structure
        field_translations = {
            "_index": "ایندکس",
            "_id": "شناسه", 
            "_score": "امتیاز",
            "@timestamp": "زمان",
            "@version": "نسخه",
            "highlight": "برجسته شده"
        }
        
        # For unknown fields, use the original field name
        # This makes the system work with ANY data structure dynamically
        
        # Build HTML table with wrapper
        html_parts = [
            f"<div style='margin: 0; font-weight: bold; margin-bottom: 8px;'>{title}</div>",
            "<div class='es-table-wrapper'>",
            "<table style='border-collapse: collapse; width: 100%; font-family: monospace; font-size: 12px; direction: rtl;'>",
            "<thead style='background-color: #f5f5f5;'>",
            "<tr>"
        ]
        
        # Header row
        for field in existing_fields:
            display_name = field_translations.get(field, field)
            html_parts.append(f"<th style='border: 1px solid #ddd; padding: 8px; text-align: right; font-weight: bold;'>{display_name}</th>")
        
        html_parts.append("</tr>")
        html_parts.append("</thead>")
        html_parts.append("<tbody>")
        
        # Data rows
        for i, row in enumerate(data):
            if i >= 20:  # Limit to 20 rows for readability
                html_parts.append("<tr style='background-color: #fff3cd;'>")
                html_parts.append(f"<td colspan='{len(existing_fields)}' style='border: 1px solid #ddd; padding: 8px; text-align: center; font-style: italic;'>... و {len(data) - 20} رکورد دیگر</td>")
                html_parts.append("</tr>")
                break
            
            # Alternate row colors
            bg_color = "#f9f9f9" if i % 2 == 0 else "#ffffff"
            html_parts.append(f"<tr style='background-color: {bg_color};'>")
            
            for field in existing_fields:
                value = row.get(field, "")
                if value is None:
                    value_str = ""
                else:
                    value_str = str(value)
                    # Limit very long values
                    if len(value_str) > 100:
                        value_str = value_str[:97] + "..."
                    
                    # Escape HTML characters
                    value_str = value_str.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                
                # Special styling for certain fields
                cell_style = "border: 1px solid #ddd; padding: 6px; text-align: right;"
                if field == "_score":
                    cell_style += " font-weight: bold; color: #007bff;"
                elif field == "highlight":
                    cell_style += " background-color: #fff3cd; font-style: italic;"
                
                html_parts.append(f"<td style='{cell_style}'>{value_str}</td>")
            
            html_parts.append("</tr>")
        
        html_parts.append("</tbody>")
        html_parts.append("</table>")
        html_parts.append("</div>")  # Close wrapper
        
        return "".join(html_parts)
