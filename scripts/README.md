# AWS Scripts

Scripts in this folder are outlined in the following table:

| Script | Purpose |
| ----------- | ----------- |
| `accounts-sso-summary.py` | Lists users with Administrative access policy and AWS SSO and SAML integrations if any.  
| `accounts-sso-status.py` | Lists accounts indicating if they have AWS SSO enabled or not.

## accounts-sso-summary.py
Lists users with Administrative access policy and AWS SSO and SAML integrations if any.

#### Requirements

A role is assumed in order to read each target account, therefore this specified role *MUST* exist on all accounts, otherwise it will fail with errors.

#### Running the script

The script will ask for the role to be assumed on the accounts and which OU id(s) to use.  Multiple OU id(s) are accepted.  The OU id(s) are passed in as a space separated string.  All accounts listed under all OUs under each OU ID will be retrieved using the role in order to obtain details of that account.

To run this script, execute the following:

```
$ pip install -r requirements.txt
$ python accounts-sso-summary.py
```

### Output

The script will output a csv file `account-ssoV2-info-[date].csv` in the directory where the script is run.

## accounts-sso-status.py
Lists accounts indicating if they have AWS SSO enabled or not.

#### Requirements

A role is assumed in order to read each target account, therefore this specified role *MUST* exist on all accounts, otherwise it will fail with errors.

#### Running the script

The script will ask for the role to be assumed on the accounts and the name of the file containing the AWS accounts.  The file must be a line separated file.

To run this script, execute the following:

```
$ pip install -r requirements.txt
$ python accounts-sso-status.py
```

### Output

The script will output a csv file `accounts-sso-status-[date].csv` in the directory where the script is run.
