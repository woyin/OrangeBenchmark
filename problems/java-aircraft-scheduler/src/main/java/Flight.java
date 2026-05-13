public class Flight {
    public String flightId, aircraftType;
    public int arrivalTime, departureTime, passengers;
    public Flight(String fid, String type, int arr, int dep, int pax) {
        flightId=fid; aircraftType=type; arrivalTime=arr; departureTime=dep; passengers=pax;
    }
}
