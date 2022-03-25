import csv
import sys
from datetime import date

import boto3
from botocore.exceptions import ClientError

# Fancy colouring
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def write_csv(result):
    """
    Writes the results to a .csv file.

    Args:
        (list) result: what you want written to the file

    """
    today = date.today()
    outputfilename = "accounts-sso-status-" + today.strftime("%d%m%Y") + ".csv"
    outputfile = csv.writer(open(outputfilename, "w+"))
    for res in result:
        outputfile.writerow(res)
    print()
    print(bcolors.HEADER + "Wrote to output file " + bcolors.UNDERLINE + outputfilename + bcolors.ENDC)

def main():
        
    # Get input from the user
    start_msg = """

                This script will process accounts in a line separated file and output whether or not the account is under AWS SSO.
                Results are written to a .csv file in the current directory.

                For each account, it will:
                * Output the AWSO SSO status, i.e if it is under AWS SSO or not
                
                Note that the IAM role *must* exist in ALL accounts for this script to execute properly without errors.
                If this role does not exist for the account, the status will be deemed as 'Unknown'.
    
    """

    print(bcolors.HEADER + start_msg + bcolors.ENDC)
    role = input('Enter IAM Role to be used e.g. SomeAdmin, press Enter to use default of `SomeAdmin`: ')
    if role == "":
        role = "SomeAdmin" # Default role
    aws_accounts_input = input('Enter name of file containing AWS accounts to process e.g. accounts.txt: ')

    print()
    print(bcolors.HEADER + "Going through all accounts in the file..." + bcolors.ENDC)  

    # Prepare CSV file results
    errorCount = 0
    successCount = 0
    result = []
    result.append(['AccountId', 'AccountAlias', 'AWS SSO', 'Errors'])

    # Open the file and read all lines
    file = open(aws_accounts_input, 'r')
    lines = file.readlines()
    i = 0
    n = len(lines)
    for line in lines:
        account = line.strip()
        account_result, success, errors, i = process_account(i, n, account, role)
        result.extend(account_result)
        successCount = successCount + success
        errorCount = errorCount + errors

    # Print out results (success and failure counts)
    print()
    print(bcolors.HEADER + "... and done going through all accounts" + bcolors.ENDC)
    print()
    print(bcolors.OKGREEN + str(successCount) + " Successful ✔️ " + bcolors.ENDC)
    print(bcolors.FAIL + str(errorCount) + " Error(s) ❗ " + bcolors.ENDC)
    
    # Write the results to a CSV file
    write_csv(result)
    
    # Print out the success troll
    done_msg = """

                CSV file written!

                    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓                    
                ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▒▒                
            ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▒▒▓▓▓▓▓▓            
          ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓          
          ▓▓▓▓▓▓░░░░░░░░▓▓▓▓▓▓░░░░░░░░▓▓▓▓▓▓          
        ▓▓▓▓▓▓░░░░░░░░░░░░▓▓░░░░░░░░░░░░▓▓▓▓▓▓        
    ▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▓▓▓▓▓▓▓▓    
  ▓▓░░░░▓▓▓▓░░░░        ░░░░░░        ░░░░▓▓▓▓░░░░▓▓  
▓▓░░░░░░▓▓▓▓░░    ████    ░░    ████    ░░▓▓▓▓░░░░░░▓▓
▓▓░░░░░░▓▓▓▓░░  ████  ██  ░░  ████  ██  ░░▓▓▓▓░░░░░░▓▓
▓▓░░░░░░▓▓▓▓░░  ████████  ░░  ████████  ░░▓▓▓▓░░░░░░▓▓
▓▓░░░░░░░░▓▓░░    ████    ░░    ████    ░░▓▓░░░░░░░░▓▓
▓▓░░░░░░▓▓▓▓▓▓░░        ░░░░░░        ░░▓▓▓▓▓▓░░░░░░▓▓
  ▓▓░░▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▓▓▓▓░░▓▓  
    ▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▓▓▓▓▓▓    
      ▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▓▓      
      ▓▓░░░░░░▓▓░░░░░░░░░░░░░░░░░░░░░░▓▓░░░░░░▓▓      
      ▓▓░░░░░░░░▓▓░░░░░░░░░░░░░░░░░░▓▓░░░░░░░░▓▓      
        ▓▓░░░░░░░░▓▓▓▓░░░░░░░░░░▓▓▓▓░░░░░░░░▓▓        
        ▓▓░░░░░░░░░░░░▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░▓▓        
          ▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░▓▓          
            ▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░▓▓            
              ▓▓▓▓░░░░░░░░░░░░░░░░░░▓▓▓▓              
                  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓                  
                 
    """
    print(bcolors.OKGREEN + done_msg + bcolors.ENDC)

def process_account(i, n, account_id, role):
    """
    Given i, n, account_id and role, returns aws sso status, success and failure counts, and status of progress
    """

    # Print a nice progress bar
    print_progress(i, n)
    i = i + 1

    result = []
    successCount = 0
    errorCount = 0

    client = boto3.client('sts')
    rolearn = 'arn:aws:iam::' + account_id + ':role/'+ role

    try:
        # Assume the role, if the role does not exist, this will simply fail
        response = client.assume_role(RoleArn=rolearn, RoleSessionName='accounts-sso-status-script')
        session = boto3.Session(aws_access_key_id=response['Credentials']['AccessKeyId'],aws_secret_access_key=response['Credentials']['SecretAccessKey'],aws_session_token=response['Credentials']['SessionToken'])
        
        # Get Alias and SAML providers
        alias, awssso, saml, samlinfo = get_alias_and_saml_providers(session)

        # Store results
        result.append([account_id, alias, awssso, "None"])
        successCount = successCount + 1

    except ClientError as err:
        result.append([account_id, "Unknown", "Unknown", str(err)])
        errorCount = errorCount + 1

    return result, successCount, errorCount, i

def print_progress(i, n):
    """
    Given i as current progress and n as the maximum value,
    this prints a fancy progress bar

    Args:
        (int) i: current progress
        (int) n: max value
    """
    sys.stdout.write('\r' + bcolors.HEADER)
    j = (i + 1) / n
    sys.stdout.write("[%-40s] %d%%" % ('='*int(40*j), 100*j))
    sys.stdout.flush()

def get_alias_and_saml_providers(session):
    """
    Given an iam client session, returns tuple of results

    Args:
        (class) boto3 Session: the boto3 session

    Returns:
        (tuple) tuple: alias, awssso, saml and samlinfo
    """
    iam = session.client('iam')

    # Get Alias
    alias = iam.list_account_aliases()
    if 'AccountAliases' in alias:
        if len(alias['AccountAliases']) == 1:
            alias = alias['AccountAliases'][0]
        else:
            alias = "No Alias"

    awssso = "No"
    saml = "No"
    samlinfo = []

    # Get SAML providers
    identityprovider = iam.list_saml_providers()
    if identityprovider['SAMLProviderList']:
        for provider in identityprovider['SAMLProviderList']:
            samlinfo.append([provider['Arn']])
            if "AWSSSO" in provider['Arn']:
                awssso = "Yes"
            saml = "Yes"

    return alias, awssso, saml, samlinfo

if __name__ == "__main__":
    main()
