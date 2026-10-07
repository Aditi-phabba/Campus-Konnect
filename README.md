# 🎓 Campus Konnect

> **"One Campus. One Community. One Connected Platform."**

Campus Konnect is a verified, campus-specific digital platform that unifies official campus announcements, event management, academic resource sharing, peer discussions, and personalized content discovery into a single, cohesive web application.

Designed to replace fragmented and informal communication channels (WhatsApp groups, unorganized email threads, bulletin boards), Campus Konnect provides an authenticated, role-based, and student-friendly experience backed by PostgreSQL and Supabase.

---

## 📋 Table of Contents
1. [Project Overview](#-project-overview)
2. [Key Features](#-key-features)
3. [Technology Stack](#-technology-stack)
4. [Architecture](#-architecture)
5. [Project Structure](#-project-structure)
6. [Prerequisites](#-prerequisites)
7. [Local Setup & Installation](#-local-setup--installation)
8. [Supabase Project Setup](#-supabase-project-setup)
9. [Running schema.sql](#-running-schemasql)
10. [Configuring Storage Buckets](#-configuring-storage-buckets)
11. [Environment Variables](#-environment-variables)
12. [Running the Application](#-running-the-application)
13. [Assigning an Administrator](#-assigning-an-administrator)
14. [Deployment to Streamlit Cloud](#-deployment-to-streamlit-cloud)
15. [Smart Feed Algorithm (Viva Explanation)](#-smart-feed-algorithm-viva-explanation)
16. [Troubleshooting](#-troubleshooting)
17. [Future Enhancements](#-future-enhancements)

---

## 🌟 Project Overview
In typical higher education institutions, crucial announcements, academic materials, hackathons, and placement circulars are scattered across multiple disparate platforms. This fragmentation leads to missed deadlines, lost academic resources, and communication silos.

**Campus Konnect** provides:
- **Centralized Campus Feed:** Social information feed for peer posts, club activities, and faculty notices.
- **Smart Campus Feed:** A transparent, rule-based recommendation engine prioritizing updates matching student department, year, and stated interests.
- **Events Center:** One-click registration for workshops, hackathons, seminars, and fests.
- **Academic Resource Hub:** Fast access and cloud storage for lecture notes, past exam papers, and lab manuals.
- **Discussion Forum:** Structured category threads for placement interview questions, academic doubts, and project matchmaking.
- **Administrative Governance:** Moderation controls, metric dashboards, and verified announcements.

---

## ⚡ Key Features

| Feature | Description |
| :--- | :--- |
| **Authentication** | Secure sign-up, sign-in, and session persistence via Supabase Auth. |
| **User Profiles** | Editable profile fields (name, department, year, bio, avatar upload, and interest tags). |
| **Campus Feed** | Create posts with categories, like/unlike, save/bookmark, comment, and edit/delete own posts. |
| **Smart Feed** | Multi-attribute scoring (+3 interest match, +2 department, +2 academic year, +1 recency, +5 announcements). |
| **Events Module** | Discover, host, and register for campus events with attendee tracking and timeline categorization. |
| **Resource Hub** | Upload and download academic files (PDF, DOCX, PPT, PNG) to Supabase Storage with semester filters. |
| **Discussion Forum** | Threaded community forum with categorized topics and nested replies. |
| **Admin Control** | Platform-wide metrics, user directory with role assignment, official notices, and moderation. |
| **Security & RLS** | PostgreSQL Row Level Security (RLS) policies enforcing ownership and role separation. |

---

## 🛠️ Technology Stack

- **Frontend & App Logic:** [Python 3.10+](https://python.org) & [Streamlit](https://streamlit.io)
- **Backend & Database:** [PostgreSQL](https://www.postgresql.org) on [Supabase](https://supabase.com)
- **Authentication:** Supabase Auth (JWT & Session Management)
- **Object Storage:** Supabase Storage (Buckets for profile avatars, resources, event posters, post media)
- **Data Manipulation:** [Pandas](https://pandas.pydata.org)
- **Environment Management:** `python-dotenv`

---

## 🏛️ Architecture

```
Student / Administrator
           │
           ▼
Streamlit Frontend (app.py)
           │
 ┌─────────┴───────────────────────────────────────────┐
 │                                                     │
 │   Pages / Views (Home, Feed, Events, Resources,    │
 │                  Discussions, Profile, Admin)       │
 │                                                     │
 │   Components (Cards, Sidebar, Navbar, Badges)       │
 │                                                     │
 │   Services Layer:                                   │
 │   ├── auth.py          ├── posts.py                 │
 │   ├── users.py         ├── events.py                │
 │   ├── resources.py     ├── discussions.py           │
 │   ├── admin.py         └── recommendations.py       │
 │                                                     │
 └─────────────────────────┬───────────────────────────┘
                           │
                           ▼
          Supabase Backend Ecosystem
         ┌──────────────────────────────┐
         │ 1. Supabase Auth             │
         │ 2. PostgreSQL with RLS       │
         │ 3. Storage Buckets           │
         └──────────────────────────────┘
```

---

## 📂 Project Structure

```
Campus-Konnect/
│
├── app.py                      # Main application entry point & routing controller
├── requirements.txt            # Python dependencies
├── README.md                   # Comprehensive documentation & viva guide
├── .env.example                # Template for environment variables
├── .gitignore                  # Git ignore rules for virtualenvs and secrets
│
├── .streamlit/
│   └── config.toml             # Streamlit theme, typography, and server configs
│
├── pages/
│   ├── home.py                 # Student dashboard & overview statistics
│   ├── feed.py                 # Social feed with Smart Feed recommendation filter
│   ├── events.py               # Event discovery, hosting, and registrations
│   ├── resources.py            # Academic notes & syllabus material repository
│   ├── discussions.py          # Category-based discussion forum
│   ├── profile.py              # Profile management, avatar upload, and user activity
│   └── admin.py                # Admin dashboard, role elevation, and content moderation
│
├── components/
│   ├── navbar.py               # Top branding and banner component
│   ├── sidebar.py              # Navigation links, user profile badge, and sign-out
│   ├── post_card.py            # Post rendering with likes, saves, and comments
│   ├── event_card.py           # Event card with status badges and registration buttons
│   ├── resource_card.py        # Resource card with file types and download links
│   ├── discussion_card.py      # Discussion thread card with reply composer
│   └── ui_components.py        # Design tokens, custom CSS, empty states, metric cards
│
├── services/
│   ├── database.py             # Supabase client factory and storage helpers
│   ├── auth.py                 # Sign-up, sign-in, session state, and profile sync
│   ├── users.py                # Profile mutations, avatar upload, activity statistics
│   ├── posts.py                # Post CRUD, likes, bookmarks, and comments
│   ├── events.py               # Event CRUD, registrations, attendee roster
│   ├── resources.py            # Resource metadata and cloud file uploads
│   ├── discussions.py          # Forum threads, replies, and queries
│   ├── admin.py                # Platform metrics, user listing, role assignment
│   └── recommendations.py      # Rule-based Smart Feed recommendation engine
│
├── utils/
│   ├── constants.py            # Categories, departments, semesters, allowed filetypes
│   ├── helpers.py              # Relative timestamps, date formatters, size calculators
│   └── validators.py           # Input sanitization and file upload validation
│
└── supabase/
    └── schema.sql              # Complete PostgreSQL schema, triggers, and RLS policies
```

---

## ⚙️ Prerequisites

Before running the project locally, ensure you have:
1. **Python 3.10, 3.11, 3.12, or 3.13** installed.
2. A free account on [Supabase](https://supabase.com).
3. Git installed on your system.

---

## 🚀 Local Setup & Installation

### Step 1: Clone the Repository
```bash
git clone https://github.com/Aditi-phabba/Campus-Konnect.git
cd Campus-Konnect
```

### Step 2: Create a Python Virtual Environment
```bash
python -m venv venv
```

### Step 3: Activate the Virtual Environment
- **On Windows (PowerShell):**
  ```powershell
  venv\Scripts\activate
  ```
- **On Windows (Command Prompt):**
  ```cmd
  venv\Scripts\activate.bat
  ```
- **On macOS / Linux:**
  ```bash
  source venv/bin/activate
  ```

### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🗄️ Supabase Project Setup

1. Go to [https://supabase.com/dashboard](https://supabase.com/dashboard) and sign in.
2. Click **New Project**, choose a project name (e.g., `campus-konnect`) and a secure database password.
3. Select the region closest to you and click **Create new project**.

---

## 📜 Running schema.sql

1. In your Supabase Dashboard, click on **SQL Editor** in the left sidebar.
2. Click **New query**.
3. Open `supabase/schema.sql` from this repository, copy all contents, paste into the SQL Editor, and click **Run**.
4. This script automatically:
   - Sets up `profiles`, `posts`, `comments`, `likes`, `saved_posts`, `events`, `event_registrations`, `resources`, `discussions`, and `discussion_comments`.
   - Creates triggers to synchronize Supabase Auth users to `profiles`.
   - Establishes Row Level Security (RLS) policies.
   - Configures storage buckets (`profile-images`, `resources`, `post-media`, `event-images`).

---

## 📦 Configuring Storage Buckets

The `supabase/schema.sql` script creates the buckets automatically. To verify:
1. Go to **Storage** in the Supabase Dashboard.
2. Ensure the following buckets exist and are marked **Public**:
   - `profile-images`
   - `resources`
   - `post-media`
   - `event-images`

---

## 🔑 Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   *(On Windows Command Prompt, use `copy .env.example .env`)*

2. In your Supabase Dashboard, navigate to **Project Settings** -> **API**.
3. Copy the **Project URL** and the **anon (public)** key.
4. Fill them into your `.env` file:
   ```env
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_KEY=your_supabase_anon_key
   ```

*(Note: Never commit your `.env` file to GitHub. It is already included in `.gitignore`.)*

---

## ▶️ Running the Application

With your virtual environment activated and `.env` configured:

```bash
streamlit run app.py
```

The application will launch in your browser at:
`http://localhost:8501`

---

## 🛡️ Assigning an Administrator

1. Open the application and create a student account through the **Create Student Account** tab (e.g., `admin@college.edu`).
2. Open your Supabase Dashboard -> **SQL Editor**.
3. Run the following SQL statement to promote your account to the `admin` role:
   ```sql
   UPDATE public.profiles
   SET role = 'admin'
   WHERE email = 'admin@college.edu';
   ```
4. Sign in (or refresh the page in Streamlit).
5. The **🛠️ Admin Dashboard** navigation tab will now be visible in your sidebar.

---

## ☁️ Deployment to Streamlit Cloud

1. Push your repository to GitHub:
   ```bash
   git add .
   git commit -m "Complete Campus Konnect MVP"
   git push origin main
   ```
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app**, select your repository (`Aditi-phabba/Campus-Konnect`), branch `main`, and main file `app.py`.
4. Under **Advanced settings**, add your Supabase credentials into **Secrets**:
   ```toml
   SUPABASE_URL = "https://your-project-id.supabase.co"
   SUPABASE_KEY = "your_supabase_anon_key"
   ```
5. Click **Deploy!**

---

## 🧠 Smart Feed Algorithm (Viva Explanation)

> **Viva Note:** The recommendation engine is implemented in [`services/recommendations.py`](file:///c:/Users/AdminS/Desktop/Campus-Konnect/services/recommendations.py). It uses a transparent, rule-based heuristic scoring system rather than a complex black-box model.

### Scoring Logic:
- **Official Pinned Announcements:** `+5.0 points`
  - High priority for college notices, examination updates, and emergency alerts.
- **Interest Alignment:** `+3.0 points`
  - When post or event content matches the student's declared interests (e.g., AI, Hackathons, Web Dev).
- **Department Affinity:** `+2.0 points`
  - Content authored by peers or faculty within the same department.
- **Academic Year Alignment:** `+2.5 points`
  - 3rd and 4th-year students receive prioritized Placement & Internship opportunities.
  - 1st-year students receive prioritized Academic & Club orientation posts.
- **Recency Boost:** `+1.0 point`
  - Content created within the last 48 hours.

---

## 🛠️ Troubleshooting

- **"Database connection not configured" on startup:**
  - Verify that `.env` is located in the root directory and contains valid `SUPABASE_URL` and `SUPABASE_KEY`.
- **"Invalid login credentials":**
  - Ensure you created the account first via the registration tab. Check if email confirmation is enabled in your Supabase Auth settings; if required, confirm via email or disable "Confirm email" in Supabase Auth -> Providers -> Email for immediate local testing.
- **Upload fails in Resource Hub:**
  - Verify that the `resources` bucket exists in Supabase Storage and has public read access.

---

## 🔮 Future Enhancements
- Fine-tuned Machine Learning models for personalized content ranking.
- AI-powered Campus Assistant / Chatbot for academic FAQs.
- Real-time peer-to-peer chat with WebSockets.
- Mobile application using React Native or Flutter.
- Multi-campus inter-collegiate networking.
