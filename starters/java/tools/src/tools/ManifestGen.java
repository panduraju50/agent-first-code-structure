package tools;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Generates manifest.json (capability -> owning file, plus the module
 * dependency edges) directly from the real source tree — nobody hand-writes
 * this file. It is deterministic (no timestamps, sorted output) so that
 * running it twice against unchanged sources produces byte-identical JSON;
 * ci.sh relies on that determinism for the manifest-drift check.
 *
 * Two things are parsed straight out of the module graph that already
 * governs compilation:
 *   - edges: "requires" lines in each module-info.java
 *   - capabilities: the first public top-level type declared in each
 *     main-source .java file, slugified from PascalCase to kebab-case
 *
 * Usage: java tools.ManifestGen <repo-root> > manifest.json
 */
public final class ManifestGen {

    // module directory name -> module name, in a fixed, meaningful order.
    private static final Map<String, String> MODULE_DIRS = new LinkedHashMap<>();

    static {
        MODULE_DIRS.put("core", "taskly.core");
        MODULE_DIRS.put("users", "taskly.users");
        MODULE_DIRS.put("tasks", "taskly.tasks");
        MODULE_DIRS.put("app", "taskly.app");
    }

    private static final Pattern REQUIRES_LINE =
            Pattern.compile("requires\\s+(?:static\\s+|transitive\\s+)*([\\w.]+)\\s*;");
    private static final Pattern EXPORTS_LINE =
            Pattern.compile("exports\\s+([\\w.]+)\\s*;");
    private static final Pattern PUBLIC_TYPE =
            Pattern.compile("public\\s+(?:final\\s+|abstract\\s+|static\\s+)*"
                    + "(?:class|interface|record|enum)\\s+(\\w+)");

    public static void main(String[] args) throws IOException {
        Path root = Paths.get(args.length > 0 ? args[0] : ".").toAbsolutePath().normalize();

        List<ModuleInfo> modules = new ArrayList<>();
        for (Map.Entry<String, String> entry : MODULE_DIRS.entrySet()) {
            modules.add(readModule(root, entry.getKey(), entry.getValue()));
        }

        List<Capability> capabilities = new ArrayList<>();
        for (ModuleInfo module : modules) {
            capabilities.addAll(findCapabilities(root, module));
        }
        // Deterministic order regardless of filesystem iteration order.
        capabilities.sort((a, b) -> a.owner.compareTo(b.owner));

        System.out.println(render(modules, capabilities));
    }

    private static ModuleInfo readModule(Path root, String dir, String name) throws IOException {
        Path moduleInfoPath = root.resolve(dir).resolve("src/main/java/module-info.java");
        // Comments are stripped first so a javadoc example (e.g. tasks'
        // module-info.java explains, in its comment, what a forbidden
        // "requires taskly.users;" line would look like) is never mistaken
        // for a real requires/exports declaration.
        String text = Files.exists(moduleInfoPath)
                ? stripComments(Files.readString(moduleInfoPath))
                : "";

        List<String> requires = new ArrayList<>();
        Matcher rm = REQUIRES_LINE.matcher(text);
        while (rm.find()) {
            if (!rm.group(1).equals("java.base")) {
                requires.add(rm.group(1));
            }
        }

        List<String> exports = new ArrayList<>();
        Matcher em = EXPORTS_LINE.matcher(text);
        while (em.find()) {
            exports.add(em.group(1));
        }

        return new ModuleInfo(name, dir, requires, exports);
    }

