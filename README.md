# Legal Document Search RAG System

## Overview
This project implements a state-of-the-art Retrieval-Augmented Generation (RAG) system specifically designed for legal document search and analysis. By combining advanced document processing, vector-based search, and a modern user interface, it provides powerful semantic search capabilities for legal professionals.

## Project Architecture

The system is built on three main pillars:

### 1. Document Processing Pipeline
Our document ingestion system employs a sophisticated processing pipeline that handles various document formats while preserving the semantic structure crucial for legal documents:

- **Multi-Format Support**: Robust handling of PDF and DOC/DOCX files using industry-standard libraries (PyMuPDF and python-docx)
- **Intelligent Text Chunking**: Implementation of context-aware document splitting using spaCy, with special attention to legal document structure (sections, articles, paragraphs)
- **Semantic Preservation**: Careful handling of document hierarchies and relationships to maintain context

### 2. Vector Search Infrastructure
The core search functionality is powered by a modern vector search implementation:

- **State-of-the-Art Embeddings**: Utilization of OpenAI's latest embedding model for optimal semantic understanding
- **Efficient Storage**: ChromaDB integration for fast and reliable vector storage and retrieval
- **Hybrid Search Capabilities**: Combination of semantic and keyword-based search for maximum accuracy

### 3. Interactive Search Interface
A Retool-based interface that provides:

- **Intuitive Query Interface**: Legal-specific search features with intelligent autocompletion
- **Flexible Search Modes**: Support for both exact phrase matching and semantic search
- **Rich Results Display**: Context-aware result presentation with relevant highlights

## Technical Highlights

- **Advanced Text Processing**: Semantic-aware document splitting with customized separators for legal documents
- **Hybrid Search Architecture**: Combination of vector similarity and traditional search methods
- **Performance Optimization**: Built-in caching and parallel processing capabilities
- **Privacy-First Design**: Local ChromaDB storage ensuring data privacy and compliance

## Performance Metrics

The system is designed to meet rigorous performance standards:

- 83% accuracy in legal QA benchmarks
- Sub-2 second latency for query processing
- Comprehensive testing protocol covering various legal query types

## Future Optimizations

The system is designed with scalability in mind, with planned improvements including:

- Enhanced metadata handling for section-level filtering
- Legal-specific query expansion
- Response caching optimization
- Parallel document processing improvements

## Development Setup

This project uses modern Python development tools to ensure code quality and maintainability:

### Prerequisites

- [Pixi](https://pixi.sh) - A fast, modern package manager built on top of Conda
- Git

### Getting Started

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd legal-search-rag
   ```

2. Install dependencies using Pixi:
   ```bash
   pixi install
   ```

### Development Tools

The project is configured with several development tools to maintain code quality:

#### Pre-commit Hooks

We use pre-commit hooks to ensure code quality before each commit. The following checks are automatically run:

- **Black**: Code formatting
- **isort**: Import sorting
- **Flake8**: Code style and documentation checks
- **MyPy**: Static type checking
- **General checks**: Trailing whitespace, file endings, YAML validation

To manually run all checks:
```bash
pixi run lint
```

#### Pixi Configuration

The project uses `pixi.toml` for dependency management and task automation:

- Python 3.9 or higher
- Development tools (black, flake8, isort, mypy, pre-commit)
- Predefined tasks for common operations

### Best Practices

1. Always ensure pre-commit hooks are installed after cloning:
   ```bash
   pixi run pre-commit install
   ```

2. Run linting before pushing changes:
   ```bash
   pixi run lint
   ```

3. Keep `pixi.toml` updated when adding new dependencies

---
*Note: This README will be updated with setup and running instructions in subsequent iterations.*
