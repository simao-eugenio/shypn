# Graceful Keyboard Interrupt Handling

**Date**: October 8, 2025  
**Change**: Added proper KeyboardInterrupt (Ctrl+C) handling

---

## Issue

When user pressed Ctrl+C to interrupt the application, Python would display a full traceback:

```
^CTraceback (most recent call last):
  File "/home/simao/projetos/shypn/src/shypn.py", line 546, in <module>
    main()
  File "/home/simao/projetos/shypn/src/shypn.py", line 542, in main
    app.run(argv)
  File "/usr/lib/python3/dist-packages/gi/overrides/Gio.py", line 40, in run
    with register_sigint_fallback(self.quit):
  File "/usr/lib/python3.12/contextlib.py", line 144, in __exit__
    next(self.gen)
  File "/usr/lib/python3/dist-packages/gi/_ossighelper.py", line 237, in register_sigint_fallback
    signal.default_int_handler(signal.SIGINT, None)
KeyboardInterrupt
```

This is technically correct but looks unprofessional and scary to users.

---

## Solution

Added try-except blocks at two levels:

### 1. In `main()` function

```python
def main(argv=None):
    # ... application setup ...
    
    try:
        return app.run(argv)
    except KeyboardInterrupt:
        print("\n✋ Application interrupted by user (Ctrl+C)")
        return 0
```

### 2. In `if __name__ == '__main__'` block

```python
if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code if exit_code is not None else 0)
    except KeyboardInterrupt:
        print("\n✋ Shutting down gracefully...")
        sys.exit(0)
```

---

## Result

Now when user presses Ctrl+C:

**Before**:
```
^CTraceback (most recent call last):
  File "/home/simao/projetos/shypn/src/shypn.py", line 546, in <module>
    main()
  [... 10 more lines of traceback ...]
KeyboardInterrupt
```

**After**:
```
^C
✋ Application interrupted by user (Ctrl+C)
```

Much cleaner! ✨

---

## Benefits

1. **User-friendly**: No scary traceback for normal Ctrl+C
2. **Professional**: Clean exit message
3. **Graceful**: Proper exit code (0) returned
4. **Dual-level protection**: Catches interrupt at both main() and top level
5. **Maintains GTK behavior**: Doesn't interfere with GTK's own signal handling

---

## Technical Details

- **KeyboardInterrupt** is a built-in Python exception raised when user presses Ctrl+C
- **Exit code 0** indicates clean shutdown (success)
- **GTK signal handling** (`register_sigint_fallback`) still works properly
- **No resource leaks**: Python and GTK both clean up normally

---

## Notes

- This only affects **terminal-launched** applications
- Applications launched from desktop shortcuts don't show these messages
- The handling is **transparent** to the GTK main loop
- User can still force-kill with `kill -9` if needed

---

## Related

This improvement complements the simulation timing system by providing:
- Clean development experience
- Professional error handling
- Better UX for developers testing the app

**Status**: ✅ Implemented and tested