    private static List<Capability> findCapabilities(Path root, ModuleInfo module) throws IOException {
        Path srcDir = root.resolve(module.dir).resolve("src/main/java");
        List<Capability> found = new ArrayList<>();
        if (!Files.isDirectory(srcDir)) {
            return found;
        }
        try (var walk = Files.walk(srcDir)) {
            List<Path> files = walk
                    .filter(p -> p.toString().endsWith(".java"))
                    .filter(p -> !p.getFileName().toString().equals("module-info.java"))
                    .sorted()
                    .toList();
            for (Path file : files) {
                String text = stripComments(Files.readString(file));
                Matcher m = PUBLIC_TYPE.matcher(text);
                if (m.find()) {
                    String typeName = m.group(1);
                    String owner = root.relativize(file).toString();
                    found.add(new Capability(slugify(typeName), owner, module.name));
                }
            }
        }
        return found;
    }

    /** PascalCase -> kebab-case, e.g. "Base62Encoder" -> "base62-encoder". */
    private static String slugify(String typeName) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < typeName.length(); i++) {
            char c = typeName.charAt(i);
            if (Character.isUpperCase(c)) {
                if (sb.length() > 0) {
                    sb.append('-');
                }
                sb.append(Character.toLowerCase(c));
            } else {
                sb.append(c);
            }
        }
        return sb.toString();
    }

    private static String render(List<ModuleInfo> modules, List<Capability> capabilities) {
        StringBuilder json = new StringBuilder();
        json.append("{\n");

        json.append("  \"modules\": [\n");
        for (int i = 0; i < modules.size(); i++) {
            ModuleInfo m = modules.get(i);
            json.append("    {\n");
            json.append("      \"name\": \"").append(esc(m.name)).append("\",\n");
            json.append("      \"path\": \"").append(esc(m.dir)).append("\",\n");
            json.append("      \"requires\": ").append(jsonArray(m.requires)).append(",\n");
            json.append("      \"exports\": ").append(jsonArray(m.exports)).append("\n");
            json.append("    }").append(i < modules.size() - 1 ? "," : "").append("\n");
        }
        json.append("  ],\n");

        json.append("  \"edges\": [\n");
        List<String> edgeLines = new ArrayList<>();
        for (ModuleInfo m : modules) {
            for (String required : m.requires) {
                edgeLines.add("    { \"from\": \"" + esc(m.name) + "\", \"to\": \""
                        + esc(required) + "\", \"type\": \"requires\" }");
            }
        }
        for (int i = 0; i < edgeLines.size(); i++) {
            json.append(edgeLines.get(i)).append(i < edgeLines.size() - 1 ? "," : "").append("\n");
        }
        json.append("  ],\n");

        json.append("  \"capabilities\": [\n");
        for (int i = 0; i < capabilities.size(); i++) {
            Capability c = capabilities.get(i);
            json.append("    {\n");
            json.append("      \"capability\": \"").append(esc(c.capability)).append("\",\n");
            json.append("      \"owner\": \"").append(esc(c.owner)).append("\",\n");
            json.append("      \"module\": \"").append(esc(c.module)).append("\"\n");
            json.append("    }").append(i < capabilities.size() - 1 ? "," : "").append("\n");
        }
        json.append("  ]\n");

        json.append("}");
        return json.toString();
    }

    private static String jsonArray(List<String> values) {
        if (values.isEmpty()) {
            return "[]";
        }
        StringBuilder sb = new StringBuilder("[");
        for (int i = 0; i < values.size(); i++) {
            sb.append("\"").append(esc(values.get(i))).append("\"");
            if (i < values.size() - 1) {
                sb.append(", ");
            }
        }
        sb.append("]");
        return sb.toString();
    }

    private static String esc(String s) {
        return s.replace("\\", "\\\\").replace("\"", "\\\"");
    }

    private record ModuleInfo(String name, String dir, List<String> requires, List<String> exports) {
    }

    private record Capability(String capability, String owner, String module) {
    }

    /** Strips line comments and block comments so javadoc examples never look like code. */
    private static String stripComments(String text) {
        String noBlock = Pattern.compile("/\\*.*?\\*/", Pattern.DOTALL).matcher(text).replaceAll("");
        return Pattern.compile("//[^\\n]*").matcher(noBlock).replaceAll("");
    }

    private ManifestGen() {
    }
}
