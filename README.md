# Architecture Solution Service

A FastAPI-based microservice that leverages a multi-agent LLM pipeline (LangGraph) to automatically process RFP (Request for Proposal) documents and generate comprehensive Solution Architecture Presentation Decks (PPTX).

## Features

- **Document Intake & Extraction**: Extracts requirements, vision, and constraints directly from uploaded PDF and DOCX files.
- **Compliance Validation**: Analyzes extracted requirements against security and compliance frameworks (HIPAA, GDPR, CCPA, PCI-DSS) using Tavily search and LLMs.
- **Architecture Solution Generation**: Dynamically fetches the organization's current tech stack via an external API and generates a detailed solution architecture using OpenAI's `gpt-4o`.
- **Diagram Generation**: Automatically generates high-quality architecture diagrams using OpenAI DALL-E image generation (`gpt-image-2`).
- **PowerPoint Generation**: Compiles all findings into a beautifully styled, highly professional 16:9 PowerPoint presentation deck using `python-pptx`.
- **API Endpoints**: Easily accessible via RESTful FastAPI endpoints.

## Technology Stack

- **Backend**: Python 3.11, FastAPI, Uvicorn
- **AI/LLM Orchestration**: LangGraph, LangChain
- **Supported Models**: OpenAI (`gpt-4o`), Anthropic (`claude-sonnet-4` as a fallback)
- **Document Processing**: PyMuPDF (`fitz`), `python-docx`, `pypdf`
- **Output Generation**: `python-pptx`, Base64 image encoding
- **Deployment**: Docker

## Prerequisites

- Python 3.11+
- OpenAI API Key
- (Optional) Anthropic API Key
- (Optional) Tavily API Key for live compliance searching

## Installation & Setup

1. **Clone the repository** and navigate to the project root.
2. **Set up a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Environment Variables**:
   Create a `.env` file in the root directory and add your keys:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   TAVILY_API_KEY=your_tavily_api_key_here
   ```

## Running the Service

### Locally (Uvicorn)
Start the FastAPI server:
```bash
python app/api.py
```
The service will be available at `http://localhost:8000`. 
Access the Swagger UI documentation at: `http://localhost:8000/api/v1/architecture/docs`

### With Docker
Build and run the Docker container:
```bash
docker build -t architecture-service .
docker run -p 8000:8000 --env-file .env architecture-service
```
Or using Docker Compose:
```bash
docker-compose up --build
```

## API Endpoints

- `GET /api/v1/architecture/health`: Health check endpoint.
- `POST /api/v1/architecture/generate`: Upload an RFP PDF/DOCX to generate the architecture deck.
- `GET /api/v1/architecture/download`: Download the latest generated `.pptx` file.
- `GET /api/v1/architecture/diagram/base64`: Fetch the latest generated architecture diagram as a base64 encoded string.

## Architecture Pipeline (Agents)

The service utilizes a LangGraph orchestrated pipeline consisting of the following agents:
1. **A1_Intake**: Validates and prepares uploaded documents.
2. **A2_Extract**: Extracts vision and critical context from documents.
3. **A3_Requirement**: Consolidates actionable requirements.
4. **A4_Compliance**: Validates requirements against known frameworks.
5. **A5_Solution**: Recommends a technical solution based on requirements, compliance, and the external tech stack API.
6. **A5_1_ArchitectureGenerator**: Coordinates image generation and structures the final PowerPoint deck.
