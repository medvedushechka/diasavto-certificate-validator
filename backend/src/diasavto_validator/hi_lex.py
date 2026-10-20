# Утверждённые маски из документа HI-LEX. Не расширять без согласования.
PREFIXES = (
    "4VB", "4JB", "4AB", "9TB", "4TB", "4HB", "9CB", "9NB",
    "4GB", "4RB", "4PB", "9VB", "4UB", "4CB", "4NB", "4DB",
    "9AB", "4FB", "4BB", "4ZB", "9HB", "4MB", "9DB", "9ZB",
    "1PB", "5PB", "9JB", "2HB", "5CB", "2JB", "2PB", "9RB",
    "9YB", "2KB", "9GB", "2YB", "7HB", "9BB",
)
PREFIX_SET = frozenset(PREFIXES)
def search_key(article: str) -> str:
    # Сохраняем внутренние пробелы и символы для корректного учёта исключений.
    return article.replace("\u00a0", " ").strip(" ").translate(
        str.maketrans("abcdefghijklmnopqrstuvwxyz", "ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    )
