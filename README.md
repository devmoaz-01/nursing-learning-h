# NurseLearn

NurseLearn is an educational nursing platform. Its content and tools support
learning and are not a substitute for clinical supervision, local policies, or
professional judgment.

## Run locally

1. Install Python 3.10 or later.
2. Install the project dependencies:

   ```powershell
   py -m pip install -r requirements.txt
   ```

3. Keep the existing `.env` file and its `DATABASE_URL`. Add these settings to
   `.env` to bootstrap the first administrator:

   ```dotenv
   ADMIN_EMAIL=your-admin-email@example.com
   ADMIN_PASSWORD=use-a-unique-password-at-least-12-characters-long
   ```

   The password above is an example only; replace it before starting the app.
   Never commit `.env` or put a real password in frontend files.
   To enable the AI Nursing Tutor with OpenRouter, put your OpenRouter API key
   and a model ID available to your account in the server's `.env` file:

   ```dotenv
   NURSELEARN_AI_BASE_URL=https://openrouter.ai/api/v1
   NURSELEARN_AI_API_KEY=your-openrouter-api-key
   NURSELEARN_AI_MODEL=provider/model
   ```

   The base URL defaults to OpenRouter if omitted. These settings are optional
   for running the rest of the site. Add your key locally; never send it in chat
   or add it to HTML or JavaScript. After changing these values, restart the
   server. The floating tutor is available without a NurseLearn account and is
   limited to 20 requests per hour per client IP in the running server process.
   Messages are sent to OpenRouter and are not saved by NurseLearn; OpenRouter's
   handling depends on your account and its current terms. Public deployment
   needs additional cross-worker abuse controls and a provider spending limit.
4. For a simple local setup, set `DATABASE_URL=sqlite:///./nurselearn.db` in
   `.env`; SQLite needs no separate database service. If you prefer PostgreSQL,
   keep your PostgreSQL `DATABASE_URL`, start PostgreSQL, and make sure the
   database named in that URL exists.
5. Start the server from the project directory:

   ```powershell
   py -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
   ```

6. Open <http://127.0.0.1:8000/>.

The first startup creates the new account/session tables and creates the
administrator if `ADMIN_EMAIL` and `ADMIN_PASSWORD` are set. Learners can create
their own accounts at `/register`. Registration cannot grant administrator
privileges.

## Deploy with Firebase Hosting and Cloud Run

Firebase Hosting serves the static frontend; Cloud Run runs the FastAPI
backend. `firebase.json` proxies `/api/**` to the `nurselearn-api` Cloud Run
service in `us-east1`, so the browser uses the same origin for API requests
and session cookies.

1. Create a Firebase project, enable billing for the linked Google Cloud
   project, and install the Firebase and Google Cloud CLIs. Select the same
   Google Cloud project in both CLIs.
2. Create a managed PostgreSQL database in a region close to the Cloud Run
   service. SQLite and the local `.db` files are not suitable for Cloud Run's
   ephemeral container filesystem.
3. In Secret Manager, create secrets for `DATABASE_URL`, `ADMIN_PASSWORD`, and
   (if enabling the AI tutor) `NURSELEARN_AI_API_KEY`. Grant the Cloud Run
   service account permission to access those secrets. Configure them as
   environment variables on the Cloud Run service; configure `ADMIN_EMAIL`,
   `NURSELEARN_PUBLIC_BASE_URL` (for example,
   `https://YOUR_PROJECT_ID.web.app`), and `NURSELEARN_AI_MODEL` as regular
   environment variables. Use a PostgreSQL SQLAlchemy URL for `DATABASE_URL`.
4. From the project root, deploy the backend as the `nurselearn-api` service in
   `us-east1`, using the included `Dockerfile` and port `8080`. Make it
   publicly invokable; application authentication is handled by NurseLearn.
   The database and required secrets must be configured before the first
   instance starts.
5. In `firebase.json`, set the Cloud Run region to the service's region if you
   chose a different one. Then run `firebase login`, select the project with
   `firebase use nursing-learning`, and run `firebase deploy --only hosting`.
