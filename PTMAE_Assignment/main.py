"""
Pure Python Transactional Micro-Banking & Audit Engine (PTMAE)
Student implementation for Python Programming Units 1-5.
Only the permitted optional modules (random and datetime) may be imported.
"""

# ------------------------- Custom exceptions -------------------------
class BaseSystemError(Exception):
    """Base exception for PTMAE system errors."""


class CorruptedRecordError(BaseSystemError):
    """Raised when a stored account record is malformed."""


class OutOfBoundsError(BaseSystemError):
    """Raised when an operation crosses a configured limit."""


class InsufficientBalanceError(BaseSystemError):
    """Raised when an account cannot cover a settlement."""


# ------------------------- Unit 1: state and trajectory -------------------------
def compound_interest(principal, annual_rate, years):
    """Calculate compound interest using arithmetic operators and loops."""
    if principal < 0 or annual_rate < 0 or years < 0:
        raise ValueError("Values must be non-negative.")
    amount = principal
    year = 0
    while year < years:
        amount = amount + amount * annual_rate / 100
        year += 1
    return amount - principal


def calculate_penalty(base_fee, days_late):
    """Calculate a growing daily penalty without importing math."""
    if base_fee < 0 or days_late < 0:
        raise ValueError("Fee and days must be non-negative.")
    total = 0
    day = 0
    while day < days_late:
        weeks = day // 7
        total = total + base_fee * (weeks + 1)
        day += 1
    return total


def trajectory_guard(starting_balance, transactions, safety_threshold):
    """Apply transactions until STOP or a balance below the threshold occurs."""
    balance = starting_balance
    processed = 0
    for transaction in transactions:
        if transaction == "STOP" or balance <= safety_threshold:
            break
        balance = balance + transaction
        processed += 1
    return balance, processed


def interactive_loop():
    """Run a nested command loop until the operator explicitly enters exit."""
    print("\\nPTMAE command centre")
    print("Commands: interest, penalty, guard, help, exit")
    running = True
    while running:
        command = input("ptmae> ").strip().lower()
        while command == "":
            print("Please enter a command.")
            command = input("ptmae> ").strip().lower()

        if command == "exit":
            running = False
        elif command == "help":
            print("interest = compound interest; penalty = late fee; guard = safety check")
        elif command == "interest":
            try:
                principal = float(input("Principal: "))
                rate = float(input("Annual rate (%): "))
                years = int(input("Years: "))
                print("Interest:", round(compound_interest(principal, rate, years), 2))
            except (ValueError, TypeError):
                print("Invalid numeric input.")
        elif command == "penalty":
            try:
                fee = float(input("Base daily fee: "))
                days = int(input("Days late: "))
                print("Penalty:", round(calculate_penalty(fee, days), 2))
            except (ValueError, TypeError):
                print("Invalid numeric input.")
        elif command == "guard":
            try:
                balance = float(input("Starting balance: "))
                threshold = float(input("Safety threshold: "))
                raw = input("Transactions (comma-separated numbers; use STOP to end): ")
                transactions = []
                token = ""
                i = 0
                while i < len(raw):
                    if raw[i] == ",":
                        clean = token.strip()
                        if clean.upper() == "STOP":
                            transactions.append("STOP")
                        elif clean != "":
                            transactions.append(float(clean))
                        token = ""
                    else:
                        token += raw[i]
                    i += 1
                clean = token.strip()
                if clean.upper() == "STOP":
                    transactions.append("STOP")
                elif clean != "":
                    transactions.append(float(clean))
                final_balance, count = trajectory_guard(balance, transactions, threshold)
                print("Final balance:", final_balance, "| Transactions applied:", count)
            except ValueError:
                print("Invalid transaction sequence.")
        else:
            print("Unknown command. Enter help to see available commands.")
    print("PTMAE session ended.")


