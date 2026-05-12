using System;
using System.Linq;
using Xunit;

public class TextSearchIndexTest
{
    private TextSearchIndex CreateSampleIndex()
    {
        var index = new TextSearchIndex();
        index.AddDocument("doc1", "the quick brown fox jumps over the lazy dog");
        index.AddDocument("doc2", "the quick blue hare jumps over the active dog");
        index.AddDocument("doc3", "a brown fox and a brown bear walked through the forest");
        return index;
    }

    [Fact]
    public void TestSingleTermSearch()
    {
        var index = CreateSampleIndex();
        var results = index.Search("fox");

        Assert.Equal(2, results.Count);
        Assert.Contains(results, r => r.DocId == "doc1");
        Assert.Contains(results, r => r.DocId == "doc3");
    }

    [Fact]
    public void TestAndQuery()
    {
        var index = CreateSampleIndex();
        var results = index.Search("brown AND fox");

        // doc1 and doc3 both have both terms
        Assert.Equal(2, results.Count);
        Assert.All(results, r => Assert.True(r.Score > 0));
    }

    [Fact]
    public void TestOrQuery()
    {
        var index = CreateSampleIndex();
        var results = index.Search("blue OR brown");

        // doc1 has brown, doc2 has blue, doc3 has brown
        Assert.Equal(3, results.Count);
    }

    [Fact]
    public void TestNotQuery()
    {
        var index = CreateSampleIndex();
        var results = index.Search("NOT fox");

        // Only doc2 does not contain "fox"
        Assert.Single(results);
        Assert.Equal("doc2", results[0].DocId);
    }

    [Fact]
    public void TestPrefixSearch()
    {
        var index = CreateSampleIndex();
        var results = index.Search("fo*");

        // "fox" is in doc1 and doc3, "forest" is in doc3
        Assert.True(results.Count >= 2);
        Assert.Contains(results, r => r.DocId == "doc1");
        Assert.Contains(results, r => r.DocId == "doc3");
    }

    [Fact]
    public void TestTfIdfRankingOrder()
    {
        var index = new TextSearchIndex();
        index.AddDocument("doc1", "apple apple apple banana");
        index.AddDocument("doc2", "apple banana banana banana");
        index.AddDocument("doc3", "cherry date elderberry fig grape");

        var results = index.Search("apple");

        Assert.Equal(2, results.Count);
        // doc1 has higher TF for "apple" (3/4 vs 1/4), same IDF
        Assert.Equal("doc1", results[0].DocId);
        Assert.True(results[0].Score > results[1].Score);
    }

    [Fact]
    public void TestNoResults()
    {
        var index = CreateSampleIndex();
        var results = index.Search("zebra");

        Assert.Empty(results);
    }

    [Fact]
    public void TestEmptyQueryThrows()
    {
        var index = CreateSampleIndex();
        Assert.Throws<ArgumentException>(() => index.Search(""));
        Assert.Throws<ArgumentException>(() => index.Search(null!));
    }

    [Fact]
    public void TestDocumentCountTracking()
    {
        var index = new TextSearchIndex();

        Assert.Equal(0, index.DocumentCount);

        index.AddDocument("doc1", "hello world");
        Assert.Equal(1, index.DocumentCount);

        index.AddDocument("doc2", "hello again");
        Assert.Equal(2, index.DocumentCount);
    }

    [Fact]
    public void TestMultiWordContentTokenization()
    {
        var index = new TextSearchIndex();
        index.AddDocument("doc1", "Hello, World! This is a test.");

        var docs = index.GetDocumentsForTerm("hello");
        Assert.Single(docs);
        Assert.Equal("doc1", docs[0]);

        docs = index.GetDocumentsForTerm("world");
        Assert.Single(docs);

        docs = index.GetDocumentsForTerm("test");
        Assert.Single(docs);
    }

    [Fact]
    public void TestGetDocumentsForTerm()
    {
        var index = CreateSampleIndex();
        var docs = index.GetDocumentsForTerm("quick");

        Assert.Equal(2, docs.Count);
        Assert.Contains("doc1", docs);
        Assert.Contains("doc2", docs);
    }

    [Fact]
    public void TestGetDocumentsForNonExistentTerm()
    {
        var index = CreateSampleIndex();
        var docs = index.GetDocumentsForTerm("nonexistent");

        Assert.Empty(docs);
    }

    [Fact]
    public void TestAddDocumentNullThrows()
    {
        var index = new TextSearchIndex();
        Assert.Throws<ArgumentException>(() => index.AddDocument(null!, "content"));
        Assert.Throws<ArgumentException>(() => index.AddDocument("doc1", null!));
    }
}
