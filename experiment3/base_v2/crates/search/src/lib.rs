use corelib::paging::page_slice;

pub fn matches(haystack: &str, needle: &str) -> bool {
    haystack.to_lowercase().contains(&needle.to_lowercase())
}

pub fn page<'a, T>(items: &'a [T], page_no: usize, size: usize) -> &'a [T] {
    page_slice(items, page_no, size)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn finds_and_pages() {
        assert!(matches("Write Docs", "docs"));
        let v = [1, 2, 3];
        assert_eq!(page(&v, 1, 2), &[1, 2]);
    }
}
