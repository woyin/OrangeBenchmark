using System;
using System.Text;

public record AdsbMessage(
    int DownlinkFormat,
    int Capability,
    string ICAO,
    int TypeCode,
    string? Callsign,
    double? AltitudeFeet,
    double? Latitude,
    double? Longitude,
    double? GroundSpeedKnots,
    double? TrackAngle,
    bool IsValid
);

public static class AdsbDecoder
{
    // Mode S CRC polynomial: 0x1FFF409 (25 bits)
    private const uint CrcPolynomial = 0xFFF409;

    private static readonly char[] CallsignCharset = new char[]
    {
        '#', 'A', 'B', 'C', 'D', 'E', 'F', 'G',
        'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O',
        'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W',
        'X', 'Y', 'Z', ' ', ' ', ' ', ' ', ' ',
        '0', '1', '2', '3', '4', '5', '6', '7',
        '8', '9', ' ', ' ', ' ', ' ', ' ', ' '
    };

    public static AdsbMessage Decode(string hexMessage)
    {
        if (string.IsNullOrEmpty(hexMessage) || hexMessage.Length < 28)
        {
            throw new ArgumentException("Message too short; must be at least 28 hex characters (14 bytes).", nameof(hexMessage));
        }

        byte[] bytes = HexToBytes(hexMessage);
        bool isValid = ValidateCrc(hexMessage);

        // Extract fields from the first 4 bytes (32 bits)
        // Byte 0: DF (5 bits) + CA (3 bits)
        int downlinkFormat = (bytes[0] >> 3) & 0x1F;
        int capability = bytes[0] & 0x07;

        // Bytes 1-3: ICAO address (24 bits)
        string icao = string.Format("{0:X6}", ((uint)bytes[1] << 16) | ((uint)bytes[2] << 8) | bytes[3]);

        // Byte 4 bits 3-7: Type Code (5 bits)
        int typeCode = (bytes[4] >> 3) & 0x1F;

        // Parse based on type code
        string? callsign = null;
        double? altitudeFeet = null;
        double? latitude = null;
        double? longitude = null;
        double? groundSpeedKnots = null;
        double? trackAngle = null;

        if (typeCode >= 1 && typeCode <= 4)
        {
            // Aircraft identification (callsign)
            // ME field is bytes 4-10 (56 bits from byte 4), but callsign data starts at bit 40 (byte 5) through bit 87
            // The 6-bit characters are in the lower 48 bits of the ME field (bytes 5-10)
            ulong me = 0;
            for (int i = 4; i < 11 && i < bytes.Length; i++)
            {
                me = (me << 8) | bytes[i];
            }
            ulong callsignData = me & 0x00FFFFFFFFFFFFUL;
            callsign = DecodeCallsign(callsignData);
        }
        else if (typeCode >= 9 && typeCode <= 18)
        {
            // Airborne position (with altitude)
            // Altitude: bits 40-51 of the message (ME bits 5-16)
            // ME starts at byte 4
            uint meWord = ((uint)bytes[4] << 16) | ((uint)bytes[5] << 8) | bytes[6];
            int rawAlt = (int)((meWord >> 5) & 0x1FFF); // 13 bits

            // Determine altitude encoding: bit 6 of rawAlt (M-bit) indicates encoding
            if ((rawAlt & 0x0040) != 0)
            {
                // Gillham encoded altitude (100 ft increments)
                int n = ((rawAlt & 0x1F80) >> 2) | ((rawAlt & 0x0020) >> 1) | (rawAlt & 0x001F);
                // Decode Gray code for the 7 MSBs (D1..D4, D0 not used in this simplified version)
                // Simplified: use the standard method
                altitudeFeet = n * 100 - 1000;
            }
            else
            {
                // Metric altitude (meters, convert to feet)
                int meters = rawAlt & 0x003F;
                altitudeFeet = meters * 3.28084;
            }

            // CPR position decoding (simplified - single message)
            // CPR format: F flag at bit 53 (ME bit 22)
            int cprFormat = (bytes[6] >> 2) & 0x01;

            // Latitude CPR: bits 54-70 (ME bits 23-39) -> 17 bits
            int cprLat = ((bytes[6] & 0x03) << 15) | (bytes[7] << 7) | (bytes[8] >> 1);
            // Longitude CPR: bits 71-87 (ME bits 40-56) -> 17 bits
            int cprLon = ((bytes[8] & 0x01) << 16) | (bytes[9] << 8) | bytes[10];

            // NL function (number of latitude zones)
            double latCpr = cprLat / 131072.0;
            double lonCpr = cprLon / 131072.0;

            if (cprFormat == 0)
            {
                // Even frame
                latitude = 360.0 / 60 * latCpr;
                longitude = 360.0 / (ZoneCountAV(latitude.Value)) * lonCpr;
            }
            else
            {
                // Odd frame
                latitude = 360.0 / 59 * latCpr - 360.0 / 4;
                longitude = 360.0 / (ZoneCountAV(latitude.Value)) * lonCpr;
            }

            // Clamp
            if (latitude < -90) latitude = -90;
            if (latitude > 90) latitude = 90;
            if (longitude < -180) longitude += 360;
            if (longitude >= 180) longitude -= 360;
        }
        else if (typeCode == 19)
        {
            // Airborne velocity
            // Subtype at ME bits 5-7
            int subtype = (bytes[4] >> 2) & 0x07;

            if (subtype == 1 || subtype == 2)
            {
                // Ground speed
                int rawSpeed = ((bytes[5] & 0x03) << 8) | bytes[6];
                if (rawSpeed > 0)
                {
                    if (subtype == 1)
                    {
                        groundSpeedKnots = rawSpeed - 1;
                    }
                    else
                    {
                        // Supersonic
                        groundSpeedKnots = (rawSpeed - 1) * 4;
                    }
                }

                int rawTrack = bytes[7] & 0xFF;
                if (rawTrack > 0)
                {
                    trackAngle = (rawTrack - 1) * 360.0 / 256.0;
                }
            }
        }

        return new AdsbMessage(
            DownlinkFormat: downlinkFormat,
            Capability: capability,
            ICAO: icao,
            TypeCode: typeCode,
            Callsign: callsign,
            AltitudeFeet: altitudeFeet,
            Latitude: latitude,
            Longitude: longitude,
            GroundSpeedKnots: groundSpeedKnots,
            TrackAngle: trackAngle,
            IsValid: isValid
        );
    }

