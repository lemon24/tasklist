Markdown-y is better.

There's support for named lists:

```markdown
# today

- unchecked item
- [ ] also unchecked item
- [x] checked item
- item with no priority
- ( ) also item with no priority
- (a) item with high priority
- [x] (b) checked with prio

# later

- something
- another thing

# parking lot

- idea I had yesterday

# trickle

- think about what you've done

```

Operations on the file are done with chained commands.

Morning scrub:

```bash
tasklist --file tasklist.md \
    move later today \
    set today --no-checked --priority none \
    edit today \
        --edit-priorities \
        --bind-new \
        --bind-remove \
        --bind-move later l \
    copy trickle today --priority high \
    sort today
```

Marking stuff as done during the day:

```bash
tasklist --file tasklist.md \
    edit today \
        --edit-checked \
        --bind-new
```

Evening scrub:

```bash
tasklist --file tasklist.md \
    edit today \
        --show-checked \
        --show-priorities \
        --bind-new \
        --bind-remove \
    move today later \
    move 'parking lot' later \
    set later --no-checked --priority none \
    sort later
```

