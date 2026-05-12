using System;
using Xunit;

public class AdsbDecoderTest
{
    // These are real ADS-B messages (with CRC) for testing

    [Fact]
    public void TestDecodeAircraftIdentification()
    {
        // DF=17, CA=5, ICAO=4840D6, TC=4, Callsign=KLM1017_
        // This is a known valid identification message
        string msg = "8D4840D6202CC371C32CE0576098";
        var result = AdsbDecoder.Decode(msg);

        Assert.Equal(17, result.DownlinkFormat);
        Assert.Equal(5, result.Capability);
        Assert.Equal("4840D6", result.ICAO);
        Assert.Equal(4, result.TypeCode);
        Assert.NotNull(result.Callsign);
        Assert.True(result.Callsign.StartsWith("KLM"));
    }

    [Fact]
    public void TestDecodePositionMessage()
    {
        // DF=17, CA=5, ICAO=4009B0, TC=11 (airborne position)
        // This message carries altitude information
        string msg = "8D4009B060B505D73F81026A0A32";
        var result = AdsbDecoder.Decode(msg);

        Assert.Equal(17, result.DownlinkFormat);
        Assert.Equal("4009B0", result.ICAO);
        Assert.True(result.TypeCode >= 9 && result.TypeCode <= 18);
        Assert.NotNull(result.AltitudeFeet);
    }

    [Fact]
    public void TestAltitudeExtraction()
    {
        // Position message with altitude
        string msg = "8D4009B060B505D73F81026A0A32";
        var result = AdsbDecoder.Decode(msg);

        Assert.NotNull(result.AltitudeFeet);
        Assert.True(result.AltitudeFeet.Value > 0);
    }

    [Fact]
    public void TestDecodeVelocityMessage()
    {
        // DF=17, CA=5, ICAO=4840D6, TC=19 (airborne velocity)
        string msg = "8D4840D69944099A8C04C50A5B22";
        var result = AdsbDecoder.Decode(msg);

        Assert.Equal(19, result.TypeCode);
        // Velocity messages may or may not have ground speed depending on subtype
    }

    [Fact]
    public void TestCrcValidation_ValidMessage()
    {
        // This message has a valid CRC
        string msg = "8D4840D6202CC371C32CE0576098";
        Assert.True(AdsbDecoder.ValidateCrc(msg));
    }

    [Fact]
    public void TestCrcValidation_InvalidMessage()
    {
        // Flip a bit to corrupt the message
        string msg = "8D4840D6202CC371C32CE0576099";
        Assert.False(AdsbDecoder.ValidateCrc(msg));
    }

    [Fact]
    public void TestDecodeCallsign()
    {
        // Known callsign encoding: "KLM1024 "
        // K=11, L=12, M=13, 1=49, 0=48, 2=50, 4=52, space=32
        // 6-bit encoding: K=010011=19, L=010100=20, M=010101=21
        // 1=110001=49, 0=110000=48, 2=110010=50, 4=110100=52, space=100000=32
        // Packed: (19<<42)|(20<<36)|(21<<30)|(49<<24)|(48<<18)|(50<<12)|(52<<6)|32
        ulong data = ((ulong)19 << 42) | ((ulong)20 << 36) | ((ulong)21 << 30)
                    | ((ulong)49 << 24) | ((ulong)48 << 18) | ((ulong)50 << 12)
                    | ((ulong)52 << 6) | (ulong)32;
        string result = AdsbDecoder.DecodeCallsign(data);
        Assert.Equal("KLM1024", result);
    }

    [Fact]
    public void TestShortMessageThrowsException()
    {
        Assert.Throws<ArgumentException>(() => AdsbDecoder.Decode("8D48"));
    }

    [Fact]
    public void TestEmptyMessageThrowsException()
    {
        Assert.Throws<ArgumentException>(() => AdsbDecoder.Decode(""));
    }
}
