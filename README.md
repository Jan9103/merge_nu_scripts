# Merge Nu Scripts

does exactly what the name says.

since both `nu -c ast` and `nu --ide-ast` do not retain all important information
this is for now regex-based and therefore limited.

## Limitations:

* `use` and `export use` have to be the first command in a line or stand directly after a `;`.
  * if either condition is met within a (multiline-) string it will get screwed up.
* `$NU_LIB_DIRS` are not supported. use relative imports instead.
* `source` is not supported.
* The conversion-script should be able to run on windows, but it has never been tested.

## Usage:

`python3 merge_nu_files.py main_file.nu`

## How does it work?

A few steps to understand why it does what:

1. FACT: `use` works the same on both files and in-file defined modules
1. SOLUTION: therefore this script just wraps files with `export module NAME {}`
1. PROBLEM: `/` can't be included in the name of a in-file module and duplicate names can exist with files.
1. SOLUTION: therefore this script generates randomised names for modules of the converted files
1. PROBLEM: the names of the modules changed
1. SOLUTION: since the name has changed we have to replace it wherever it has been importing (using regex)
1. PROBLEM: `use foo.nu` now no longer offers `foo test`, but instead `RANDOM_TEXT test` due to the randomisation
1. SOLUTION: `use foo` and `use abc foo` both result in `foo`, therefore just add a submodule with the original name below the generated name

