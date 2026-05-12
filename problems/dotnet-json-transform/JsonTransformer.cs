using System;
using System.Collections.Generic;
using System.Text;
using System.Text.Json;

public static class JsonTransformer
{
    public static string Transform(string inputJson, string rulesJson)
    {
        if (string.IsNullOrEmpty(inputJson))
            throw new ArgumentException("Input JSON cannot be null or empty.", nameof(inputJson));
        if (string.IsNullOrEmpty(rulesJson))
            throw new ArgumentException("Rules JSON cannot be null or empty.", nameof(rulesJson));

        using var inputDoc = JsonDocument.Parse(inputJson);
        using var rulesDoc = JsonDocument.Parse(rulesJson);

        var current = CloneElement(inputDoc.RootElement);
        var rules = rulesDoc.RootElement;

        if (rules.ValueKind != JsonValueKind.Array)
            return current.GetRawText();

        foreach (var rule in rules.EnumerateArray())
        {
            current = ApplyRule(current, rule);
        }

        return FormatJson(current);
    }

    public static JsonElement Select(JsonElement root, string path)
    {
        if (string.IsNullOrEmpty(path))
            return root;

        var parts = path.Split('.');
        var current = root;

        foreach (var part in parts)
        {
            if (current.ValueKind != JsonValueKind.Object)
                throw new InvalidOperationException($"Cannot navigate into non-object element at '{part}'.");

            if (!current.TryGetProperty(part, out current))
                throw new KeyNotFoundException($"Property '{part}' not found in JSON path '{path}'.");
        }

        return CloneElement(current);
    }

    private static JsonElement ApplyRule(JsonElement current, JsonElement rule)
    {
        if (rule.TryGetProperty("$select", out var selectPath))
        {
            return Select(current, selectPath.GetString()!);
        }

        if (rule.TryGetProperty("$rename", out var renameMap))
        {
            return ApplyRename(current, renameMap);
        }

        if (rule.TryGetProperty("$filter", out var filterSpec))
        {
            return ApplyFilter(current, filterSpec);
        }

        if (rule.TryGetProperty("$map", out var mapSpec))
        {
            return ApplyMap(current, mapSpec);
        }

        return current;
    }

    private static JsonElement ApplyRename(JsonElement current, JsonElement renameMap)
    {
        if (current.ValueKind != JsonValueKind.Object)
            return current;

        var dict = new Dictionary<string, JsonElement>();
        foreach (var prop in current.EnumerateObject())
        {
            var newName = prop.Name;
            if (renameMap.TryGetProperty(prop.Name, out var replacement))
            {
                newName = replacement.GetString()!;
            }
            dict[newName] = prop.Value;
        }

        return ToJsonElement(dict);
    }

    private static JsonElement ApplyFilter(JsonElement current, JsonElement filterSpec)
    {
        if (current.ValueKind != JsonValueKind.Array)
            return current;

        var field = filterSpec.GetProperty("field").GetString()!;
        var equalsValue = filterSpec.GetProperty("equals").GetString()!;

        var results = new List<JsonElement>();
        foreach (var item in current.EnumerateArray())
        {
            if (item.TryGetProperty(field, out var fieldValue))
            {
                if (fieldValue.ValueKind == JsonValueKind.String &&
                    fieldValue.GetString() == equalsValue)
                {
                    results.Add(item);
                }
                else if (fieldValue.ValueKind == JsonValueKind.Number &&
                    fieldValue.GetInt32().ToString() == equalsValue)
                {
                    results.Add(item);
                }
            }
        }

        return ToJsonElement(results);
    }

    private static JsonElement ApplyMap(JsonElement current, JsonElement mapSpec)
    {
        if (current.ValueKind != JsonValueKind.Array)
            return current;

        var selectField = mapSpec.GetProperty("select").GetString()!;

        var results = new List<JsonElement>();
        foreach (var item in current.EnumerateArray())
        {
            if (item.TryGetProperty(selectField, out var fieldValue))
            {
                results.Add(fieldValue);
            }
        }

        return ToJsonElement(results);
    }

    private static JsonElement ToJsonElement(Dictionary<string, JsonElement> dict)
    {
        using var ms = new System.IO.MemoryStream();
        using (var writer = new Utf8JsonWriter(ms))
        {
            writer.WriteStartObject();
            foreach (var kvp in dict)
            {
                writer.WritePropertyName(kvp.Key);
                kvp.Value.WriteTo(writer);
            }
            writer.WriteEndObject();
        }
        var doc = JsonDocument.Parse(ms.ToArray());
        return doc.RootElement.Clone();
    }

    private static JsonElement ToJsonElement(List<JsonElement> list)
    {
        using var ms = new System.IO.MemoryStream();
        using (var writer = new Utf8JsonWriter(ms))
        {
            writer.WriteStartArray();
            foreach (var item in list)
            {
                item.WriteTo(writer);
            }
            writer.WriteEndArray();
        }
        var doc = JsonDocument.Parse(ms.ToArray());
        return doc.RootElement.Clone();
    }

    private static JsonElement CloneElement(JsonElement element)
    {
        var bytes = JsonSerializer.SerializeToUtf8Bytes(element);
        using var doc = JsonDocument.Parse(bytes);
        return doc.RootElement.Clone();
    }

    private static string FormatJson(JsonElement element)
    {
        return element.GetRawText();
    }
}
