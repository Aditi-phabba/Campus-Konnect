"""
Campus Konnect - Constants & Metadata Definitions
Defines system-wide constants, categories, options, and branding metadata.
"""

APP_NAME = "Campus Konnect"
APP_TAGLINE = "One Campus. One Community. One Connected Platform."
APP_DESCRIPTION = (
    "A verified, campus-specific digital platform bringing official announcements, "
    "events, academic resources, discussions, and student collaboration into one unified ecosystem."
)

# User Roles
ROLE_STUDENT = "student"
ROLE_ADMIN = "admin"
ROLES = [ROLE_STUDENT, ROLE_ADMIN]

# Academic Departments
DEPARTMENTS = [
    "Computer Science & Engineering",
    "Information Technology",
    "Data Science & AI",
    "Electronics & Communication",
    "Electrical Engineering",
    "Mechanical Engineering",
    "Civil Engineering",
    "Management Studies / MBA",
    "Applied Sciences & Humanities",
    "Other Department"
]

# Academic Years
YEARS = [1, 2, 3, 4, 5]
YEAR_LABELS = {
    1: "1st Year (Freshman)",
    2: "2nd Year (Sophomore)",
    3: "3rd Year (Junior)",
    4: "4th Year (Senior)",
    5: "5th Year (Dual/Postgrad)"
}

# Student Interest Tags
INTEREST_OPTIONS = [
    "Artificial Intelligence",
    "Machine Learning",
    "Web Development",
    "Mobile Apps",
    "Cybersecurity",
    "Cloud Computing",
    "Data Science",
    "Competitive Coding",
    "Robotics & IoT",
    "Blockchain",
    "Hackathons",
    "UI/UX Design",
    "Open Source",
    "Placements & Careers",
    "Internships",
    "Research & Papers",
    "Entrepreneurship",
    "Cultural & Music",
    "Photography & Film",
    "Sports & Fitness",
    "Debating & MUN",
    "Gaming & Esports"
]

# Post Categories
STUDENT_POST_CATEGORIES = [
    "Academic",
    "Opportunity",
    "Club",
    "Placement",
    "General"
]

POST_CATEGORIES = [
    "Announcement",
    "Academic",
    "Opportunity",
    "Club",
    "Placement",
    "General"
]


# Event Categories
EVENT_CATEGORIES = [
    "Workshop",
    "Seminar",
    "Hackathon",
    "Club",
    "Cultural",
    "Sports",
    "Placement",
    "Academic",
    "Other"
]

# Resource Types & Semesters
RESOURCE_TYPES = [
    "Notes",
    "Previous Year Paper",
    "Lab Manual",
    "Assignment",
    "Presentation",
    "Study Material",
    "Reference",
    "Other"
]

SEMESTERS = list(range(1, 9))

# Discussion Categories
DISCUSSION_CATEGORIES = [
    "Academics",
    "Placements",
    "Projects",
    "Events",
    "Clubs",
    "General"
]

# File Upload Rules
ALLOWED_RESOURCE_EXTENSIONS = ["pdf", "doc", "docx", "ppt", "pptx", "png", "jpg", "jpeg"]
ALLOWED_IMAGE_EXTENSIONS = ["png", "jpg", "jpeg", "webp"]
MAX_RESOURCE_FILE_SIZE_MB = 20
MAX_IMAGE_FILE_SIZE_MB = 5

# Storage Buckets
BUCKET_PROFILE_IMAGES = "profile-images"
BUCKET_RESOURCES = "resources"
BUCKET_POST_MEDIA = "post-media"
BUCKET_EVENT_IMAGES = "event-images"
