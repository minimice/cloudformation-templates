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
    outputfilename = "account-ssoV2-info-" + today.strftime("%d%m%Y") + ".csv"
    outputfile = csv.writer(open(outputfilename, "w+"))
    for res in result:
        outputfile.writerow(res)
    print()
    print(bcolors.HEADER + "Wrote to output file " + bcolors.UNDERLINE + outputfilename + bcolors.ENDC)

def main():
        
    # Get input from the user
    start_msg = """

                This script will retrieve all accounts under an OU.  Results are written to a .csv file in the current directory.

                For each account, it will:
                * List users with 'AdministratorAccess' policy
                * Indicate if the account has AWS SSO and other SAML integrations
                
                Note that the IAM role *must* exist in ALL accounts under this OU for this script to execute properly without errors.
                If this role does not exist for the account, all results for that account will be deemed as 'Unknown'.
    
    """

    print(bcolors.HEADER + start_msg + bcolors.ENDC)
    role = input('Enter IAM Role to be used e.g. SomeAdmin, press Enter to use default of `SomeAdmin`: ')
    if role == "":
        role = "SomeAdmin" # Default role
    parent_raw = input('Enter OU ID(s) separated by spaces e.g. ou-ejdd-me3dd1mm ou-ejdd-no1rr1mm: ')

    parent_list = parent_raw.split()

    print()
    all_ou_list = []

    org = boto3.client('organizations')
    # Get OU full list
    for parent in parent_list:
        print(bcolors.HEADER + "Getting OU list starting at '" + parent + "'..." + bcolors.ENDC)
        ou_list = get_ou_list(org, parent, "")
        ou_name = get_ou_name(org, parent)
        ou_list.append({"Name": ou_name, "Id": parent})
        print(bcolors.HEADER + "Will go through all accounts listed under these OUs..." + bcolors.ENDC)
        for ou in ou_list:
            print(bcolors.OKCYAN + ou["Name"] + bcolors.ENDC)
        all_ou_list.extend(ou_list)
    print(bcolors.HEADER + "... and that's the end of the OU list" + bcolors.ENDC)
    
    # Prepare CSV file results
    errorCount = 0
    successCount = 0
    result = []
    result.append(['OU Name', 'OU ID', 'AccountId', 'AccountName', 'User(s)','Count of User(s)','AWS SSO', 'SAML integration', 'SAML additional info', 'Errors'])

    # Go through all the OUs in the list
    print()
    print(bcolors.HEADER + "Going through all accounts under every OU in the OU list..." + bcolors.ENDC)

    # Process each ou, and print out a progress bar while doing it
    i = 0
    n = len(all_ou_list)
    for ou in all_ou_list:
        ou_result, success, errors, i = process_ou(i, n, org, ou["Id"], ou["Name"], role)
        result.extend(ou_result)
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
    
        ░░░░░▄▄▄▄▀▀▀▀▀▀▀▀▄▄▄▄▄▄░░░░░░░
        ░░░░░█░░░░▒▒▒▒▒▒▒▒▒▒▒▒░░▀▀▄░░░░
        ░░░░█░░░▒▒▒▒▒▒░░░░░░░░▒▒▒░░█░░░
        ░░░█░░░░░░▄██▀▄▄░░░░░▄▄▄░░░░█░░
        ░▄▀▒▄▄▄▒░█▀▀▀▀▄▄█░░░██▄▄█░░░░█░
        █░▒█▒▄░▀▄▄▄▀░░░░░░░░█░░░▒▒▒▒▒░█
        █░▒█░█▀▄▄░░░░░█▀░░░░▀▄░░▄▀▀▀▄▒█
        ░█░▀▄░█▄░█▀▄▄░▀░▀▀░▄▄▀░░░░█░░█░
        ░░█░░░▀▄▀█▄▄░█▀▀▀▄▄▄▄▀▀█▀██░█░░
        ░░░█░░░░██░░▀█▄▄▄█▄▄█▄████░█░░░
        ░░░░█░░░░▀▀▄░█░░░█░█▀██████░█░░
        ░░░░░▀▄░░░░░▀▀▄▄▄█▄█▄█▄█▄▀░░█░░
        ░░░░░░░▀▄▄░▒▒▒▒░░░░░░░░░░▒░░░█░
        ░░░░░░░░░░▀▀▄▄░▒▒▒▒▒▒▒▒▒▒░░░░█░
        ░░░░░░░░░░░░░░▀▄▄▄▄▄░░░░░░░░█░░
    
    """
    print(bcolors.OKGREEN + done_msg + bcolors.ENDC)

def process_ou(i, n, org, ou_id, ou_name, role):
    """
    Given i, n, org, ou_id, ou_name and role, returns ou information, success, failure count, and status of progress
    """

    # Print a nice progress bar
    print_progress(i, n)
    i = i + 1

    # Get accounts under the OU
    accounts = org.list_accounts_for_parent(ParentId=ou_id)
    results = accounts['Accounts']

    while "NextToken" in accounts:
        accounts = org.list_accounts_for_parent(ParentId=ou_id,NextToken=accounts["NextToken"])
        results.extend(accounts["Accounts"])

    result = []
    successCount = 0
    errorCount = 0

    # Go through each account in the OU
    for a in results:

        client = boto3.client('sts')
        account_id = a['Id']
        account_name = a['Name']
        rolearn = 'arn:aws:iam::' + account_id + ':role/'+ role

        try:
            # Assume the role, if the role does not exist, this will simply fail
            response = client.assume_role(RoleArn=rolearn, RoleSessionName='accounts-sso-summary-script')
            session = boto3.Session(aws_access_key_id=response['Credentials']['AccessKeyId'],aws_secret_access_key=response['Credentials']['SecretAccessKey'],aws_session_token=response['Credentials']['SessionToken'])
            
            # Get users who are admin
            adminUsers = get_admin_users(session)

            # Get SAML providers
            awssso, saml, samlinfo = get_saml_providers(session)

            # Store results
            result.append([ou_name, ou_id, account_id, account_name, list(adminUsers), len(adminUsers), awssso, saml, samlinfo, "None"])
            # print(bcolors.OKGREEN + "Accessing account '" + account_name + "' OK" + bcolors.ENDC)
            successCount = successCount + 1

        except ClientError as err:
            result.append([ou_name, ou_id, account_id, account_name, "Unknown", "Unknown", "Unknown", "Unknown", "Unknown", str(err)])
            # print(bcolors.FAIL + "Unable to access account '" + account_name + "'" + bcolors.ENDC + ", Error: " + str(err))
            errorCount = errorCount + 1
            continue

    return result, successCount, errorCount, i

def get_ou_name(client, parent):
    """
    Given client and parent id, returns the name of the OU

    Args:
        (class) client: the boto3 client
        (str) parent: OU ID, starts with 'r-' for root and 'ou-' for an OU
    """
    ou_name = ""
    if parent.startswith("r-"): # Root
        ou_name = "Root"
    else:
        # Find the name
        unit_name = client.describe_organizational_unit(
            OrganizationalUnitId=parent
        )
        ou_name = unit_name["OrganizationalUnit"]["Name"]
    return ou_name

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

def get_saml_providers(session):
    """
    Given an iam client session, returns tuple of results

    Args:
        (class) boto3 Session: the boto3 session

    Returns:
        (tuple) tuple: awssso, saml and samlinfo
    """
    iam = session.client('iam')

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

    return awssso, saml, samlinfo

def get_admin_users(session):
    """
    Given an iam client session, returns all admin users

    Args:
        (class) boto3 Session: the boto3 session

    Returns:
        (set) adminUsers: list of unique admin users
    """
    iam = session.client('iam')
    adminUsers = set() # We only want unique users

    # Get users who are admin
    users = iam.list_users()
    for user in users['Users']:
        policies = iam.list_attached_user_policies(UserName=user['UserName'])
        for policy in policies['AttachedPolicies']:
            if policy['PolicyName'] == 'AdministratorAccess':
                adminUsers.add("[" + user['UserName'] + "]")

    # Get groups which are admin and add users who are members of the admin group
    groups = iam.list_groups()
    if groups['Groups']:
        for group in groups['Groups']:
            gpolicy = iam.list_attached_group_policies(GroupName=group['GroupName'])
            for poli in gpolicy['AttachedPolicies']:
                if poli['PolicyName'] == 'AdministratorAccess':
                    us = iam.get_group(GroupName=group['GroupName'])
                    for u in us['Users']:
                        adminUsers.add("[" + u['UserName'] + "]")
    
    return adminUsers

def get_ou_list(client, parent_id, prefix):
    """
    Given a parent ID, this is a recursive function that returns *all* OUs as a list
    under the parent ID.

    Args:
        (str) parent_id: the id of the OU.

    Returns:
        (list) result: the full list of OUs under the parent and its children.
    """

    ou_list = []
    olist = client.list_organizational_units_for_parent(
        ParentId=parent_id, MaxResults=20
    )

    # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/organizations.html#Organizations.Client.list_organizational_units_for_parent
    # Note:
    # Always check the NextToken response parameter for a null value when calling a List* operation.
    # These operations can occasionally return an empty set of results even when there are more results available.
    # The NextToken response parameter value is null only when there are no more results to display.

    if not prefix:
        prefix = get_ou_name(client, parent_id) + " > "
    else:
        prefix = prefix + " > "
    
    while "NextToken" in olist:

        for ou in olist["OrganizationalUnits"]:
            ou_list.append({"Name": prefix + ou["Name"], "Id": ou["Id"]})

        olist = client.list_organizational_units_for_parent(
            ParentId=parent_id, MaxResults=20, NextToken=olist["NextToken"]
        )

    for ou in olist["OrganizationalUnits"]:
        ou_list.append({"Name": prefix + ou["Name"], "Id": ou["Id"]})

    if not ou_list:
        return ou_list # Empty list

    for ou in ou_list:
        ou_list.extend(get_ou_list(client, ou["Id"], ou["Name"]))

    return ou_list


if __name__ == "__main__":
    main()
