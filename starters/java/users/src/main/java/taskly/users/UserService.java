package taskly.users;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicLong;

import taskly.core.id.Base62Encoder;
import taskly.core.validate.Validators;

/**
 * In-memory user directory.
 *
 * Every cross-cutting concern here is borrowed from taskly.core rather than
 * reimplemented: id generation goes through {@link Base62Encoder#encode(long)}
 * and both fields are checked through {@link Validators}.
 */
public final class UserService {

    private final Map<String, User> byId = new LinkedHashMap<>();
    private final AtomicLong sequence = new AtomicLong(1);

    public User create(String name, String email) {
        String validName = Validators.requireNonEmpty(name, "name");
        String validEmail = Validators.requireEmail(email);
        String id = Base62Encoder.encode(sequence.getAndIncrement());
        User user = new User(id, validName, validEmail);
        byId.put(id, user);
        return user;
    }

    public Optional<User> get(String id) {
        return Optional.ofNullable(byId.get(id));
    }
}