6. Verify `https://nursing-learning.web.app/api/health`, then test registration,
   login, and the AI tutor. For a custom domain, use its HTTPS origin as
   `NURSELEARN_PUBLIC_BASE_URL` and add it to
   `NURSELEARN_CORS_ALLOWED_ORIGINS`.

### Migrate an existing SQLite database

The project includes a guarded SQLite-to-PostgreSQL importer. First configure
the local private `.env.neon` with `DATABASE_URL` set to the production
PostgreSQL connection string, and start the Cloud Run service once so it creates
the schema. Install PostgreSQL client tools (including `pg_restore`) locally.
From the project root, run its read-only comparison and keep the report private:

```powershell
py -3.15 -m backend.database.sqlite_to_postgres `
  --env-file .env.neon `
  --stage-report (Join-Path $env:TEMP "nurselearn-migration-review.json")
```

Review the report before importing. Import requires the verified PostgreSQL
backup, a documented IANA timezone and evidence for naive SQLite timestamps,
and an explicit confirmation flag. It skips conflicting rows rather than
overwriting them; do not proceed until conflicts and unique-key collisions
have been reviewed. The SQLite source is read-only. Never commit or share the
staging report or database connection string.

Never put database credentials, admin passwords, or AI provider keys in
`frontend/`, `firebase.json`, or source control. The in-process AI rate limit
is intended for a single local server and is not sufficient abuse protection
for a public multi-instance deployment.

Password reset is available at `/forgot-password` and `/reset-password` after
SMTP settings are configured in the server environment. Set
`NURSELEARN_PUBLIC_BASE_URL` to the canonical HTTPS origin in production.
Reset tokens are single-use, expire after 30 minutes, and are stored only as
hashes. The API intentionally returns the same reset-request response whether
or not an active account uses the supplied email. Do not enable reset email
delivery until SMTP STARTTLS and the public HTTPS URL have been verified.
Account pages are available at `/login`, `/register`, and `/profile`.

## Backend structure

The existing FastAPI and plain HTML/CSS/JavaScript stack is retained. The
`py -m uvicorn main:app` command remains the supported entry point. The project
folders are organized as follows:

```text
NurseLearn/
├── backend/
│   ├── auth/          # Authentication and role checks
│   ├── database/      # Sessions, initialization, and migrations
│   ├── routes/        # API endpoints and static page routes
│   ├── services/      # AI, research, and content services
│   ├── utils/         # Shared helpers
│   ├── app.py         # Assemble application routes
│   ├── application.py # FastAPI configuration and startup
│   ├── config.py      # Environment settings and project paths
│   └── schemas.py     # Validated API request models
├── frontend/
│   ├── index.html
│   └── assets/
│       ├── css/styles.css
│       ├── images/rifaf-fayoum-logo.png
│       └── js/
│           ├── app.js
│           ├── emergency_resources.js
│           ├── learning_features.js
│           └── nursing_tools.js
├── main.py            # Stable Uvicorn entry point
├── database.py        # SQLAlchemy engine
├── models.py          # Canonical database models
├── schema.sql         # Schema reference
├── requirements.txt
└── .env.example
```

The root `database.py` and `models.py` remain in place because they are the
shared SQLAlchemy engine and canonical models used throughout the application.
The live database and `.env` also remain in the project root and are not moved.

- `main.py` preserves the existing Uvicorn import path.
- `frontend/` contains the home page and its CSS, JavaScript, and image assets.
  FastAPI serves these files from `/` and `/assets/...`; the previous asset
  URLs remain supported for compatibility.
- `backend/app.py` assembles the routers; `backend/application.py` configures
  FastAPI, CORS, and startup.
- `backend/routes/` contains the existing authentication, tutor, home,
  assessment, knowledge, community, tools, research, and static-file routes.
- `backend/auth/` contains password/session authorization and first-admin
  bootstrap logic.
- `backend/config.py` centralizes environment-backed settings and project paths.
- `backend/database/` contains request-scoped sessions, startup initialization,
  and compatibility migrations. The existing root `database.py` remains the
  SQLAlchemy engine source.
- `backend/services/` contains AI tutor, research, content seeding, and API
  response-formatting logic.
- `backend/schemas.py` contains validated API request models, and
  `backend/utils/` contains shared validation helpers.
