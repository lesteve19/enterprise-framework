import boto3
import botocore
import json
import sys
from string import Template
from jira import JIRA
from botocore.exceptions import ClientError



#------------------------------------#
#----------GLOBAL VARIABLES----------#
#------------------------------------#

region = "us-east-2"
project = sys.argv[1]
comp_table = f'{project}-competencies'
proj_table = f'{project}-projects'
secret_name = "jira_token"
db_client = boto3.client('dynamodb', region_name=region)
sec_client = boto3.client('secretsmanager', region_name=region)
jira_server = "https://keepitsts.atlassian.net"
jira_user = "steven.lecompte@simpletechnology.io"
jira_proj_id = 10069


def jira_conn():
    try:
        get_secret_value_response = sec_client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e

    api_token = get_secret_value_response['SecretString']
    api_token = json.loads(api_token)
    jira = JIRA(server=jira_server, basic_auth=(jira_user, api_token["api_token"]))

    return jira


jira = jira_conn()


issue_dict = {
    'project': {'id': jira_proj_id},
    'summary': 'Updates from jira-python',
    'description': 'Yeah buddy',
    'issuetype': {'name': 'Story'},
    'labels': ["entfrm-availability", "entfrm-compute"],
}

issues = jira.search_issues("project = 'ENTFRM' ORDER BY created ASC")
for issue in issues:
    issue_info = jira.issue(issue)
    issue_type = issue_info.fields.issuetype
    issue_status = issue_info.fields.status
    print(f'{issue} status is {issue_status} and has a type of {issue_type}')
    if issue.fields.issuetype == "Story"
        issue.update(fields=issue_dict)





# jira.create_issue(fields=issue_dict)


# projects = jira.projects()
# print(projects)

# for project in projects:
#     print(project)




# core_list = open("core.csv").read().splitlines()
# for l in core_list:
#     comp_itself = l.split(',', 1)[0]
#     comp_projects = l.split(',', 1)[1]
#     print("-------------------------------------------------------")
#     print(f'{comp_itself} relies on these projects: {comp_projects}')
#     print("-------------------------------------------------------")


# onlycomps = []
# for t in comp_list:
#     onlycomps.append(t["compname"])
#     if t["compname"] not in core_list:
#         print(f'REMOVING {t["compname"]} from table, as it is no longer in the primary comp list')
#         db_client.delete_item(
#             TableName = comp_table,
#             Key = {
#                 "competency": {
#                     "S": t["compname"]
#                 }
#             }
#         )


#----------------------------------------#
#----------TABLE CONFIGURATIONS----------#
#----------------------------------------#

#-----Read Competencies table and format list-----#
# def get_comps(client):
#     comp_map = []
#     comp_contents = client.scan(TableName=comp_table)
#     for row in comp_contents['Items']:
#         comp = {}
#         compname = row["competency"]["S"]
#         action = row["action"]["S"]
#         category = row["category"]["S"]
#         currentpoints = row["current-points"]["N"]
#         integration = row["integration"]["S"]
#         maxpoints = row["max-points"]["N"]
#         sector = row["sector"]["S"]
#         solution = row["solution"]["S"]
#         comp["compname"]=compname
#         comp["action"]=action
#         comp["category"]=category
#         comp["currentpoints"]=currentpoints
#         comp["integration"]=integration
#         comp["maxpoints"]=maxpoints
#         comp["sector"]=sector
#         comp["solution"]=solution
#         comp_map.append(comp)

#     return comp_map


#-----Check that all comps are populated in the table-----#
# comp_list = get_comps(db_client)
# core_list = open("comp_list.txt").read().splitlines()
# onlycomps = []
# for t in comp_list:
#     onlycomps.append(t["compname"])
#     if t["compname"] not in core_list:
#         print(f'REMOVING {t["compname"]} from table, as it is no longer in the primary comp list')
#         db_client.delete_item(
#             TableName = comp_table,
#             Key = {
#                 "competency": {
#                     "S": t["compname"]
#                 }
#             }
#         )






# for entry in core_list:
#     if entry not in onlycomps:
#         print(f'POPULATING {entry}')
#         components = entry.split('-')
#         data = dict(
#             sector = components[0],
#             category = components[1],
#             action = components[2],
#             solution = components[3],
#             integration = components[4],
#         )

#         with open('comp_table_template.json', 'r') as json_file:
#             content = ''.join(json_file.readlines())
#             template = Template(content)
#             configuration = json.loads(template.substitute(data))
#             db_client.put_item(
#                 TableName = comp_table,
#                 Item = configuration
#             )

#     else:
#         print(f'.....{entry} .....already exists')
#         continue
    
    

# #-----Read Projects table and format list-----#
# def get_projs(client):
#     proj_map = []
#     proj_contents = client.scan(TableName=proj_table)
#     for row in comp_contents['Items']:
#         print("DO STUFF")






# #-----Calculate points-----#
# current_points = []
# total_points = []
# comp_list = get_comps(db_client)
# sector_list = []
# s_list = []

# for comp in comp_list:
#     if comp["sector"] not in sector_list:
#         sector_list.append(comp["sector"])
#         sector_dict = {"sector": comp["sector"], "current": comp["currentpoints"], "max": comp["maxpoints"], "total": 1}
#         s_list.append(sector_dict)
#     else:
#         for s in s_list:
#             if s["sector"] == comp["sector"]:
#                 newcurrent = int(s["current"])+int(comp["currentpoints"])
#                 newmax = int(s["max"])+int(comp["maxpoints"])
#                 newtotal = s["total"]+1
#                 s.update({"sector": comp["sector"], "current": int(newcurrent), "max": int(newmax), "total": int(newtotal)})
#     current_points.append(int(comp["currentpoints"]))
#     total_points.append(int(comp["maxpoints"]))


# for sec in s_list:
#     per = int(sec["current"])/int(sec["max"])
#     print("-----------------------------------------------")
#     print("-----------------------------------------------")
#     print(f'{sec["sector"].upper()} SECTOR')
#     print(f'{sec["sector"]} has {sec["total"]} core competencies')
#     print(f'Current {sec["sector"]} points:  {sec["current"]}')
#     print(f'Total {sec["sector"]} points:    {sec["max"]}')
#     print(f'{sec["sector"]} percentage:  {round(per*100,2)}%')

# cp = sum(current_points)
# tp = sum(total_points)
# pp = cp/tp
# percent = round(pp*100,2)

# print("-----------------------------------------------")
# print("-----------------------------------------------")
# print("-----------------------------------------------")
# print("-----------------------------------------------")
# print("TOTALS")
# print(f'Total core competencies:  {len(comp_list)}')
# print(f'Current points achieved:  {cp}')
# print(f'Total possible points:    {tp}')
# print(f'Total percentage:         {percent}%')
# print("-----------------------------------------------")
# print("-----------------------------------------------")