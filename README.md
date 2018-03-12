A utility that extracts MozReview patch data as a static HTML directory.

Extracted patches are written out as a HTML directory tree.

## Usage

Run `python migrate.py --help` for detailed usage instructions.

## Output

**NOTE: Do not modify the output directory between application runs!**

When the script is run with `--update-inplace` it will scan the output
directory contents to avoid re-downloading existing patches.  Modifying the 
output directory contents may break this behaviour.

### Example output

```
$ python migrate.py 169494..169498
Outputting files to directory 'site'
Rate-limiting to 1.0 seconds between requests
...

$ tree site/
site/
├── 169494
│   ├── index.html
│   ├── r169494-diff1.patch
│   ├── r169494-diff2.patch
│   ├── r169494-diff3.patch
│   └── r169494-diff4.patch
├── 169496
│   ├── index.html
│   ├── r169496-diff1.patch
│   ├── r169496-diff2.patch
│   ├── r169496-diff3.patch
│   └── r169496-diff4.patch
└── 169498
    ├── index.html
    ├── r169498-diff1.patch
    ├── r169498-diff2.patch
    ├── r169498-diff3.patch
    └── r169498-diff4.patch
```
