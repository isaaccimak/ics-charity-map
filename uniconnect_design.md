# UniConnect — System Design

A two-sided matching platform connecting recent graduates with current university students.

---

## Actors

- **Graduate** — recently graduated, applies to connect with someone at their chosen uni
- **Uni Student** — currently enrolled, signs up via the site, can accept/decline graduate posts
- **Admin** — reviews graduate screening submissions and activates student accounts

---

## Tech Stack

- **Frontend**: React + TypeScript (SPA)
- **Backend**: Node.js (Express) or Python (Django REST)
- **Database**: PostgreSQL
- **File Storage**: S3-compatible (AWS S3 / Cloudflare R2)
- **Job Queue**: Redis + BullMQ (or Celery)
- **Email**: AWS SES or SendGrid
- **Auth**: JWT (access + refresh tokens); magic links for students
- **Hosting**: Railway / Render / Fly.io

---

## Database Schema

```sql
universities (id, name, slug, country, active)

graduates (
  id, email, password_hash, full_name, graduation_year, degree_subject,
  university_id,        -- FK: chosen target uni
  bio, linkedin_url, profile_photo_key, gender,
  status,               -- pending | under_review | approved | rejected
  rejection_note, submitted_at, reviewed_at, reviewed_by
)

graduate_preferences (
  id, graduate_id,
  gender_pref TEXT[],   -- e.g. ['female'] or [] for any
  year_of_study_min, year_of_study_max
)

graduate_documents (
  id, graduate_id,
  doc_type,             -- student_card | degree_cert | linkedin_screenshot
  s3_key, uploaded_at
)

students (
  id, email, password_hash, full_name,
  university_id, year_of_study, gender,
  status,               -- pending | active | suspended
  activated_at, created_at
)

graduate_posts (
  id, graduate_id, university_id, message,
  status,               -- active | matched | expired | withdrawn
  published_at, expires_at, matched_at
)

connections (
  id, graduate_post_id, graduate_id, student_id,
  status,               -- pending | accepted | declined | expired
  offered_at, expires_at, responded_at,
  UNIQUE (graduate_post_id, student_id)
)
```

---

## Graduate Registration Form

Fields collected when a graduate signs up:

| Field | Type | Notes |
|-------|------|-------|
| Full name | Text | Required |
| Email | Email | Required, used for login |
| Password | Password | Required, min 8 chars |
| Graduation year | Number | Required, e.g. 2024 |
| Degree subject | Text | Required, e.g. "Computer Science" |
| Target university | Select | Required, dropdown from `universities` table |
| Gender | Select | Required: Male / Female / Non-binary / Prefer not to say |
| Bio | Textarea | Required, max 300 chars — shown to students |
| LinkedIn URL | URL | Optional |
| Profile photo | File upload | Optional, stored in S3 |
| Verification document | File upload | Required — student card, degree cert, or LinkedIn screenshot. Stored in S3, visible to admins only |

After submission: account created with `status = pending`. Graduate sees a "your application is under review" screen.

---

## Uni Student Registration Form

Fields collected when a student signs up on the site:

| Field | Type | Notes |
|-------|------|-------|
| Full name | Text | Required |
| Email | Email | Required, used for login |
| Password | Password | Required, min 8 chars |
| University | Select | Required, dropdown from `universities` table |
| Year of study | Select | Required: 1st / 2nd / 3rd / 4th / 5th / Postgrad |
| Gender | Select | Required: Male / Female / Non-binary / Prefer not to say |

After submission: account created with `status = pending`. Student sees a "your account is awaiting approval" screen. Admin activates the account manually.

---

## Flow 1: Graduate Onboarding & Screening

1. Graduate fills in the registration form and submits
2. Account created with `status = pending`; documents uploaded to S3
3. Admin sees the new application in the dashboard and reviews the profile + documents
4. Admin approves or rejects (with optional note)
5. Graduate receives email with the decision
6. If approved: graduate can set preferences and publish posts

---

## Flow 2: Uni Student Onboarding

1. Student fills in the registration form and submits
2. Account created with `status = pending`
3. Admin reviews pending students in the dashboard and clicks "Activate"
4. Student status set to `active`; welcome email sent with a magic login link (or they log in with their password directly)

---

## Flow 3: Graduate Post & Fan-Out

