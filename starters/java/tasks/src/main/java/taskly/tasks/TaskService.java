package taskly.tasks;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.NoSuchElementException;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicLong;

import taskly.core.id.Base62Encoder;
import taskly.core.validate.Validators;

/**
 * In-memory task list.
 *
 * Id generation and title validation are both borrowed from taskly.core —
 * this module never redefines either. Assignment takes a plain String id so
 * this module has no import from taskly.users.
 */
public final class TaskService {

    private final Map<String, Task> byId = new LinkedHashMap<>();
    private final AtomicLong sequence = new AtomicLong(1);

    public Task create(String title) {
        String validTitle = Validators.requireNonEmpty(title, "title");
        String id = Base62Encoder.encode(sequence.getAndIncrement());
        Task task = new Task(id, validTitle, null);
        byId.put(id, task);
        return task;
    }

    public List<Task> list() {
        return Collections.unmodifiableList(new ArrayList<>(byId.values()));
    }

    public Task assign(String taskId, String assigneeId) {
        Task existing = byId.get(taskId);
        if (existing == null) {
            throw new NoSuchElementException("no such task: " + taskId);
        }
        String validAssigneeId = Validators.requireNonEmpty(assigneeId, "assigneeId");
        Task updated = existing.withAssignee(validAssigneeId);
        byId.put(taskId, updated);
        return updated;
    }

    public Optional<Task> get(String id) {
        return Optional.ofNullable(byId.get(id));
    }
}
