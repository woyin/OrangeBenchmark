using System;
using Xunit;

public class PalindromeCheckerTest
{
    [Fact]
    public void TestBasicPalindrome()
    {
        Assert.True(PalindromeChecker.IsPalindrome("racecar"));
    }

    [Fact]
    public void TestNotPalindrome()
    {
        Assert.False(PalindromeChecker.IsPalindrome("hello"));
    }

    [Fact]
    public void TestWithSpaces()
    {
        Assert.True(PalindromeChecker.IsPalindrome("A man a plan a canal Panama"));
    }

    [Fact]
    public void TestWithPunctuation()
    {
        Assert.True(PalindromeChecker.IsPalindrome("A man, a plan, a canal: Panama"));
    }

    [Fact]
    public void TestCaseInsensitive()
    {
        Assert.True(PalindromeChecker.IsPalindrome("Racecar"));
    }

    [Fact]
    public void TestEmptyString()
    {
        Assert.True(PalindromeChecker.IsPalindrome(""));
    }

    [Fact]
    public void TestNullString()
    {
        Assert.True(PalindromeChecker.IsPalindrome(null));
    }

    [Fact]
    public void TestSingleCharacter()
    {
        Assert.True(PalindromeChecker.IsPalindrome("a"));
    }

    [Fact]
    public void TestTwoCharacters()
    {
        Assert.True(PalindromeChecker.IsPalindrome("aa"));
        Assert.False(PalindromeChecker.IsPalindrome("ab"));
    }

    [Fact]
    public void TestNumbers()
    {
        Assert.True(PalindromeChecker.IsPalindrome("12321"));
        Assert.False(PalindromeChecker.IsPalindrome("12345"));
    }
}
