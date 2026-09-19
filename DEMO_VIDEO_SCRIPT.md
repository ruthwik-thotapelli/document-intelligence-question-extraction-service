# 🎬 Pragati Bharati - Demo Video Script (Top 1% Pitch)

**Goal:** This script is designed to make you sound like a Senior Staff Engineer. It highlights the architecture, fault tolerance, and AI integration within a tight 4-5 minute window.

---

## 1. The Hook & Architecture (0:00 - 1:00)

**[Screen: Show the GitHub README with the beautiful wave banner and Architecture Diagram]**

> "Hi, I'm Ruthwik. This is my submission for the Pragati Bharati Document Intelligence Service. 
>
> My goal was to build a system that doesn't just work locally, but is entirely production-ready. As you can see in the architecture diagram here, the core pipeline is completely decoupled. 
> 
> The FastAPI gateway instantly returns a `202 Accepted` to prevent HTTP blocking, and offloads the heavy AI extraction to Celery workers backed by Redis. However, I know reviewers don't always want to spin up Docker containers, so I engineered a **graceful fallback mechanism**. If the system detects that Redis or PostgreSQL aren't running, it seamlessly falls back to a synchronous execution loop and auto-generates a local SQLite database in WAL-mode for concurrency."

## 2. The Frontend UI (1:00 - 2:00)

**[Screen: Switch to your browser at `http://localhost:8000/`]**

> "While the assignment focused heavily on backend APIs, I wanted to prove that my APIs are ready for downstream consumption. So, I built a lightweight Single Page Application using Vue.js and Tailwind CSS that is served directly from the FastAPI root.
>
> Let's go ahead and create an account. The backend is using strict JWT Bearer authentication with bcrypt password hashing."
> 
> *(Register a user and log in on the UI)*
> 
> "Now that we are authenticated, we have access to the extraction dashboard."

## 3. The Extraction Pipeline (2:00 - 3:30)

**[Screen: Click 'Upload Document', select `samples/question_paper.pdf`, and hit 'Upload & Parse']**

> "I'm going to upload a sample question paper. Watch the progress bar—FastAPI instantly accepted the file, and the UI is now long-polling the `/status` endpoint. 
>
> Under the hood, I completely bypassed traditional OCR engines like Tesseract because they are brittle when dealing with math formulas or questions split across pages. Instead, I integrated **Google Gemini 1.5 Flash Vision**. 
>
> It natively understands the document visually and maps the unstructured pixels directly into a strict JSON schema."
> 
> *(Wait for the progress bar to turn green and display the results)*

## 4. The Results & Conclusion (3:30 - 4:30)

**[Screen: Scroll through the beautiful extracted questions on the right side of the UI]**

> "As you can see, the extraction was flawless.
> 
> It identified the question numbers, isolated the multiple-choice options into an array, and even pulled the Answer Key from the bottom of the document and mapped it back to the specific questions. 
>
> Every extraction is also assigned an AI Confidence Score. If a score drops below 70%, my backend automatically flags it in a dedicated `/warnings` endpoint for Human-In-The-Loop review.
>
> The code is heavily documented, typed, formatted with Ruff, and secured against Path Traversal and MIME-type spoofing.
>
> Thank you for reviewing my submission. I'd love to walk you through the codebase in more detail during the technical interview."

---

### 💡 Pro-Tips for Recording
1. **Be confident:** Speak slowly and clearly. You are explaining *your* system.
2. **Pre-load:** Have `http://localhost:8000/` open before you hit record so you don't have to type it.
3. **Pacing:** Don't rush through the UI. Let the progress bar finish naturally while you talk about Gemini.
