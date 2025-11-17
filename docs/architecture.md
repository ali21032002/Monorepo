# Architecture

This document describes the overall architecture of the Mentora system.

## System Overview

Mentora is a microservices-based monorepo architecture with the following components:

## Components

### Backend Service
- **Technology**: FastAPI (Python)
- **Port**: 8000
- **Purpose**: Main API service for text extraction and analysis
- **Key Features**:
  - Entity and relationship extraction
  - Multi-model analysis
  - Chat interface
  - File processing

### Frontend
- **Technology**: React + TypeScript + Vite
- **Port**: 5173
- **Purpose**: User interface for visualization and interaction
- **Key Features**:
  - Text input and analysis
  - Chart visualization
  - Chat interface
  - Authentication

### Speech-to-Text Service
- **Technology**: FastAPI (Python) + Vosk
- **Port**: 8001
- **Purpose**: Speech recognition with hybrid Persian models
- **Key Features**:
  - Audio transcription
  - Hybrid model support
  - Multiple language support

### User Service
- **Technology**: FastAPI (Python)
- **Port**: 8002
- **Purpose**: Authentication and user management
- **Key Features**:
  - User registration
  - Login/authentication
  - User profile management

### Shared Package (LangExtract)
- **Location**: `monorepo/shared/langextract`
- **Purpose**: Core extraction logic shared across services
- **Key Modules**:
  - `core.py`: Main extraction functions
  - `schemas.py`: Data structures
  - `prompts.py`: LLM prompts
  - `ollama_backend.py`: Ollama integration

### CLI
- **Technology**: Typer (Python)
- **Purpose**: Command-line interface for extraction
- **Key Features**:
  - Text extraction
  - File processing
  - HTML report generation

## Data Flow

1. User input (text/audio/file) → Frontend or CLI
2. Frontend/CLI → Backend API
3. Backend → LangExtract Core
4. LangExtract Core → Ollama LLM
5. LLM Response → LangExtract Core (processing)
6. Processed Results → Backend API
7. Backend API → Frontend/CLI
8. Frontend → Visualization/Display

## External Dependencies

- **Ollama**: Local LLM service (default: http://127.0.0.1:11434)
- **Vosk Models**: Speech recognition models
- **Elasticsearch**: Search and indexing (optional)

## Deployment

The system can be deployed using:
- Docker Compose (see `docker-compose.yml`)
- Individual service deployment
- Local development setup

