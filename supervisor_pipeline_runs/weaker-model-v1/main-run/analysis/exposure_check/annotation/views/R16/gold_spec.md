# Run R16: the injected fault (answer key for questions Q1–Q3)

- Gold method (contains the injected omission): `org.apache.commons.codec.net.URLCodec::decodeOctets`
- Gold file in the workspace: `src/java/org/apache/commons/codec/net/URLCodec.java` (lines 152–168)
- Method the failing test calls (facade): `org.apache.commons.codec.binary.Base64::decodeBase64`
- Failing test: `org.apache.commons.codec.binary.Base64Test::testUUID`
- Text removed from the gold (the omission): `int value = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/".indexOf(base64Data[i]);             if (value < 0) {                 value = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_".indexOf(base64Data[i]);             }`
- The same place in the variant now reads: `int value = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/".indexOf(base64Data[i]);`

Gold method as the agent's workspace has it (lines marked >> are the edited region, the 'faulty line'):
```java
  152        public static int decodeOctets(byte[] base64Data, byte[] octets) {
  153            int bits = 0;
  154            int bitCount = 0;
  155            int pos = 0;
  156            for (int i = 0; i < base64Data.length && base64Data[i] != '='; i++) {
  157 >>             int value = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/".indexOf(base64Data[i]);
  158                if (value >= 0) {
  159                    bits = (bits << 6) | value;
  160                    bitCount += 6;
  161                    if (bitCount >= 8) {
  162                        bitCount -= 8;
  163                        octets[pos++] = (byte) (bits >> bitCount);
  164                    }
  165                }
  166            }
  167            return pos;
  168        }
```
