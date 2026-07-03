# Cryptographic AI Governance Gateway - Project Overview

Welcome to the **Cryptographic AI Governance Gateway**! As a beginner Python developer, this document will help you understand the architecture, the technology stack, and how to run the application locally.

---

## 1. Project Context

### What is this project?
The Cryptographic AI Governance Gateway is a **stateless interception proxy**. It acts as a middleman between enterprise applications (like an internal chat tool) and external Large Language Models (LLMs) like OpenAI or Anthropic. Before a prompt reaches the AI, this gateway analyzes it.

### Why are we building this?
When employees use Generative AI, they might accidentally paste sensitive data—like Social Security Numbers, passwords, or confidential company secrets. This gateway intercepts the payload and checks it against Data Loss Prevention (DLP) rules to block or redact sensitive information before it leaves the company network.

### How do you find/use this?
Instead of an application sending a request directly to `https://api.openai.com/v1/chat`, the application sends its request to this Gateway's API (e.g., `http://localhost:8000/api/v1/chat`). The gateway scans the payload and, if it's safe, forwards it to the actual LLM. 

### How does this system ease our work?
Security is hard. If a company has 10 different AI applications, forcing every single development team to build their own security and PII-redaction logic is inefficient and risky. By using a centralized Gateway, individual developers can just build their apps, knowing the Gateway will handle security, compliance, and tracing automatically.

---

## 2. Tech Stack Selection

For this project, we carefully selected a modern, highly efficient Python technology stack:

### Python
**Why chosen:** Python is the undisputed king of AI integration, string processing, and data science. It is highly readable and has a massive ecosystem of libraries.

### FastAPI & Uvicorn
**Why chosen:** Since this is a proxy gateway, it will spend a lot of time waiting for the LLM to respond. **FastAPI** is a modern, asynchronous web framework. It allows the server to handle thousands of requests concurrently without blocking.
- **Compared to others (Flask/Django):** FastAPI is significantly faster for API development. It also automatically generates interactive API documentation (Swagger UI) using Python type hints, which saves a lot of development time.
- **Uvicorn:** This is the lightning-fast ASGI (Asynchronous Server Gateway Interface) server that actually runs our FastAPI code.

### PyAhoCorasick (Data Loss Prevention)
**Why chosen:** To block sensitive keywords, we use the `pyahocorasick` library, which implements the **Aho-Corasick algorithm**. 
- **Efficiency:** If we used standard Regular Expressions (Regex) or a simple `for keyword in list_of_bad_words` loop, the server would slow down significantly as the list of keywords grew. The Aho-Corasick algorithm builds a mathematical automaton (a state machine) that can search the input string for *all* keywords simultaneously in a single pass. It runs in $O(n+m+z)$ time complexity, making it extremely fast regardless of how many sensitive words we are looking for.

### OpenTelemetry
**Why chosen:** Observability is crucial for a gateway. We need to know exactly how much time the DLP scan took versus how long the LLM took. OpenTelemetry is an open-source, vendor-neutral standard for distributed tracing. Instead of locking into one specific tool (like Datadog or New Relic), OpenTelemetry allows us to capture traces ("spans") and export them anywhere.

---

## 3. Project File Structure Explained

```text
├── .venv/                      # Your local Python Virtual Environment (keeps dependencies isolated)
├── requirements.txt            # A list of all the 3rd-party libraries the project needs
├── app/
│   ├── main.py                 # The entry point of our application. It initializes FastAPI.
│   ├── api/
│   │   ├── router.py           # Defines the actual URL endpoints (e.g., POST /api/v1/chat)
│   ├── core/
│   │   ├── config.py           # Stores environment variables and settings (like our secret keywords)
│   ├── dlp/
│   │   ├── scanner.py          # The Aho-Corasick logic that scans text for sensitive words
│   ├── telemetry/
│   │   ├── tracing.py          # Configures OpenTelemetry to track request speeds
```

---

## 4. How to Run This Application Step-by-Step

Follow these steps to run the application on your local machine:

### Step 1: Open Your Terminal
Open the terminal inside your code editor (like VSCode) and ensure you are in the root directory of the project (`cryptographic gateway - python project`).

### Step 2: Activate the Virtual Environment
We need to activate the virtual environment so Python knows where to find our installed libraries.
- **On Mac/Linux:**
  ```bash
  source .venv/bin/activate
  ```
- **On Windows (Command Prompt):**
  ```cmd
  .venv\Scripts\activate.bat
  ```
- **On Windows (PowerShell):**
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
*(You should see `(.venv)` appear at the beginning of your terminal prompt).*

### Step 3: Install Dependencies (If not already installed)
If this is your first time setting up the project, install the required packages:
```bash
pip install -r requirements.txt
```

### Step 4: Run the Server
Start the Uvicorn development server. The `--reload` flag means the server will automatically restart if you make any changes to the code.
```bash
uvicorn app.main:app --reload
```

### Step 5: Test the Application
Once the server is running, you can test it in two ways:

**Option A: The Interactive UI**
Open your web browser and go to: [http://localhost:8000/docs](http://localhost:8000/docs)
FastAPI automatically generates this page. You can click on the `POST /api/v1/chat` endpoint, click "Try it out", enter a JSON payload like `{"message": "Hello!"}`, and click "Execute".

**Option B: Terminal (cURL)**
Open a *new* terminal window and send a safe request:
```bash
curl -X POST http://localhost:8000/api/v1/chat -H "Content-Type: application/json" -d '{"message": "Hello, how are you today?"}'
```
Now, test the DLP scanner by sending a sensitive keyword:
```bash
curl -X POST http://localhost:8000/api/v1/chat -H "Content-Type: application/json" -d '{"message": "My PASSWORD is secret"}'
```
You should see a `403 Forbidden` error because the DLP scanner caught the word "PASSWORD".
