# Git ignores

First test

```
rmdir /S /Q test1
mkdir test1 && cd test1 && git init
copy ..\test1.gitignore .gitignore
mkdir A
mkdir B
mkdir C
echo one > A\1.txt
echo two > A\2.cs
echo three > B\3.cs
echo four > C\4.txt
git add --dry-run .
```

Second test

```
rmdir /S /Q test2
mkdir test2 && cd test2 && git init
copy ..\test2.gitignore .gitignore
git add --dry-run .
mkdir A
mkdir A\B
echo one > A\B\1.txt
git add --dry-run .
```