    public static bool ValidateCrc(string hexMessage)
    {
        if (string.IsNullOrEmpty(hexMessage) || hexMessage.Length < 28)
        {
            return false;
        }

        byte[] bytes = HexToBytes(hexMessage);
        return ComputeCrc(bytes) == 0;
    }

    public static string DecodeCallsign(ulong data)
    {
        var sb = new StringBuilder(8);
        // 8 characters, 6 bits each, stored MSB first in the 48-bit value
        for (int i = 7; i >= 0; i--)
        {
            int charIndex = (int)((data >> (i * 6)) & 0x3F);
            sb.Append(CallsignCharset[charIndex]);
        }

        // Trim trailing spaces
        return sb.ToString().TrimEnd();
    }

    private static uint ComputeCrc(byte[] bytes)
    {
        // Mode S CRC: process all bytes including the 3-byte trailer
        uint crc = 0;
        int totalBits = bytes.Length * 8;

        for (int i = 0; i < totalBits; i++)
        {
            int byteIdx = i / 8;
            int bitIdx = 7 - (i % 8);
            int bit = (bytes[byteIdx] >> bitIdx) & 1;

            // Check the MSB of the current CRC (bit 24 of the 25-bit shift register)
            int msb = (int)((crc >> 24) & 1);
            crc <<= 1;
            crc |= (uint)bit;

            if (msb != 0)
            {
                crc ^= CrcPolynomial;
            }
        }

        return crc & 0xFFFFFF;
    }

    private static byte[] HexToBytes(string hex)
    {
        if (hex.Length % 2 != 0)
        {
            hex = "0" + hex;
        }
        byte[] bytes = new byte[hex.Length / 2];
        for (int i = 0; i < bytes.Length; i++)
        {
            bytes[i] = Convert.ToByte(hex.Substring(i * 2, 2), 16);
        }
        return bytes;
    }

    private static double ZoneCountAV(double lat)
    {
        // Number of longitude zones at a given latitude
        if (lat < 10.47047130) return 59;
        if (lat < 14.82817437) return 58;
        if (lat < 18.18626357) return 57;
        if (lat < 21.02939493) return 56;
        if (lat < 23.54504487) return 55;
        if (lat < 25.82924707) return 54;
        if (lat < 27.93898710) return 53;
        if (lat < 29.91135686) return 52;
        if (lat < 31.77209708) return 51;
        if (lat < 33.53993436) return 50;
        if (lat < 35.22899598) return 49;
        if (lat < 36.85025108) return 48;
        if (lat < 38.41241892) return 47;
        if (lat < 39.92256684) return 46;
        if (lat < 41.38651832) return 45;
        if (lat < 42.80914012) return 44;
        if (lat < 44.19454951) return 43;
        if (lat < 45.54626723) return 42;
        if (lat < 46.86733252) return 41;
        if (lat < 48.16039128) return 40;
        if (lat < 49.42776439) return 39;
        if (lat < 50.67150166) return 38;
        if (lat < 51.89342469) return 37;
        if (lat < 53.09516153) return 36;
        if (lat < 54.27817472) return 35;
        if (lat < 55.44378444) return 34;
        if (lat < 56.59318756) return 33;
        if (lat < 57.72747354) return 32;
        if (lat < 58.84763776) return 31;
        if (lat < 59.95459277) return 30;
        if (lat < 61.04917774) return 29;
        if (lat < 62.13216659) return 28;
        if (lat < 63.20427479) return 27;
        if (lat < 64.26616523) return 26;
        if (lat < 65.31845310) return 25;
        if (lat < 66.36171008) return 24;
        if (lat < 67.39646774) return 23;
        if (lat < 68.42322022) return 22;
        if (lat < 69.44242631) return 21;
        if (lat < 70.45451075) return 20;
        if (lat < 71.45986473) return 19;
        if (lat < 72.45884545) return 18;
        if (lat < 73.45177442) return 17;
        if (lat < 74.43893416) return 16;
        if (lat < 75.42056257) return 15;
        if (lat < 76.39684391) return 14;
        if (lat < 77.36789461) return 13;
        if (lat < 78.33374083) return 12;
        if (lat < 79.29428225) return 11;
        if (lat < 80.24923213) return 10;
        if (lat < 81.19801349) return 9;
        if (lat < 82.13956981) return 8;
        if (lat < 83.07199445) return 7;
        if (lat < 83.99173563) return 6;
        if (lat < 84.89166191) return 5;
        if (lat < 85.75541621) return 4;
        if (lat < 86.53536998) return 3;
        if (lat < 87.00000000) return 2;
        return 1;
    }
}
