"""Single source of truth for the assessment form: what is asked, how, and which model column it feeds.

`GET /schema` serves FIELDS, request validation checks against it, and inputs.py reads the model columns
from it. Categorical option values are exactly the category strings the pipelines were trained on.
"""

IMPORTANCE_OPTIONS = [
    {"value": 4, "label": "Very important"},
    {"value": 3, "label": "Somewhat important"},
    {"value": 2, "label": "Somewhat unimportant"},
    {"value": 1, "label": "Not important at all"},
]


def _labels(*values):
    return [{"value": v, "label": v} for v in values]


# (api name, model column, label, help) for the nine importance ratings; 4 = very important
IMPORTANCE = [
    ("advancement", "FACADV", "Opportunities for advancement", None),
    ("benefits", "FACBEN", "Benefits", None),
    ("challenge", "FACCHAL", "Intellectual challenge", None),
    ("independence", "FACIND", "Independence", None),
    ("location", "FACLOC", "Location", None),
    ("responsibility", "FACRESP", "Level of responsibility", None),
    ("salary", "FACSAL", "Salary", None),
    ("security", "FACSEC", "Job security", None),
    ("society", "FACSOC", "Contribution to society", None),
]

TELEWORK_OPTIONS = _labels(
    "Allowed to telework, and did", "Allowed to telework, and didn't", "Not allowed or required to telework",
    "Telework didn't make sense for job", "Required to telework")
TELEWORKS = {"Allowed to telework, and did", "Required to telework"}  # the only answers with telework days

# categorical form fields: api name -> (model column, label, options)
CATEGORICAL = {
    "sex": ("SEX_2023", "Sex", _labels("Female", "Male")),
    "race_ethnicity": ("RACETHM", "Race/ethnicity", _labels(
        "Asian", "American Indian/Alaska Native", "Black", "Hispanic, any race", "White",
        "Native Hawaiian/Pacific Islander", "Multiple race")),
    "citizenship": ("CTZN", "Citizenship", _labels(
        "U.S. citizen, native", "U.S. citizen, naturalized", "Permanent resident", "Temporary resident")),
    "marital_status": ("MARSTA", "Marital status", _labels(
        "Married", "Marriage-like relationship", "Widowed", "Separated", "Divorced", "Never married")),
    "highest_degree": ("DGRDG", "Highest degree", _labels("Bachelor's", "Master's", "Doctorate", "Professional")),
    "degree_field": ("NDGMEMG", "Field of highest degree", _labels(
        "Computer and mathematical sciences", "Life sciences", "Physical sciences", "Social sciences",
        "Engineering", "S&E-related fields", "Non-S&E fields")),
    "employer_type": ("NEDTP", "Employer type", _labels(
        "Self-employed, not incorporated", "Self-employed, incorporated", "Private for-profit",
        "Private not-for-profit", "Local government", "State government", "U.S. military",
        "U.S. federal government (civilian)", "Other employer type")),
    "telework": ("TELEC", "Telework situation", TELEWORK_OPTIONS),
}

EMPLOYER_SIZE_OPTIONS = [
    {"value": 1, "label": "10 or fewer employees"}, {"value": 2, "label": "11-24 employees"},
    {"value": 3, "label": "25-99 employees"}, {"value": 4, "label": "100-499 employees"},
    {"value": 5, "label": "500-999 employees"}, {"value": 6, "label": "1,000-4,999 employees"},
    {"value": 7, "label": "5,000-24,999 employees"}, {"value": 8, "label": "25,000+ employees"},
]
RELATEDNESS_OPTIONS = [
    {"value": 1, "label": "Closely related"}, {"value": 2, "label": "Somewhat related"},
    {"value": 3, "label": "Not related"},
]
TELEWORK_DAYS_OPTIONS = [{"value": d, "label": f"{d} day{'s' if d != 1 else ''} per week"} for d in range(5)]

BOOLEANS = {  # api name -> (model column, label, group)
    "offers_health_insurance": ("JOBINS", "Employer offers health insurance", "Benefits"),
    "offers_pension": ("JOBPENS", "Employer offers a pension/retirement plan", "Benefits"),
    "offers_profit_sharing": ("JOBPROFT", "Employer offers profit sharing", "Benefits"),
    "offers_paid_leave": ("JOBVAC", "Employer offers paid vacation/sick/personal days", "Benefits"),
    "expertise_natural_sci_eng": ("MGRNAT", "Job requires expertise in engineering, computer science, math "
                                  "or natural sciences", "Job requirements"),
    "expertise_other": ("MGROTH", "Job requires expertise in other fields (e.g. health, business)",
                        "Job requirements"),
    "expertise_social_sci": ("MGRSOC", "Job requires expertise in the social sciences", "Job requirements"),
}

# numeric form fields: api name -> (model column, label, min, max, group, help)
NUMBERS = {
    "age": ("AGE", "Age", 16, 100, "About you", "Years"),
    "tenure_years": ("tenure_years", "Years in your current job", 0, 60, "Your job", "0 if you started this year"),
    "hours_per_week": ("HRSWK", "Hours worked per week", 1, 96, "Your job", "96 means 96 or more"),
    "weeks_per_year": ("WKSWK", "Weeks worked per year", 1, 52, "Your job", "52 if you work all year"),
    "salary": ("SALARY", "Annual salary (USD)", 0, 100_000_000, "Your job", "Before taxes; 0 if you report none"),
}


def _field(name, label, type_, group, **kw):
    return {"name": name, "label": label, "type": type_, "group": group, "required": False,
            "options": None, "min": None, "max": None, "default": None, "help": None, **kw}


def build_fields():
    fields = [_field("occupation_code", "Occupation", "occupation", "Your job", required=True,
                     help="Pick from GET /occupations; sends the occupation's code")]
    for name, (_, label, lo, hi, group, hlp) in NUMBERS.items():
        fields.append(_field(name, label, "number", group, min=lo, max=hi, help=hlp,
                             default=52 if name == "weeks_per_year" else None))
    fields.append(_field("employer_size", "Employer size", "select", "Your job", options=EMPLOYER_SIZE_OPTIONS))
    fields.append(_field("degree_relatedness", "How related is your job to your highest degree?", "select",
                         "Your job", options=RELATEDNESS_OPTIONS))
    for name, (_, label, options) in CATEGORICAL.items():
        group = {"sex": "About you", "race_ethnicity": "About you", "citizenship": "About you",
                 "marital_status": "About you", "highest_degree": "Education", "degree_field": "Education"}
        fields.append(_field(name, label, "select", group.get(name, "Your job"), options=options))
    fields.append(_field("telework_days", "Days you telework per week", "select", "Your job",
                         options=TELEWORK_DAYS_OPTIONS,
                         help="Only ask when telework is 'Allowed to telework, and did' or 'Required to "
                              "telework'; otherwise it counts as 0"))
    for name, (_, label, group) in BOOLEANS.items():
        fields.append(_field(name, label, "boolean", group))
    for name, _, label, hlp in IMPORTANCE:
        fields.append(_field(f"importance.{name}", f"How important is: {label}?", "select", "What you value",
                             options=IMPORTANCE_OPTIONS, help=hlp))
    return fields


FIELDS = build_fields()
