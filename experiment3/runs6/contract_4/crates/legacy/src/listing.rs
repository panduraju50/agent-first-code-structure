//! Older listing helpers. Pages here are 0-indexed.

pub fn take_page<T>(items: &[T], page: usize, size: usize) -> &[T] {
    if size == 0 {
        return &[];
    }
    let start = page * size;
    if start >= items.len() {
        return &[];
    }
    &items[start..usize::min(start + size, items.len())]
}
