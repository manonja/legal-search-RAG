# Cost Control and Admin Dashboard for RAG Systems

## Introduction

When deploying LLM-powered RAG systems in production, cost management becomes a critical concern. OpenAI API calls can quickly become expensive, especially when generating lengthy responses from large context windows. This article explains how we implemented cost control and administrative monitoring in our legal search RAG system.

## The Problem: Uncontrolled API Costs

LLM APIs pose several cost-related challenges:

1. **Unpredictable token usage**: The number of tokens used in a request can vary significantly based on query complexity and context length
2. **No built-in rate limiting**: Most API providers don't implement usage-based rate limiting, making it easy to exceed budgets
3. **Lack of visibility**: Without proper monitoring, it's difficult to track usage patterns and optimize costs

## Our Solution

We implemented a comprehensive cost control system with two main components:

1. **Cost Control Middleware**: Real-time monitoring and control of API requests
2. **Admin Dashboard**: Monitoring and management of usage metrics and budget settings

### Cost Control Middleware

Our middleware sits between incoming requests and the API, performing several key functions:

```python
class CostControlMiddleware(BaseHTTPMiddleware):
    """Middleware for controlling OpenAI API costs."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip checks for excluded paths
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return await call_next(request)

        # Only apply to specific endpoints
        if request.method == "POST" and path == "/rag-search":
            # Check if quota is exceeded
            exceeded, reason = check_quota_exceeded()
            if exceeded:
                logger.warning(f"Request blocked: {reason}")
                return Response(
                    content=f"{{\"error\": \"API quota exceeded. {reason}\"}}",
                    status_code=429,
                    media_type="application/json"
                )

            # Pre-request cost estimation
            # ...
```

#### Key Features:

1. **Pre-request Cost Estimation**: Before sending a request to OpenAI, we estimate its cost based on token count
2. **Budget Enforcement**: Automatically rejects requests when monthly budgets or query limits are exceeded
3. **High Cost Warnings**: Flags potentially expensive requests before they're processed
4. **Selective Application**: Only applies to specific endpoints, allowing system routes to function normally

#### How It Works:

1. Each incoming request is intercepted by the middleware
2. For RAG search requests, we check if the monthly quota has been exceeded
3. If within quota, we estimate the cost based on input size and model parameters
4. For high-cost requests, we add a warning header but allow the request to proceed
5. Usage metrics are tracked in a database for reporting

### Admin Dashboard

The admin dashboard provides visibility and control over API usage:

```python
@router.get("/dashboard", response_model=Dict[str, DashboardResponse])
async def get_dashboard(api_key: str = Depends(get_api_key)) -> Dict[str, DashboardResponse]:
    """Get dashboard data combining usage, quota, and other statistics."""
    # Get current and historical usage data
    # ...

    # Calculate projections and monthly comparisons
    # ...

    return {
        "data": DashboardResponse(
            current_usage=current_usage,
            quota=quota_data,
            thresholds=threshold_data,
            previous_month=prev_month_data,
            month_over_month=month_over_month,
            projected_monthly_cost=projected_cost,
            cost_per_query=cost_per_query,
            generated_at=datetime.now().isoformat()
        )
    }
```

#### Key Features:

1. **Usage Monitoring**: Detailed metrics on queries, tokens, and costs
2. **Budget Management**: Ability to set and adjust monthly budgets
3. **Historical Reporting**: Month-over-month comparisons and historical trends
4. **Quota Configuration**: Adjust parameters like monthly query limits and warning thresholds
5. **API Security**: Admin API secured with API key authentication

## Implementation Details

### 1. Token Counting and Cost Estimation

We implemented utilities to estimate token usage and associated costs:

```python
def estimate_tokens_and_cost(
    messages: List[Dict[str, str]],
    model: str = "gpt-4",
    max_tokens: int = 1000
) -> Dict[str, Union[int, float]]:
    """Estimate token usage and cost for API request."""
    # Calculate input tokens from messages
    # Estimate output tokens (max_tokens)
    # Look up costs based on model pricing
    # ...
```

This allows us to predict costs before making API calls.

### 2. Usage Database

All usage data is stored in a database for tracking and reporting:

```python
def log_api_usage(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cost: float,
    query_text: str
) -> None:
    """Log API usage to database."""
    # Insert usage record
    # Update monthly aggregates
    # ...
```

### 3. Quota Management

Quotas are configurable and can be updated through the admin API:

```python
def update_quota_settings(
    monthly_budget: Optional[float] = None,
    max_queries_per_month: Optional[int] = None,
    cost_warning_threshold: Optional[float] = None
) -> None:
    """Update quota settings in the database."""
    # ...
```

## Benefits

Our cost control system provides several key benefits:

1. **Budget Predictability**: No surprise bills at the end of the month
2. **Usage Optimization**: Identify high-cost queries and patterns for optimization
3. **Protect Against Abuse**: Prevent excessive usage that could indicate misuse or attacks
4. **Business Planning**: Better forecasting of API costs for budgeting purposes

## Best Practices for RAG Cost Control

Based on our implementation, here are some best practices:

1. **Implement Pre-request Estimation**: Always try to estimate costs before making API calls
2. **Set Reasonable Thresholds**: Determine what constitutes a "high cost" request for your use case
3. **Track Usage Patterns**: Monitor which queries or features drive the most costs
4. **Consider Caching**: Implement caching for common queries to reduce redundant API calls
5. **Use Tiered Models**: Not every query needs GPT-4; use cheaper models when appropriate
6. **Set Hard Limits**: Implement automatic cutoffs to prevent runaway costs
7. **Configure Alerts**: Set up notifications when usage approaches budget limits

## Conclusion

Effective cost control is essential for production RAG systems. By implementing middleware to monitor requests in real-time and providing an admin dashboard for oversight, you can maintain control over API costs while still delivering high-quality responses to users.

Our implementation is designed to be easily adaptable to other RAG systems and can be extended with additional features like per-user quotas or time-based rate limiting as needed.
