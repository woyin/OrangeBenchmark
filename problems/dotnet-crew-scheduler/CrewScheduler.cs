using System;
using System.Collections.Generic;
using System.Linq;

public record FlightSegment(
    string FlightId,
    DateTime DepartureTime,
    DateTime ArrivalTime,
    string Origin,
    string Destination,
    string AircraftType
);

public record CrewMember(
    string Id,
    HashSet<string> Qualifications
);

public record ScheduleResult(
    Dictionary<string, List<FlightSegment>> Assignments,
    int CoveredFlights,
    int TotalFlights
);

public class CrewScheduler
{
    public ScheduleResult Schedule(List<FlightSegment> flights, List<CrewMember> crew, int maxDutyHours, int minRestHours)
    {
        if (flights == null) throw new ArgumentNullException(nameof(flights));
        if (crew == null) throw new ArgumentNullException(nameof(crew));

        var assignments = new Dictionary<string, List<FlightSegment>>();
        foreach (var c in crew)
        {
            assignments[c.Id] = new List<FlightSegment>();
        }

        var sortedFlights = flights.OrderBy(f => f.DepartureTime).ToList();
        var covered = new HashSet<string>();

        foreach (var flight in sortedFlights)
        {
            // Find first available qualified crew
            foreach (var member in crew)
            {
                if (!member.Qualifications.Contains(flight.AircraftType))
                    continue;

                if (CanAssign(assignments[member.Id], flight, maxDutyHours, minRestHours))
                {
                    assignments[member.Id].Add(flight);
                    covered.Add(flight.FlightId);
                    break;
                }
            }
        }

        return new ScheduleResult(assignments, covered.Count, flights.Count);
    }

    public static bool IsValidSchedule(Dictionary<string, List<FlightSegment>> schedule, int maxDutyHours, int minRestHours)
    {
        foreach (var kvp in schedule)
        {
            var segments = kvp.Value.OrderBy(s => s.DepartureTime).ToList();

            for (int i = 0; i < segments.Count; i++)
            {
                // Check rest between consecutive flights
                if (i > 0)
                {
                    var rest = segments[i].DepartureTime - segments[i - 1].ArrivalTime;
                    if (rest < TimeSpan.FromHours(minRestHours))
                        return false;
                }

                // Check max duty hours in any 24h window
                var windowStart = segments[i].DepartureTime;
                var windowEnd = windowStart.AddHours(24);
                var flightsInWindow = segments
                    .Where(s => s.DepartureTime >= windowStart && s.DepartureTime < windowEnd)
                    .ToList();

                if (flightsInWindow.Count > 0)
                {
                    var dutyStart = flightsInWindow.First().DepartureTime;
                    var dutyEnd = flightsInWindow.Last().ArrivalTime;
                    var dutyHours = (dutyEnd - dutyStart).TotalHours;

                    if (dutyHours > maxDutyHours)
                        return false;
                }
            }
        }

        return true;
    }

    public static int GetCoveragePercent(Dictionary<string, List<FlightSegment>> schedule, List<FlightSegment> allFlights)
    {
        if (allFlights == null || allFlights.Count == 0)
            return 0;

        var assignedFlightIds = new HashSet<string>();
        foreach (var kvp in schedule)
        {
            foreach (var seg in kvp.Value)
            {
                assignedFlightIds.Add(seg.FlightId);
            }
        }

        return (int)Math.Round((double)assignedFlightIds.Count / allFlights.Count * 100);
    }

    private static bool CanAssign(List<FlightSegment> assigned, FlightSegment flight, int maxDutyHours, int minRestHours)
    {
        if (assigned.Count == 0)
            return true;

        // Check rest from last assigned flight
        var last = assigned[assigned.Count - 1];
        if (last.ArrivalTime > flight.DepartureTime)
            return false;

        var rest = flight.DepartureTime - last.ArrivalTime;
        if (rest < TimeSpan.FromHours(minRestHours))
            return false;

        // Check duty hours in the 24h window
        var windowStart = flight.DepartureTime.AddHours(-24);
        var flightsInWindow = assigned
            .Where(s => s.DepartureTime >= windowStart)
            .ToList();
        flightsInWindow.Add(flight);

        var dutyStart = flightsInWindow.First().DepartureTime;
        var dutyEnd = flightsInWindow.Last().ArrivalTime;
        var dutyHours = (dutyEnd - dutyStart).TotalHours;

        return dutyHours <= maxDutyHours;
    }
}
