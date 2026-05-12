using System;
using System.Collections.Generic;
using System.Linq;
using Xunit;

public class CrewSchedulerTest
{
    private static readonly DateTime BaseTime = new DateTime(2024, 6, 1, 8, 0, 0);

    [Fact]
    public void TestBasicAssignment()
    {
        var flights = new List<FlightSegment>
        {
            new("F1", BaseTime, BaseTime.AddHours(2), "JFK", "LAX", "B737"),
        };
        var crew = new List<CrewMember>
        {
            new("C1", new HashSet<string> { "B737" }),
        };

        var scheduler = new CrewScheduler();
        var result = scheduler.Schedule(flights, crew, 10, 8);

        Assert.Equal(1, result.CoveredFlights);
        Assert.Equal(1, result.TotalFlights);
        Assert.Single(result.Assignments["C1"]);
    }

    [Fact]
    public void TestQualificationFiltering()
    {
        var flights = new List<FlightSegment>
        {
            new("F1", BaseTime, BaseTime.AddHours(2), "JFK", "LAX", "B737"),
        };
        var crew = new List<CrewMember>
        {
            new("C1", new HashSet<string> { "A320" }),
            new("C2", new HashSet<string> { "B737" }),
        };

        var scheduler = new CrewScheduler();
        var result = scheduler.Schedule(flights, crew, 10, 8);

        Assert.Equal(1, result.CoveredFlights);
        Assert.Empty(result.Assignments["C1"]);
        Assert.Single(result.Assignments["C2"]);
    }

    [Fact]
    public void TestMaxDutyHoursRespected()
    {
        // Three flights that would exceed 8h duty if all assigned
        var flights = new List<FlightSegment>
        {
            new("F1", BaseTime, BaseTime.AddHours(3), "JFK", "ORD", "B737"),
            new("F2", BaseTime.AddHours(4), BaseTime.AddHours(7), "ORD", "DEN", "B737"),
            new("F3", BaseTime.AddHours(8), BaseTime.AddHours(12), "DEN", "LAX", "B737"),
        };
        var crew = new List<CrewMember>
        {
            new("C1", new HashSet<string> { "B737" }),
        };

        var scheduler = new CrewScheduler();
        var result = scheduler.Schedule(flights, crew, 8, 1);

        // C1 can do F1 and F2 (duty = 7h), F3 would make it 12h duty > 8
        Assert.True(result.CoveredFlights >= 2);
        Assert.True(IsValidSchedule(result.Assignments, 8, 1));
    }

    [Fact]
    public void TestMinRestRespected()
    {
        var flights = new List<FlightSegment>
        {
            new("F1", BaseTime, BaseTime.AddHours(2), "JFK", "ORD", "B737"),
            // Only 2h rest between F1 arrival and F2 departure (< 4h min rest)
            new("F2", BaseTime.AddHours(4), BaseTime.AddHours(6), "ORD", "LAX", "B737"),
        };
        var crew = new List<CrewMember>
        {
            new("C1", new HashSet<string> { "B737" }),
        };

        var scheduler = new CrewScheduler();
        var result = scheduler.Schedule(flights, crew, 10, 4);

        // With 4h min rest, only F1 can be assigned (gap is 2h)
        Assert.Equal(1, result.CoveredFlights);
    }

    [Fact]
    public void TestInsufficientCrewPartialCoverage()
    {
        // Two simultaneous flights but only one crew
        var flights = new List<FlightSegment>
        {
            new("F1", BaseTime, BaseTime.AddHours(2), "JFK", "LAX", "B737"),
            new("F2", BaseTime, BaseTime.AddHours(2), "SFO", "SEA", "B737"),
        };
        var crew = new List<CrewMember>
        {
            new("C1", new HashSet<string> { "B737" }),
        };

        var scheduler = new CrewScheduler();
        var result = scheduler.Schedule(flights, crew, 10, 8);

        Assert.Equal(1, result.CoveredFlights);
        Assert.Equal(2, result.TotalFlights);
    }

    [Fact]
    public void TestEmptyInputs()
    {
        var scheduler = new CrewScheduler();
        var result = scheduler.Schedule(new List<FlightSegment>(), new List<CrewMember>(), 10, 8);

        Assert.Equal(0, result.CoveredFlights);
        Assert.Equal(0, result.TotalFlights);
    }

    [Fact]
    public void TestNullInputs()
    {
        var scheduler = new CrewScheduler();
        Assert.Throws<ArgumentNullException>(() => scheduler.Schedule(null!, new List<CrewMember>(), 10, 8));
        Assert.Throws<ArgumentNullException>(() => scheduler.Schedule(new List<FlightSegment>(), null!, 10, 8));
    }

    [Fact]
    public void TestSingleCrewSingleFlight()
    {
        var flights = new List<FlightSegment>
        {
            new("F1", BaseTime, BaseTime.AddHours(1), "JFK", "BOS", "A320"),
        };
        var crew = new List<CrewMember>
        {
            new("C1", new HashSet<string> { "A320" }),
        };

        var scheduler = new CrewScheduler();
        var result = scheduler.Schedule(flights, crew, 10, 8);

        Assert.Equal(100, CrewScheduler.GetCoveragePercent(result.Assignments, flights));
    }

    [Fact]
    public void TestIsValidSchedule_Valid()
    {
        var schedule = new Dictionary<string, List<FlightSegment>>
        {
            ["C1"] = new List<FlightSegment>
            {
                new("F1", BaseTime, BaseTime.AddHours(2), "JFK", "LAX", "B737"),
                new("F2", BaseTime.AddHours(12), BaseTime.AddHours(15), "LAX", "SFO", "B737"),
            }
        };

        Assert.True(CrewScheduler.IsValidSchedule(schedule, 10, 8));
    }

    [Fact]
    public void TestIsValidSchedule_InvalidRest()
    {
        var schedule = new Dictionary<string, List<FlightSegment>>
        {
            ["C1"] = new List<FlightSegment>
            {
                new("F1", BaseTime, BaseTime.AddHours(2), "JFK", "LAX", "B737"),
                new("F2", BaseTime.AddHours(3), BaseTime.AddHours(5), "LAX", "SFO", "B737"),
            }
        };

        Assert.False(CrewScheduler.IsValidSchedule(schedule, 10, 8));
    }

    private static bool IsValidSchedule(Dictionary<string, List<FlightSegment>> schedule, int maxDuty, int minRest)
    {
        return CrewScheduler.IsValidSchedule(schedule, maxDuty, minRest);
    }
}
