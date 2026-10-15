import com.sun.source.tree.ClassTree;
import com.sun.source.tree.CompilationUnitTree;
import com.sun.source.tree.MethodTree;
import com.sun.source.util.JavacTask;
import com.sun.source.util.SourcePositions;
import com.sun.source.util.TreePathScanner;
import com.sun.source.util.Trees;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.Deque;
import java.util.List;
import javax.tools.JavaCompiler;
import javax.tools.JavaFileObject;
import javax.tools.StandardJavaFileManager;
import javax.tools.ToolProvider;

public final class JavaMethodCatalog {
    private static final class Entry {
        String className;
        String method;
        String file;
        long lineStart;
        long lineEnd;
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 1) {
            throw new IllegalArgumentException("Expected repository root");
        }
        Path root = Path.of(args[0]).toAbsolutePath().normalize();
        List<Path> files = new ArrayList<>();
        try (var paths = Files.walk(root)) {
            paths.filter(Files::isRegularFile)
                    .filter(path -> path.toString().endsWith(".java"))
                    .filter(path -> isProduction(root.relativize(path)))
                    .forEach(files::add);
        }
        files.sort(Comparator.comparing(Path::toString));
        List<Entry> entries = new ArrayList<>();
        for (Path file : files) {
            parseFile(root, file, entries);
        }
        entries.sort(Comparator.comparing((Entry entry) -> entry.className)
                .thenComparing(entry -> entry.method)
                .thenComparing(entry -> entry.file)
                .thenComparingLong(entry -> entry.lineStart));
        System.out.println(toJson(entries));
    }

    private static boolean isProduction(Path relative) {
        String normalized = relative.toString().replace('\\', '/');
        return normalized.startsWith("source/")
                || normalized.startsWith("src/main/")
                || normalized.startsWith("src/java/")
                || normalized.startsWith("gson/src/main/")
                || normalized.startsWith("src/com/");
    }

    private static void parseFile(Path root, Path file, List<Entry> entries) throws IOException {
        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        if (compiler == null) {
            throw new IllegalStateException("A JDK is required to build the Java method catalog");
        }
        try (StandardJavaFileManager manager = compiler.getStandardFileManager(null, null, StandardCharsets.UTF_8)) {
            Iterable<? extends JavaFileObject> units = manager.getJavaFileObjects(file.toFile());
            JavacTask task = (JavacTask) compiler.getTask(null, manager, diagnostic -> {}, List.of("-proc:none"), null, units);
            Trees trees = Trees.instance(task);
            SourcePositions positions = trees.getSourcePositions();
            for (CompilationUnitTree unit : task.parse()) {
                String packageName = unit.getPackageName() == null ? "" : unit.getPackageName().toString();
                new TreePathScanner<Void, Void>() {
                    private final Deque<String> classes = new ArrayDeque<>();

                    @Override
                    public Void visitClass(ClassTree node, Void unused) {
                        String name = node.getSimpleName().toString();
                        if (name.isEmpty()) {
                            return super.visitClass(node, unused);
                        }
                        classes.addLast(name);
                        super.visitClass(node, unused);
                        classes.removeLast();
                        return null;
                    }

                    @Override
                    public Void visitMethod(MethodTree node, Void unused) {
                        if (classes.isEmpty()) return null;
                        Entry entry = new Entry();
                        String nestedName = String.join("$", classes);
                        entry.className = packageName.isEmpty() ? nestedName : packageName + "." + nestedName;
                        String methodName = node.getName().toString();
                        entry.method = "<init>".equals(methodName) ? classes.getLast() : methodName;
                        entry.file = root.relativize(file).toString().replace('\\', '/');
                        long start = positions.getStartPosition(unit, node);
                        long end = positions.getEndPosition(unit, node);
                        entry.lineStart = start < 0 ? -1 : unit.getLineMap().getLineNumber(start);
                        entry.lineEnd = end < 0 ? -1 : unit.getLineMap().getLineNumber(end);
                        entries.add(entry);
                        return super.visitMethod(node, unused);
                    }
                }.scan(unit, null);
            }
        }
    }

    private static String toJson(List<Entry> entries) {
        StringBuilder json = new StringBuilder("{\"schema_version\":\"d4j-java-method-catalog/v2\",\"methods\":[");
        for (int index = 0; index < entries.size(); index++) {
            if (index > 0) json.append(',');
            Entry entry = entries.get(index);
            json.append("{\"class\":\"").append(escape(entry.className))
                    .append("\",\"method\":\"").append(escape(entry.method))
                    .append("\",\"qualified\":\"").append(escape(entry.className + "::" + entry.method))
                    .append("\",\"file\":\"").append(escape(entry.file))
                    .append("\",\"source_type\":\"production\",\"line_start\":").append(entry.lineStart)
                    .append(",\"line_end\":").append(entry.lineEnd).append('}');
        }
        return json.append("]}").toString();
    }

    private static String escape(String value) {
        return value.replace("\\", "\\\\").replace("\"", "\\\"")
                .replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t");
    }
}