- The existing root `models.py` remains the canonical SQLAlchemy model module
  to avoid changing database table names or existing data.
- Passwords use PBKDF2-HMAC-SHA256 with per-password salts; opaque session and
  password-reset tokens are generated server-side and only their hashes are
  persisted. Session cookies are HttpOnly, SameSite=Lax, and Secure for HTTPS.
  Active sessions can be inspected/revoked from the profile page, and password
  changes/recovery revoke existing sessions.
- `user` accounts can access their own assessment history, `content_editor`
  accounts can manage knowledge resources, `researcher` accounts can access
  research analytics, and `admin` accounts can manage content, moderation, and
  user roles. Registration never accepts a client-selected role.
- State-changing requests validate browser origins; failed login and password
  reset requests are rate-limited using hashed identifiers in the database.

## Database structure and migrations

SQLite remains the active database; no database-engine migration is performed.
`models.py` defines the SQLAlchemy tables and relationships. Startup creates
missing tables, then applies idempotent, add-only revisions recorded in
`schema_migrations`. Existing rows and the historical `assessments` and
`assessment_answers` tables are retained. The old `assessments` table contains
result records, so new assessment definitions live in `assessment_definitions`
instead of changing that table's meaning.

- `users`, `roles`, and `user_roles` represent accounts and role assignments.
  The existing `users.role` field remains compatible with authentication; a
  SQLite trigger keeps it synchronized with the role relation.
- `assessment_definitions`, `questions`, `learner_assessment_attempts`,
  `research_assessment_responses`, and `assessment_attempt_answers` represent
  assessment definitions, questions, learner/research attempts, and normalized
  answers. Existing JSON answer snapshots are retained for backward
  compatibility and copied into the normalized answer table by migration.
- `knowledge_articles` remains the shared learning-resource table. Video
  resources use `resource_type="video"` and `video_url` rather than duplicating
  article fields in a separate video table. Existing thumbnail, author, publish,
  and timestamp fields are retained or added without removing content.
- `bookmarks`, `emergency_resources`, and `nursing_tools` provide relational
  storage for those resource types. Existing browser bookmarks and emergency
  and tool catalogs continue to work as before; these tables do not silently
  switch their current client-side behavior to server storage.
- AI tutor conversations are intentionally not stored; only the existing
  account-based request-usage records are retained.
- SQLite connections enable foreign-key checks and a bounded busy timeout.
  `schema.sql` documents the migration source of truth; it is not an alternate
  schema to execute manually.

## Implemented foundation

- Server-side learner registration and sign-in with hashed passwords and
  HttpOnly session cookies.
- Interactive assessments with server-checked answers, topic feedback, answer
  explanations, and personalized review.
- Signed-in assessment history saved privately per account with idempotent
  submissions; guest history remains in the current browser.
- Administrator article management with draft, publish, unpublish, and delete
  actions.
- Knowledge Center starts with 37 curated learning resources based on public
  WHO, CDC, and MedlinePlus references, including emergency nursing, critical
  care, pediatric, surgical safety, video, infographic, and FAQ examples. Each
  item links to its original source. Startup adds missing seed articles without
  duplicating or deleting existing library content and upgrades older article
  tables with the metadata required by the library.
- The Knowledge Center provides source-linked resource detail pages, dynamic
  category/type/difficulty filters, keyword search, date and popularity sorting,
  featured/latest/trending shelves, related learning, and responsive video and
  infographic cards. Resource categories and types remain administrator-editable
  free text rather than a fixed taxonomy.
- Bookmarks are saved in the current browser without collecting an account or
  patient identifier. Aggregate resource view/save counters support popularity
  ordering; these counters are educational product analytics, not academic
  research data.
- Public resource endpoints show only published articles.
- Public assessment questions include learning categories but never expose
  correct answers. Assessment submissions return a topic-level score breakdown
  for immediate educational feedback.
- The learner dashboard connects assessment results to relevant Knowledge Center
  topics and shows a personal score history. Educational assessment attempts
  are separate from academic research records.
