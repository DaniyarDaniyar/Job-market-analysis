"""Transparent English dictionary extraction; a mention is not proficiency."""
import re

PATTERNS = {
    'Python': r'python', 'SQL': r'sql|postgresql|mysql|sql server',
    'Java': r'java', 'JavaScript': r'javascript', 'TypeScript': r'typescript',
    'C++': r'c\+\+', 'C#': r'c\#', 'AWS': r'aws|amazon web services',
    'Azure': r'azure', 'GCP': r'gcp|google cloud', 'Docker': r'docker',
    'Kubernetes': r'kubernetes|k8s', 'Excel': r'(?:microsoft\s+)?excel(?!\s+at\b)',
    'Power BI': r'power\s?bi', 'Tableau': r'tableau', 'Spark': r'apache spark|pyspark',
    'Machine learning': r'machine learning', 'Statistics': r'statistics|statistical',
    'Communication': r'communication', 'Leadership': r'leadership',
    'Project management': r'project management', 'Sales': r'sales',
    'Customer service': r'customer service', 'Accounting': r'accounting',
    'Nursing': r'nursing', 'Git': r'git|github', 'Linux': r'linux',
    'React': r'react(?:\.js)?', 'TensorFlow': r'tensorflow', 'PyTorch': r'pytorch',
}
COMPILED = {k: re.compile(r'(?<!\w)(?:'+v+r')(?!\w)', re.I) for k,v in PATTERNS.items()}

def extract_skills(text: str) -> list[str]:
    return sorted(name for name, pattern in COMPILED.items() if pattern.search(str(text)))

def classify_role(title: str) -> str:
    text = title.lower()
    rules = [('Data & analytics', r'data|analyst|analytics|machine learning|statistic'),
             ('Software & IT', r'software|developer|devops|cloud|\bit\b|cyber|programmer'),
             ('Healthcare', r'nurs|physician|therap|medical|health|dental'),
             ('Sales & marketing', r'sales|marketing|account executive'),
             ('Finance', r'financ|accountant|accounting|audit'),
             ('Engineering', r'engineer|technician'),
             ('Operations & service', r'operations|customer|warehouse|driver|retail')]
    for name, pattern in rules:
        if re.search(pattern, text):
            return name
    return 'Other'
