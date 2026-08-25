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
import java.util.stream.Collectors;
import java.util.stream.Stream;

/**
 * Design D boundary enforcer.
 *
 * javac + module-info.java already give us a COMPILER-enforced graph: a
 * domain module that does not "requires" another domain module cannot even
 * import its packages — that half of Design D is verified for free every
 * time `javac` runs (see build.sh). What javac does NOT stop is someone
 * quietly ADDING the forbidden "requires" line, or reimplementing a core
 * primitive inside a domain module instead of importing it. This tool
 * checks those two "should not, but nothing physically stops it" rules:
 *
 *   1. No domain module-info.java may require another domain module.
 *      (taskly.users may require taskly.core, never taskly.tasks, and
 *       vice versa. taskly.app, the composition root, is exempt.)
 *
 *   2. No file outside taskly.core may define a base62 encoder or a
 *      duplicate of the Validators primitives (requireEmail / requireNonEmpty).
 *
 * Usage: java tools.BoundaryCheck <repo-root>
 * Exit code 0 = clean, 1 = violations found (prints each one).
 */
public final class BoundaryCheck {

    private static final Map<String, String> DOMAIN_MODULES = new LinkedHashMap<>();

    static {
        DOMAIN_MODULES.put("users", "taskly.users");
        DOMAIN_MODULES.put("tasks", "taskly.tasks");
    }

    private static final String CORE_MODULE = "taskly.core";

    private static final Pattern REQUIRES_LINE =
            Pattern.compile("requires\\s+(?:static\\s+|transitive\\s+)*([\\w.]+)\\s*;");

    // Definition patterns for the primitives that must live only in core.
    // All of these are matched AFTER stripComments() has removed // and
    // /* */ text, so a javadoc example or explanatory comment mentioning
    // "requires taskly.users;" or a method name can never trip these —
    // only actual code does.
    private static final Pattern BASE62_CLASS_DEF =
            Pattern.compile("\\bclass\\s+\\w*[Bb]ase62\\w*");
    // The exact alphabet used by taskly.core's encoder, and modulo/divide-by-62
    // arithmetic, are the two concrete tells of a re-implemented base62 codec —
    // far more precise than matching any identifier containing "Base62".
    private static final Pattern BASE62_ALPHABET_LITERAL =
            Pattern.compile(Pattern.quote(
                    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"));
    private static final Pattern BASE62_ARITHMETIC =
            Pattern.compile("[%/]\\s*62\\b");
    private static final Pattern REQUIRE_EMAIL_DEF =
            Pattern.compile("\\bString\\s+requireEmail\\s*\\(");
    private static final Pattern REQUIRE_NON_EMPTY_DEF =
            Pattern.compile("\\bString\\s+requireNonEmpty\\s*\\(");

    public static void main(String[] args) throws IOException {
        Path root = Paths.get(args.length > 0 ? args[0] : ".").toAbsolutePath().normalize();
        List<String> violations = new ArrayList<>();

        checkDomainRequires(root, violations);
        checkNoDuplicatePrimitives(root, violations);

        if (violations.isEmpty()) {
            System.out.println("boundary-check: OK — no domain-to-domain edges, "
                    + "no duplicate primitives outside " + CORE_MODULE);
            return;
        }

        System.out.println("boundary-check: FAILED with " + violations.size() + " violation(s):");
        for (String v : violations) {
            System.out.println("  - " + v);
        }
        System.exit(1);
    }

    /** Rule 1: a domain module-info.java must never require another domain module. */
    private static void checkDomainRequires(Path root, List<String> violations) throws IOException {
        for (Map.Entry<String, String> entry : DOMAIN_MODULES.entrySet()) {
            String dir = entry.getKey();
            String ownModule = entry.getValue();
            Path moduleInfo = root.resolve(dir).resolve("src/main/java/module-info.java");
            if (!Files.exists(moduleInfo)) {
                violations.add("missing module-info.java for domain '" + dir + "' at " + moduleInfo);
                continue;
            }
            String text = stripComments(Files.readString(moduleInfo));
            Matcher m = REQUIRES_LINE.matcher(text);
            while (m.find()) {
                String required = m.group(1);
                if (required.equals("java.base")) {
                    continue;
                }
                boolean isOtherDomain = DOMAIN_MODULES.values().stream()
                        .anyMatch(mod -> mod.equals(required) && !mod.equals(ownModule));
                if (isOtherDomain) {
                    violations.add(ownModule + " requires " + required
                            + " — domain-to-domain edges are forbidden ("
                            + root.relativize(moduleInfo) + ")");
                }
            }
        }
    }

    /** Rule 2: no base62 / validator primitive may be (re)defined outside core. */
    private static void checkNoDuplicatePrimitives(Path root, List<String> violations) throws IOException {
        Path coreDir = root.resolve("core");
        List<Path> javaFiles;
        try (Stream<Path> walk = Files.walk(root)) {
            javaFiles = walk
                    .filter(p -> p.toString().endsWith(".java"))
                    .filter(p -> !p.startsWith(coreDir))
                    .filter(p -> !p.toString().contains(FILE_SEP + "out" + FILE_SEP)
                            && !p.toString().contains(FILE_SEP + "out-test" + FILE_SEP)
                            && !p.toString().contains(FILE_SEP + "tools" + FILE_SEP))
                    .collect(Collectors.toList());
        }

        for (Path file : javaFiles) {
            String text = stripComments(Files.readString(file));
            String relative = root.relativize(file).toString();
            if (BASE62_CLASS_DEF.matcher(text).find()) {
                violations.add(relative + " defines a class named like a base62 encoder outside taskly.core");
            }
            if (BASE62_ALPHABET_LITERAL.matcher(text).find()) {
                violations.add(relative + " duplicates taskly.core's base62 alphabet literal");
            }
            if (BASE62_ARITHMETIC.matcher(text).find()) {
                violations.add(relative + " performs base62-style (% 62 or / 62) arithmetic outside taskly.core");
            }
            if (REQUIRE_EMAIL_DEF.matcher(text).find()) {
                violations.add(relative + " redefines requireEmail(...) outside taskly.core");
            }
            if (REQUIRE_NON_EMPTY_DEF.matcher(text).find()) {
                violations.add(relative + " redefines requireNonEmpty(...) outside taskly.core");
            }
        }
    }

    /** Strips line comments and block comments so javadoc examples never look like code. */
    private static String stripComments(String text) {
        String noBlock = Pattern.compile("/\\*.*?\\*/", Pattern.DOTALL).matcher(text).replaceAll("");
        return Pattern.compile("//[^\\n]*").matcher(noBlock).replaceAll("");
    }

    private static final String FILE_SEP = java.io.File.separator;

    private BoundaryCheck() {
    }
}
