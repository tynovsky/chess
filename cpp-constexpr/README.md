# C++ variant played in Compile Time

This is C++ variant that can be played fully on compile time. After compilation, compiler knows the result(s) and saves only instructions needed for printing the strings such as "Checkmate!" etc.

## Compiling

For this to work it requires at least C++17 with following args:

```
-std=c++17 -O3 -fconstexpr-steps=351843720
```

![Assembly](assembly.png?raw=true)

## Warning

If you are compiling multiple games (more than 2 usually), it takes **a lot of time**.

If you are brave enough tho & have powerful machine, feel free to uncomment code in the main function that will allow to play specified amount (`N`) of games.
