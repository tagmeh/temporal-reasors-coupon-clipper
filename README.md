# Reasors.com Digital Coupon Clipper (Unofficial)

**This project is an unofficial tool and is not affiliated with, endorsed by, or related to Reasors.com or Reasor's Foods in any way.**

## Use Case

This repository provides a [Temporal](https://temporal.io/) workflow to automate the clipping of digital coupons from [Reasors.com](https://reasors.com). The workflow is designed to handle multiple accounts, securely storing credentials and automating the coupon clipping process.

## Setup

### 1. Clone the Repository

```sh
git clone https://github.com/tagmeh/temporal-reasors-coupon-clipper.git
cd temporal-reasors-coupon-clipper
```

### 2. Setup your env


### 3. Install Dependencies
Install Python 3.12 and then install dependencies:
```sh
pip install -r requirements.txt
# or, if using pipenv:
pipenv install
```

### 4. Configure Environment Variables
Rename `example.env` to `.env`
Set a value for `DECRYPTION_MASTER_KEY`. This is your secret key for encrypting/decrypting passwords. Any password string will do, consider making it long.

### 5. Encrypt Your Password
To add your Reasors.com account:
1. Run the password encryption script:
   ```sh
   python encrypt_password.py
   ```
2. The first time you run it, if `PASSWORD_SALT_BASE64` is empty, it will generate a salt and print it. Copy this value into your `.env` as `PASSWORD_SALT_BASE64`.
3. Enter your Reasors.com password (in plaintext) when prompted. The script will output an encrypted password.
4. Copy the encrypted password.

### 6. Add Your Account (THIS IS CHANGING TO USE A DATABASE. PENDING REVISIONS.)
Edit `accounts.json` (see `accounts-example.json`):
```json
{
  "accounts": [
    {
      "username": "your-email@example.com",
      "password": "paste-your-encrypted-password-here"
    }
  ]
}
```
You can add multiple accounts if desired.

### 7. Run the Worker and Workflow
If you need to set up your local Temporal development server: https://learn.temporal.io/getting_started/python/dev_environment/

Make sure the Temporal server is running.
Start the Temporal worker:
From the top level:
```shell
python run_worker.py
```

In a separate terminal (or a new tab), start the workflow:
```shell
python run_workflow.py
```

The parent workflow will create a child workflow for each account in `accounts.json`, clipping all available coupons for each.

### How It Works
- Credentials are securely encrypted and decrypted only at runtime.
- The parent workflow (`ClipCouponsWorkflow`) spawns a child workflow (`ClipCouponsChildWorkflow`) for each account.
- Each child workflow logs in, fetches available coupons, and clips them.

### Future Features
- Save clipped coupons to a database.
- Track and update when a user redeems a coupon, per user.
- Add built-in scheduling to the worker (instead of relying on the Temporal GUI).
--- 
**Disclaimer:**
This project is for educational and personal use only. It is not affiliated with, endorsed by, or related to Reasors.com or Reasor's Foods. Use at your own risk.