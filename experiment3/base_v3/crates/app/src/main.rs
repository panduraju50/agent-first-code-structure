use notifier::Notifier;
use tasks::TaskStore;
use users::UserStore;

fn main() {
    let mut users = UserStore::new();
    let mut tasks = TaskStore::new();
    let mut notifier = Notifier::new();

    let alice = users.create("alice@example.com").expect("valid email");
    let task = tasks.create("p1", "write the report").expect("valid title");
    tasks.assign(&task.id, &alice.id).expect("task exists");
    let note = notifier.send(&alice.id, &format!("assigned: {}", task.title), 0);

    println!("user {} task {} note {}", alice.id, task.id, note.reference);
}
