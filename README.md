# Reasors Digital Coupon Clipper Temporal Workflow

**This project is an unofficial tool and is not affiliated with, endorsed by, or related to Reasors.com or Reasor's Foods in any way.**

## Use Case

This repository provides a [Temporal](https://temporal.io/) workflow to automate the clipping of digital coupons from [Reasors.com](https://reasors.com). The workflow is designed to handle multiple accounts, securely storing credentials, clipping coupons for each account. 

## Setup

### 1. Clone the Repository

```sh
git clone https://github.com/tagmeh/temporal-reasors-coupon-clipper.git
cd temporal-reasors-coupon-clipper
````

### 2. Install Dependencies
Install Python 3.12 and install dependencies:
```sh
pip install -r requirements.txt
# or, if using pipenv:
pipenv install
```

### 3. Configure Environment Variables
Rename `example.env` to `.env`
Set a value for `DECRYPTION_MASTER_KEY`. This is your secret key for encrypting/decrypting passwords. Any password string will do, consider making it long.  
Update `SERVER_URL` to your Temporal server.

### 4. Encrypt Your Password/Add Accounts.
To add your Reasors.com account:
1. Run the password encryption script:
   ```sh
   python -m app.scripts.encrypt_password
   ```
2. The first time you run it, if `PASSWORD_SALT_BASE64` is empty, it will generate a salt and print it. Copy this value into your `.env` as `PASSWORD_SALT_BASE64`.
3. Enter your Reasors.com password (in plaintext) when prompted. The script will output an encrypted password.
4. Copy the encrypted password.


### 5. Run the Worker and Workflow
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

The parent workflow will create a child workflow for each account in the database (Account table), clipping all available coupons for each row/account in the table.

### How It Works
- Credentials are securely encrypted in the database, then decrypted only at runtime.
- The parent workflow (`ClipCouponsWorkflow`) spawns a child workflow (`ClipCouponsChildWorkflow`) for each account.
- Each child workflow logs in, fetches available coupons, and clips them.
- The savings happen when you scan your store loyalty card at checkout. Relevant coupons are automatically applied to the order. 


### Cancelled Features
- I had previously wanted to track savings over time, however the API doesn't indicate when you've used a coupon. So I've scrapped the database tables responsible for saving the clipped coupon and redeemed coupon data.
- The idea was floated to add an interface via Discord, but the only use-case would be to add more accounts. Who wants to send their plaintext password via Discord?
--- 
**Disclaimer:**
This project is for educational purposes to learn Temporal. It is not affiliated with, endorsed by, or related to Reasors.com or Reasor's Foods. Use at your own risk.