# ------------------------- Unit 2: native parser and closures -------------------------
def parse_raw_log_line(line, delimiter=",", quote_char='"'):
    """Parse a delimited line manually, supporting quoted delimiters and doubled quotes."""
    tokens = []
    field = ""
    in_quotes = False
    index = 0
    while index < len(line):
        character = line[index]
        next_character = line[index + 1:index + 2]
        if in_quotes:
            if character == quote_char and next_character == quote_char:
                field += quote_char
                index += 1
            elif character == quote_char:
                in_quotes = False
            else:
                field += character
        elif character == quote_char:
            in_quotes = True
        elif character == delimiter:
            tokens.append(field.strip())
            field = ""
        else:
            field += character
        index += 1
    if in_quotes:
        raise CorruptedRecordError("Unclosed quoted field.")
    tokens.append(field.strip())
    return tokens


def create_audit_filter(threshold):
    """Return a closure that counts each audited value and checks its threshold."""
    audited_count = 0

    def validate(amount):
        nonlocal audited_count
        audited_count += 1
        return amount >= threshold

    def get_count():
        """Expose the number of validations performed by this closure."""
        return audited_count

    validate.get_count = get_count
    return validate


def build_positional_filters(number_of_columns):
    """Build filters that test whether a positional value is positive."""
    filters = []
    position = 0
    while position < number_of_columns:
        filters.append(lambda row, k=position: len(row) > k and row[k] > 0)
        position += 1
    return filters


# ------------------------- Unit 3: reverse index and in-place queue -------------------------
raw_db = {
    "BRANCH_01": [
        ("Acc101", {"DEPOSIT", "UPI"}),
        ("Acc102", {"LOAN", "UPI"})
    ],
    "BRANCH_02": [
        ("Acc101", {"SAVINGS", "UPI"}),
        ("Acc103", {"CARD", "DEPOSIT"})
    ]
}


def build_reverse_index(database):
    """Map every service tag to sorted, unique (account ID, branch ID) pairs."""
    all_tags = {tag for rows in database.values() for account_id, tags in rows for tag in tags}
    return {
        tag: sorted({
            (account_id, branch_id)
            for branch_id, rows in database.items()
            for account_id, tags in rows
            if tag in tags
        })
        for tag in all_tags
    }


def clean_transaction_queue(data_list):
    """Clean a heterogeneous list in place and preserve its top-level identity."""
    for index in range(len(data_list)):
        item = data_list[index]
        if isinstance(item, tuple):
            item = list(item)
            data_list[index] = item

        if isinstance(item, set):
            even_values = {value for value in item if isinstance(value, int) and value % 2 == 0}
            item.difference_update(even_values)
        elif isinstance(item, list):
            item.sort(reverse=True)

    # Remove duplicate primitive values (integers, strings, floats) in first-seen order.
    index = 0
    while index < len(data_list):
        value = data_list[index]
        is_primitive = isinstance(value, (int, float, str, bool))
        duplicate = False
        if is_primitive:
            earlier = 0
            while earlier < index:
                previous = data_list[earlier]
                if isinstance(previous, (int, float, str, bool)) and type(previous) == type(value) and previous == value:
                    duplicate = True
                    break
                earlier += 1
        if duplicate:
            del data_list[index]
        else:
            index += 1
    return data_list


# ------------------------- Unit 4: in-place file modification and audit logs -------------------------
def _append_line(path, text):
    """Append one line while ensuring the file is properly closed."""
    with open(path, "a", encoding="utf-8") as file_handle:
        file_handle.write(text + "\n")


