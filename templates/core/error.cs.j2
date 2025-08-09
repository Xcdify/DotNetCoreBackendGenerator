using System;

namespace Core.Common
{
    /// <summary>
    /// Represents an error with type and message
    /// </summary>
    public class Error : IEquatable<Error>
    {
        public Error(string message, ErrorType type = ErrorType.General, string? code = null)
        {
            Message = message ?? throw new ArgumentNullException(nameof(message));
            Type = type;
            Code = code;
        }

        /// <summary>
        /// Gets the error message
        /// </summary>
        public string Message { get; }

        /// <summary>
        /// Gets the error type
        /// </summary>
        public ErrorType Type { get; }

        /// <summary>
        /// Gets the optional error code
        /// </summary>
        public string? Code { get; }

        public bool Equals(Error? other)
        {
            if (other is null) return false;
            if (ReferenceEquals(this, other)) return true;
            return Message == other.Message && Type == other.Type && Code == other.Code;
        }

        public override bool Equals(object? obj)
        {
            return Equals(obj as Error);
        }

        public override int GetHashCode()
        {
            return HashCode.Combine(Message, Type, Code);
        }

        public override string ToString()
        {
            return Code is not null ? $"[{Code}] {Message}" : Message;
        }

        public static bool operator ==(Error? left, Error? right)
        {
            return Equals(left, right);
        }

        public static bool operator !=(Error? left, Error? right)
        {
            return !Equals(left, right);
        }

        /// <summary>
        /// Creates a validation error
        /// </summary>
        public static Error Validation(string message, string? code = null)
        {
            return new Error(message, ErrorType.Validation, code);
        }

        /// <summary>
        /// Creates a not found error
        /// </summary>
        public static Error NotFound(string message, string? code = null)
        {
            return new Error(message, ErrorType.NotFound, code);
        }

        /// <summary>
        /// Creates a conflict error
        /// </summary>
        public static Error Conflict(string message, string? code = null)
        {
            return new Error(message, ErrorType.Conflict, code);
        }

        /// <summary>
        /// Creates an unauthorized error
        /// </summary>
        public static Error Unauthorized(string message, string? code = null)
        {
            return new Error(message, ErrorType.Unauthorized, code);
        }

        /// <summary>
        /// Creates a forbidden error
        /// </summary>
        public static Error Forbidden(string message, string? code = null)
        {
            return new Error(message, ErrorType.Forbidden, code);
        }

        /// <summary>
        /// Creates an internal error
        /// </summary>
        public static Error Internal(string message, string? code = null)
        {
            return new Error(message, ErrorType.Internal, code);
        }
    }

    /// <summary>
    /// Defines the type of error
    /// </summary>
    public enum ErrorType
    {
        General,
        Validation,
        NotFound,
        Conflict,
        Unauthorized,
        Forbidden,
        Internal
    }
}