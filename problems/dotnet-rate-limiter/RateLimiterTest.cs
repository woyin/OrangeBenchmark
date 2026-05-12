using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Xunit;

public class RateLimiterTest
{
    [Fact]
    public void TestSlidingWindow_BasicAllow()
    {
        var limiter = RateLimiter.CreateSlidingWindow(3, TimeSpan.FromSeconds(10));

        Assert.True(limiter.TryAcquire());
        Assert.True(limiter.TryAcquire());
        Assert.True(limiter.TryAcquire());
    }

    [Fact]
    public void TestSlidingWindow_DenyOverLimit()
    {
        var limiter = RateLimiter.CreateSlidingWindow(2, TimeSpan.FromSeconds(10));

        Assert.True(limiter.TryAcquire());
        Assert.True(limiter.TryAcquire());
        Assert.False(limiter.TryAcquire());
    }

    [Fact]
    public void TestSlidingWindow_WindowReset()
    {
        var limiter = RateLimiter.CreateSlidingWindow(2, TimeSpan.FromMilliseconds(100));

        Assert.True(limiter.TryAcquire());
        Assert.True(limiter.TryAcquire());
        Assert.False(limiter.TryAcquire());

        Thread.Sleep(150);

        Assert.True(limiter.TryAcquire());
    }

    [Fact]
    public void TestTokenBucket_InitialBurst()
    {
        var limiter = RateLimiter.CreateTokenBucket(5, 1.0);

        // Should allow 5 requests immediately (initial burst)
        for (int i = 0; i < 5; i++)
        {
            Assert.True(limiter.TryAcquire());
        }
        Assert.False(limiter.TryAcquire());
    }

    [Fact]
    public void TestTokenBucket_Refill()
    {
        var limiter = RateLimiter.CreateTokenBucket(5, 100.0); // 100 tokens/sec

        // Exhaust all tokens
        for (int i = 0; i < 5; i++)
        {
            Assert.True(limiter.TryAcquire());
        }
        Assert.False(limiter.TryAcquire());

        // Wait for some refill
        Thread.Sleep(50);

        // Should have refilled some tokens
        Assert.True(limiter.TryAcquire());
    }

    [Fact]
    public void TestTryAcquire_MultiplePermits()
    {
        var limiter = RateLimiter.CreateTokenBucket(10, 1.0);

        Assert.True(limiter.TryAcquire(5));
        Assert.True(limiter.TryAcquire(5));
        Assert.False(limiter.TryAcquire(1));
    }

    [Fact]
    public void TestConcurrentAccess()
    {
        var limiter = RateLimiter.CreateSlidingWindow(1000, TimeSpan.FromSeconds(10));
        var results = new bool[500];
        var threads = new List<Thread>();

        for (int i = 0; i < 500; i++)
        {
            int idx = i;
            threads.Add(new Thread(() =>
            {
                results[idx] = limiter.TryAcquire();
            }));
        }

        foreach (var t in threads)
        {
            t.Start();
        }
        foreach (var t in threads)
        {
            t.Join();
        }

        // All 500 should succeed within 1000 limit
        Assert.All(results, r => Assert.True(r));
        Assert.Equal(500, limiter.GetAvailablePermits());
    }

    [Fact]
    public void TestGetAvailablePermits_SlidingWindow()
    {
        var limiter = RateLimiter.CreateSlidingWindow(5, TimeSpan.FromSeconds(10));

        Assert.Equal(5, limiter.GetAvailablePermits());
        limiter.TryAcquire();
        Assert.Equal(4, limiter.GetAvailablePermits());
        limiter.TryAcquire();
        limiter.TryAcquire();
        Assert.Equal(2, limiter.GetAvailablePermits());
    }

    [Fact]
    public void TestGetAvailablePermits_TokenBucket()
    {
        var limiter = RateLimiter.CreateTokenBucket(10, 1.0);

        Assert.Equal(10, limiter.GetAvailablePermits());
        limiter.TryAcquire(3);
        Assert.Equal(7, limiter.GetAvailablePermits());
    }

    [Fact]
    public void TestInvalidParameters()
    {
        Assert.Throws<ArgumentException>(() => RateLimiter.CreateSlidingWindow(0, TimeSpan.FromSeconds(1)));
        Assert.Throws<ArgumentException>(() => RateLimiter.CreateTokenBucket(0, 1.0));
        Assert.Throws<ArgumentException>(() => RateLimiter.CreateTokenBucket(10, 0));
    }

    [Fact]
    public void TestZeroPermitsThrows()
    {
        var limiter = RateLimiter.CreateTokenBucket(5, 1.0);
        Assert.Throws<ArgumentException>(() => limiter.TryAcquire(0));
    }
}
