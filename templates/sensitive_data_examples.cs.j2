using Destructurama.Attributed;

namespace Core.Common.Examples
{
    /// <summary>
    /// Example class demonstrating sensitive data masking using Destructurama attributes.
    /// Use these attributes on your entities to protect sensitive information in logs.
    /// </summary>
    public class SensitiveDataExamples
    {
        /// <summary>
        /// Regular property - will be logged normally
        /// </summary>
        public string Username { get; set; } = string.Empty;

        /// <summary>
        /// Property marked with [NotLogged] - completely excluded from logs
        /// Best for passwords, API keys, etc.
        /// </summary>
        [NotLogged]
        public string Password { get; set; } = string.Empty;

        /// <summary>
        /// Property with [LogMasked] - shows first 3 and last 2 characters
        /// Good for email addresses, phone numbers, etc.
        /// </summary>
        [LogMasked(ShowFirst = 3, ShowLast = 2)]
        public string Email { get; set; } = string.Empty;

        /// <summary>
        /// Property with [LogMasked] preserving format - shows only specified characters
        /// Excellent for credit cards, SSNs, etc.
        /// </summary>
        [LogMasked(ShowFirst = 4, ShowLast = 4, PreserveLength = true)]
        public string CreditCard { get; set; } = string.Empty;

        /// <summary>
        /// Property with [LogMasked] with custom mask
        /// </summary>
        [LogMasked(Text = "[SENSITIVE]")]
        public string ApiKey { get; set; } = string.Empty;

        /// <summary>
        /// Property with [LogReplaced] - uses regex to replace sensitive parts
        /// Useful when only part of the string is sensitive
        /// </summary>
        [LogReplaced(@"(\w+@)(\w+)(\.\w+)", "$1***$3")]
        public string ContactInfo { get; set; } = string.Empty;
    }

    /// <summary>
    /// Example login request demonstrating real-world usage
    /// </summary>
    public class LoginRequest
    {
        public string Username { get; set; } = string.Empty;

        [NotLogged]
        public string Password { get; set; } = string.Empty;

        [LogMasked(ShowFirst = 3, ShowLast = 2)]
        public string Email { get; set; } = string.Empty;

        public string UserAgent { get; set; } = string.Empty;

        public DateTime LoginTime { get; set; } = DateTime.UtcNow;
    }

    /// <summary>
    /// Example user profile with various sensitive fields
    /// </summary>
    public class UserProfile
    {
        public int Id { get; set; }

        public string FirstName { get; set; } = string.Empty;

        public string LastName { get; set; } = string.Empty;

        [LogMasked(ShowFirst = 3, ShowLast = 2)]
        public string Email { get; set; } = string.Empty;

        [LogMasked(Text = "[PHONE_REDACTED]")]
        public string PhoneNumber { get; set; } = string.Empty;

        [LogMasked(ShowFirst = 4, ShowLast = 4, PreserveLength = true)]
        public string SocialSecurityNumber { get; set; } = string.Empty;

        [NotLogged]
        public string PasswordHash { get; set; } = string.Empty;

        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    }
}