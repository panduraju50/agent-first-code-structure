package taskly.users;

/**
 * Plain-Java test (no framework, no network install): a main() with checks
 * that exits non-zero on the first failure. Run via test.sh / `make test`.
 */
public final class UserServiceTest {

    private static int failures = 0;

    public static void main(String[] args) {
        createAssignsBase62IdAndStoresUser();
        createRejectsInvalidEmail();
        createRejectsBlankName();
        getReturnsEmptyForUnknownId();

        if (failures > 0) {
            System.out.println("FAIL: " + failures + " check(s) failed in UserServiceTest");
            System.exit(1);
        }
        System.out.println("PASS: UserServiceTest");
    }

    private static void createAssignsBase62IdAndStoresUser() {
        UserService service = new UserService();
        User user = service.create("Ada Lovelace", "ada@example.com");
        check("id is non-empty", user.id() != null && !user.id().isEmpty());
        check("name preserved", user.name().equals("Ada Lovelace"));
        check("email preserved", user.email().equals("ada@example.com"));
        check("get roundtrips", service.get(user.id()).orElseThrow().equals(user));
    }

    private static void createRejectsInvalidEmail() {
        UserService service = new UserService();
        try {
            service.create("Grace Hopper", "not-an-email");
            check("invalid email should have thrown", false);
        } catch (IllegalArgumentException expected) {
            check("invalid email throws IllegalArgumentException", true);
        }
    }

    private static void createRejectsBlankName() {
        UserService service = new UserService();
        try {
            service.create("   ", "grace@example.com");
            check("blank name should have thrown", false);
        } catch (IllegalArgumentException expected) {
            check("blank name throws IllegalArgumentException", true);
        }
    }

    private static void getReturnsEmptyForUnknownId() {
        UserService service = new UserService();
        check("unknown id is empty", service.get("zzz").isEmpty());
    }

    private static void check(String description, boolean condition) {
        if (condition) {
            System.out.println("  ok - " + description);
        } else {
            System.out.println("  NOT OK - " + description);
            failures++;
        }
    }
}
