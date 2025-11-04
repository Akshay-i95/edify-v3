"""
Namespace Validation Module for Edify AI Assistant

This module provides namespace validation functionality to ensure users only access
content appropriate to their grade level and department access permissions.

Features:
- Grade-level access validation for KB namespaces
- Department access validation for Edipedia namespaces  
- User-friendly error messages for access violations
- Grade mention detection in user queries
"""

import re
import logging
from typing import List, Dict, Optional, Tuple, Set
from enum import Enum

class NamespaceType(Enum):
    KB_ESP = "kb-esp"       # Early School Program (Playgroup to IK3)
    KB_PSP = "kb-psp"       # Primary School Program (Grade 1-5)
    KB_MSP = "kb-msp"       # Middle School Program (Grade 6-10)
    KB_SSP = "kb-ssp"       # Senior School Program (Grade 11-12)
    EDIPEDIA_K12 = "edipedia-k12"           # K12 General Content
    EDIPEDIA_PRESCHOOLS = "edipedia-preschools"  # Preschool Content
    EDIPEDIA_EDIFYHO = "edipedia-edifyho"        # Head Office/Administrative

class NamespaceValidator:
    """Validates user access to different namespaces based on grade levels and departments"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Define grade mappings for KB namespaces
        self.KB_NAMESPACE_MAPPINGS = {
            NamespaceType.KB_ESP.value: {
                'grades': ['playgroup', 'nursery', 'lkg', 'ukg', 'ik1', 'ik2', 'ik3'],
                'grade_numbers': [],  # No numeric grades for early childhood
                'display_name': 'Early School Program',
                'age_range': 'Playgroup to IK3',
                'description': 'Early childhood education content'
            },
            NamespaceType.KB_PSP.value: {
                'grades': ['grade1', 'grade2', 'grade3', 'grade4', 'grade5'],
                'grade_numbers': [1, 2, 3, 4, 5],
                'display_name': 'Primary School Program', 
                'age_range': 'Grades 1-5',
                'description': 'Primary school curriculum content'
            },
            NamespaceType.KB_MSP.value: {
                'grades': ['grade6', 'grade7', 'grade8', 'grade9', 'grade10'],
                'grade_numbers': [6, 7, 8, 9, 10],
                'display_name': 'Middle School Program',
                'age_range': 'Grades 6-10', 
                'description': 'Middle school curriculum content'
            },
            NamespaceType.KB_SSP.value: {
                'grades': ['grade11', 'grade12'],
                'grade_numbers': [11, 12],
                'display_name': 'Senior School Program',
                'age_range': 'Grades 11-12',
                'description': 'Senior school curriculum content'
            }
        }
        
        # Define access mappings for Edipedia namespaces
        self.EDIPEDIA_NAMESPACE_MAPPINGS = {
            NamespaceType.EDIPEDIA_K12.value: {
                'departments': ['academic', 'curriculum', 'teaching', 'k12'],
                'display_name': 'K12 Academic Content',
                'description': 'General K12 educational content and policies'
            },
            NamespaceType.EDIPEDIA_PRESCHOOLS.value: {
                'departments': ['preschool', 'early_childhood', 'nursery'],
                'display_name': 'Preschool Content',
                'description': 'Preschool and early childhood education content'
            },
            NamespaceType.EDIPEDIA_EDIFYHO.value: {
                'departments': ['administration', 'hr', 'finance', 'operations', 'head_office'],
                'display_name': 'Administrative Content',
                'description': 'Administrative policies and procedures'
            }
        }
        
        # Grade detection patterns
        self.GRADE_PATTERNS = [
            # Numeric patterns
            r'\bgrade\s*(\d{1,2})\b',           # "grade 7", "grade7"
            r'\b(\d{1,2})(?:st|nd|rd|th)\s*grade\b',  # "7th grade", "1st grade"
            r'\bclass\s*(\d{1,2})\b',           # "class 7", "class7"
            r'\b(\d{1,2})(?:st|nd|rd|th)\s*class\b',  # "7th class"
            r'\bstd\s*(\d{1,2})\b',             # "std 7", "std7"
            r'\b(\d{1,2})(?:st|nd|rd|th)\s*std\b',    # "7th std"
            r'\blevel\s*(\d{1,2})\b',           # "level 7"
            r'\b(\d{1,2})(?:st|nd|rd|th)\s*level\b',  # "7th level"
            
            # Named patterns for early childhood
            r'\b(playgroup|nursery|lkg|ukg|ik1|ik2|ik3)\b',
            r'\b(pre-k|pre-kindergarten|kindergarten)\b',
            r'\b(toddler|infant|baby)\b',
            
            # School level patterns
            r'\b(primary\s*school|elementary\s*school)\b',
            r'\b(middle\s*school|junior\s*high)\b', 
            r'\b(high\s*school|senior\s*school|secondary\s*school)\b',
        ]
        
        self.logger.info("NamespaceValidator initialized with KB and Edipedia mappings")
    
    def validate_query_access(self, query: str, user_namespaces: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate if user has access to content mentioned in their query
        
        Args:
            query: User's query text
            user_namespaces: List of namespaces user has access to
            
        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if access is allowed, False if denied
            - error_message: Error message if access denied, None if allowed
        """
        try:
            # Detect grades mentioned in query
            mentioned_grades = self._detect_grades_in_query(query)
            
            if not mentioned_grades:
                # No specific grades mentioned, allow access
                return True, None
            
            # Check if any mentioned grades are outside user's access
            accessible_grades = self._get_accessible_grades(user_namespaces)
            
            # Find grades that user doesn't have access to
            inaccessible_grades = []
            for grade in mentioned_grades:
                if not self._is_grade_accessible(grade, accessible_grades):
                    inaccessible_grades.append(grade)
            
            if inaccessible_grades:
                # Generate appropriate error message
                error_message = self._generate_access_error_message(
                    inaccessible_grades, user_namespaces, accessible_grades
                )
                return False, error_message
            
            return True, None
            
        except Exception as e:
            self.logger.error(f"Error in namespace validation: {str(e)}")
            # On error, allow access (fail open)
            return True, None
    
    def _detect_grades_in_query(self, query: str) -> Set[str]:
        """Detect grade levels mentioned in the user's query"""
        mentioned_grades = set()
        query_lower = query.lower()
        
        try:
            # Check each pattern
            for pattern in self.GRADE_PATTERNS:
                matches = re.findall(pattern, query_lower, re.IGNORECASE)
                
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0] if match[0] else match[1]
                    
                    # Convert numeric matches to grade format
                    if match.isdigit():
                        grade_num = int(match)
                        if 1 <= grade_num <= 12:
                            mentioned_grades.add(f"grade{grade_num}")
                    else:
                        # Add named grades directly
                        mentioned_grades.add(match.lower())
            
            # Special handling for school level mentions
            if any(term in query_lower for term in ['primary school', 'elementary school']):
                mentioned_grades.update(['grade1', 'grade2', 'grade3', 'grade4', 'grade5'])
            elif any(term in query_lower for term in ['middle school', 'junior high']):
                mentioned_grades.update(['grade6', 'grade7', 'grade8', 'grade9', 'grade10'])
            elif any(term in query_lower for term in ['high school', 'senior school', 'secondary school']):
                mentioned_grades.update(['grade11', 'grade12'])
            
            if mentioned_grades:
                self.logger.info(f"Detected grades in query: {mentioned_grades}")
            
            return mentioned_grades
            
        except Exception as e:
            self.logger.error(f"Error detecting grades in query: {str(e)}")
            return set()
    
    def _get_accessible_grades(self, namespaces: List[str]) -> Set[str]:
        """Get all grades accessible through the given namespaces"""
        accessible_grades = set()
        
        try:
            for namespace in namespaces:
                if namespace in self.KB_NAMESPACE_MAPPINGS:
                    mapping = self.KB_NAMESPACE_MAPPINGS[namespace]
                    accessible_grades.update(mapping['grades'])
                # For Edipedia namespaces, allow all grades (they're general content)
                elif namespace.startswith('edipedia-'):
                    # Edipedia content is generally accessible regardless of grade
                    all_kb_grades = set()
                    for kb_mapping in self.KB_NAMESPACE_MAPPINGS.values():
                        all_kb_grades.update(kb_mapping['grades'])
                    accessible_grades.update(all_kb_grades)
            
            self.logger.debug(f"Accessible grades for namespaces {namespaces}: {accessible_grades}")
            return accessible_grades
            
        except Exception as e:
            self.logger.error(f"Error getting accessible grades: {str(e)}")
            return set()
    
    def _is_grade_accessible(self, grade: str, accessible_grades: Set[str]) -> bool:
        """Check if a specific grade is accessible"""
        # Direct match
        if grade in accessible_grades:
            return True
        
        # Check numeric equivalents for named grades
        grade_lower = grade.lower()
        
        # Special mappings for common grade references
        grade_mappings = {
            'kindergarten': ['ik1', 'ik2', 'ik3'],
            'pre-k': ['playgroup', 'nursery', 'lkg', 'ukg'],
            'pre-kindergarten': ['playgroup', 'nursery', 'lkg', 'ukg']
        }
        
        if grade_lower in grade_mappings:
            return any(mapped_grade in accessible_grades for mapped_grade in grade_mappings[grade_lower])
        
        return False
    
    def _generate_access_error_message(self, inaccessible_grades: List[str], 
                                     user_namespaces: List[str], 
                                     accessible_grades: Set[str]) -> str:
        """Generate user-friendly error message for access violations"""
        try:
            # Format the inaccessible grades nicely
            formatted_grades = []
            for grade in inaccessible_grades:
                if grade.startswith('grade'):
                    grade_num = grade.replace('grade', '')
                    formatted_grades.append(f"Grade {grade_num}")
                else:
                    formatted_grades.append(grade.title())
            
            # Get user's accessible grade ranges
            accessible_ranges = self._get_accessible_grade_ranges(user_namespaces)
            
            # Build the error message
            if len(formatted_grades) == 1:
                grade_text = formatted_grades[0]
            else:
                grade_text = ', '.join(formatted_grades[:-1]) + f" and {formatted_grades[-1]}"
            
            error_message = (
                f"I'm sorry, but you don't have access to {grade_text} content. "
                f"Your current access is limited to: {accessible_ranges}. "
                f"Please ask about topics within your accessible grade levels, or contact "
                f"your administrator if you need access to additional grade levels."
            )
            
            return error_message
            
        except Exception as e:
            self.logger.error(f"Error generating access error message: {str(e)}")
            return (
                "I'm sorry, but you don't have access to the grade level mentioned in your query. "
                "Please ask about topics within your accessible grade levels."
            )
    
    def _get_accessible_grade_ranges(self, namespaces: List[str]) -> str:
        """Get human-readable description of accessible grade ranges"""
        try:
            ranges = []
            
            for namespace in namespaces:
                if namespace in self.KB_NAMESPACE_MAPPINGS:
                    mapping = self.KB_NAMESPACE_MAPPINGS[namespace]
                    ranges.append(mapping['age_range'])
                elif namespace in self.EDIPEDIA_NAMESPACE_MAPPINGS:
                    mapping = self.EDIPEDIA_NAMESPACE_MAPPINGS[namespace]
                    ranges.append(mapping['display_name'])
            
            if not ranges:
                return "your assigned content areas"
            
            return ', '.join(ranges)
            
        except Exception as e:
            self.logger.error(f"Error getting accessible grade ranges: {str(e)}")
            return "your assigned content areas"
    
    def get_namespace_info(self, namespace: str) -> Optional[Dict]:
        """Get information about a specific namespace"""
        if namespace in self.KB_NAMESPACE_MAPPINGS:
            return self.KB_NAMESPACE_MAPPINGS[namespace]
        elif namespace in self.EDIPEDIA_NAMESPACE_MAPPINGS:
            return self.EDIPEDIA_NAMESPACE_MAPPINGS[namespace]
        return None
    
    def get_all_kb_namespaces(self) -> List[str]:
        """Get all available KB namespaces"""
        return list(self.KB_NAMESPACE_MAPPINGS.keys())
    
    def get_all_edipedia_namespaces(self) -> List[str]:
        """Get all available Edipedia namespaces"""
        return list(self.EDIPEDIA_NAMESPACE_MAPPINGS.keys())
    
    def get_all_namespaces(self) -> List[str]:
        """Get all available namespaces"""
        return self.get_all_kb_namespaces() + self.get_all_edipedia_namespaces()


# Global instance for easy import
namespace_validator = NamespaceValidator()