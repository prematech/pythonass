# PTMAE — Project Documentation

**Project:** Pure Python Transactional Micro-Banking & Audit Engine  
**Course:** Python Programming (Units 1–5)  
**Main program:** `main.py`

## 1. Objective

PTMAE is a command-line learning project that models selected banking operations, validates transaction records, creates audit views, and demonstrates object-oriented settlement rules. It uses plain text files rather than a database engine and avoids third-party packages.

## 2. How to run

1. Install Python 3.x.
2. Keep `main.py` and this file in the same project folder.
3. Open Command Prompt or a terminal in that folder.
4. Run `python main.py` (on some Windows systems, use `py main.py`).
5. Review the demonstrations. Type `y` when asked if you want to open the interactive command centre.

The program may create `accounts.db` if it does not already exist. File-update tests can also create `ledger.txt` and `corrupted.log`. These are runtime data files; the assignment submission folder should initially contain only `main.py` and `documentation.md`.

## 3. Features

- **State control:** compound-interest and late-penalty calculations use loops and arithmetic operators.
- **Trajectory guard:** stops processing when a stop marker appears or the balance falls below the configured threshold.
- **Manual parser:** handles delimiters, quoted fields, doubled quote characters, empty fields, and trailing delimiters without `split()` or `replace()`.
- **Closures:** an audit filter uses `nonlocal` to count calls; positional lambdas bind their loop index with a default argument.
- **Reverse index:** maps each service tag to sorted unique `(account_id, branch_id)` pairs.
- **In-place queue cleaning:** converts tuples to lists, removes even integers from sets, sorts nested lists in descending order, and removes repeated primitive values while preserving the original top-level list identity.
- **File audit:** validates records in `accounts.db`, updates a matching record through `r+`, records invalid lines in `corrupted.log`, and logs accepted updates to `ledger.txt`.
- **Polymorphic settlement:** Savings, Current, and Credit accounts apply different rules; each account in a batch is handled independently.

## 4. Command-centre commands

| Command | Purpose |
|---|---|
| `help` | Shows available commands |
| `interest` | Calculates compound interest from principal, rate, and years |
| `penalty` | Calculates a growing late fee |
| `guard` | Applies a list of transaction changes until a guard condition is reached |
| `exit` | Ends the interactive loop |

## 5. Architecture diagram

```text
                   +-------------------------+
                   |       main()            |
                   +------------+------------+
                                |
              +-----------------+------------------+
              |                 |                  |
      +-------v------+  +-------v------+   +-------v-------+
      | Unit 1       |  | Unit 2       |   | Unit 3        |
      | State/loops  |  | Parser/scope |   | Reverse index |
      | Guard logic  |  | Closures     |   | Queue cleanup |
      +--------------+  +--------------+   +---------------+
              |                 |                  |
              +-----------------+------------------+
                                |
                       +--------v---------+
                       | Unit 4            |
                       | File validation   |
                       | r+ update + logs  |
                       +--------+----------+
                                |
                       +--------v----------+
                       | Unit 5             |
                       | Account hierarchy  |
                       | Polymorphic rules  |
                       +--------------------+
```

### Class relationship

```text
Account
  +-- SavingsAccount
  +-- CurrentAccount
  +-- CreditAccount

BaseSystemError
  +-- CorruptedRecordError
  +-- OutOfBoundsError
  +-- InsufficientBalanceError
```

## 6. Data and file format

`accounts.db` uses one comma-separated record per line:

```text
SAV101,SAVINGS,5200.00
CUR101,CURRENT,800.00
CRD101,CREDIT,0.00
```

Each record contains an account ID, account type (`SAVINGS`, `CURRENT`, or `CREDIT`), and numeric balance. Malformed records are written to `corrupted.log` with their line number. Accepted account updates are appended to `ledger.txt`.

**Important:** The file-update function is a teaching demonstration, not a production banking storage engine. Run experiments on sample data, not real financial records.

## 7. State and scope tracking

| Name | Scope/type | Purpose |
|---|---|---|
| `audited_count` | `nonlocal` closure variable | Counts validations for one audit filter |
| `k` | Lambda default argument | Captures the correct positional index in each filter |
| `Account.total_accounts` | Class attribute | Counts account instances created |
| `Account.__balance` | Private/name-mangled instance attribute | Stores an account's balance |
| `Account._account_id` | Protected-by-convention attribute | Stores the account identifier |
| `CurrentAccount.__overdraft_limit` | Private subclass attribute | Defines the allowed overdraft |
| `CreditAccount.__credit_limit` | Private subclass attribute | Tracks remaining credit limit |
| Global mutable state | Not used to pass closure state | Functions receive data through parameters |

## 8. Unit-wise syllabus mapping

| Unit | Concepts demonstrated | Where to review |
|---|---|---|
| Unit 1 | Nested loops, conditions, arithmetic, short-circuit guard | `compound_interest`, `calculate_penalty`, `trajectory_guard`, `interactive_loop` |
| Unit 2 | Functions, manual parsing, slicing/indexing, `nonlocal`, lambdas | `parse_raw_log_line`, `create_audit_filter`, `build_positional_filters` |
| Unit 3 | Sets, tuples, lists, comprehensions, sorting, in-place mutation | `build_reverse_index`, `clean_transaction_queue` |
| Unit 4 | Text files, `r+`, `seek`, `tell`, `truncate`, exceptions, audit logs | `update_account_record`, `_append_line` |
| Unit 5 | Classes, inheritance, encapsulation, `super()`, overriding, polymorphism | `Account`, subclasses, `execute_batch_settlement` |

## 9. Pre-submission checklist

- [ ] Run `python main.py` and read the output.
- [ ] Try the interactive commands and the invalid-input paths.
- [ ] Test the parser with quoted commas and doubled quotes.
- [ ] Confirm that `id(queue)` remains unchanged after queue cleaning.
- [ ] Test the file updater only with a copy of sample `accounts.db`.
- [ ] Be prepared to explain the closure, reverse index, in-place mutation, file shifting, and account settlement rules.
- [ ] Keep the submitted folder limited to `main.py` and `documentation.md`.
- [ ] Rename the containing folder using your own semester, division, enrollment number, and name.

## 10. Originality and understanding

This implementation is structured for this assignment brief and should be reviewed and tested by the student before submission. Read each function, change sample values, run tests, and make sure you can explain the logic in your own words. Do not submit work you cannot explain during evaluation.
