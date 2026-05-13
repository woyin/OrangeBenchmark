// Placeholder for HttpResponse
public class HttpResponse {
    public int statusCode;
    public String body;

    public static HttpResponse ok(String body) { return new HttpResponse(); }
    public static HttpResponse notFound() { return new HttpResponse(); }
    public static HttpResponse badRequest(String message) { return new HttpResponse(); }
}
