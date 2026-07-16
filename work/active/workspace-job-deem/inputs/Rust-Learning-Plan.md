# Rust Learning Plan — Absolute Beginner → Good Intermediate

> **Purpose:** A complete, book-anchored roadmap from zero Rust knowledge to confident intermediate. Linear progression — unlike the Python Roadmap (which is symptom-driven), Rust's concepts build strictly on each other and must be learned in order. **Don't skip ahead.** Ownership → Borrowing → Lifetimes is an unbreakable dependency chain.
>
> **Primary books (local):**
> - *The Rust Programming Language* (The Book) — `Plans/Programming/rust/Rust/books/The-Rust-Programming-Language.epub` | free online at https://doc.rust-lang.org/book/ — THE canonical reference; Rust 2024 edition (3rd ed).
> - *Comprehensive Rust* (Google Android team) — `Plans/Programming/rust/Rust/books/Comprehensive-Rust-Google.pdf` | free online at https://google.github.io/comprehensive-rust/ — excellent 4-day accelerated treatment; use as a parallel reference and for exercises.
>
> **Recommended purchase (deep understanding):**
> - *Programming Rust* 2nd ed — Jim Blandy, Jason Orendorff, Leonora Tindall (O'Reilly) — THE book for "why does Rust work this way?"; goes deeper than The Book on every topic; buy it. Available via O'Reilly Learning subscription.
> - *Rust in Action* — Tim McNamara (Manning) — project-driven; systems-level intuition. Good after Phase 2.
>
> **Exercises:** [Rustlings](https://github.com/rust-lang/rustlings) (100 guided exercises, installed as a cargo project — the Rust-native equivalent of pen-and-paper drills). Clone once, use throughout.
>
> **C++ background note:** Your C++ muscle memory is both an asset and a trap. Memory management intuition transfers. The instinct to manually control lifetimes will fight the borrow checker. Let the compiler teach you — don't fight it; read its error messages like documentation.
>
> *Created KW 24 (Jun 13, 2026). Book chapters verified against Rust 2024 / The Book 3rd ed.*

---

## Phase map

| Phase | Steps | Focus | Time estimate |
|---|---|---|---|
| **0** | Setup | Tooling | 30 min |
| **1** | 1–7 | Ownership, types, enums, errors | 2–3 weeks |
| **2** | 8–12 | Traits, generics, lifetimes, iterators, smart pointers | 3–4 weeks |
| **3** | 13–17 | Concurrency, async, ecosystem, idiomatic Rust | 3–4 weeks |
| **Advanced** | 18–20 | Pull-based: unsafe, macros, type-level tricks | ongoing |

---

## Prerequisite reading order (The Book chapters)

The Book: **2 → 3 → 4 → 5 → 6 → 8 → 9 → 10 → 11 → 13 → 14 → 15 → 16 → 17 → 18 → 19** (Ch 7 and 12 interleaved as shown in steps). Don't read linearly; follow the steps below — each step tells you exactly which sections to read.

---

## Phase 0 — Tooling & Hello World

*Time: 30 min. Do this once, never repeat.*

### Setup
- **Install Rust:** `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh` — installs `rustc`, `cargo`, `rustup` (the version manager).
- **IDE:** VS Code + [rust-analyzer](https://marketplace.visualstudio.com/items?itemName=rust-lang.rust-analyzer) extension. Rust-analyzer is non-optional — it catches borrow-checker errors in real time, shows type inferences inline, and explains compiler errors. No other editor setup even comes close.
- **Offline Book:** `rustup doc --book` opens The Book locally in your browser (always in sync with your installed compiler).
- **Offline std docs:** `rustup doc --std` opens the standard library docs offline.
- **Clone Rustlings:** `cargo install rustlings && rustlings init` — creates a local directory of 100 exercises sorted by topic. Run `rustlings` in that directory; it watches your file and re-runs the exercise on save.

### First program
- **The Book:** Ch 1 (Installation, Hello World, Hello Cargo) — takes ~20 min, do it all.
- **Key cargo commands:** `cargo new`, `cargo build`, `cargo run`, `cargo check` (type-checks without building — fast), `cargo test`, `cargo doc --open`.
- **Done when:** `cargo new hello && cd hello && cargo run` prints "Hello, world!" and you understand the `Cargo.toml` / `src/main.rs` split.

---

## Phase 1 — Foundations

---

## Step 1 — Variables, types, functions, control flow

*Time: 1–2 days. These feel familiar from C++ — the syntax is different but concepts aren't new.*

### Core reading
- **The Book Ch 2** (Programming a Guessing Game) — READ + TYPE this out; don't copy-paste. You'll touch `use`, `let`, `match`, `String`, `io::stdin`, `loop`, `Result` all at once. This is the fastest "feel of Rust" you can get.
- **The Book Ch 3** (Common Programming Concepts) — variables, mutability (`let` vs `let mut`), shadowing, scalar/compound types, functions, statements vs expressions (critical!), control flow.
- **Comprehensive Rust** Day 1, Part 1 (pp. 1–40 in PDF) — covers same ground with concise slides; read after Ch 2–3 as a fast re-pass.

### Key Rust differences from C++
- `let` bindings are immutable by default — the compiler enforces it. `let mut` for mutable.
- **Shadowing** (`let x = 5; let x = x + 1;`) is not reassignment — it creates a new binding. This allows changing the type. It will feel weird; it's intentional.
- **Expressions vs statements:** `if` is an expression that returns a value. `{ let x = 1; x + 1 }` is a block that returns `2`. Functions return the last expression without a semicolon.
- Rust has no implicit type coercion — ever. `5 + 2.0` is a compile error.

### Supplementary
- [A half-hour to learn Rust](https://fasterthanli.me/articles/a-half-hour-to-learn-rust) ⭐ — a rapid-fire syntax tour by Amos (fasterthanlime); ~30 min read; excellent for feeling out where Rust is different from C/C++. Read after Ch 3.
- **Rustlings:** exercises `variables`, `functions`, `if`, `primitive_types` — ~15 exercises.

### Done when
You can write a small program from scratch: read user input, parse it, do a computation with a loop and `if`, print results. Reaching for `let` (not `int`) and using `{}` blocks as expressions feel natural.

---

## Step 2 — Ownership: the core concept of Rust

*Time: 3–5 days. This is the most important block in this entire plan. Do not rush it. Re-read until the model is solid.*

**The C++ analogy:** C++ gives you a gun and says "point it safely." Rust takes the gun away and gives you a set of compile-time rules that guarantee memory safety — at the cost of having to learn those rules. Ownership is those rules.

### Core reading
- **The Book Ch 4** §4.1 (What Is Ownership?) — all three ownership rules + the stack/heap mental model. Read slowly.
- **Programming Rust Ch 4** (Ownership) ⭐ — if you buy one chapter of Programming Rust, it's this one. Goes much deeper than The Book: ownership as "unique owner" analogous to C++ RAII, move semantics, Copy types, why no GC is needed, why double-free is impossible. The C++ parallels here directly map to what you know.

### The three ownership rules (memorize these)
1. Each value in Rust has exactly one *owner*.
2. When the owner goes out of scope, the value is *dropped* (destructor called — RAII, exactly like C++).
3. There can only be one owner at a time.

### Key concepts
- **Move semantics:** assigning or passing a non-Copy value transfers ownership. The old variable is invalid. This is why `let s2 = s1; println!("{}", s1)` fails — `s1` was moved. C++ move semantics are voluntary; Rust's are mandatory and checked.
- **Copy types:** primitives (i32, bool, f64, char, tuples of Copy types) are copied on assignment — no move, old variable still valid. Non-Copy types (String, Vec, Box, most structs) are moved.
- **Clone:** `s1.clone()` deep-copies and is explicit. The compiler forces you to be explicit about expensive copies.
- **Drop order:** fields drop in declaration order; local variables drop in reverse declaration order.

### Supplementary
- [Visualizing memory layout of Rust's data types](https://cheats.rs/#memory-layout) — the "Rust cheat sheet" memory section; shows stack vs heap for each type visually.
- [Programming Rust Ch 4 §"Ownership in practice"](https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html) — skip if you don't have the book; The Book Ch 4.1 covers the essentials.
- [Rustonomicon §Ownership](https://doc.rust-lang.org/nomicon/ownership.html) — short supplementary read once Ch 4 clicks.
- **Rustlings:** `move_semantics` (6 exercises) — essential drill for this step.

### Done when
Given a code snippet, you can predict (without running) whether a move has occurred and whether any variable is invalid after the move. You can explain *why* `String` moves but `i32` copies.

---

## Step 3 — Borrowing & references

*Time: 3–4 days. The runtime cost of a reference is zero — it compiles to a pointer. The borrow checker's rules are the entire safety guarantee.*

### Core reading
- **The Book Ch 4** §4.2 (References and Borrowing) + §4.3 (The Slice Type) — read all of it.
- **Programming Rust Ch 5** (References) ⭐ — the deepest treatment; covers reference mechanics, the borrow checker's algorithm, shared vs mutable references, implicit reborrowing.
- **Comprehensive Rust** Day 1, Part 3 (Ownership and Borrowing section in PDF).

### The borrow checker rules (memorize these)
At any given point in time, for a given value, you can have **either**:
- Any number of *shared* (immutable) references: `&T` — many readers at once.
- Exactly *one* mutable reference: `&mut T` — one writer, no readers.

Never both. This prevents data races at compile time. It's stronger than any runtime lock.

### Key concepts
- `&value` creates a shared reference; `&mut value` creates a mutable reference.
- References must never outlive the value they refer to (the borrow checker enforces this).
- **Slices** (`&str`, `&[T]`) are fat references — a pointer + a length. `&str` is a borrowed string slice; `String` owns the data. Always prefer `&str` in function parameters over `&String`.
- **The "NLL" borrow checker:** Non-Lexical Lifetimes mean the borrow ends when the reference is last *used*, not when it goes out of scope. This makes many "obvious" programs compile.

### Supplementary
- [Rust Book §References and Borrowing visualization](https://doc.rust-lang.org/book/ch04-02-references-and-borrowing.html) — the animated diagrams in the HTML version are particularly clear.
- [Ryan Levick — Introduction to Rust (YouTube)](https://www.youtube.com/watch?v=WnWGO-tLtLA) ⭐ (~1h) — Microsoft engineer; the borrowing + lifetimes sections are the clearest video explanation of the borrow checker I know of. Watch after reading Ch 4.
- **Rustlings:** `borrowing` exercises.
- **Exercise:** write `fn longest(s1: &str, s2: &str) -> &str` that returns the longer string. Watch it fail without a lifetime annotation — this primes Step 9.

### Done when
You can explain the difference between `fn foo(s: String)`, `fn foo(s: &String)`, and `fn foo(s: &str)` — and why the third is almost always correct. You can fix a borrow-checker error by reading the error message, not by guessing.

---

## Step 4 — Structs

*Time: 1–2 days. Familiar territory from C++ — the syntax is new, the concept isn't.*

### Core reading
- **The Book Ch 5** (Using Structs to Structure Related Data) — all three sections: defining/instantiating, method syntax, example program.
- **Programming Rust Ch 9** (Structs) — covers tuple structs, unit structs, struct update syntax, field visibility (`pub`), and why Rust structs don't have constructors (use `::new()` convention instead).
- **Comprehensive Rust** Day 2, Structs section.

### Key concepts
- **Methods and `impl` blocks:** `fn` definitions inside `impl StructName {}`. `&self` = immutable reference to the instance; `&mut self` = mutable; `self` = takes ownership (rare).
- **Associated functions** (`Self::new()`): `impl` functions without `self` — the Rust constructor pattern. `Rectangle::new(width, height)` rather than a constructor keyword.
- **Derived traits:** `#[derive(Debug, Clone, PartialEq)]` — the compiler generates implementations for free. `{:?}` prints Debug output; `{:#?}` pretty-prints it. Always derive Debug on your structs.
- **No struct inheritance** — Rust has no class hierarchy. Composition + traits replace it (Step 8).

### Supplementary
- [Rust By Example §Structs](https://doc.rust-lang.org/rust-by-example/custom_types/structs.html) — concise reference with runnable examples.
- **Rustlings:** `structs` exercises.

### Done when
You can define a struct with an `impl` block, implement `new()`, add methods with `&self` and `&mut self`, and use `#[derive(Debug)]` to print it. You understand that `impl` blocks can be split across multiple blocks.

---

## Step 5 — Enums, pattern matching, `Option`

*Time: 2–3 days. Rust enums are not C++ enums — they are algebraic data types (tagged unions). This is one of the most powerful features of the language.*

### Core reading
- **The Book Ch 6** (Enums and Pattern Matching) — all three sections: defining enums, `match`, `if let`.
- **Programming Rust Ch 10** (Enums and Patterns) ⭐ — comprehensive; covers all pattern types, guards, binding with `@`, destructuring, `matches!` macro.
- **Comprehensive Rust** Day 2, Enums and Pattern Matching section.

### Key concepts
- **Enum variants can hold data:** `enum Message { Quit, Move { x: i32, y: i32 }, Write(String), Color(u8, u8, u8) }` — each variant is its own type. This is Rust's algebraic data type (ADT).
- **`Option<T>`** replaces null. `Some(value)` or `None`. You cannot use a value without handling the `None` case — the compiler forces you. This eliminates null pointer exceptions. It's `std::optional<T>` from C++17, but mandatory.
- **`match` is exhaustive** — you must handle every variant. The compiler tells you if you miss one. Add `_ => {}` for a catch-all.
- **`if let`:** syntactic sugar for a `match` with one arm you care about.
- **`while let`:** loops while a pattern matches.

### Pattern matching cheat-sheet
```rust
match value {
    Some(x) if x > 0 => println!("positive: {x}"),  // guard
    Some(x)          => println!("non-positive: {x}"),
    None             => println!("nothing"),
}
// Destructuring
let Point { x, y } = p;
let (a, b, c) = tuple;
if let Ok(val) = result { /* use val */ }
```

### Supplementary
- [Rust By Example §Enums](https://doc.rust-lang.org/rust-by-example/custom_types/enum.html) — runnable examples for each variant shape.
- [The Book — Patterns and Matching (Ch 18)](https://doc.rust-lang.org/book/ch18-00-patterns.html) — defer full chapter until Phase 2; skim §18.3 (pattern syntax reference) now as a cheat sheet.
- **Rustlings:** `enums`, `option`, `pattern_matching` exercises.
- **Exercise:** implement a `Shape` enum (Circle, Rectangle, Triangle with relevant fields) and a `fn area(shape: &Shape) -> f64` using `match`. Add a `perimeter` method on the enum via `impl Shape`.

### Done when
You can model a domain with `enum` instead of inheritance-hierarchy structs. Given `Option<T>`, you reach for `match`, `if let`, `.unwrap_or()`, `.map()`, `.and_then()` instinctively — not `.unwrap()` everywhere.

---

## Step 6 — Collections

*Time: 1–2 days. Mostly familiar from C++ STL, with different names.*

### Core reading
- **The Book Ch 8** (Common Collections) — Vec, String, HashMap.
- **Programming Rust Ch 16** (Collections) — deeper; covers VecDeque, BTreeMap, HashSet, BinaryHeap, the entry API.

### Key concepts & C++ mappings
| Rust | C++ | Notes |
|---|---|---|
| `Vec<T>` | `std::vector<T>` | Growable heap array. Most common. |
| `HashMap<K, V>` | `std::unordered_map<K, V>` | Hash map; keys must be `Hash + Eq`. |
| `BTreeMap<K, V>` | `std::map<K, V>` | Sorted; use when iteration order matters. |
| `HashSet<T>` | `std::unordered_set<T>` | |
| `String` | `std::string` | Owned UTF-8 string. Heap-allocated. |
| `&str` | `std::string_view` | Borrowed string slice. Always UTF-8. |
| `VecDeque<T>` | `std::deque<T>` | |

- **Vec common patterns:** `vec![1, 2, 3]`, `.push()`, `.pop()`, `.iter()`, `.into_iter()`, slicing with `&v[1..3]`.
- **Entry API:** `map.entry(key).or_insert(default)` — the idiomatic way to insert-or-update. Avoids double-lookup.
- **String is not indexable** by character position (`s[0]` won't compile) — Rust strings are UTF-8 and characters are variable-width. Use `.chars()` to iterate, `.as_bytes()` for byte access.

### Supplementary
- [Rust std::collections docs](https://doc.rust-lang.org/std/collections/) — the "when to use which collection" table at the top is excellent; bookmark it.
- [Rust By Example §Vec](https://doc.rust-lang.org/rust-by-example/std/vec.html), [§HashMap](https://doc.rust-lang.org/rust-by-example/std/hash.html).
- **Rustlings:** `vecs`, `hashmaps`, `strings` exercises.
- **Exercise:** word frequency counter — read a string, split on whitespace, count each word's occurrences using a `HashMap`, print the 5 most frequent. Use the entry API.

### Done when
Given a problem, you pick the right collection type, use the entry API instead of `contains_key` + `insert`, and iterate with `.iter()` (borrows) vs `.into_iter()` (consumes) consciously.

---

## Step 7 — Error handling

*Time: 2 days. Rust has no exceptions. Error handling is explicit and type-checked — you cannot accidentally ignore an error.*

### Core reading
- **The Book Ch 9** (Error Handling) — `panic!`, `Result<T, E>`, the `?` operator, when to use each.
- **Programming Rust Ch 7** (Error Handling) ⭐ — the best treatment; covers error type design, boxing errors, printing errors, custom error types, the `Error` trait.

### Key concepts
- **`Result<T, E>`** is Rust's error type: `Ok(value)` on success, `Err(error)` on failure. Every fallible function returns it. You cannot use the value without handling the error.
- **`panic!`** is for unrecoverable bugs (index out of bounds, assertion failures) — not for expected errors. It unwinds the stack. Never `panic!` in library code.
- **The `?` operator:** `let f = File::open("foo.txt")?;` — if `Err`, returns early from the function with that error; if `Ok`, unwraps to the value. Works only in functions returning `Result` (or `Option`). This replaces Java's checked exceptions without the verbosity.
- **Error conversion:** `?` automatically converts error types using `From::from`. Define `impl From<IoError> for MyError` and `?` does the rest.

### The three ways to handle a `Result`
```rust
match result {
    Ok(val) => use(val),
    Err(e)  => handle(e),
}
// or
let val = result?;           // propagate upward (most common in real code)
let val = result.unwrap();   // panic on Err (only in tests/prototypes)
let val = result.unwrap_or(default);  // provide fallback
```

### Supplementary
- [Rust By Example §Error handling](https://doc.rust-lang.org/rust-by-example/error.html) — excellent progression: `panic`, `Option`, `Result`, `?`, `Box<dyn Error>`, custom types.
- [Andrew Gallant — Error Handling in Rust](https://blog.burntsushi.net/rust-error-handling/) ⭐ — long-form blog post; the canonical reference on idiomatic error handling in Rust. Read after The Book Ch 9.
- **Rustlings:** `error_handling` exercises.
- **Job preview:** you'll want `thiserror` and `anyhow` crates for production code (Step 17) — The Book only covers `std`; that's fine for now.

### Done when
You never write `.unwrap()` except in tests or when you have a proof the value is `Ok`. Every function you write either returns `Result` or is a `main`/test function. You can chain `?` operators naturally.

---

## Phase 1 checkpoint

Before continuing: you now understand Rust's entire memory safety model (ownership + borrowing), can model domains with structs and enums, handle errors explicitly, and use standard collections. This is the hardest conceptual wall — Phase 2 builds on it rather than surprises you again.

**Rustlings checkpoint:** Complete all exercises from `move_semantics` through `error_handling`. If you're stuck on an exercise for more than 20 minutes, re-read the relevant step above — the exercises are designed to test exactly one concept.

---

## Phase 2 — The Rust Core

---

## Step 8 — Traits: Rust's interface system

*Time: 3–4 days. Traits are the Rust equivalent of C++ concepts, Java interfaces, and Python ABCs — but more powerful because they can be implemented retroactively for any type.*

### Core reading
- **The Book Ch 10** §10.1–10.2 (Generic Data Types + Traits) — defining traits, implementing traits on types, default implementations, trait as function parameter (`impl Trait`), returning `impl Trait`.
- **Programming Rust Ch 11** (Traits and Generics) ⭐ — the most important chapter in Programming Rust; covers trait objects (`dyn Trait`), object safety, blanket implementations, the `Sized` bound, operator overloading via traits.
- **Comprehensive Rust** Day 3, Traits section.

### Key concepts
- **Defining a trait:** `trait Summary { fn summarize(&self) -> String; }` — interface declaration. Types opt in with `impl Summary for MyType { fn summarize(&self) -> String { ... } }`.
- **Blanket implementations:** `impl<T: Display> ToString for T {}` — implement a trait for *every type* satisfying some bound. Used heavily in std.
- **Static dispatch (`impl Trait`):** `fn notify(item: &impl Summary)` — monomorphized at compile time, zero overhead.
- **Dynamic dispatch (`dyn Trait`):** `fn notify(item: &dyn Summary)` — vtable dispatch, runtime cost of one pointer indirection. Use when you need heterogeneous collections of trait objects.
- **`Box<dyn Trait>`:** the common pattern for owned trait objects — heap-allocated, single pointer, runtime dispatch. Use when types are known only at runtime.
- **Key standard traits you'll use constantly:** `Debug`, `Clone`, `PartialEq`, `Eq`, `Hash`, `Display`, `From`/`Into`, `Iterator`, `Default`, `Send`, `Sync`.

### C++ mapping
| Rust | C++ |
|---|---|
| `impl Trait` parameter | Template parameter with concept constraint |
| `dyn Trait` | Virtual base class pointer |
| `Box<dyn Trait>` | `unique_ptr<Base>` |
| Blanket impl | Partial template specialization |
| `derive` macro | No equivalent; must write by hand |

### Supplementary
- [Rust By Example §Traits](https://doc.rust-lang.org/rust-by-example/trait.html) — runnable examples.
- [Jon Gjengset — Crust of Rust: Dispatch and Fat Pointers (YouTube)](https://www.youtube.com/watch?v=xcygqF5LVmM) ⭐ — Jon (author of *Rust for Rustaceans*) live-codes how `dyn Trait` works under the hood; essential watch for the static vs dynamic dispatch mental model.
- **Rustlings:** `traits` exercises.
- **Exercise:** define a `Drawable` trait with `fn draw(&self)` and `fn bounding_box(&self) -> (f64, f64, f64, f64)`. Implement it for `Circle` and `Rectangle`. Write a `fn render_all(shapes: &[Box<dyn Drawable>])` function.

### Done when
You know when to use `impl Trait` vs `dyn Trait`, can write blanket implementations, and understand that `derive` generates trait impls. You reach for traits to express shared behavior rather than trying to use struct inheritance.

---

## Step 9 — Generics + Lifetimes

*Time: 4–5 days. Generics are familiar from C++ templates. Lifetimes are completely new — the most conceptually foreign part of Rust, but also the most mechanical once the mental model clicks.*

### Generics (2 days)
- **The Book Ch 10** §10.0–10.1 (Generic Data Types) + revisit §10.2 (Traits as Bounds).
- **Programming Rust Ch 13** (Utility Traits) — after generics basics; covers generic implementations of std traits.
- Key mental model: generic functions are *monomorphized* — the compiler generates a concrete copy per type, like C++ templates. No runtime overhead.
- Trait bounds (`<T: Clone + Debug>` or `where T: Clone + Debug`) restrict what types are acceptable.

### Lifetimes (3 days)
- **The Book Ch 10** §10.3 (Validating References with Lifetimes) — read twice.
- **Programming Rust Ch 5** §"Lifetime Annotations" ⭐ — the clearest explanation of *why* lifetimes exist; shows the borrow checker's algorithm visually.

**The core insight:** lifetime annotations don't *create* lifetimes — they *describe relationships* between lifetimes so the compiler can verify them. The borrow checker already knows all actual lifetimes from the code; annotations are just how you tell it which lifetimes are connected.

```rust
// Without lifetime annotation, compiler can't know whether the return
// borrows from s1 or s2:
fn longest<'a>(s1: &'a str, s2: &'a str) -> &'a str {
    if s1.len() >= s2.len() { s1 } else { s2 }
}
// 'a means "the return reference is valid at least as long as the
// shorter of s1 and s2." No memory is allocated or freed.
```

### Lifetime elision rules (3 rules the compiler applies automatically)
1. Each reference parameter gets its own lifetime.
2. If there's exactly one input lifetime, it's assigned to all output lifetimes.
3. If one of the input lifetimes is `&self` or `&mut self`, it's assigned to all output lifetimes.

If these three rules don't fully determine output lifetimes, you must annotate.

### `'static` lifetime
A reference with lifetime `'static` lasts for the entire program. String literals (`"hello"`) are `&'static str` — stored in the binary. Don't reach for `'static` to silence compiler errors; it's almost always wrong as a fix.

### Supplementary
- [Common Rust Lifetime Misconceptions](https://github.com/pretzelhammer/rust-blog/blob/master/posts/common-rust-lifetime-misconceptions.md) ⭐ — by pretzelhammer; addresses the 9 most common wrong mental models. Read after The Book Ch 10.3.
- [Rust Book (Brown interactive ed.) — References & Borrowing](https://rust-book.cs.brown.edu/ch04-02-references-and-borrowing.html) — Aquascope permission diagrams (R/W/O/F) visualize borrow scopes line by line.
- [Jon Gjengset — Crust of Rust: Lifetime Annotations (YouTube)](https://www.youtube.com/watch?v=rAl-9HwD858) ⭐ — live coding session; the most helpful video on lifetimes in existence.
- **Rustlings:** `lifetimes` exercises.

### Done when
You can add lifetime annotations to a function by reasoning about which outputs borrow from which inputs — not by trial-and-error. The elision rules are automatic. You are not afraid of the `'a` syntax.

---

## Step 10 — Modules, packages, crates, workspaces

*Time: 1–2 days. Rust's module system is more explicit than C++ namespaces but follows strict rules.*

### Core reading
- **The Book Ch 7** (Managing Growing Projects) — all of it: packages, crates, modules, `use`, `pub`, `super`, `self`.
- **The Book Ch 14** §14.1–14.3 (Cargo, crates.io, workspaces) — publishing, features, workspaces.

### Key concepts
- **Crate** = compilation unit (binary crate = executable, library crate = `.rlib`). A package can have one library crate and multiple binary crates.
- **Module** (`mod my_module { ... }`) = namespace + privacy boundary. Default: everything is private. `pub` makes items public.
- **`use`:** brings paths into scope. `use std::collections::HashMap;`. Glob: `use std::collections::*;` (avoid in non-test code).
- **File structure:** `mod foo;` in `main.rs` looks for `src/foo.rs` or `src/foo/mod.rs`. The file IS the module — no header files.
- **Privacy rule:** a child module can access anything in its parent; parent cannot access child's private items.

### The `src/` layout pattern (follow this always)
```
my_project/
├── Cargo.toml
└── src/
    ├── lib.rs         ← library root (if lib crate)
    ├── main.rs        ← binary entry point
    └── models/
        ├── mod.rs     ← or just src/models.rs for a flat module
        └── user.rs
```

### Supplementary
- [The Cargo Book](https://doc.rust-lang.org/cargo/) — reference for everything Cargo; skim the table of contents; read §Workspaces and §Features when you need them.
- [Rust API Guidelines §Naming](https://rust-lang.github.io/api-guidelines/naming.html) — brief; sets the standard for crate/module naming conventions.
- **Exercise:** reorganize a previous step's code (e.g., the Shape exercise) into a library crate with proper modules: `shapes::circle`, `shapes::rectangle`, and a `main.rs` binary that imports from the library.

### Done when
You understand why `mod foo;` finds a file, what `pub(crate)` restricts access to, and how to structure a multi-file project. `cargo doc --open` shows your module tree correctly.

---

## Step 11 — Closures & iterators (deep)

*Time: 3–4 days. Iterators in Rust are zero-cost abstractions — a chain of `.map().filter().collect()` compiles to the same machine code as a hand-written loop.*

### Core reading
- **The Book Ch 13** (Functional Language Features: Closures and Iterators) — both sections.
- **Programming Rust Ch 15** (Iterators) ⭐ — the deepest treatment; the `IntoIterator` trait, external vs internal iteration, implementing `Iterator` yourself, adapters, consumers, `collect()` as a generic operation.
- **Comprehensive Rust** Day 3, Closures and Iterators.

### Key concepts — Closures
- Closures are anonymous functions that capture their environment: `|x| x + 1`.
- **Capture modes:** closures capture by borrow (`&T`) if possible, by mutable borrow (`&mut T`) if needed, by move if forced with `move ||`. The compiler infers this.
- **Fn traits:** `Fn` (borrows immutably), `FnMut` (borrows mutably), `FnOnce` (takes ownership, callable once). Function parameters express which they need.
- **Closure as parameter:** `fn apply<F: Fn(i32) -> i32>(f: F, x: i32) -> i32 { f(x) }` — static dispatch, no allocation.

### Key concepts — Iterators
- All iterators implement `trait Iterator { type Item; fn next(&mut self) -> Option<Self::Item>; }`.
- **Adapter methods** (lazy — return new iterators): `.map()`, `.filter()`, `.take()`, `.skip()`, `.zip()`, `.enumerate()`, `.flat_map()`, `.chain()`, `.peekable()`.
- **Consumer methods** (trigger evaluation): `.collect()`, `.count()`, `.sum()`, `.fold()`, `.for_each()`, `.find()`, `.any()`, `.all()`, `.max()`, `.min()`.
- **`collect::<Vec<_>>()`** — the type annotation tells collect what container to build. Also builds `HashMap`, `String`, `BTreeSet`, etc.
- **Implementing `Iterator`:** define `type Item` and `fn next()` — you get all adapters for free.

### C++ comparison
Rust iterator chains = C++20 ranges. But Rust ranges arrived in 2015 and are pervasive across the entire ecosystem; they're the idiomatic way to process sequences, not an optional add-on.

### Supplementary
- [Writing an Iterator in Rust](https://dev.to/wrongbyte/implementing-iterator-and-intoiterator-in-rust-3nio) — step-by-step implementation of a custom iterator.
- [Rust By Example §Iterators](https://doc.rust-lang.org/rust-by-example/trait/iter.html).
- **Rustlings:** `iterators` (5 exercises), `closures`.
- **Exercise:** given a `Vec<String>` of words, write a pipeline (single expression, no loops) that: filters words longer than 3 chars, maps each to its length, deduplicates, sorts, and collects into a `Vec<usize>`. Then implement a `Fibonacci` struct that implements `Iterator` yielding Fibonacci numbers lazily.

### Done when
You write iterator chains instead of `for` loops wherever the logic is clear. You can implement `Iterator` on your own struct. You understand why iterator chains don't allocate intermediate Vec storage.

---

## Step 12 — Smart pointers & interior mutability

*Time: 3–4 days. This is the escape valve from the borrow checker for cases where ownership is genuinely complex.*

### Core reading
- **The Book Ch 15** (Smart Pointers) — all sections: `Box`, `Deref`, `Drop`, `Rc`, `RefCell`, cycles.
- **Programming Rust Ch 5** §"Reference-Counted Types: Rc and Arc" + Ch 5 §"Cell and RefCell" ⭐.

### Key smart pointers

| Type | Use case | Thread-safe? |
|---|---|---|
| `Box<T>` | Heap allocation; recursive types; owned trait objects | N/A (not shared) |
| `Rc<T>` | Multiple owners, single thread (reference counted) | No |
| `Arc<T>` | Multiple owners, multiple threads (atomic ref count) | Yes |
| `RefCell<T>` | Interior mutability, borrow-checking at runtime, single thread | No |
| `Mutex<T>` | Interior mutability + thread safety | Yes (Step 13) |
| `Cell<T>` | Interior mutability for Copy types | No |

- **`Box<T>`:** heap allocation. Costs one pointer dereference to access. Use for: recursive types (`enum List { Cons(i32, Box<List>), Nil }`), large values you want to move without copying, `Box<dyn Trait>`.
- **`Rc<T>`:** reference-counted shared ownership. Cloning `Rc` doesn't copy data — it increments the count. `Rc::clone()` is idiomatic (not `rc.clone()`); it signals "shared ownership" not "deep copy."
- **`RefCell<T>`:** defers borrow checking to runtime. `.borrow()` → `Ref<T>`, `.borrow_mut()` → `RefMut<T>`. Panics at runtime if you violate the borrow rules. Use only when you're sure the logic is correct but the compiler can't prove it.
- **Common pattern:** `Rc<RefCell<T>>` — shared, mutably-accessible data within a single thread. `Arc<Mutex<T>>` is the multi-threaded equivalent.

### Supplementary
- [Rust Book §Reference Cycles](https://doc.rust-lang.org/book/ch15-06-reference-cycles.html) — `Weak<T>` to break cycles. Read when relevant.
- [Manish Goregaokar — Rust's Memory Model](https://manishearth.github.io/blog/2015/05/27/wrapper-types-in-rust-choosing-your-guarantees/) ⭐ — "Choosing Your Guarantees"; classic blog post on when to use which wrapper type.
- **Rustlings:** `smart_pointers` exercises.

### Done when
Given a design problem ("I need shared ownership of X" or "I need to mutate through a shared reference"), you pick the right wrapper type. You understand that `RefCell` shifts safety from compile time to runtime — and that this is a deliberate trade-off, not a bug.

---

## Phase 2 checkpoint

You now have a complete intermediate Rust toolkit: generics, traits, lifetimes, modules, iterators, smart pointers. At this point you can read most Rust open-source code (minus async and unsafe). You can build non-trivial single-threaded programs.

**Project:** Build a small but complete Rust CLI tool — something directly related to your job. E.g., a file analyzer, a data transformer, a benchmark runner. Use `clap` for CLI argument parsing, `serde_json` for data, `thiserror` for errors. This anchors Phase 2 before Phase 3.

---

## Phase 3 — Good Intermediate

---

## Step 13 — Testing & documentation

*Time: 1 day. Rust has first-class testing and documentation built into cargo.*

### Core reading
- **The Book Ch 11** (Writing Automated Tests) — unit tests (`#[test]`, `assert_eq!`, `assert!`, `should_panic`), integration tests (`tests/` directory), test organization.
- **The Book Ch 14** §14.2 (Publishing to Crates.io — skip the publishing parts, read the doc comments section).

### Key patterns
```rust
#[cfg(test)]
mod tests {
    use super::*;   // bring parent module items into scope

    #[test]
    fn test_add() {
        assert_eq!(add(2, 3), 5);
    }

    #[test]
    #[should_panic(expected = "overflow")]
    fn test_overflow() {
        add(i32::MAX, 1);
    }
}
```
- Unit tests live in the same file as the code (inside `#[cfg(test)] mod tests {}`).
- Integration tests live in `tests/` directory at the crate root — they test public API only.
- **Doc tests:** code examples in `///` doc comments are run as tests by `cargo test`. Write them for all public functions.
- `cargo test -- --nocapture` shows `println!` output during tests.

### Documentation
- `///` for doc comments (rendered as HTML by `cargo doc --open`). `//!` for module/crate-level docs.
- Always document public items. Doc comments support Markdown. Include an "# Examples" section with a doc-test.

### Supplementary
- [Rust By Example §Testing](https://doc.rust-lang.org/rust-by-example/testing.html).
- [The Cargo Book §Testing](https://doc.rust-lang.org/cargo/commands/cargo-test.html).

### Done when
`cargo test` runs your tests. You write at least one unit test and one doc-test per public function you author.

---

## Step 14 — Concurrency

*Time: 3–4 days. Rust's ownership system makes data races a compile-time error. "Fearless concurrency" is not a slogan — the type system enforces it.*

### Core reading
- **The Book Ch 16** (Fearless Concurrency) — threads, message passing (`mpsc` channels), `Mutex<T>`, `Arc<T>`, `Send` + `Sync` marker traits.
- **Programming Rust Ch 19** (Concurrency) ⭐ — covers thread pools (Rayon), channels (`crossbeam`), `Arc<Mutex>`, and why the type system prevents data races.
- **Comprehensive Rust** Concurrency day (available as a full-day module in the PDF).

### Key concepts
- **`thread::spawn`** — takes a closure, runs it in a new OS thread, returns a `JoinHandle`. The closure must be `'static + Send`.
- **`mpsc` (multi-producer, single-consumer) channels:** `let (tx, rx) = std::sync::mpsc::channel();` — `tx.send(val)`, `rx.recv()`. Transfers ownership of values across threads.
- **`Arc<Mutex<T>>`:** the standard pattern for shared mutable state across threads. `Arc::clone(&arc)` is cheap (atomic ref count). `arc.lock().unwrap()` blocks until acquired; returns a `MutexGuard<T>` that auto-unlocks on drop (RAII — exactly like C++ `lock_guard`).
- **`Send` + `Sync` marker traits:** `Send` = type can be moved to another thread; `Sync` = `&T` can be shared across threads. The compiler derives these automatically; you cannot accidentally share non-thread-safe types across threads.

### Why this matters for your job (BIFOLD/DEEM)
Data pipelines are inherently parallelizable. `rayon` (Step 17) turns a `.iter()` into a parallel iterator with one `.par_iter()` change — but it requires your types to be `Send + Sync`, which ownership enforces automatically.

### Supplementary
- [Jon Gjengset — Crust of Rust: Channels (YouTube)](https://www.youtube.com/watch?v=b4mS5UPHh20) — live implementation of `mpsc` channel from scratch; teaches why channels work the way they do.
- [The Rustonomicon §Concurrency](https://doc.rust-lang.org/nomicon/concurrency.html) — formal explanation of `Send`/`Sync`.
- **Rustlings:** `threads` exercises.
- **Exercise:** parallel word counter — given a `Vec<String>` (file paths), spawn one thread per file, read and count words, send counts back via channel, sum in main thread. Then rewrite using `Arc<Mutex<HashMap>>` shared state.

### Done when
You know when to use channels (message passing, prefer this) vs `Arc<Mutex>` (shared state, when necessary). Compiler errors about non-Send types tell you what's wrong. You never manually track "is this thread safe?" — the types do it.

---

## Step 15 — Async Rust basics

*Time: 4–5 days. Async in Rust is more complex than Python's asyncio or JavaScript's Promises, but gives you OS-thread performance with async-task concurrency.*

### Core reading
- **The Book Ch 17** (Async and Await) — new in the 2024 edition; full chapter. Read all of it.
- **Comprehensive Rust** Async chapter (dedicated chapter in the PDF).
- **[The Async Book](https://rust-lang.github.io/async-book/)** (free, online) — the official supplementary reference. Read Ch 1–3 after The Book Ch 17.

### Key concepts
- **`async fn`** returns a `Future<Output = T>` — a value that represents a computation that hasn't started yet. A Future does nothing until polled.
- **`await`** — pauses the current async task and gives the runtime control until the Future is ready. Only inside `async` contexts.
- **Runtimes:** Rust's standard library has no async runtime. You need an external one. **[Tokio](https://tokio.rs)** is the dominant choice (web servers, networking, databases). `async-std` is the alternative.
- **`#[tokio::main]`** — macro that sets up the Tokio runtime and makes `main` async.
- **`tokio::spawn`** — spawns an async task (green thread). Much cheaper than OS threads.
- **`tokio::join!`** — runs multiple futures concurrently, waits for all.

### Minimal async example
```rust
// Cargo.toml: tokio = { version = "1", features = ["full"] }
#[tokio::main]
async fn main() {
    let result = fetch_data().await;
    println!("{result}");
}

async fn fetch_data() -> String {
    tokio::time::sleep(std::time::Duration::from_millis(100)).await;
    "done".to_string()
}
```

### Important nuance
Async Rust has its own "borrow checker" headaches: futures must be `Send` to be spawned across threads (`tokio::spawn` requires this), and you can't hold a non-`Send` type across an `await` point. These errors are cryptic at first; they get clearer with practice.

### Supplementary
- [Tokio Tutorial](https://tokio.rs/tokio/tutorial) ⭐ — the official Tokio tutorial; covers channels, tasks, select!, shared state. Do this tutorial end-to-end.
- [Jon Gjengset — Decrusting the Tokio Crate (YouTube)](https://www.youtube.com/watch?v=o2ob8zkeq2s) — deep dive; post-tutorial once you want to understand the internals.
- [fasterthanlime — Understanding Rust futures by going way too deep](https://fasterthanli.me/articles/understanding-rust-futures-by-going-way-too-deep) ⭐ — the best explanation of how futures poll under the hood; long but essential.
- **Exercise:** build a simple async HTTP client that fetches 5 URLs concurrently using `tokio::join!` or `tokio::spawn`, collecting all responses.

### Done when
You can write async functions, spawn tasks with `tokio::spawn`, use channels between tasks, and understand why `async` blocks don't run until `.await`-ed or polled by a runtime.

---

## Step 16 — Error handling patterns (production-level)

*Time: 1 day. You know `Result` from Step 7. This step adds the ecosystem tools that make production error handling ergonomic.*

### Core reading
- [`thiserror` crate docs](https://docs.rs/thiserror) — derive macro for custom error types in libraries. Eliminates boilerplate.
- [`anyhow` crate docs](https://docs.rs/anyhow) — type-erased errors (`anyhow::Error`) for application code; `anyhow::Context` adds context to errors. Use in binary crates, not libraries.
- [Jane Lossy — Error Handling in Rust (blog)](https://nrc.github.io/error-docs/intro.html) — covers when to use each approach.

### The pattern
```rust
// Library crate: use thiserror
#[derive(thiserror::Error, Debug)]
enum MyError {
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),
    #[error("parse error at line {line}: {msg}")]
    Parse { line: usize, msg: String },
}

// Application/binary crate: use anyhow
fn main() -> anyhow::Result<()> {
    let data = std::fs::read_to_string("config.toml")
        .context("reading config file")?;
    // ... 
    Ok(())
}
```

### Done when
Your library crates use `thiserror` with meaningful error variants. Your binary `main` functions use `anyhow::Result<()>`. `.context("doing X")` wraps errors with human-readable context.

---

## Step 17 — Ecosystem essentials

*Time: 2–3 days. Rust's standard library is intentionally minimal. These crates are de facto standard for almost every Rust project.*

### Must-know crates

**Serialization: `serde`**
- [serde.rs](https://serde.rs) — THE Rust serialization framework; supports JSON, TOML, YAML, MessagePack, and 30+ formats.
- `#[derive(Serialize, Deserialize)]` on any struct/enum — zero-effort JSON serialization.
- With `serde_json`: `serde_json::to_string(&value)?` and `serde_json::from_str::<MyType>(&text)?`.
- Essential for almost any data engineering work.

**CLI argument parsing: `clap`**
- [clap.rs](https://docs.rs/clap) — derive-based CLI parsing with help text, validation, subcommands generated automatically from a struct.
```rust
#[derive(clap::Parser)]
struct Args {
    #[arg(short, long)]
    input: PathBuf,
    #[arg(short, long, default_value = "10")]
    count: usize,
}
```

**Parallel iteration: `rayon`**
- [rayon](https://docs.rs/rayon) — data parallelism via parallel iterators. Change `.iter()` to `.par_iter()` — done.
- Requires `Send + Sync` on items; the compiler tells you if something isn't.
- Highly relevant for data pipeline work at BIFOLD/DEEM.

**HTTP client: `reqwest`**
- [reqwest](https://docs.rs/reqwest) — the dominant async HTTP client; built on Tokio. `reqwest::get(url).await?.text().await?`.

**Config file reading: `config` or `toml`**
- [toml](https://docs.rs/toml) — parse TOML config files into Rust structs via serde.

**Logging: `tracing`**
- [tracing](https://docs.rs/tracing) — structured, async-aware logging. `tracing::info!("started")`, `tracing::error!(err = ?e, "failed")`.
- Replaces `println!` debugging in production code.

### Supplementary
- [lib.rs](https://lib.rs) — curated crate index; better search than crates.io for finding quality crates in a category.
- [blessed.rs](https://blessed.rs/crates) ⭐ — "blessed" community picks for the best crate per category. Bookmark this.
- **Exercise:** build the Phase 2 checkpoint CLI project with `clap` + `serde_json` + `thiserror` + `tracing`. Refactor the error handling to use `thiserror` in the library logic and `anyhow` at the CLI boundary.

### Done when
You have `serde`, `clap`, `thiserror`, and `tracing` in your project template. You look up `blessed.rs` before reaching for a new crate. You know why these crates don't live in std (intentional minimalism — keeps the language stable while ecosystem evolves faster).

---

## Phase 3 checkpoint — "Good intermediate"

At this point you can:
- Write complete, well-structured Rust programs from scratch
- Handle errors idiomatically without panicking
- Use traits and generics fluidly
- Write safe concurrent code
- Build async network clients/servers
- Use the core ecosystem crates
- Read and understand most Rust library source code

**Final project:** take something from your BIFOLD/DEEM job — a data transformation, a benchmark, a small service — and build it in Rust. The constraint of a real task forces the intermediate skills to solidify.

---

## Advanced tier — pull-based, post-intermediate

---

## Step 18 — Unsafe Rust

*Read when you need it: FFI, performance-critical code, implementing data structures.*

- **The Book Ch 19** §19.1 (Unsafe Rust) — the five unsafe superpowers: raw pointers, unsafe fns, unsafe trait impl, mutable statics, external functions.
- **[The Rustonomicon](https://doc.rust-lang.org/nomicon/)** ⭐ — "the Dark Arts of Unsafe Rust." The authoritative deep reference. Read front-to-back when you start writing `unsafe` blocks regularly.
- **Rule:** `unsafe {}` blocks should be as small as possible and wrapped in a safe abstraction. Every `unsafe` block is a contract you promise to uphold manually.
- **Relevance:** FFI with C libraries (common in ML/DE work calling C backends) requires `unsafe`.

---

## Step 19 — Macros

*Read when you encounter macro-heavy code or want to write derive macros.*

- **The Book Ch 19** §19.6 (Macros) — declarative macros (`macro_rules!`), procedural macros.
- [The Little Book of Rust Macros](https://veykril.github.io/tlborm/) — the canonical free resource for `macro_rules!` in depth.
- [Jon Gjengset — Crust of Rust: Procedural Macros (YouTube)](https://www.youtube.com/watch?v=geovSK3wMB8) — live implementation of a derive macro.
- Most Rust code *uses* macros (via `#[derive(...)]` or crates like `clap`) but rarely *writes* them. Learn to use before you learn to write.

---

## Step 20 — Advanced type-level programming

*Read after ~6 months of Rust use; needed for framework development, not application development.*

- *Rust for Rustaceans* — Jon Gjengset (No Starch Press) ⭐ — THE intermediate-to-advanced book. Assumes you're comfortable with everything in this plan. Covers: type system internals, advanced lifetimes, `Pin`, object safety, API design, testing, macros. Buy this when you finish Phase 3.
- [Rust Reference](https://doc.rust-lang.org/reference/) — the formal language spec; use for precise semantics, not learning.
- [The `Pin` type](https://doc.rust-lang.org/std/pin/index.html) — needed for writing your own async code; read the `std::pin` module docs.

---

## Practice grounds (cross-step)

| Resource | What for |
|---|---|
| [Rustlings](https://github.com/rust-lang/rustlings) | 100 exercises, exactly one concept per exercise; primary drill throughout Phase 1–2 |
| [Exercism Rust track](https://exercism.org/tracks/rust) | ~100 exercises with community mentor feedback; filter by topic |
| [Advent of Code](https://adventofcode.com) | Algorithm problems; standard Rust practice; prior years available year-round |
| [LeetCode in Rust](https://leetcode.com) | Good for forcing familiarity with Vec/HashMap/BTreeMap patterns under pressure |
| [Rust By Example](https://doc.rust-lang.org/rust-by-example/) | Runnable code reference; one page per concept, always has a `try it` button |
| [Rust Playground](https://play.rust-lang.org) | Quick experiments without a local project; share links to code snippets |
| [Tour of Rust](https://tourofrust.com) | Interactive step-by-step intro; good when a concept explanation isn't clicking from text alone |
| **Your BIFOLD/DEEM job** | The real practice ground — building something that matters forces Phase 3 consolidation |

---

## Two meta-rules

1. **Read error messages like documentation.** Rust's compiler errors are unusually helpful — they often tell you exactly what to do. Treat a new kind of error as a learning opportunity, not a failure. `rustc --explain E0502` gives a multi-paragraph explanation of any error code.
2. **Write it first, then make it idiomatic.** Don't try to write "Rusty" code on the first pass. Write the obvious version (with explicit types, no iterator chains, plain loops), get it compiling, get it tested — *then* refactor toward idiomatic Rust. Trying to be idiomatic on the first pass while fighting the borrow checker leads to frustration.
