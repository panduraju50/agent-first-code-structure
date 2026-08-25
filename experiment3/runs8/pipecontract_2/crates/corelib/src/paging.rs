//! Slicing a list into pages. Pages are 1-indexed.

pub fn page_slice<T>(items: &[T], page: usize, size: usize) -> &[T] {
    if size == 0 || page == 0 {
        return &[];
    }
    let start = (page - 1) * size;
    if start >= items.len() {
        return &[];
    }
    let end = usize::min(start + size, items.len());
    &items[start..end]
}

pub fn page_count(total: usize, size: usize) -> usize {
    if size == 0 {
        return 0;
    }
    total.div_ceil(size)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn first_page_is_page_one() {
        let v = [1, 2, 3, 4, 5];
        assert_eq!(page_slice(&v, 1, 2), &[1, 2]);
        assert_eq!(page_slice(&v, 3, 2), &[5]);
    }
}
