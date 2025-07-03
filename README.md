# 🧰 Goodibox

A collection of heterogeneous Python utilities for common programming tasks. Everything I found myself copy-pasting over and over again until I got sick of it.

## Features

- **Zero dependencies**: pure Python standard library
- **Type-safe**: fully type annotated including generics
- **Production-ready**: used in real projects
- **Copy-friendly**: take what you need, leave what you don't

## Examples

### Date and Time Operations

```python
# Convert ISO string to date
>>> to_date("2023-12-25")
datetime.date(2023, 12, 25)

# Get date from N days ago
>>> days_ago(7)
datetime.date(2024, 1, 9)  # assuming today is 2024-01-16

# Generate date range
>>> list(daterange(date(2024, 1, 1), date(2024, 1, 4)))
[
    datetime.date(2024, 1, 1),
    datetime.date(2024, 1, 2),
    datetime.date(2024, 1, 3),
]
```

### Data Structure Utilities

```python
# Invert a dictionary
>>> inverse_mapping({"a": 1, "b": 2, "c": 1})
{1: "a", 2: "b"}

# Filter dictionary by keys
>>> dict(filter_by_keys({"apple": 5, "banana": 3, "cherry": 8}, lambda k: k.startswith("a")))
{"apple": 5}

# Create ordered dictionary with convenient syntax
>>> ordered_dict("first", 1, "second", 2, "third", 3)
OrderedDict([('first', 1), ('second', 2), ('third', 3)])
```

### String and Text Processing

```python
# Create quoted comma-separated list
>>> quoted_comma_separated(["apple", "banana", "cherry"])
"'apple', 'banana', 'cherry'"

# Join with formatting template
>>> join_format(" OR ", "tag = '{}'", ["blue", "red"])
"tag = 'blue' OR tag = 'red'"

# Remove blank lines from multiline string
>>> remove_blank_lines("line1\n\n   \nline2\n\nline3")
"line1\nline2\nline3"
```

### File I/O Operations

```python
# Read JSON from file
>>> read_json_from_file("config.json")
{"name": "myapp", "version": "1.0.0"}

# Read JSON Lines file
>>> read_jsonlines_from_file("data.jsonl")
[{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
```

### Debugging and Logging

```python
# Log function arguments (decorator)
@log_arguments
def process_data(items, threshold=0.5):
    pass

# Log execution time (decorator)
log_exec_time = ExecutionTimeLogger(post_msg="{func} took {secs}s")

@log_exec_time(level=DEBUG)
def expensive_operation():
    time.sleep(2)
    return "done"
```

### Error Handling and Control Flow

```python
# Safely execute code that might fail
>>> suppress(lambda: int("not_a_number"))
None

# Conditionally append to iterable
>>> list(append_if("maybe", ["always", "present"]))
["always", "present", "maybe"]

# Conditionally prepend to iterable
>>> list(prepend_if(None, ["item1", "item2"])
["item1", "item2"]
```

### Hashing

```python
# Generate MD5 hash
>>> hex_hash("hello world")
"5d41402abc4b2a76b9719d911017c592"
```
