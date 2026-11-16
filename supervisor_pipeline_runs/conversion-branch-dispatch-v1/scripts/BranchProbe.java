import org.apache.commons.lang3.BitField;
import org.apache.commons.lang3.Conversion;
import org.apache.commons.lang3.builder.Folding;

/** Local two-branch probe: selector mapping, alternate (narrow) branch against the untouched Conversion oracles, trigger values. */
public class BranchProbe {
    public static void main(final String[] args) {
        System.out.println("sel32=" + Folding.forWidth(32).getClass().getSimpleName());
        System.out.println("sel16=" + Folding.forWidth(16).getClass().getSimpleName());
        System.out.println("sel8=" + Folding.forWidth(8).getClass().getSimpleName());
        final short[] s = {0x1234, (short) 0x9ABC, 0x5678};
        final int[] si = {0x1234, 0x9ABC, 0x5678};
        final long[] inits = {0L, 0x123456789ABCDEF0L, -1L};
        final int[][] cases16 = {{0, 0, 2}, {1, 8, 2}, {0, 16, 3}, {2, 40, 1}, {0, 4, 2}};
        boolean ok16 = true; int n16 = 0;
        for (final long init : inits) {
            for (final int[] c : cases16) {
                final long o = Conversion.shortArrayToLong(s, c[0], init, c[1], c[2]);
                final int[] run = new int[c[2]]; System.arraycopy(si, c[0], run, 0, c[2]);
                final long w = BitField.widen(run, init, c[1], 16, 0xffffL);
                final long n = Folding.NARROW.fold(toLongs(run, 0xffffL), init, c[1], 16, 0xffffL);
                ok16 &= (o == w) && (o == n); n16++;
            }
        }
        System.out.println("narrow16_matches_oracle=" + ok16 + " cases=" + n16);
        final byte[] b = {(byte) 0xC1, (byte) 0xF0, (byte) 0xF1, (byte) 0xCD};
        final int[] bi = {0xC1, 0xF0, 0xF1, 0xCD};
        final int[][] cases8 = {{0, 0, 4}, {1, 8, 2}, {0, 24, 3}, {2, 48, 2}, {0, 3, 1}};
        boolean ok8 = true; int n8 = 0;
        for (final long init : inits) {
            for (final int[] c : cases8) {
                final long o = Conversion.byteArrayToLong(b, c[0], init, c[1], c[2]);
                final int[] run = new int[c[2]]; System.arraycopy(bi, c[0], run, 0, c[2]);
                final long w = BitField.widen(run, init, c[1], 8, 0xffL);
                ok8 &= (o == w); n8++;
            }
        }
        System.out.println("narrow8_matches_oracle=" + ok8 + " cases=" + n8);
        final int[] src = {0xCDF1F0C1, 0x0F123456, 0x78000000};
        System.out.println("trigger1=" + Long.toHexString(Conversion.intArrayToLong(src, 1, 0L, 8, 1)));
        System.out.println("trigger2=" + Long.toHexString(Conversion.intArrayToLong(src, 0, 0x123456789ABCDEF0L, 16, 1)));
        System.out.println("standard_direct=" + Long.toHexString(Folding.STANDARD.fold(new long[] {0x0F123456L}, 0L, 8, 32, 0xffffffffL)));
        System.out.println("narrow_on_word=" + Long.toHexString(Folding.NARROW.fold(new long[] {0x0F123456L}, 0L, 8, 32, 0xffffffffL)));
        System.out.println("widen32_selected=" + Long.toHexString(BitField.widen(new int[] {0x0F123456}, 0L, 8, 32, 0xffffffffL)));
    }

    private static long[] toLongs(final int[] run, final long field) {
        final long[] r = new long[run.length];
        for (int i = 0; i < run.length; i++) { r[i] = run[i] & field; }
        return r;
    }
}
