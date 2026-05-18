using System;
using Xunit;

public class StringReverserTest
{
    [Fact]
    public void TestBasicReverse()
    {
        Assert.Equal("olleh", StringReverser.Reverse("hello"));
    }

    [Fact]
    public void TestEmptyString()
    {
        Assert.Equal("", StringReverser.Reverse(""));
    }

    [Fact]
    public void TestNullString()
    {
        Assert.Equal("", StringReverser.Reverse(null));
    }

    [Fact]
    public void TestSingleCharacter()
    {
        Assert.Equal("a", StringReverser.Reverse("a"));
    }

    [Fact]
    public void TestWithSpaces()
    {
        Assert.Equal("dlrow olleh", StringReverser.Reverse("hello world"));
    }

    [Fact]
    public void TestPalindrome()
    {
        Assert.Equal("racecar", StringReverser.Reverse("racecar"));
    }

    [Fact]
    public void TestWithNumbers()
    {
        Assert.Equal("321", StringReverser.Reverse("123"));
    }

    [Fact]
    public void TestMixedContent()
    {
        Assert.Equal("!dlroW olleH", StringReverser.Reverse("Hello World!"));
    }
}
