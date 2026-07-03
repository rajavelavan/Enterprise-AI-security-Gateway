# Cryptographic AI Governance Gateway

## 1. About the Project

**What this project is**  
The Cryptographic AI Governance Gateway is a stateless interception proxy designed to sit between enterprise applications (e.g., internal chat tools, productivity software) and external Large Language Models (LLMs) like OpenAI or Anthropic.

**Why we are building this**  
As businesses rapidly adopt Generative AI, they face the real-world problem of "shadow AI", un-auditable LLM actions, and a critical lack of enterprise Data Loss Prevention (DLP) at the gateway level. Employees might inadvertently share sensitive information—such as Social Security Numbers, API keys, or confidential company secrets—with third-party LLM providers. Without a centralized interception layer, forcing every development team to build their own security policies across fragmented applications is highly inefficient and creates significant risk.

**What the output of the product is**  
The gateway intercepts outgoing API requests directed towards LLMs, scans the payload against configured DLP rules using a highly efficient pattern-matching algorithm, and either blocks the request entirely (returning a `403 Forbidden`) or redacts the sensitive information before seamlessly forwarding the sanitized prompt to the destination LLM. 

**How this is helpful in the real world**  
By centralizing AI security at the gateway level, individual enterprise development teams can confidently build AI-integrated applications without worrying about implementing their own complex security, compliance, and PII-redaction logic. This significantly reduces enterprise risk, ensures regulatory compliance, and provides security teams with a single pane of glass for auditing all AI interactions.

**The ultimate goal of this product**  
The ultimate goal is to provide a unified, performant, and secure enterprise gateway that empowers companies to safely leverage the power of AI technologies while guaranteeing that no sensitive data ever leaves the corporate network unencrypted or unchecked.

---

## 2. Getting Started

**Prerequisites**  
- Python 3.8 or newer installed on your system.

**Step-by-step instructions on how to set up the virtual environment**  
1. Open your terminal and navigate to the root directory of the project.
2. Create a new virtual environment to keep dependencies isolated:
   ```bash
   python3 -m venv .venv
   ```
3. Activate the virtual environment:
   - **On macOS/Linux:**
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

**How to install the required packages from requirements.txt**  
With your virtual environment active, run the following command to install all necessary dependencies:
```bash
pip install -r requirements.txt
```

**The exact terminal commands to start the FastAPI server locally**  
Start the Uvicorn development server with live-reloading enabled by running:
```bash
uvicorn app.main:app --reload
```

**How to test it**  
Once the server is running, you can test it via the terminal using `curl`:

*Example of a safe request:*
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you today?"}'
```

*Example of a blocked request (DLP triggers on a sensitive keyword like "PASSWORD"):*
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "My PASSWORD is secret"}'
```
You can also explore and test the endpoints interactively by navigating to the auto-generated Swagger UI at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## 3. Tech Stack Documentation

### Python
- **What kind of technology it is:** A high-level, general-purpose programming language.
- **The specific purpose in this project:** Acts as the primary language to build the gateway logic, handle text processing, and manage the web server architecture.
- **Why we chose it over alternatives:** Python has an unparalleled ecosystem for AI integration, string manipulation, and data science. Its high readability accelerates development and onboarding compared to lower-level languages.
- **How it contributes to scalability, reliability, and maintainability:** Python’s vast ecosystem provides robust, well-maintained libraries that ensure the codebase remains maintainable and highly extensible over time.
- **What developers can do with it:** Developers can easily extend the gateway by integrating with new Python-based AI SDKs, building custom middlewares, or leveraging native Python data processing tools.

### FastAPI
- **What kind of technology it is:** A modern, fast (high-performance) web framework for building APIs with Python based on standard Python type hints.
- **The specific purpose in this project:** Handles incoming HTTP requests from enterprise applications and routes them asynchronously through the gateway's security and processing pipeline.
- **Why we chose it over alternatives:** As a proxy gateway, the application spends significant time awaiting I/O (LLM responses). We chose FastAPI over Flask or Django because of its native `asyncio` support and automatic API documentation generation, which makes it significantly faster for API development.
- **How it contributes to scalability, reliability, and maintainability:** By executing non-blocking operations, FastAPI allows the server to handle thousands of concurrent requests efficiently without choking.
- **What developers can do with it:** Developers can quickly add new endpoints, rely on automatic request validation, and utilize the auto-generated Swagger UI for seamless testing and API discovery.

### Uvicorn
- **What kind of technology it is:** A lightning-fast ASGI (Asynchronous Server Gateway Interface) server implementation.
- **The specific purpose in this project:** Serves as the underlying web server that runs the FastAPI application and handles the raw network connections.
- **Why we chose it over alternatives:** It is the recommended standard for running FastAPI applications, providing the robust asynchronous environment required by FastAPI to achieve its high performance.
- **How it contributes to scalability, reliability, and maintainability:** It ensures high throughput and low latency, maximizing the performance of the asynchronous web framework under heavy enterprise load.
- **What developers can do with it:** Developers can configure worker processes, tune server performance for production deployments, and easily integrate it into Docker containers.

### pyahocorasick
- **What kind of technology it is:** A fast and memory-efficient Python extension (written in C) that implements the Aho-Corasick automaton.
- **The specific purpose in this project:** Powers the Data Loss Prevention (DLP) scanner to detect and redact sensitive keywords in outgoing text payloads.
- **Why we chose it over alternatives:** Traditional Regular Expressions (Regex) or loop-based substring searches scale poorly as the list of sensitive words grows. Pyahocorasick builds a mathematical state machine that searches for *all* keywords simultaneously in a single pass ($O(n+m+z)$ time complexity), making it vastly superior to regex for multi-keyword scanning.
- **How it contributes to scalability, reliability, and maintainability:** Ensures that the DLP scanning step adds near-zero latency to the gateway, even with tens of thousands of restricted keywords.
- **What developers can do with it:** Developers can efficiently update the dictionary of blocked terms or integrate complex pattern-matching rules without degrading request latency.

### OpenTelemetry
- **What kind of technology it is:** An open-source, vendor-neutral standard and set of APIs/SDKs for distributed tracing and observability.
- **The specific purpose in this project:** Instruments the gateway to trace request lifecycles, accurately measuring how much time is spent in the DLP scan versus waiting for the external LLM to respond.
- **Why we chose it over alternatives:** It avoids vendor lock-in compared to using specific agents like Datadog or New Relic. It allows the gateway to capture traces ("spans") and export telemetry data to any compliant backend of the enterprise's choosing.
- **How it contributes to scalability, reliability, and maintainability:** Provides deep visibility into system bottlenecks, making it easy to diagnose performance issues, track latency, and monitor system health at scale.
- **What developers can do with it:** Developers can add custom spans to new features, track precise execution times, and hook the application up to observability dashboards like Jaeger, Prometheus, or Grafana.

### Pydantic
- **What kind of technology it is:** A data parsing and validation library utilizing standard Python type hints.
- **The specific purpose in this project:** Manages application settings (via `pydantic-settings`), environment variables, and defines the structure and validation rules for incoming API payloads.
- **Why we chose it over alternatives:** It integrates flawlessly with FastAPI. Instead of manually writing logic to check if a request has the correct fields, Pydantic guarantees data integrity before the business logic is even executed.
- **How it contributes to scalability, reliability, and maintainability:** Significantly reduces boilerplate code, minimizes runtime errors caused by malformed data, and self-documents the expected data structures, ensuring long-term maintainability.
- **What developers can do with it:** Developers can easily define robust, strongly-typed data models for new LLM providers, ensuring type safety and immediate validation feedback for invalid API requests.