def update_account_record(path, account_id, new_balance):
    """
    Validate account records and update a matching line in r+ mode.
    If the replacement line changes length, shift the tail in chunks before writing.
    """
    processed = 0
    rejected = 0
    target_found = False
    line_number = 0
    try:
        with open(path, "r+", encoding="utf-8", newline="") as file_handle:
            while True:
                record_start = file_handle.tell()
                line = file_handle.readline()
                if line == "":
                    break
                line_number += 1
                content = line.rstrip("\r\n")
                try:
                    fields = parse_raw_log_line(content)
                    if len(fields) != 3:
                        raise CorruptedRecordError("Expected 3 fields.")
                    record_id = fields[0]
                    account_type = fields[1].upper()
                    balance = float(fields[2])
                    if record_id == "" or account_type not in ("SAVINGS", "CURRENT", "CREDIT"):
                        raise CorruptedRecordError("Unknown account ID or account type.")
                    if balance < 0:
                        raise CorruptedRecordError("Stored balance cannot be negative.")
                except (ValueError, CorruptedRecordError) as error:
                    rejected += 1
                    _append_line("corrupted.log", "line " + str(line_number) + ": " + content + " | " + str(error))
                    continue

                if record_id == account_id and not target_found:
                    replacement = record_id + "," + account_type + "," + str(new_balance) + "\n"
                    old_record_length = len(line)
                    new_record_length = len(replacement)
                    tail_start = file_handle.tell()

                    if new_record_length == old_record_length:
                        file_handle.seek(record_start)
                        file_handle.write(replacement)
                    else:
                        # Shift the remaining text in bounded chunks, from the end when growing.
                        file_handle.seek(0, 2)
                        end_position = file_handle.tell()
                        if new_record_length > old_record_length:
                            extra = new_record_length - old_record_length
                            position = end_position
                            while position > tail_start:
                                chunk_start = position - 1024
                                if chunk_start < tail_start:
                                    chunk_start = tail_start
                                file_handle.seek(chunk_start)
                                chunk = file_handle.read(position - chunk_start)
                                file_handle.seek(chunk_start + extra)
                                file_handle.write(chunk)
                                position = chunk_start
                        else:
                            reduction = old_record_length - new_record_length
                            position = tail_start
                            while position < end_position:
                                file_handle.seek(position)
                                chunk = file_handle.read(1024)
                                if chunk == "":
                                    break
                                file_handle.seek(position - reduction)
                                file_handle.write(chunk)
                                position += len(chunk)
                            file_handle.truncate(end_position - reduction)

                        file_handle.seek(record_start)
                        file_handle.write(replacement)
                        file_handle.truncate(end_position + new_record_length - old_record_length)

                    processed += 1
                    target_found = True
                    break
        if target_found:
            _append_line("ledger.txt", account_id + " -> " + str(new_balance))
        elif processed == 0:
            print("Account ID not found:", account_id)
    except OSError as error:
        raise CorruptedRecordError("File operation failed: " + str(error))
    finally:
        print("File update summary | processed:", processed, "| rejected:", rejected)
    return processed, rejected


# ------------------------- Unit 5: encapsulated accounts and polymorphism -------------------------
class Account:
    """Base account with a private balance and a shared account counter."""
    total_accounts = 0

    def __init__(self, account_id, balance):
        if not isinstance(account_id, str) or account_id.strip() == "":
            raise TypeError("Account ID must be a non-empty string.")
        self._account_id = account_id
        self.__balance = 0.0
        self.set_balance(balance)
        Account.total_accounts += 1

    def get_balance(self):
        """Return the private account balance."""
        return self.__balance

    def set_balance(self, value):
        """Set balance after checking its numeric type and range."""
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("Balance must be an integer or float.")
        if value < 0:
            raise OutOfBoundsError("Balance cannot be negative.")
        self.__balance = float(value)

    def process_settlement(self, amount):
        """Interface implemented by each concrete account type."""
        raise NotImplementedError("Subclasses must implement settlement.")

    def _set_balance_allowing_overdraft(self, value):
        """Internal helper used by account types that permit negative balances."""
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("Balance must be numeric.")
        self.__balance = float(value)


class SavingsAccount(Account):
    """Savings account that must retain a minimum balance of 1000."""
    def __init__(self, account_id, balance):
        super().__init__(account_id, balance)

    def process_settlement(self, amount):
        if amount < 0:
            raise OutOfBoundsError("Settlement amount must be non-negative.")
        remaining = self.get_balance() - amount
        if remaining < 1000:
            raise InsufficientBalanceError("Savings balance would fall below 1000.")
        self.set_balance(remaining)


class CurrentAccount(Account):
    """Current account that supports a configured overdraft limit."""
    def __init__(self, account_id, balance, overdraft_limit):
        super().__init__(account_id, balance)
        if overdraft_limit < 0:
            raise OutOfBoundsError("Overdraft limit cannot be negative.")
        self.__overdraft_limit = overdraft_limit

    def process_settlement(self, amount):
        if amount < 0:
            raise OutOfBoundsError("Settlement amount must be non-negative.")
        remaining = self.get_balance() - amount
        if remaining < -self.__overdraft_limit:
            raise OutOfBoundsError("Current account overdraft limit exceeded.")
        self._set_balance_allowing_overdraft(remaining)


