from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Experience:
    position_title: str
    institution_name: str
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    duration: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    linkedin_url: Optional[str] = None

@dataclass
class Education:
    institution_name: str
    degree: Optional[str] = None
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    description: Optional[str] = None
    linkedin_url: Optional[str] = None

@dataclass
class Interest:
    name: str
    category: str
    linkedin_url: Optional[str] = None

@dataclass
class Accomplishment:
    category: str
    title: str
    issuer: Optional[str] = None
    issued_date: Optional[str] = None
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None

@dataclass
class Contact:
    type: str
    value: str
    label: Optional[str] = None

@dataclass
class Person:
    linkedin_url: str
    name: str
    headline: Optional[str] = None
    location: Optional[str] = None
    about: Optional[str] = None
    experiences: List[Experience] = field(default_factory=list)
    educations: List[Education] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    
    open_to_work: bool = False
    interests: List[Interest] = field(default_factory=list)
    accomplishments: List[Accomplishment] = field(default_factory=list)
    contacts: List[Contact] = field(default_factory=list)