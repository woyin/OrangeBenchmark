using System;
using System.Collections.Generic;
using System.Linq;

public record SearchResult(string DocId, double Score);

public class TextSearchIndex
{
    private readonly Dictionary<string, Dictionary<string, int>> _invertedIndex = new();
    private readonly Dictionary<string, int> _docTermCounts = new();
    private readonly HashSet<string> _allTerms = new();

    public int DocumentCount => _docTermCounts.Count;

    public void AddDocument(string docId, string content)
    {
        if (string.IsNullOrEmpty(docId))
            throw new ArgumentException("Document ID cannot be null or empty.", nameof(docId));
        if (string.IsNullOrEmpty(content))
            throw new ArgumentException("Content cannot be null or empty.", nameof(content));

        var tokens = Tokenize(content);
        var termCounts = new Dictionary<string, int>();

        foreach (var token in tokens)
        {
            if (termCounts.ContainsKey(token))
                termCounts[token]++;
            else
                termCounts[token] = 1;
        }

        _docTermCounts[docId] = tokens.Count;

        foreach (var kvp in termCounts)
        {
            if (!_invertedIndex.ContainsKey(kvp.Key))
                _invertedIndex[kvp.Key] = new Dictionary<string, int>();

            _invertedIndex[kvp.Key][docId] = kvp.Value;
            _allTerms.Add(kvp.Key);
        }
    }

    public List<SearchResult> Search(string query)
    {
        if (string.IsNullOrEmpty(query))
            throw new ArgumentException("Query cannot be null or empty.", nameof(query));

        var tokens = query.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        if (tokens.Length == 0)
            return new List<SearchResult>();

        // Check for NOT operator
        if (tokens.Length >= 2 && tokens[0] == "NOT")
        {
            var excludeTerm = tokens[1].ToLowerInvariant();
            var allDocs = _docTermCounts.Keys.ToHashSet();
            var excludeDocs = GetDocumentsForTerm(excludeTerm).ToHashSet();
            allDocs.ExceptWith(excludeDocs);

            return allDocs
                .Select(docId => new SearchResult(docId, 1.0))
                .OrderByDescending(r => r.DocId)
                .ToList();
        }

        // Check for AND operator
        if (tokens.Length == 3 && tokens[1] == "AND")
        {
            var term1 = tokens[0].ToLowerInvariant();
            var term2 = tokens[2].ToLowerInvariant();

            var docs1 = GetTfIdfScores(term1);
            var docs2 = GetTfIdfScores(term2);

            var commonDocs = docs1.Keys.Intersect(docs2.Keys);

            return commonDocs
                .Select(docId => new SearchResult(docId, docs1[docId] + docs2[docId]))
                .OrderByDescending(r => r.Score)
                .ThenBy(r => r.DocId)
                .ToList();
        }

        // Check for OR operator
        if (tokens.Length == 3 && tokens[1] == "OR")
        {
            var term1 = tokens[0].ToLowerInvariant();
            var term2 = tokens[2].ToLowerInvariant();

            var allScores = new Dictionary<string, double>();
            foreach (var kvp in GetTfIdfScores(term1))
                allScores[kvp.Key] = kvp.Value;
            foreach (var kvp in GetTfIdfScores(term2))
            {
                if (allScores.ContainsKey(kvp.Key))
                    allScores[kvp.Key] += kvp.Value;
                else
                    allScores[kvp.Key] = kvp.Value;
            }

            return allScores
                .Select(kvp => new SearchResult(kvp.Key, kvp.Value))
                .OrderByDescending(r => r.Score)
                .ThenBy(r => r.DocId)
                .ToList();
        }

        // Check for prefix match (term ending with *)
        if (tokens.Length == 1 && tokens[0].EndsWith("*"))
        {
            var prefix = tokens[0][..^1].ToLowerInvariant();
            var matchingTerms = _allTerms.Where(t => t.StartsWith(prefix)).ToList();

            var allScores = new Dictionary<string, double>();
            foreach (var term in matchingTerms)
            {
                foreach (var kvp in GetTfIdfScores(term))
                {
                    if (allScores.ContainsKey(kvp.Key))
                        allScores[kvp.Key] += kvp.Value;
                    else
                        allScores[kvp.Key] = kvp.Value;
                }
            }

            return allScores
                .Select(kvp => new SearchResult(kvp.Key, kvp.Value))
                .OrderByDescending(r => r.Score)
                .ThenBy(r => r.DocId)
                .ToList();
        }

        // Simple single term search
        var searchTerm = tokens[0].ToLowerInvariant();
        var scores = GetTfIdfScores(searchTerm);

        return scores
            .Select(kvp => new SearchResult(kvp.Key, kvp.Value))
            .OrderByDescending(r => r.Score)
            .ThenBy(r => r.DocId)
            .ToList();
    }

    public List<string> GetDocumentsForTerm(string term)
    {
        var normalized = term.ToLowerInvariant();
        if (_invertedIndex.TryGetValue(normalized, out var docs))
            return docs.Keys.ToList();
        return new List<string>();
    }

    private Dictionary<string, double> GetTfIdfScores(string term)
    {
        var result = new Dictionary<string, double>();

        if (!_invertedIndex.TryGetValue(term, out var docs))
            return result;

        int df = docs.Count;
        double idf = Math.Log((double)DocumentCount / df);

        foreach (var kvp in docs)
        {
            double tf = (double)kvp.Value / _docTermCounts[kvp.Key];
            result[kvp.Key] = tf * idf;
        }

        return result;
    }

    private static List<string> Tokenize(string content)
    {
        var tokens = new List<string>();
        var current = new List<char>();

        foreach (char c in content)
        {
            if (char.IsLetterOrDigit(c))
            {
                current.Add(char.ToLowerInvariant(c));
            }
            else
            {
                if (current.Count > 0)
                {
                    tokens.Add(new string(current.ToArray()));
                    current.Clear();
                }
            }
        }

        if (current.Count > 0)
        {
            tokens.Add(new string(current.ToArray()));
        }

        return tokens;
    }
}
