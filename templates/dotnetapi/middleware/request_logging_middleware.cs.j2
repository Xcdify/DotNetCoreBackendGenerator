using Serilog;
using Serilog.Events;
using System.Diagnostics;
using System.Text;

namespace WebApi.Middleware
{
    /// <summary>
    /// Middleware for structured request/response logging with sensitive data sanitization
    /// </summary>
    public class RequestLoggingMiddleware
    {
        private readonly RequestDelegate _next;
        private readonly ILogger<RequestLoggingMiddleware> _logger;
        private static readonly Serilog.ILogger Log = Serilog.Log.ForContext<RequestLoggingMiddleware>();

        // Sensitive headers to exclude from logging
        private static readonly HashSet<string> SensitiveHeaders = new(StringComparer.OrdinalIgnoreCase)
        {
            "authorization",
            "cookie",
            "x-api-key",
            "x-auth-token",
            "authentication"
        };

        // Sensitive query parameters to exclude from logging
        private static readonly HashSet<string> SensitiveQueryParams = new(StringComparer.OrdinalIgnoreCase)
        {
            "password",
            "token",
            "api_key",
            "secret",
            "auth"
        };

        public RequestLoggingMiddleware(RequestDelegate next, ILogger<RequestLoggingMiddleware> logger)
        {
            _next = next;
            _logger = logger;
        }

        public async Task InvokeAsync(HttpContext context)
        {
            var stopwatch = Stopwatch.StartNew();
            var request = context.Request;
            
            // Log request
            LogRequest(context);

            // Capture response for logging
            var originalResponseBodyStream = context.Response.Body;
            using var responseBody = new MemoryStream();
            context.Response.Body = responseBody;

            Exception? exception = null;
            try
            {
                await _next(context);
            }
            catch (Exception ex)
            {
                exception = ex;
                throw;
            }
            finally
            {
                stopwatch.Stop();
                
                // Copy response back to original stream
                responseBody.Seek(0, SeekOrigin.Begin);
                await responseBody.CopyToAsync(originalResponseBodyStream);
                context.Response.Body = originalResponseBodyStream;

                // Log response
                LogResponse(context, stopwatch.ElapsedMilliseconds, exception);
            }
        }

        private static void LogRequest(HttpContext context)
        {
            var request = context.Request;
            
            Log.Information("HTTP {RequestMethod} {RequestPath} started {RemoteIpAddress} {UserAgent}",
                request.Method,
                GetSanitizedPath(request),
                context.Connection.RemoteIpAddress?.ToString(),
                request.Headers.UserAgent.ToString());
        }

        private static void LogResponse(HttpContext context, long elapsedMs, Exception? exception)
        {
            var request = context.Request;
            var response = context.Response;

            if (exception != null)
            {
                Log.Error(exception,
                    "HTTP {RequestMethod} {RequestPath} responded {StatusCode} in {Elapsed}ms with exception",
                    request.Method,
                    GetSanitizedPath(request),
                    response.StatusCode,
                    elapsedMs);
            }
            else
            {
                var logLevel = response.StatusCode >= 500 ? LogEventLevel.Error :
                              response.StatusCode >= 400 ? LogEventLevel.Warning :
                              LogEventLevel.Information;

                Log.Write(logLevel,
                    "HTTP {RequestMethod} {RequestPath} responded {StatusCode} in {Elapsed}ms",
                    request.Method,
                    GetSanitizedPath(request),
                    response.StatusCode,
                    elapsedMs);
            }
        }

        private static string GetSanitizedPath(HttpRequest request)
        {
            var path = request.Path.ToString();
            
            if (!request.QueryString.HasValue)
                return path;

            var queryBuilder = new StringBuilder();
            var query = request.Query;
            
            foreach (var kvp in query)
            {
                if (queryBuilder.Length > 0)
                    queryBuilder.Append('&');
                
                queryBuilder.Append(kvp.Key);
                queryBuilder.Append('=');
                
                // Sanitize sensitive query parameters
                if (SensitiveQueryParams.Contains(kvp.Key))
                {
                    queryBuilder.Append("[REDACTED]");
                }
                else
                {
                    queryBuilder.Append(kvp.Value);
                }
            }

            return $"{path}?{queryBuilder}";
        }

        private static Dictionary<string, string> GetSanitizedHeaders(IHeaderDictionary headers)
        {
            return headers
                .Where(h => !SensitiveHeaders.Contains(h.Key))
                .ToDictionary(h => h.Key, h => h.Value.ToString());
        }
    }

    /// <summary>
    /// Extension method to register request logging middleware
    /// </summary>
    public static class RequestLoggingMiddlewareExtensions
    {
        public static IApplicationBuilder UseRequestLogging(this IApplicationBuilder builder)
        {
            return builder.UseMiddleware<RequestLoggingMiddleware>();
        }
    }
}