- The dashboard also summarizes study-plan completion, saved resources, and
  recent activity. Assessment history is fetched for the signed-in account;
  bookmarks, study checklists, and activity are stored locally in browser
  spaces separated by account and are not represented as server-synced data.
- Anonymous bilingual AI Nursing Tutor with selectable teaching styles,
  server-side OpenRouter credentials, and an in-process per-IP request limit.
- Question bank with category/difficulty filters, server-checked answers,
  explanations, and source links.
- Moderated learning community; submissions require an account and administrator
  approval before publication.
- Learning Studio with fictional case practice, browser-saved flashcards,
  educational calculators, anatomy summaries, skills checklists, bilingual
  terminology, care-plan exercises, evidence links, study goals, course progress,
  handover practice, emergency escalation scenarios, and a personal dashboard.
- Interactive Tools provides browser-local adult BMI and fluid-balance arithmetic,
  prescribed dose-to-volume conversion, IV-rate practice, Glasgow Coma Scale
  component scoring, an adult resting vital-signs reference, and linked emergency
  first-aid references. Tool definitions, form fields, explanations, disclaimers,
  and sources are registered in a small frontend catalog so more tools can be
  added without rebuilding the section layout. Recent results are stored only
  in this browser; entered values are not stored or sent to the server.
- Emergency Quick Resources provides instant search, eight source-linked first-aid
  topic cards, concise and expanded reading modes, and keyboard-accessible topic
  details. A locally saved emergency number can be called from the page; the
  interface does not guess emergency numbers. St John Ambulance is a UK source,
  so users must follow their local emergency service and current local guidance.
- Research/admin dashboard with protected article publishing controls and
  community moderation. Academic research collection is currently disabled.

## Feature rollout

The requested feature set is connected through the existing learning pages and
the Learning Studio:

1. **Foundation (implemented):** account registration and sign-in; protected
   administrator dashboard; article drafts, publishing, editing, and deletion.
2. **Learning library and practice:** nursing encyclopedia; smart question
   bank; case simulator; flashcards and spaced repetition; educational
   calculators; anatomy atlas; skills lab; reviewed medication reference;
   English/Arabic medical dictionary; assessment trainer; care-plan builder;
   evidence-based library; documentation and handover practice; emergency
   learning scenarios.
3. **Personalized learning and community:** the browser-local learner dashboard
   recommends Knowledge Center topics from assessment results; the study
   planner and moderated discussion forum are available. Course enrollment,
   cross-device progress sync, and educational completion certificates are not
   part of the current implementation.
4. **Research and administration:** research collection is disabled; article
   publishing controls, community moderation, and privacy safeguards remain.

Guest assessment history and personal study progress are stored in the current
browser only. Signed-in assessment history is saved to the learner's account for
personal use. These educational records are not included in research summaries.
Research collection must not be enabled without an institution-approved
protocol, participant consent, retention rules, and export controls.

The AI tutor uses OpenRouter's OpenAI-compatible Chat Completions endpoint;
its endpoint and credentials are configured only on the server.
Never put an AI API key in HTML or JavaScript.

## Home page

The home page connects assessment, topic feedback, source-linked learning, and
re-assessment. Its platform statistics are loaded from `/api/home/stats`;
statistics remain unavailable rather than showing invented totals if the
backend cannot be reached. The latest library card uses the most recently
ordered published resource. Article publication dates are not available in the
current article model, so the page does not invent one.

The assessment presents one question at a time, saves recoverable browser
drafts, confirms before submission, and shows server-checked scoring and answer
explanations. Signed-in attempts use `/api/assessment/history` and are stored
separately from the legacy aggregate `assessments` table. Guest attempts are
stored in the browser. Academic research summaries remain disabled and exclude
these educational attempts.

Emergency quick-access cards link to St John Ambulance (UK) public first-aid
references for CPR, choking, severe bleeding, burns, seizures, and shock. They
are educational links, not emergency dispatch; local services and protocols
take priority. The page also avoids fabricated learner testimonials and
explains its privacy and healthcare limitations using in-product dialogs.

Medication information, clinical procedures, emergency guidance, and reference
content require qualified professional review and dated source citations before
publication. The platform is educational and does not provide patient-specific
medical advice or professional certification.