class CreditAccount(Account):
    """Credit account that applies a 2.5 percent surcharge to each settlement."""
    def __init__(self, account_id, balance, credit_limit):
        super().__init__(account_id, balance)
        if credit_limit < 0:
            raise OutOfBoundsError("Credit limit cannot be negative.")
        self.__credit_limit = float(credit_limit)

    def process_settlement(self, amount):
        if amount < 0:
            raise OutOfBoundsError("Settlement amount must be non-negative.")
        charged_amount = amount + amount * 2.5 / 100
        if charged_amount > self.__credit_limit:
            raise OutOfBoundsError("Credit limit exceeded.")
        self.__credit_limit = self.__credit_limit - charged_amount
        # Credit balance represents the amount already used.
        self._set_balance_allowing_overdraft(self.get_balance() + charged_amount)


def execute_batch_settlement(account_list, transaction_amount):
    """Process every account independently and return success/failure counts."""
    successes = 0
    failures = 0
    for account in account_list:
        try:
            account.process_settlement(transaction_amount)
        except BaseSystemError as error:
            failures += 1
            print(account._account_id, "FAILED:", error)
        except (TypeError, ValueError) as error:
            failures += 1
            print(account._account_id, "FAILED:", error)
        else:
            successes += 1
            print(account._account_id, "SETTLED. Balance:", account.get_balance())
    print("Batch summary | successes:", successes, "| failures:", failures)
    return successes, failures


# ------------------------- Demonstration and menu -------------------------
def run_demonstrations():
    """Exercise each major requirement with small, readable examples."""
    print("\\n=== PTMAE requirement demonstrations ===")
    print("Compound interest on 1000 at 5% for 2 years:", round(compound_interest(1000, 5, 2), 2))
    print("Penalty for 10 days at 5 per day:", calculate_penalty(5, 10))
    print("Trajectory guard:", trajectory_guard(2000, [-200, -300, "STOP", 100], 1000))

    print("\\nManual parser:")
    print(parse_raw_log_line('Acc101,SAVINGS,"note, with comma"'))
    print(parse_raw_log_line('Acc102,CURRENT,"said ""hello"""'))

    audit = create_audit_filter(500)
    print("Audit decisions:", audit(700), audit(200), "| audited:", audit.get_count())
    positional_filters = build_positional_filters(3)
    print("Positional filter checks:", [test([4, -1, 9]) for test in positional_filters])

    reverse_index = build_reverse_index(raw_db)
    print("\\nReverse index:")
    for tag in sorted(reverse_index):
        print(tag, "->", reverse_index[tag])

    queue = [(3, 1), [2, 9, 4], {1, 2, 3, 4}, 7, 7, "A", "A"]
    original_identity = id(queue)
    clean_transaction_queue(queue)
    print("Cleaned queue:", queue, "| identity preserved:", id(queue) == original_identity)

    # Create a tiny demonstration database in append mode only if it does not exist.
    try:
        with open("accounts.db", "r", encoding="utf-8"):
            pass
    except FileNotFoundError:
        with open("accounts.db", "w", encoding="utf-8") as database:
            database.write("SAV101,SAVINGS,5200.00\\nCUR101,CURRENT,800.00\\nCRD101,CREDIT,0.00\\n")
    print("\\nFile-update demo uses accounts.db in the current folder.")
    print("Run update_account_record('accounts.db', 'SAV101', 5150.00) to test an in-place update.")

    savings = SavingsAccount("SAV101", 5200)
    current = CurrentAccount("CUR101", 800, 500)
    credit = CreditAccount("CRD101", 0, 3000)
    print("\\nPrivate attribute demonstration via mangled name:", savings._Account__balance)
    try:
        print(savings.__balance)
    except AttributeError:
        print("Direct savings.__balance access correctly raises AttributeError.")
    execute_batch_settlement([savings, current, credit], 800)
    print("Total accounts created:", Account.total_accounts)


def main():
    """Run demonstrations, then offer the interactive command loop."""
    run_demonstrations()
    choice = input("\\nOpen interactive command centre? (y/n): ").strip().lower()
    if choice == "y":
        interactive_loop()


if __name__ == "__main__":
    main()
