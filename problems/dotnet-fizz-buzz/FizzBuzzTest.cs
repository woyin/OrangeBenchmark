using System;
using System.Collections.Generic;
using Xunit;

public class FizzBuzzTest
{
    [Fact]
    public void TestBasic()
    {
        var expected = new List<string> { "1", "2", "Fizz", "4", "Buzz", "Fizz", "7", "8", "Fizz", "Buzz", "11", "Fizz", "13", "14", "FizzBuzz" };
        Assert.Equal(expected, FizzBuzz.Generate(15));
    }

    [Fact]
    public void TestZero()
    {
        Assert.Equal(new List<string>(), FizzBuzz.Generate(0));
    }

    [Fact]
    public void TestNegative()
    {
        Assert.Equal(new List<string>(), FizzBuzz.Generate(-5));
    }

    [Fact]
    public void TestMultipleOfThreeOnly()
    {
        Assert.Equal(new List<string> { "1", "2", "Fizz" }, FizzBuzz.Generate(3));
    }

    [Fact]
    public void TestMultipleOfFiveOnly()
    {
        Assert.Equal(new List<string> { "1", "2", "Fizz", "4", "Buzz" }, FizzBuzz.Generate(5));
    }

    [Fact]
    public void TestSingleFizzBuzz()
    {
        var result = FizzBuzz.Generate(15);
        Assert.Equal("FizzBuzz", result[14]);
    }
}
