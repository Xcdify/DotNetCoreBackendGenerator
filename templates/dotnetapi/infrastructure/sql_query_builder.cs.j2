using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using Dapper;

namespace Infrastructure.Data.Common
{
    public sealed class SqlQueryBuilder
    {
        private readonly string _tableName;
        private readonly List<string> _selectColumns = new();
        private readonly List<string> _whereClauses = new();
        private readonly List<string> _orderByClauses = new();
        private readonly DynamicParameters _parameters = new();
        private int? _limit;
        private int? _offset;
        private int _paramIndex = 0;
        private readonly HashSet<string> _allowedColumns;

        private SqlQueryBuilder(string tableName, IEnumerable<string>? allowedColumns)
        {
            _tableName = tableName;
            _allowedColumns = new HashSet<string>(allowedColumns ?? Enumerable.Empty<string>(), StringComparer.OrdinalIgnoreCase);
        }

        public static SqlQueryBuilder From(string tableName, IEnumerable<string>? allowedColumns = null) => new SqlQueryBuilder(tableName, allowedColumns);

        private string AddParameter(object value, string baseName = "p")
        {
            var name = $"{baseName}{_paramIndex++}";
            _parameters.Add(name, value);
            return name;
        }

        private void EnsureAllowed(string column)
        {
            if (_allowedColumns.Count > 0 && !_allowedColumns.Contains(column))
                throw new ArgumentException($"Column '{column}' is not allowed.");
        }

        public SqlQueryBuilder Select(params string[] columns)
        {
            _selectColumns.AddRange(columns);
            return this;
        }

        public SqlQueryBuilder WhereEquals(string column, object? value)
        {
            if (value is null) return this;
            EnsureAllowed(column);
            var p = AddParameter(value, column);
            _whereClauses.Add($"{column} = @{p}");
            return this;
        }

        public SqlQueryBuilder WhereLike(string column, string? pattern, bool caseInsensitive = true)
        {
            if (string.IsNullOrWhiteSpace(pattern)) return this;
            EnsureAllowed(column);
            var p = AddParameter(pattern, column);
            _whereClauses.Add($"{column} {(caseInsensitive ? "ILIKE" : "LIKE")} @{p}");
            return this;
        }

        public SqlQueryBuilder SearchAcross(IEnumerable<string> columns, string? term)
        {
            if (string.IsNullOrWhiteSpace(term)) return this;
            var likeValue = $"%{term}%";
            var ors = new List<string>();
            foreach (var col in columns)
            {
                EnsureAllowed(col);
                var p = AddParameter(likeValue, "search");
                ors.Add($"{col}::text ILIKE @{p}");
            }
            if (ors.Count > 0)
            {
                _whereClauses.Add("(" + string.Join(" OR ", ors) + ")");
            }
            return this;
        }

        public SqlQueryBuilder ApplyFilters(IDictionary<string, object?>? filters)
        {
            if (filters is null || filters.Count == 0) return this;
            foreach (var kv in filters)
            {
                if (kv.Value is null) continue;
                WhereEquals(kv.Key, kv.Value);
            }
            return this;
        }

        public SqlQueryBuilder OrderBy(string column, bool descending = false)
        {
            EnsureAllowed(column);
            _orderByClauses.Add($"{column} {(descending ? "DESC" : "ASC")}");
            return this;
        }

        public SqlQueryBuilder Paginate(int pageNumber, int pageSize)
        {
            var offset = (pageNumber - 1) * pageSize;
            _offset = offset;
            _limit = pageSize;
            _parameters.Add("offset", offset);
            _parameters.Add("limit", pageSize);
            return this;
        }

        public (string Sql, DynamicParameters Parameters) BuildSelect()
        {
            var sb = new StringBuilder();
            var cols = _selectColumns.Count > 0 ? string.Join(", ", _selectColumns) : "*";
            sb.Append($"SELECT {cols} FROM {_tableName}");
            if (_whereClauses.Count > 0)
            {
                sb.Append(" WHERE ");
                sb.Append(string.Join(" AND ", _whereClauses));
            }
            if (_orderByClauses.Count > 0)
            {
                sb.Append(" ORDER BY ");
                sb.Append(string.Join(", ", _orderByClauses));
            }
            if (_limit.HasValue)
            {
                sb.Append(" LIMIT @limit OFFSET @offset");
            }
            return (sb.ToString(), _parameters);
        }

        public (string Sql, DynamicParameters Parameters) BuildCount()
        {
            var sb = new StringBuilder();
            sb.Append($"SELECT COUNT(*) FROM {_tableName}");
            if (_whereClauses.Count > 0)
            {
                sb.Append(" WHERE ");
                sb.Append(string.Join(" AND ", _whereClauses));
            }
            return (sb.ToString(), _parameters);
        }
    }
}


