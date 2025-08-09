using Serilog.Context;

namespace WebApi.Middleware
{
    /// <summary>
    /// Middleware to handle correlation IDs for request tracing
    /// </summary>
    public class CorrelationMiddleware
    {
        private const string CorrelationIdHeaderName = "X-Correlation-Id";
        private readonly RequestDelegate _next;

        public CorrelationMiddleware(RequestDelegate next)
        {
            _next = next;
        }

        public async Task InvokeAsync(HttpContext context)
        {
            var correlationId = GetOrCreateCorrelationId(context);
            
            // Add to response headers
            context.Response.Headers.TryAdd(CorrelationIdHeaderName, correlationId);
            
            // Add to Serilog LogContext for all subsequent logs
            using (LogContext.PushProperty("CorrelationId", correlationId))
            {
                await _next(context);
            }
        }

        private static string GetOrCreateCorrelationId(HttpContext context)
        {
            // Try to get from request headers first
            if (context.Request.Headers.TryGetValue(CorrelationIdHeaderName, out var correlationId) &&
                !string.IsNullOrEmpty(correlationId.FirstOrDefault()))
            {
                return correlationId.FirstOrDefault()!;
            }

            // Generate new correlation ID if not provided
            return Guid.NewGuid().ToString("D");
        }
    }

    /// <summary>
    /// Extension method to register correlation middleware
    /// </summary>
    public static class CorrelationMiddlewareExtensions
    {
        public static IApplicationBuilder UseCorrelationId(this IApplicationBuilder builder)
        {
            return builder.UseMiddleware<CorrelationMiddleware>();
        }
    }
}