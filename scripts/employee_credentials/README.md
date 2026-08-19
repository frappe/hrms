# Employee credential rotation & delivery

Two one-off admin scripts, run directly against a Frappe HR site's Python
environment (not a Frappe app / not installed via `bench get-app`).

## What they do

1. **`1_configure_sendgrid.py`** — sets up the site's default Outgoing Email
   Account using the shared Clustox SendGrid relay.
2. **`2_rotate_and_email_passwords.py`** — for every **Active** Employee with
   an **enabled**, linked User account, generates a fresh unique 20-character
   alphanumeric password, sets it on the account, and emails it to them.

Both were built and verified against a local test site. The SendGrid key in
use only authenticates from specific machines (currently: the GPU machine) —
if `1_configure_sendgrid.py` fails to save with an authentication error,
that's expected anywhere else.

## Before running anywhere

1. Copy `smtp_config.example.json` to `smtp_config.json` **next to these
   scripts** and fill in the real API key. This file is gitignored — it
   must never be committed.
2. In both scripts, update `SITE_NAME` to the target site's real name, and
   in `2_rotate_and_email_passwords.py` also update `SITE_URL` to the
   real login URL.

## Run order

```
env/bin/python 1_configure_sendgrid.py
```
Sets up the Email Account. Only succeeds where the SendGrid key authenticates.

```
env/bin/python 2_rotate_and_email_passwords.py   # with COUNT_ONLY = True
```
Touches nothing. Prints exactly who would be affected — **read this list
before proceeding**, especially on an environment with more users than it
was last tested against.

```
env/bin/python 2_rotate_and_email_passwords.py   # COUNT_ONLY = False, SEND_EMAILS = False
```
Sets real passwords, previews email content, sends nothing. Safe dry run
against the real dataset.

```
env/bin/python 2_rotate_and_email_passwords.py   # SEND_EMAILS = True
```
The real send.

After confirming all emails arrived correctly, delete the generated
`password_audit_DO_NOT_SHARE.json` (gitignored, but don't leave it sitting
around regardless) — it's the only place the real passwords briefly exist
outside each recipient's own inbox.

## Guarantees baked into the password generation

- Every password is exactly 20 characters, alphanumeric, generated with
  Python's `secrets` module (cryptographically secure).
- Uniqueness across the whole batch is generated and **hard-verified before
  any account is touched** — if that check ever failed, the script aborts
  before setting or sending anything.
- User discovery is dynamic (queries `Employee` joined to `User` at runtime)
  rather than a hardcoded list, so it scales correctly to however many
  people actually exist on the target site.
