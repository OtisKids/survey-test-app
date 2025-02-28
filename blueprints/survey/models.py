# blueprints/survey/models.py
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Question:
    """Question model for surveys"""
    id: int
    text: str
    category: str = "General"
    type: str = "scale"
    options: List[str] = field(default_factory=list)
    min_value: int = 0
    max_value: int = 10
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "text": self.text,
            "category": self.category,
            "type": self.type,
            "options": self.options,
            "min_value": self.min_value,
            "max_value": self.max_value
        }

@dataclass
class Survey:
    """Survey model"""
    id: int
    title: str
    description: str
    category: str = "General"
    questions: List[Question] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "questions": [q.to_dict() for q in self.questions],
            "created_at": self.created_at.isoformat()
        }

@dataclass
class SurveyResponse:
    """Survey response model"""
    username: str
    survey_id: int
    answers: List[Any]
    timestamp: datetime = field(default_factory=datetime.now)
    survey_type: str = "standard"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "username": self.username,
            "survey_id": self.survey_id,
            "answers": self.answers,
            "timestamp": self.timestamp.isoformat(),
            "survey_type": self.survey_type
        }
'''
def survey_from_dict(data: Dict) -> Optional[Survey]:
    """Create a Survey object from dictionary data"""
    try:
        questions = []
        for q in data.get("questions", []):
            questions.append(Question(
                id=q.get("id", 0),
                text=q.get("text", ""),
                category=q.get("category", "General"),
                type=q.get("type", "scale"),
                options=q.get("options", []),
                min_value=q.get
'''