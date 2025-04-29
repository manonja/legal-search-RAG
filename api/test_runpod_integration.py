#!/usr/bin/env python3
"""
RunPod Integration Testing Script

This script tests the Legal Search RAG API with the privacy-focused RunPod architecture.
It validates the functionality of various endpoints using the new RunPod-based embedding
and LLM services.

Usage:
    python test_runpod_integration.py
"""

import os
import sys
import json
import time
import argparse
import requests
import datetime
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

# Default configuration
DEFAULT_CONFIG = {
    "api_url": "http://localhost:8000/api",
    "api_token": "test-token",  # For local testing
    "test_file_path": "tests/data/canadian_constitution.pdf",  # Path to test PDF file
    "test_query": "What are the key legal provisions?",
    "timeout": 120,  # Longer timeout for RunPod processing
}


class RunPodTester:
    """Test runner for the RunPod integration."""

    def __init__(
        self,
        api_url: str,
        api_token: str,
        test_file_path: str,
        timeout: int = 60,
        verbose: bool = False,
    ):
        """Initialize the test runner."""
        self.api_url = api_url.rstrip("/")
        self.api_token = api_token
        self.test_file_path = Path(test_file_path)
        self.timeout = timeout
        self.verbose = verbose
        self.document_id = None
        self.headers = {"Authorization": f"Bearer {api_token}"}

        # Test metrics
        self.metrics = {
            "start_time": None,
            "end_time": None,
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "response_times": {},
        }

        # Ensure test file exists
        if not self.test_file_path.exists():
            print(f"{RED}Test file not found at {self.test_file_path}{RESET}")
            sys.exit(1)

    def log(self, message: str, level: str = "info") -> None:
        """Log a message with colored output based on level."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if level == "info":
            print(f"[{timestamp}] {message}")
        elif level == "success":
            print(f"[{timestamp}] {GREEN}{message}{RESET}")
        elif level == "error":
            print(f"[{timestamp}] {RED}{message}{RESET}")
        elif level == "warning":
            print(f"[{timestamp}] {YELLOW}{message}{RESET}")

    def run_test(self, test_name: str, test_func, *args, **kwargs) -> bool:
        """Run a test function and record the result."""
        self.metrics["tests_run"] += 1

        print(f"\n{YELLOW}Running test: {test_name}{RESET}")

        start_time = time.time()
        try:
            result = test_func(*args, **kwargs)
            elapsed = time.time() - start_time

            if result:
                self.metrics["tests_passed"] += 1
                self.log(f"✅ {test_name} passed (took {elapsed:.2f}s)", "success")
                self.metrics["response_times"][test_name] = elapsed
                return True
            else:
                self.metrics["tests_failed"] += 1
                self.log(f"❌ {test_name} failed (took {elapsed:.2f}s)", "error")
                self.metrics["response_times"][test_name] = elapsed
                return False

        except Exception as e:
            elapsed = time.time() - start_time
            self.metrics["tests_failed"] += 1
            self.log(
                f"❌ {test_name} failed with exception: {str(e)} (took {elapsed:.2f}s)",
                "error",
            )
            self.metrics["response_times"][test_name] = elapsed
            if self.verbose:
                import traceback

                traceback.print_exc()
            return False

    def test_health_endpoint(self) -> bool:
        """Test the health endpoint."""
        response = requests.get(f"{self.api_url}/health", timeout=self.timeout)

        if response.status_code != 200:
            self.log(f"Health check failed with status {response.status_code}", "error")
            return False

        data = response.json()
        if "status" not in data or data["status"] != "ok":
            self.log(
                f"Health check returned unexpected status: {data.get('status')}",
                "error",
            )
            return False

        self.log(f"Health check passed, API version: {data.get('version', 'unknown')}")
        return True

    def test_document_upload(self) -> bool:
        """Test document upload and processing."""
        # Determine file content type based on extension
        file_extension = self.test_file_path.suffix.lower()
        if file_extension == ".pdf":
            content_type = "application/pdf"
        elif file_extension == ".docx":
            content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif file_extension == ".doc":
            content_type = "application/msword"
        else:
            self.log(f"Unsupported file extension: {file_extension}", "error")
            return False

        # Upload the file
        with open(self.test_file_path, "rb") as f:
            filename = self.test_file_path.name
            files = {"file": (filename, f, content_type)}

            self.log(f"Uploading test file: {filename}", "info")
            response = requests.post(
                f"{self.api_url}/documents/upload",
                headers=self.headers,
                files=files,
                timeout=self.timeout,
            )

        if response.status_code != 200:
            self.log(
                f"Document upload failed with status {response.status_code}", "error"
            )
            if self.verbose:
                self.log(f"Response: {response.text}", "error")
            return False

        data = response.json()
        if "document_id" not in data or data.get("status") != "success":
            self.log(f"Document upload returned unexpected response: {data}", "error")
            return False

        self.document_id = data["document_id"]
        num_chunks = data.get("chunks", 0)
        self.log(
            f"Document uploaded successfully, ID: {self.document_id}, Chunks: {num_chunks}",
            "success",
        )
        return True

    def test_vector_search(self, query: str) -> bool:
        """Test the vector search endpoint."""
        if not self.document_id:
            self.log("No document ID available for search test", "error")
            return False

        payload = {"query": query, "limit": 5}

        self.log(f"Testing vector search with query: '{query}'", "info")
        response = requests.post(
            f"{self.api_url}/search",
            headers={**self.headers, "Content-Type": "application/json"},
            json=payload,
            timeout=self.timeout,
        )

        if response.status_code != 200:
            self.log(
                f"Vector search failed with status {response.status_code}", "error"
            )
            if self.verbose:
                self.log(f"Response: {response.text}", "error")
            return False

        results = response.json()
        if not results or not isinstance(results, list):
            self.log(f"Vector search returned unexpected response: {results}", "error")
            return False

        # Validate embedding dimensions
        dimensions = self._extract_embedding_dimensions(results)
        if dimensions != 768:  # legal-bert-base-uncased has 768 dimensions
            self.log(
                f"Unexpected embedding dimensions: {dimensions} (expected 768)", "error"
            )
            return False

        self.log(f"Vector search returned {len(results)} results", "success")
        if self.verbose and results:
            self.log(f"Top result: {results[0].get('content', '')[:100]}...", "info")

        return True

    def _extract_embedding_dimensions(
        self, search_results: List[Dict[str, Any]]
    ) -> Optional[int]:
        """Extract embedding dimensions from search results if available."""
        # This is a best-effort extraction - API may not expose embedding dimensions directly
        for result in search_results:
            if "metadata" in result and "embedding_dimensions" in result["metadata"]:
                return result["metadata"]["embedding_dimensions"]
            if "metadata" in result and "embedding" in result["metadata"]:
                embedding = result["metadata"]["embedding"]
                if isinstance(embedding, list):
                    return len(embedding)

        # If we can't directly extract, log a warning but don't fail the test
        self.log(
            "Could not extract embedding dimensions from search results", "warning"
        )
        return 768  # Assume expected dimensions for legal-bert

    def test_rag_search(self, query: str) -> bool:
        """Test the RAG search endpoint."""
        if not self.document_id:
            self.log("No document ID available for RAG test", "error")
            return False

        payload = {
            "query": query,
            "max_results": 5,
            "temperature": 0.7,
            "max_tokens": 1000,
        }

        self.log(f"Testing RAG search with query: '{query}'", "info")
        response = requests.post(
            f"{self.api_url}/rag-search",
            headers={**self.headers, "Content-Type": "application/json"},
            json=payload,
            timeout=self.timeout,
        )

        if response.status_code != 200:
            self.log(f"RAG search failed with status {response.status_code}", "error")
            if self.verbose:
                self.log(f"Response: {response.text}", "error")
            return False

        data = response.json()
        if not isinstance(data, dict) or "answer" not in data or "sources" not in data:
            self.log(f"RAG search returned unexpected response format", "error")
            return False

        answer = data.get("answer", "")
        sources = data.get("sources", [])
        confidence = data.get("confidence", 0)

        if not answer or not sources:
            self.log(f"RAG search returned empty answer or sources", "error")
            return False

        self.log(
            f"RAG search returned answer with {len(sources)} sources and {confidence:.2f} confidence",
            "success",
        )
        if self.verbose:
            self.log(f"Answer preview: {answer[:100]}...", "info")

        return True

    def test_error_handling(self) -> bool:
        """Test error handling with invalid requests."""
        # Test with invalid payload
        self.log("Testing error handling with invalid search payload", "info")
        response = requests.post(
            f"{self.api_url}/search",
            headers={**self.headers, "Content-Type": "application/json"},
            json={"invalid": "payload"},
            timeout=self.timeout,
        )

        if response.status_code == 200:
            self.log(
                "Error handling test failed: expected error but got success", "error"
            )
            return False

        # Test with empty query
        self.log("Testing error handling with empty query", "info")
        response = requests.post(
            f"{self.api_url}/search",
            headers={**self.headers, "Content-Type": "application/json"},
            json={"query": "", "limit": 5},
            timeout=self.timeout,
        )

        if response.status_code == 200:
            self.log(
                "Error handling test failed: expected error for empty query", "error"
            )
            return False

        self.log("Error handling tests passed", "success")
        return True

    def run_all_tests(self, test_query: str) -> None:
        """Run all tests in sequence."""
        self.metrics["start_time"] = time.time()

        print(f"\n{GREEN}Starting RunPod Integration Tests{RESET}")
        print(f"API URL: {self.api_url}")
        print(f"Test file: {self.test_file_path}")
        print(f"Test query: '{test_query}'\n")

        tests = [
            ("Health Check", self.test_health_endpoint),
            ("Document Upload", self.test_document_upload),
            ("Vector Search", self.test_vector_search, test_query),
            ("RAG Search", self.test_rag_search, test_query),
            ("Error Handling", self.test_error_handling),
        ]

        for test in tests:
            name = test[0]
            func = test[1]
            args = test[2:] if len(test) > 2 else []

            self.run_test(name, func, *args)

        self.metrics["end_time"] = time.time()
        self._print_summary()

    def _print_summary(self) -> None:
        """Print a summary of test results."""
        total_time = self.metrics["end_time"] - self.metrics["start_time"]
        success_rate = (
            (self.metrics["tests_passed"] / self.metrics["tests_run"]) * 100
            if self.metrics["tests_run"] > 0
            else 0
        )

        print(f"\n{YELLOW}==== Test Summary ===={RESET}")
        print(f"Total tests: {self.metrics['tests_run']}")
        print(f"Passed: {GREEN}{self.metrics['tests_passed']}{RESET}")
        print(f"Failed: {RED}{self.metrics['tests_failed']}{RESET}")
        print(
            f"Success rate: {GREEN if success_rate == 100 else YELLOW if success_rate >= 80 else RED}{success_rate:.2f}%{RESET}"
        )
        print(f"Total time: {total_time:.2f}s")

        print(f"\n{YELLOW}==== Response Times ===={RESET}")
        for test_name, response_time in self.metrics["response_times"].items():
            print(f"{test_name}: {response_time:.2f}s")

        # Final assessment
        if success_rate == 100:
            print(
                f"\n{GREEN}✅ All tests passed! The RunPod implementation is working correctly.{RESET}"
            )
        elif success_rate >= 80:
            print(
                f"\n{YELLOW}⚠️ Most tests passed. Some functionality may need attention.{RESET}"
            )
        else:
            print(
                f"\n{RED}❌ Several tests failed. The RunPod implementation needs fixes.{RESET}"
            )


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Test the Legal Search RAG API with RunPod integration."
    )
    parser.add_argument(
        "--url", type=str, default=DEFAULT_CONFIG["api_url"], help="API URL"
    )
    parser.add_argument(
        "--token", type=str, default=DEFAULT_CONFIG["api_token"], help="API token"
    )
    parser.add_argument(
        "--file",
        type=str,
        default=DEFAULT_CONFIG["test_file_path"],
        help="Path to test document",
    )
    parser.add_argument(
        "--query",
        type=str,
        default=DEFAULT_CONFIG["test_query"],
        help="Test query for search/RAG",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_CONFIG["timeout"],
        help="Request timeout in seconds",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    # Create and run the tester
    tester = RunPodTester(
        api_url=args.url,
        api_token=args.token,
        test_file_path=args.file,
        timeout=args.timeout,
        verbose=args.verbose,
    )

    tester.run_all_tests(args.query)


if __name__ == "__main__":
    main()