1. Approved graduate sets preferences (gender filter, optional year of study range)
2. Graduate writes a short message and clicks Publish — a `graduate_posts` row is created with `status = active`
3. A graduate can have **multiple active posts** (e.g. one per university they're targeting)
4. A background job (`fan_out_post`) runs immediately after publish:
   - Queries all `active` students at the post's university whose gender matches the preference
   - Creates a `connections` row for each eligible student: `status = pending`, `expires_at = NOW() + 7 days`
   - Enqueues a notification email per student

```
fan_out_post(graduate_post_id):
  post = GraduatePosts.find(post_id)
  prefs = GraduatePreferences.find(post.graduate_id)

  students = Students.where(
    university_id: post.university_id,
    status: 'active',
    gender: IN(prefs.gender_pref)   // skip filter if gender_pref is empty
  )

  for student in students:
    Connections.upsert({
      graduate_post_id: post.id,
      graduate_id: post.graduate_id,
      student_id: student.id,
      status: 'pending',
      offered_at: NOW(),
      expires_at: NOW() + 7 days
    }, on_conflict: ignore)         // safe to re-run
    enqueue notify_student(student.id, post.id)
```

---

## Flow 4: Student Accepts / Declines

1. Student sees pending graduate posts in their feed (filtered to their uni, sorted newest first)
2. Student views the graduate's profile (name, bio, degree, graduation year)
3. Student accepts or declines within 7 days — after that the connection auto-expires

**On accept:**
- `connections` row: `status = accepted`, `responded_at = NOW()`
- `graduate_posts` row: `status = matched`, `matched_at = NOW()`
- All other pending connections for that post: `status = expired`
- Graduate's dashboard updates to show the post as accepted — they can see which student accepted
- Student is notified by site admins via an external channel; student finds the graduate themselves through the platform

**On decline:** connection row set to `declined`. No notification sent to the graduate.

---

## API Endpoints

```
POST   /auth/register/graduate               Graduate signup
POST   /auth/register/student                Student signup
POST   /auth/login                           Login (graduates + students)
POST   /auth/magic-link                      Request magic link (students)
POST   /auth/magic-link/verify               Exchange token for JWT

POST   /graduates/me/profile                 Update profile + get S3 upload URLs
GET    /graduates/me                         Get own profile + screening status
POST   /graduates/me/preferences             Set/update matching preferences
POST   /graduates/me/posts                   Publish a new post (requires approved status)
GET    /graduates/me/posts                   List own posts + connection status per post
DELETE /graduates/me/posts/:id               Withdraw a post

GET    /students/me/feed                     Paginated pending graduate posts
POST   /students/me/connections/:id/accept   Accept a connection
POST   /students/me/connections/:id/decline  Decline a connection

GET    /admin/graduates/pending              List graduates awaiting review
PATCH  /admin/graduates/:id/decision         Approve or reject { decision, note }
GET    /admin/students/pending               List students awaiting activation
PATCH  /admin/students/:id/activate          Activate student account
```

---

## Background Jobs

| Job | Trigger | What it does |
|-----|---------|--------------|
| `fan_out_post` | Graduate publishes post | Creates connection rows + sends student notification emails |
| `expire_connections` | Cron daily | Sets connections past `expires_at` to `expired` |
| `expire_posts` | Cron daily | Sets posts past `expires_at` to `expired`; emails graduate |
| `send_email` | Enqueued by other jobs | Sends templated email via SES/SendGrid with retry |

---

## Email Notifications

| Event | Recipient | Content |
|-------|-----------|---------|
| Graduate approved | Graduate | "You're approved — set preferences and publish your post" |
| Graduate rejected | Graduate | Rejection reason + option to reapply after 7 days |
| New graduate post | Eligible students | "Someone new is looking to connect at your uni" |
| Post expired (30 days) | Graduate | "Your post expired — republish to stay active" |
| Student activated | Student | Welcome email with magic login link |

---

## Auth

- **Graduates**: email + password → JWT access token (15 min) + refresh token (30 days, rotated on use)
- **Students**: email + password → JWT; magic link available as an alternative on first login
- **Admins**: email + password + TOTP (2FA); separate JWT with `role: admin` claim

---

## Key Business Rules

- A graduate must be `approved` before they can publish posts
- A graduate can have **multiple active posts** at the same time (e.g. targeting different universities)
- A post is shown only to students at the post's chosen university
- Once a student accepts a post, that post is closed — no further connections possible on it
- Connection offers expire after **7 days** if not responded to
- Posts expire after 30 days if unmatched
- After rejection, a graduate must wait 7 days before reapplying
- Verification documents are accessible only to admins (pre-signed S3 URLs, 1-hour expiry)
- On acceptance, no emails are sent — graduate sees the accepted status on their dashboard; admin notifies the student via an external channel
