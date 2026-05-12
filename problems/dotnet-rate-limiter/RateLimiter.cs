using System;
using System.Collections.Generic;
using System.Threading;

public class RateLimiter
{
    private enum LimiterType
    {
        SlidingWindow,
        TokenBucket
    }

    private readonly LimiterType _type;
    private readonly int _maxRequests;
    private readonly TimeSpan _window;
    private readonly int _maxBurst;
    private readonly double _refillRatePerSecond;

    private readonly object _lock = new();
    private readonly LinkedList<DateTime> _timestamps = new();
    private double _tokens;
    private DateTime _lastRefillTime;

    private RateLimiter(LimiterType type, int maxRequests, TimeSpan window, int maxBurst, double refillRatePerSecond)
    {
        _type = type;
        _maxRequests = maxRequests;
        _window = window;
        _maxBurst = maxBurst;
        _refillRatePerSecond = refillRatePerSecond;

        if (type == LimiterType.TokenBucket)
        {
            _tokens = maxBurst;
            _lastRefillTime = DateTime.UtcNow;
        }
    }

    public static RateLimiter CreateSlidingWindow(int maxRequests, TimeSpan window)
    {
        if (maxRequests <= 0)
            throw new ArgumentException("Max requests must be positive.", nameof(maxRequests));
        return new RateLimiter(LimiterType.SlidingWindow, maxRequests, window, 0, 0);
    }

    public static RateLimiter CreateTokenBucket(int maxBurst, double refillRatePerSecond)
    {
        if (maxBurst <= 0)
            throw new ArgumentException("Max burst must be positive.", nameof(maxBurst));
        if (refillRatePerSecond <= 0)
            throw new ArgumentException("Refill rate must be positive.", nameof(refillRatePerSecond));
        return new RateLimiter(LimiterType.TokenBucket, 0, TimeSpan.Zero, maxBurst, refillRatePerSecond);
    }

    public bool TryAcquire()
    {
        return TryAcquire(1);
    }

    public bool TryAcquire(int permits)
    {
        if (permits <= 0)
            throw new ArgumentException("Permits must be positive.", nameof(permits));

        lock (_lock)
        {
            return _type switch
            {
                LimiterType.SlidingWindow => TryAcquireSlidingWindow(permits),
                LimiterType.TokenBucket => TryAcquireTokenBucket(permits),
                _ => false
            };
        }
    }

    public int GetAvailablePermits()
    {
        lock (_lock)
        {
            return _type switch
            {
                LimiterType.SlidingWindow => GetAvailableSlidingWindow(),
                LimiterType.TokenBucket => GetAvailableTokenBucket(),
                _ => 0
            };
        }
    }

    private bool TryAcquireSlidingWindow(int permits)
    {
        var now = DateTime.UtcNow;
        var cutoff = now - _window;

        // Remove expired timestamps
        while (_timestamps.Count > 0 && _timestamps.First!.Value < cutoff)
        {
            _timestamps.RemoveFirst();
        }

        if (_timestamps.Count + permits <= _maxRequests)
        {
            for (int i = 0; i < permits; i++)
            {
                _timestamps.AddLast(now);
            }
            return true;
        }

        return false;
    }

    private int GetAvailableSlidingWindow()
    {
        var now = DateTime.UtcNow;
        var cutoff = now - _window;

        while (_timestamps.Count > 0 && _timestamps.First!.Value < cutoff)
        {
            _timestamps.RemoveFirst();
        }

        return Math.Max(0, _maxRequests - _timestamps.Count);
    }

    private bool TryAcquireTokenBucket(int permits)
    {
        RefillTokens();

        if (_tokens >= permits)
        {
            _tokens -= permits;
            return true;
        }

        return false;
    }

    private int GetAvailableTokenBucket()
    {
        RefillTokens();
        return (int)Math.Floor(_tokens);
    }

    private void RefillTokens()
    {
        var now = DateTime.UtcNow;
        var elapsed = (now - _lastRefillTime).TotalSeconds;

        if (elapsed > 0)
        {
            _tokens = Math.Min(_maxBurst, _tokens + elapsed * _refillRatePerSecond);
            _lastRefillTime = now;
        }
    }
}
