using System;

namespace Core.Common
{
    /// <summary>
    /// Represents the result of an operation that can succeed or fail
    /// </summary>
    /// <typeparam name="T">The type of the success value</typeparam>
    public class Result<T>
    {
        private Result(bool isSuccess, T? value, Error? error)
        {
            IsSuccess = isSuccess;
            Value = value;
            Error = error;
        }

        /// <summary>
        /// Gets a value indicating whether the operation was successful
        /// </summary>
        public bool IsSuccess { get; }

        /// <summary>
        /// Gets a value indicating whether the operation failed
        /// </summary>
        public bool IsFailure => !IsSuccess;

        /// <summary>
        /// Gets the success value if the operation succeeded
        /// </summary>
        public T? Value { get; }

        /// <summary>
        /// Gets the error if the operation failed
        /// </summary>
        public Error? Error { get; }

        /// <summary>
        /// Creates a successful result
        /// </summary>
        public static Result<T> Success(T value)
        {
            return new Result<T>(true, value, null);
        }

        /// <summary>
        /// Creates a failed result
        /// </summary>
        public static Result<T> Failure(Error error)
        {
            return new Result<T>(false, default, error);
        }

        /// <summary>
        /// Creates a failed result with error message
        /// </summary>
        public static Result<T> Failure(string message, ErrorType type = ErrorType.General)
        {
            return new Result<T>(false, default, new Error(message, type));
        }

        /// <summary>
        /// Implicitly converts a value to a successful result
        /// </summary>
        public static implicit operator Result<T>(T value)
        {
            return Success(value);
        }

        /// <summary>
        /// Implicitly converts an error to a failed result
        /// </summary>
        public static implicit operator Result<T>(Error error)
        {
            return Failure(error);
        }
    }

    /// <summary>
    /// Represents the result of an operation that doesn't return a value
    /// </summary>
    public class Result
    {
        private Result(bool isSuccess, Error? error)
        {
            IsSuccess = isSuccess;
            Error = error;
        }

        /// <summary>
        /// Gets a value indicating whether the operation was successful
        /// </summary>
        public bool IsSuccess { get; }

        /// <summary>
        /// Gets a value indicating whether the operation failed
        /// </summary>
        public bool IsFailure => !IsSuccess;

        /// <summary>
        /// Gets the error if the operation failed
        /// </summary>
        public Error? Error { get; }

        /// <summary>
        /// Creates a successful result
        /// </summary>
        public static Result Success()
        {
            return new Result(true, null);
        }

        /// <summary>
        /// Creates a failed result
        /// </summary>
        public static Result Failure(Error error)
        {
            return new Result(false, error);
        }

        /// <summary>
        /// Creates a failed result with error message
        /// </summary>
        public static Result Failure(string message, ErrorType type = ErrorType.General)
        {
            return new Result(false, new Error(message, type));
        }

        /// <summary>
        /// Implicitly converts an error to a failed result
        /// </summary>
        public static implicit operator Result(Error error)
        {
            return Failure(error);
        }
    }
}