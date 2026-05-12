using System;
using System.Text.Json;
using Xunit;

public class JsonTransformerTest
{
    [Fact]
    public void TestSimpleRename()
    {
        string input = """{"name": "Alice", "age": 30}""";
        string rules = """[{"$rename": {"name": "fullName"}}]""";

        string result = JsonTransformer.Transform(input, rules);

        using var doc = JsonDocument.Parse(result);
        Assert.True(doc.RootElement.TryGetProperty("fullName", out var name));
        Assert.Equal("Alice", name.GetString());
        Assert.False(doc.RootElement.TryGetProperty("name", out _));
    }

    [Fact]
    public void TestNestedPathSelect()
    {
        string input = """{"user": {"profile": {"email": "test@example.com"}}}""";
        string rules = """[{"$select": "user.profile.email"}]""";

        string result = JsonTransformer.Transform(input, rules);

        using var doc = JsonDocument.Parse(result);
        Assert.Equal("test@example.com", doc.RootElement.GetString());
    }

    [Fact]
    public void TestArrayFilter()
    {
        string input = """[{"name": "Alice", "status": "active"}, {"name": "Bob", "status": "inactive"}, {"name": "Charlie", "status": "active"}]""";
        string rules = """[{"$filter": {"field": "status", "equals": "active"}}]""";

        string result = JsonTransformer.Transform(input, rules);

        using var doc = JsonDocument.Parse(result);
        Assert.Equal(2, doc.RootElement.GetArrayLength());
    }

    [Fact]
    public void TestArrayMap()
    {
        string input = """[{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]""";
        string rules = """[{"$map": {"select": "name"}}]""";

        string result = JsonTransformer.Transform(input, rules);

        using var doc = JsonDocument.Parse(result);
        Assert.Equal(2, doc.RootElement.GetArrayLength());
        Assert.Equal("Alice", doc.RootElement[0].GetString());
        Assert.Equal("Bob", doc.RootElement[1].GetString());
    }

    [Fact]
    public void TestMultipleRulesChained()
    {
        // Select nested array, then filter
        string input = """{"users": [{"name": "Alice", "status": "active"}, {"name": "Bob", "status": "inactive"}]}""";
        string rules = """[{"$select": "users"}, {"$filter": {"field": "status", "equals": "active"}}]""";

        string result = JsonTransformer.Transform(input, rules);

        using var doc = JsonDocument.Parse(result);
        Assert.Equal(1, doc.RootElement.GetArrayLength());
    }

    [Fact]
    public void TestNoMatchingFieldSelect()
    {
        string input = """{"name": "Alice"}""";
        string rules = """[{"$rename": {"foo": "bar"}}]""";

        string result = JsonTransformer.Transform(input, rules);

        using var doc = JsonDocument.Parse(result);
        // Original field should still be there
        Assert.True(doc.RootElement.TryGetProperty("name", out _));
    }

    [Fact]
    public void TestEmptyRulesArray()
    {
        string input = """{"key": "value"}""";
        string rules = """[]""";

        string result = JsonTransformer.Transform(input, rules);

        using var doc = JsonDocument.Parse(result);
        Assert.True(doc.RootElement.TryGetProperty("key", out var val));
        Assert.Equal("value", val.GetString());
    }

    [Fact]
    public void TestNullInputThrows()
    {
        Assert.Throws<ArgumentException>(() => JsonTransformer.Transform(null!, "[]"));
        Assert.Throws<ArgumentException>(() => JsonTransformer.Transform("{}", null!));
    }

    [Fact]
    public void TestSelectMethod()
    {
        string input = """{"a": {"b": {"c": 42}}}""";
        using var doc = JsonDocument.Parse(input);

        var result = JsonTransformer.Select(doc.RootElement, "a.b.c");

        Assert.Equal(42, result.GetInt32());
    }

    [Fact]
    public void TestComplexNestedTransform()
    {
        string input = """{"data": {"items": [{"id": 1, "name": "X"}, {"id": 2, "name": "Y"}]}}""";
        string rules = """[{"$select": "data.items"}, {"$map": {"select": "name"}}]""";

        string result = JsonTransformer.Transform(input, rules);

        using var doc = JsonDocument.Parse(result);
        Assert.Equal(2, doc.RootElement.GetArrayLength());
        Assert.Equal("X", doc.RootElement[0].GetString());
        Assert.Equal("Y", doc.RootElement[1].GetString());
    }
}
