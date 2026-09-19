# 🎥 Demo Video Script & Recording Guide

To secure top marks, your demo video needs to be professional, concise, and prove that you met all **10 Demonstration Requirements** outlined in the assignment.

**Target Video Length:** 4–6 minutes.
**Tools Recommended:** OBS Studio, Loom, or Zoom screen recording.

---

## 🎬 Preparation Before Recording
1. Start Docker Compose: `make up` (or `docker-compose up -d`).
2. Ensure you have your `GEMINI_API_KEY` loaded in the `.env` file so extraction works perfectly.
3. Keep the `samples/` folder open in your file explorer.
4. Have Postman open with the provided Collection loaded, or keep the Swagger UI (`http://localhost:8000/docs`) open.
5. Have a Database viewer (like DBeaver or pgAdmin) open to show the PostgreSQL tables if needed (optional but impressive).

---

## 📝 Script & Flow

### 1. Introduction (0:00 - 0:30)
* **Action:** Show the Swagger UI or Postman overview.
* **Speech:** *"Hello, this is my submission for the Document Intelligence Service. I built this using FastAPI, PostgreSQL, Redis, and Celery for asynchronous processing. For the AI extraction, I'm utilizing the Google Gemini 1.5 Flash Vision model, which natively understands complex layouts, imperfect scans, and handwritten texts without relying on fragile OCR pipelines."*

### 2. Authentication & JWT (0:30 - 1:00)
* **Action:** Execute the `Register User` and `Login` requests in Postman.
* **Speech:** *"Security is a core requirement. I implemented JWT-based authentication. Here I register a user and log in to receive a Bearer token. All subsequent endpoints validate this token and ensure users can only access their own documents."*

### 3. Uploading a PDF (1:00 - 1:45)
* **Action:** Execute `3a. Upload PDF` using `samples/question_paper.pdf`.
* **Speech:** *"Here I am uploading a PDF document. The API validates the file type, checks file size, and verifies the magic bytes to prevent malicious uploads. The document is saved securely, and a background Celery task is dispatched. The API returns a 202 Accepted immediately so the client doesn't block."*
* **Action:** Execute `4. Check Processing Status`.
* **Speech:** *"We can poll the status endpoint, which shows the state transitioning from pending to processing, and finally to completed."*

### 4. Uploading an Image & Imperfect Documents (1:45 - 2:30)
* **Action:** Execute `3b. Upload Image` using `samples/question_image.png`.
* **Speech:** *"The system also handles image formats seamlessly. I'll upload a PNG containing a question. Because we use Gemini Vision, it easily handles blurry or rotated scans, split pages, and inconsistent formatting without breaking."*

### 5. Retrieving Structured Questions (2:30 - 3:30)
* **Action:** Execute `5. Get Extracted Questions` using the PDF document ID.
* **Speech:** *"Let's look at the extracted data from the PDF. As required, it's a completely structured JSON. You can see we successfully extracted the question text, question number, an array of multiple-choice options, and the source pages. Notice how it seamlessly handled the question that spanned across multiple pages."*

### 6. Answer Key Detection (3:30 - 4:15)
* **Action:** Execute `7. Get Answer Key`.
* **Speech:** *"The model also correctly identified the answer key located at the end of the document. Here is the endpoint specifically dedicated to retrieving answers, mapping the extracted answers directly back to their corresponding questions. If the answer key was uploaded separately, the system allows linking the documents together."*

### 7. Confidence Scoring & Review Items (4:15 - 5:00)
* **Action:** Execute `8. Get Warnings`.
* **Speech:** *"For imperfect documents, silent failures are dangerous. My system assigns a confidence score to every extraction. This `/warnings` endpoint flags any questions that received a low confidence score, lack an answer, or missed a question number, allowing human reviewers to easily audit uncertain extractions."*

### 8. Error Handling & Architecture (5:00 - 5:30)
* **Action:** Execute `3c. Upload Invalid File` or `10. Access Without Token`.
* **Speech:** *"I've implemented robust error handling. Uploading unsupported files throws a 415 error, and accessing without a token throws a 401. Looking at the architecture, using Celery and Redis ensures this service can scale horizontally to process hundreds of concurrent documents. Thank you."*

---

## 🌟 Pro-Tips for Impressing the Recruiter
* **Be confident:** Speak clearly and don't rush.
* **Show, don't just tell:** Highlight the JSON responses on screen when you mention specific fields.
* **Mention idempotency:** Briefly mention that your Celery tasks are idempotent (won't re-process completed docs if retried).
* **Upload to OneDrive:** Render to 1080p MP4. Upload the MP4 and a `.zip` of the source code to OneDrive. Share the link with "Anyone with the link can view" permissions.
